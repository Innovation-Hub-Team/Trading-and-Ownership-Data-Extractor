import asyncio
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple, List
import random

from playwright.async_api import async_playwright, Browser, Page, TimeoutError as PlaywrightTimeoutError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.base import init_db
from app.models import Company

# Initialize database
_, SessionLocal = init_db("sqlite:///data/financial_analysis.db")

# Constants
BASE_URL = "https://www.saudiexchange.sa/wps/portal/saudiexchange/companies/company-profile-main/"
PDF_DIR = Path("data/pdfs")
PDF_DIR.mkdir(parents=True, exist_ok=True)

# Statement type priorities (most preferred first)
STATEMENT_PRIORITIES = [
    "annual",
    "quarterly", 
    "interim",
    "financial",
    "report"
]

async def setup_stealth_browser():
    """Setup Playwright browser with stealth configuration from download_pdf_playwright.py."""
    playwright = await async_playwright().start()
    
    browser = await playwright.chromium.launch(
        headless=False,  # Start with non-headless for testing
        args=[
            '--no-sandbox',
            '--disable-blink-features=AutomationControlled',
            '--disable-dev-shm-usage',
            '--disable-extensions',
            '--no-first-run',
            '--disable-default-apps',
            '--disable-popup-blocking',
            '--disable-translate',
            '--disable-background-timer-throttling',
            '--disable-backgrounding-occluded-windows',
            '--disable-renderer-backgrounding',
            '--disable-features=TranslateUI',
            '--disable-ipc-flooding-protection',
            '--disable-web-security',
            '--disable-features=VizDisplayCompositor'
        ]
    )
    
    context = await browser.new_context(
        viewport={'width': 1920, 'height': 1080},
        user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        accept_downloads=True,
        locale='en-US',
        timezone_id='America/New_York',
        permissions=['geolocation'],
        extra_http_headers={
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0'
        }
    )
    
    # Add stealth scripts from download_pdf_playwright.py
    await context.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined,
        });
        
        Object.defineProperty(navigator, 'plugins', {
            get: () => [1, 2, 3, 4, 5],
        });
        
        Object.defineProperty(navigator, 'languages', {
            get: () => ['en-US', 'en'],
        });
        
        window.chrome = {
            runtime: {},
        };
        
        Object.defineProperty(navigator, 'permissions', {
            get: () => ({
                query: () => Promise.resolve({ state: 'granted' }),
            }),
        });
    """)
    
    return playwright, browser, context

async def navigate_to_company_profile(page: Page, symbol: str) -> bool:
    """Navigate to the company profile page using the working approach from download_annual_reports.py."""
    search_url = "https://www.saudiexchange.sa/wps/portal/saudiexchange/hidden/search/!ut/p/z0/04_Sj9CPykssy0xPLMnMz0vMAfIjo8ziTR3NDIw8LAz8DTxCnA3MDILdzUJDLAyNHI30C7IdFQEEx_vC/"
    await page.goto(search_url, wait_until="domcontentloaded", timeout=60000)
    print(f"Navigated to search page for symbol {symbol}")
    try:
        # Focus the input, fill the symbol, and submit search
        await page.wait_for_selector("#query-input", timeout=5000)
        await page.click("#query-input")
        await page.fill("#query-input", symbol)
        await page.wait_for_timeout(500)
        # Use only JS click to submit
        await page.evaluate("document.querySelector('div.srchBlueBtn').click()")
        await page.wait_for_timeout(2000)
        # Print all a.pageLink elements for debugging
        links = await page.query_selector_all("a.pageLink")
        print('--- <a.pageLink> elements on the page ---')
        for i, link in enumerate(links):
            text = (await link.text_content() or '').strip()
            href = await link.get_attribute('href')
            print(f'{i}: text="{text}", href="{href}"')
        print('--- end of <a.pageLink> debug ---')
        # Find and click the 'Visit Profile' button by text
        visit_links = []
        for link in links:
            text = (await link.text_content() or "").strip().lower()
            if text == "visit profile":
                visit_links.append(link)
        if not visit_links:
            print(f"❌ No 'Visit Profile' link found for symbol {symbol}")
            return False
        await visit_links[0].click()
        await page.wait_for_load_state('domcontentloaded')
        print(f"✅ Clicked 'Visit Profile' for symbol {symbol}")
        return True
    except Exception as e:
        print(f"❌ Search failed for {symbol}: {e}")
        return False

async def get_latest_annual_report(page: Page, symbol: str) -> Optional[Tuple[str, int]]:
    """Navigate to company profile and find the latest annual report PDF URL and its year - from download_annual_reports.py."""
    # Use the working navigation function
    if not await navigate_to_company_profile(page, symbol):
        return None
    print("On company profile page, waiting for content...")
    await page.wait_for_timeout(3000)  # Wait longer for the page to load tabs
    # Print all <li> elements' text for debugging
    tabs = await page.query_selector_all("li")
    # Robust: Find the 'FINANCIAL STATEMENTS AND REPORTS' tab by substring
    try:
        target_text = "financial statements and reports"
        for tab in tabs:
            tab_text = (await tab.text_content() or "").strip().lower()
            if target_text in tab_text:
                await tab.scroll_into_view_if_needed()
                await tab.click()
                print(f"✅ Clicked tab: {tab_text}")
                break
        else:
            print("❌ 'Financial Statements and Reports' tab not found by substring.")
            return None
    except PlaywrightTimeoutError:
        print("❌ Timeout while trying to find financial tab.")
        return None
    # Wait for the financial statements table to appear
    try:
        table_selector = "table:has-text('Annual')"
        await page.wait_for_selector(table_selector, timeout=10000)
        print("Financial statements table loaded.")
    except Exception as e:
        print(f"Could not find financial statements table: {e}")
        return None
    # Find the header row to get the years
    header_cells = await page.query_selector_all("table thead tr th")
    years = []
    for cell in header_cells:
        text = (await cell.text_content()).strip()
        if text.isdigit():
            years.append(int(text))
    if not years:
        print("No years found in table header.")
        return None
    
    # Find the 'Annual' row
    rows = await page.query_selector_all("table tbody tr")
    annual_row = None
    for row in rows:
        first_cell = await row.query_selector("td")
        if first_cell and (await first_cell.text_content()).strip().lower() == "annual":
            annual_row = row
            break
    if not annual_row:
        print("No 'Annual' row found in table.")
        return None
    
    # Find the cells for all years in the 'Annual' row
    annual_cells = await annual_row.query_selector_all("td")
    # The first cell is the label, so offset by 1
    # Go from left to right (most recent year to oldest)
    for i, year in enumerate(years):
        cell_index = i + 1  # offset by 1 for the label cell
        if cell_index >= len(annual_cells):
            continue
        cell = annual_cells[cell_index]
        pdf_link = await cell.query_selector("a[href$='.pdf']")
        if pdf_link:
            pdf_url = await pdf_link.get_attribute("href")
            if pdf_url:
                print(f"🎯 Found PDF URL for {symbol} {year} (most recent available): {pdf_url}")
                return pdf_url, year
    
    print("No PDF link found in any year in 'Annual' row.")
    return None

async def download_pdf_with_stealth(page: Page, pdf_url: str, symbol: str, year: int) -> bool:
    """Download PDF using the working stealth approach from download_pdf_playwright.py."""
    try:
        # Create filename
        filename = f"{symbol}_annual_{year}.pdf"
        pdf_path = PDF_DIR / filename
        
        # Check if already exists
        if pdf_path.exists():
            print(f"⚠️  {filename} already exists, skipping...")
            return True
        
        print(f"📥 Downloading {filename}...")
        
        # Prepend base URL if needed
        if not pdf_url.startswith("http"):
            pdf_url = f"https://www.saudiexchange.sa{pdf_url}"
        
        # Navigate to PDF URL with stealth (from download_pdf_playwright.py)
        response = await page.goto(pdf_url, wait_until='networkidle')
        
        # Check if we got a PDF
        content_type = response.headers.get('content-type', '')
        if 'pdf' in content_type.lower():
            print(f"✅ Successfully accessed PDF for {symbol}")
            
            # Download PDF content using the working method
            pdf_content = await page.evaluate("""
                async () => {
                    try {
                        const response = await fetch(window.location.href);
                        const arrayBuffer = await response.arrayBuffer();
                        return Array.from(new Uint8Array(arrayBuffer));
                    } catch (error) {
                        console.error('Error fetching PDF:', error);
                        return null;
                    }
                }
            """)
            
            if pdf_content:
                with open(pdf_path, 'wb') as f:
                    f.write(bytes(pdf_content))
                print(f"✅ Downloaded {filename} ({len(pdf_content)} bytes)")
                return True
            else:
                print(f"❌ Failed to get PDF content for {symbol}")
                return False
        else:
            print(f"❌ Did not get PDF content for {symbol} (Content-Type: {content_type})")
            return False
            
    except Exception as e:
        print(f"❌ Download error for {symbol}: {e}")
        return False

async def process_company_with_retry(browser: Browser, symbol: str, max_retries: int = 3) -> bool:
    """Process a single company with retry logic."""
    for attempt in range(max_retries):
        try:
            page = await browser.new_page()
            
            # Add human-like behavior
            await page.mouse.move(random.randint(100, 500), random.randint(100, 300))
            await asyncio.sleep(random.uniform(0.5, 1.5))
            
            # Find latest financial statement using working navigation
            result = await get_latest_annual_report(page, symbol)
            if not result:
                await page.close()
                if attempt < max_retries - 1:
                    print(f"🔄 Retrying {symbol} (attempt {attempt + 2}/{max_retries})...")
                    await asyncio.sleep(random.uniform(2, 5))
                    continue
                return False
            
            pdf_url, year = result
            
            # Download the PDF using working stealth method
            success = await download_pdf_with_stealth(page, pdf_url, symbol, year)
            await page.close()
            
            if success:
                return True
            elif attempt < max_retries - 1:
                print(f"🔄 Retrying {symbol} (attempt {attempt + 2}/{max_retries})...")
                await asyncio.sleep(random.uniform(2, 5))
            
        except Exception as e:
            print(f"❌ Error processing {symbol} (attempt {attempt + 1}): {e}")
            await page.close()
            if attempt < max_retries - 1:
                await asyncio.sleep(random.uniform(2, 5))
    
    return False

async def download_all_financial_statements():
    """Download the most recent financial statements for all companies."""
    session = SessionLocal()
    
    try:
        # Get all company symbols
        companies = session.execute(select(Company.symbol)).scalars().all()
        print(f"📋 Found {len(companies)} companies to process")
        
        # Setup browser with stealth configuration
        playwright, browser, context = await setup_stealth_browser()
        
        try:
            success_count = 0
            failed_count = 0
            
            for i, symbol in enumerate(companies, 1):
                print(f"\n{'='*50}")
                print(f"📊 Processing {symbol} ({i}/{len(companies)})")
                print(f"{'='*50}")
                
                success = await process_company_with_retry(browser, symbol)
                
                if success:
                    success_count += 1
                    print(f"✅ Successfully processed {symbol}")
                else:
                    failed_count += 1
                    print(f"❌ Failed to process {symbol}")
                
                # Add delay between companies
                if i < len(companies):
                    delay = random.uniform(3, 7)
                    print(f"⏳ Waiting {delay:.1f} seconds before next company...")
                    await asyncio.sleep(delay)
            
            # Summary
            print(f"\n{'='*50}")
            print(f"📊 DOWNLOAD SUMMARY")
            print(f"{'='*50}")
            print(f"✅ Successful: {success_count}")
            print(f"❌ Failed: {failed_count}")
            print(f"📈 Success Rate: {(success_count/(success_count+failed_count)*100):.1f}%")
            
        finally:
            await browser.close()
            await playwright.stop()
            
    finally:
        session.close()

if __name__ == "__main__":
    # Uncomment to download all reports
    asyncio.run(download_all_financial_statements())
    # # Test with a single company first
    # async def test_single_company():
    #     session = SessionLocal()
    #     try:
    #         # Test with SABIC
    #         symbol = "2010"
    #         print(f"🧪 Testing with {symbol}...")
    #         
    #         playwright, browser, context = await setup_stealth_browser()
    #         try:
    #             success = await process_company_with_retry(browser, symbol)
    #             print(f"Test result: {'✅ SUCCESS' if success else '❌ FAILED'}")
    #         finally:
    #             await browser.close()
    #             await playwright.stop()
    #     finally:
    #         session.close()
    # # Run the test
    # asyncio.run(test_single_company()) 