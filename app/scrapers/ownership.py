"""Module for scraping foreign ownership data from Tadawul.

This module provides both async and sync interfaces for scraping foreign ownership data
from Tadawul, with support for database integration and file-based output.

Example:
    # Async usage with database:
    async with TadawulOwnershipScraper(base_url="https://www.saudiexchange.sa") as scraper:
        data = await scraper.get_foreign_ownership_table()
        await scraper.save_ownership_data(db_session, data)

    # Sync usage for file output:
    scraper = TadawulOwnershipScraper(base_url="https://www.saudiexchange.sa")
    scraper.scrape_to_files(output_dir="data/ownership")
"""
import json
import csv
import logging
from datetime import date
from pathlib import Path
from typing import Optional, Dict, Any, List, Union
import aiohttp
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session
from playwright.async_api import async_playwright, TimeoutError
from playwright.sync_api import sync_playwright

from app.models.models import Company, OwnershipData

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TadawulOwnershipScraper:
    """Scraper for foreign ownership data from Tadawul.
    
    This class provides both async and sync interfaces for scraping foreign ownership data
    from Tadawul. It supports both database integration and file-based output.
    """
    
    def __init__(self, base_url: str, request_delay: float = 1.0, playwright_browser=None, playwright_context=None):
        """Initialize the scraper.
        
        Args:
            base_url: Base URL for Tadawul website
            request_delay: Delay between requests in seconds
            playwright_browser: Optional existing Playwright browser instance
            playwright_context: Optional existing Playwright context
        """
        self.base_url = base_url.rstrip('/')
        self.request_delay = request_delay
        self.session: Optional[aiohttp.ClientSession] = None
        self.playwright_browser = playwright_browser
        self.playwright_context = playwright_context
        self._launched_browser = False

    async def __aenter__(self):
        """Set up async session and browser with proper fingerprinting."""
        self.session = aiohttp.ClientSession()
        if self.playwright_browser is None:
            p = await async_playwright().start()
            self.playwright_browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-features=IsolateOrigins,site-per-process',
                ]
            )
            self._launched_browser = True
        
        if self.playwright_context is None:
            self.playwright_context = await self.playwright_browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
                locale='ar-SA',
                timezone_id='Asia/Riyadh',
                geolocation={'latitude': 24.7136, 'longitude': 46.6753},
                permissions=['geolocation'],
                extra_http_headers={
                    'Accept-Language': 'ar-SA,ar;q=0.9,en-US;q=0.8,en;q=0.7',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                }
            )
            await self.playwright_context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Clean up async resources."""
        if self.session:
            await self.session.close()
        if self._launched_browser and self.playwright_browser:
            await self.playwright_browser.close()

    async def get_foreign_ownership_table(self) -> list[dict]:
        """Scrape the foreign ownership table from Tadawul.
        
        Returns:
            List of dictionaries containing foreign ownership data for each company.
            
        Raises:
            ValueError: If the table cannot be found or no data is extracted.
            TimeoutError: If the page takes too long to load.
        """
        if not self.playwright_context:
            raise RuntimeError("Scraper must be used as an async context manager")

        page = await self.playwright_context.new_page()
        url = f"{self.base_url}/wps/portal/saudiexchange/newsandreports/reports-publications/foreign-ownership?locale=ar"
        logger.info(f"Navigating to {url}")
        
        try:
            await page.goto(url, wait_until="networkidle", timeout=60000)
            logger.info("Waiting for table to load...")
            await page.wait_for_selector("table tbody tr", timeout=30000)
            
            rows = await page.query_selector_all("table tbody tr")
            data = []
            
            for row in rows:
                cols = await row.query_selector_all("td")
                if len(cols) >= 5:
                    try:
                        entry = {
                            "symbol": (await cols[0].inner_text()).strip(),
                            "company_name": (await cols[1].inner_text()).strip(),
                            "foreign_ownership": (await cols[2].inner_text()).strip(),
                            "max_allowed": (await cols[3].inner_text()).strip(),
                            "investor_limit": (await cols[4].inner_text()).strip()
                        }
                        data.append(entry)
                        logger.debug(f"Extracted data for {entry['symbol']}")
                    except Exception as e:
                        logger.warning(f"Error processing row: {e}")
                        continue
            
            if not data:
                raise ValueError("No data was extracted from the table")
            
            logger.info(f"Successfully extracted data for {len(data)} companies")
            return data
            
        except TimeoutError:
            logger.error("Timeout while waiting for the table to load")
            raise
        finally:
            await page.close()

    async def save_ownership_data(self, db: Session, data: List[Dict[str, Any]]) -> List[OwnershipData]:
        """Save ownership data to the database.
        
        Args:
            db: Database session
            data: List of ownership data dictionaries
            
        Returns:
            List of created OwnershipData records
        """
        saved_records = []
        for entry in data:
            try:
                # Get or create company
                company = db.query(Company).filter_by(symbol=entry['symbol']).first()
                if not company:
                    logger.warning(f"Company with symbol {entry['symbol']} not found in database")
                    continue

                # Create ownership data record
                ownership_data = OwnershipData(
                    company_id=company.id,
                    scrape_date=date.today(),
                    ownership_percentage=float(entry['foreign_ownership'].replace('%', '').replace(',', '')),
                    source_url=f"{self.base_url}/market/company-profile/{entry['symbol']}"
                )

                db.add(ownership_data)
                saved_records.append(ownership_data)
                
            except Exception as e:
                logger.error(f"Error saving data for {entry['symbol']}: {e}")
                continue
        
        db.commit()
        for record in saved_records:
            db.refresh(record)
        
        return saved_records

    def scrape_to_files(self, output_dir: str = ".", debug: bool = False) -> None:
        """Synchronous method to scrape data and save to files.
        
        Args:
            output_dir: Directory where output files will be saved
            debug: If True, runs in visible mode and saves debug info
            
        Raises:
            ValueError: If the table cannot be found or no data is extracted
            TimeoutError: If the page takes too long to load
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        json_path = output_path / "foreign_ownership_data.json"
        csv_path = output_path / "foreign_ownership_data.csv"
        
        logger.info("Starting foreign ownership data scraping...")
        
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=not debug,  # Run in visible mode if debugging
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-features=IsolateOrigins,site-per-process',
                ]
            )
            
            context = browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
                locale='ar-SA',
                timezone_id='Asia/Riyadh',
                geolocation={'latitude': 24.7136, 'longitude': 46.6753},
                permissions=['geolocation'],
                extra_http_headers={
                    'Accept-Language': 'ar-SA,ar;q=0.9,en-US;q=0.8,en;q=0.7',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                }
            )
            
            context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """)
            
            page = context.new_page()
            
            try:
                url = f"{self.base_url}/wps/portal/saudiexchange/newsandreports/reports-publications/foreign-ownership?locale=ar"
                logger.info(f"Navigating to {url}")
                
                # Navigate with longer timeout and wait for network idle
                page.goto(url, wait_until="networkidle", timeout=120000)
                logger.info("Page loaded, waiting for content...")
                
                # Wait for any content to appear
                logger.info("Waiting for any table content...")
                try:
                    # First try waiting for the table
                    page.wait_for_selector("table", timeout=60000)
                    logger.info("Table element found")
                    
                    # Then wait for rows with a shorter timeout
                    page.wait_for_selector("table tbody tr", timeout=30000)
                    logger.info("Table rows found")
                except TimeoutError:
                    if debug:
                        # Save debug info
                        debug_path = output_path / "debug"
                        debug_path.mkdir(exist_ok=True)
                        page.screenshot(path=str(debug_path / "page.png"))
                        with open(debug_path / "page.html", "w", encoding="utf-8") as f:
                            f.write(page.content())
                        logger.info(f"Debug info saved to {debug_path}")
                    raise
                
                # Get all rows
                rows = page.query_selector_all("table tbody tr")
                logger.info(f"Found {len(rows)} rows in table")
                
                data = []
                for i, row in enumerate(rows, 1):
                    cols = row.query_selector_all("td")
                    if len(cols) >= 5:
                        try:
                            entry = {
                                "symbol": cols[0].inner_text().strip(),
                                "company_name": cols[1].inner_text().strip(),
                                "foreign_ownership": cols[2].inner_text().strip(),
                                "max_allowed": cols[3].inner_text().strip(),
                                "investor_limit": cols[4].inner_text().strip()
                            }
                            data.append(entry)
                            if i % 50 == 0:  # Log progress every 50 rows
                                logger.info(f"Processed {i} rows...")
                        except Exception as e:
                            logger.warning(f"Error processing row {i}: {e}")
                            continue
                
                if not data:
                    raise ValueError("No data was extracted from the table")
                
                logger.info(f"Successfully extracted data for {len(data)} companies")
                
                # Save as JSON
                logger.info(f"Saving data to {json_path}")
                with open(json_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                
                # Save as CSV
                logger.info(f"Saving data to {csv_path}")
                with open(csv_path, "w", newline='', encoding="utf-8") as f:
                    writer = csv.DictWriter(f, fieldnames=["symbol", "company_name", "foreign_ownership", "max_allowed", "investor_limit"])
                    writer.writeheader()
                    writer.writerows(data)
                
                logger.info("Data successfully saved to both JSON and CSV files")
                
            except TimeoutError:
                logger.error("Timeout while waiting for the table to load")
                raise
            except Exception as e:
                logger.error(f"Error during scraping: {e}")
                raise
            finally:
                context.close()
                browser.close()

if __name__ == "__main__":
    # Example usage with debug mode
    scraper = TadawulOwnershipScraper(base_url="https://www.saudiexchange.sa")
    scraper.scrape_to_files(debug=True)  # Enable debug mode to see the browser 