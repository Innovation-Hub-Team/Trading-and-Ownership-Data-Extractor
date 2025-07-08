"""Command-line interface for the financial analysis pipeline."""
import asyncio
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional
import click
from dotenv import load_dotenv
from sqlalchemy.orm import Session

from app.models.base import init_db
from app.models.models import Company
from app.scrapers.ownership import TadawulOwnershipScraper
from app.pdf.fetcher import TadawulPDFFetcher
from app.pdf.extractor import PDFExtractor
from app.calculator.reinvested import ReinvestedEarningsCalculator

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=os.getenv('LOG_LEVEL', 'DEBUG'),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize database
engine, SessionLocal = init_db(os.getenv('DATABASE_URL', 'sqlite:///data/financial_analysis.db'))

def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@click.group()
def cli():
    """Financial analysis pipeline CLI."""
    pass

@cli.command()
@click.option('--symbol', help='Company symbol to process (e.g., 2030)')
@click.option('--all', is_flag=True, help='Process all companies')
def run_pipeline(symbol: Optional[str], all: bool):
    """Run the complete pipeline for one or all companies."""
    if not symbol and not all:
        click.echo("Please specify either --symbol or --all")
        return

    # Get list of companies to process
    db = next(get_db())
    if symbol:
        companies = db.query(Company).filter(Company.symbol == symbol).all()
        if not companies:
            click.echo(f"Company with symbol {symbol} not found")
            return
    else:
        companies = db.query(Company).all()
        if not companies:
            click.echo("No companies found in the database.")
            return

    # Run the pipeline
    asyncio.run(run_pipeline_async(companies))

async def run_pipeline_async(companies: List[Company]):
    """Run the pipeline asynchronously for a list of companies."""
    # Initialize components
    ownership_scraper = TadawulOwnershipScraper(
        base_url=os.getenv('TADAWUL_BASE_URL', 'https://www.tadawul.com.sa'),
        request_delay=float(os.getenv('TADAWUL_REQUEST_DELAY', '1.0'))
    )
    
    pdf_fetcher = TadawulPDFFetcher(
        base_url=os.getenv('TADAWUL_BASE_URL', 'https://www.tadawul.com.sa'),
        storage_path=os.getenv('PDF_STORAGE_PATH', 'data/pdfs'),
        request_delay=float(os.getenv('TADAWUL_REQUEST_DELAY', '1.0'))
    )
    
    pdf_extractor = PDFExtractor(
        tesseract_cmd=os.getenv('TESSERACT_CMD', '/usr/local/bin/tesseract'),
        ocr_language=os.getenv('OCR_LANGUAGE', 'ara+eng')
    )
    
    db = next(get_db())
    calculator = ReinvestedEarningsCalculator(db)

    # Process each company
    async with ownership_scraper, pdf_fetcher:
        for company in companies:
            try:
                click.echo(f"\nProcessing {company.symbol} ({company.arabic_name})...")
                
                # 1. Scrape ownership data
                click.echo("Scraping ownership data...")
                ownership_data = await ownership_scraper.get_ownership_data(company.symbol)
                await ownership_scraper.save_ownership_data(db, ownership_data)
                
                # 2. Fetch latest annual report
                click.echo("Fetching latest annual report...")
                report_data = await pdf_fetcher.get_latest_annual_report(company.symbol)
                pdf_path = await pdf_fetcher.download_pdf(company.symbol, report_data)
                
                # 3. Extract retained earnings
                click.echo("Extracting retained earnings...")
                amount, method, confidence = pdf_extractor.extract_retained_earnings(pdf_path)
                pdf_extractor.save_retained_earnings(
                    db, company.id, report_data['year'],
                    amount, pdf_path, method, confidence
                )
                
                # 4. Calculate reinvested earnings
                click.echo("Calculating reinvested earnings...")
                calculator.calculate_reinvested_earnings(company.id, report_data['year'])
                
                click.echo(f"Successfully processed {company.symbol}")
                
            except Exception as e:
                logger.error(f"Error processing {company.symbol}: {e}")
                continue

@cli.command()
@click.option('--symbol', help='Company symbol to show results for')
@click.option('--all', is_flag=True, help='Show results for all companies')
def show_results(symbol: Optional[str], all: bool):
    """Show reinvested earnings results."""
    if not symbol and not all:
        click.echo("Please specify either --symbol or --all")
        return

    db = next(get_db())
    calculator = ReinvestedEarningsCalculator(db)
    
    # (--all) Check if any companies exist (if not using --symbol)
    if not symbol and db.query(Company).count() == 0:
        click.echo("No companies found in the database.")
        return

    # Get company ID if symbol is provided
    company_id = None
    if symbol:
        company = db.query(Company).filter(Company.symbol == symbol).first()
        if not company:
            click.echo(f"Company with symbol {symbol} not found")
            return
        company_id = company.id

    # Get and display results
    results = calculator.get_reinvested_earnings_summary(company_id)
    if not results:
        click.echo("No reinvested earnings results found.")
        return

    # Print results in a table format
    click.echo("\nReinvested Earnings Summary")
    click.echo("=" * 100)
    click.echo(f"{'Symbol':<10} {'Company':<30} {'Year':<6} {'Retained Earnings':>20} {'Ownership %':>12} {'Reinvested':>20}")
    click.echo("-" * 100)
    
    for r in results:
        click.echo(
            f"{r['symbol']:<10} "
            f"{r['arabic_name'][:28]:<30} "
            f"{r['year']:<6} "
            f"{r['retained_earnings']:>20,.2f} "
            f"{r['ownership_percentage']:>11.2f}% "
            f"{r['reinvested_earnings']:>20,.2f}"
        )

@cli.command()
@click.option("--save", is_flag=True, help="Save extracted data (companies) into the database (if not, print to stdout).")
@click.option("--playwright-browser", envvar="PLAYWRIGHT_BROWSER", default=None, help="Shared Playwright browser (optional).")
@click.option("--playwright-context", envvar="PLAYWRIGHT_CONTEXT", default=None, help="Shared Playwright context (optional).")
def extract_ownership(save, playwright_browser, playwright_context):
    """Extract (and optionally save) the foreign ownership table (companies) from the Tadawul foreign ownership page (https://www.saudiexchange.sa/wps/portal/saudiexchange/newsandreports/reports-publications/foreign-ownership?locale=ar). (This is a placeholder implementation; you'll need to inspect the page to get the correct selector and parsing logic.) (Note: You'll need to install Playwright (e.g. via pip install playwright) and run "playwright install" to download a browser.)"""
    async def _extract_ownership_async():
         scraper = TadawulOwnershipScraper(base_url=os.getenv("TADAWUL_BASE_URL", "https://www.tadawul.com.sa"), playwright_browser=playwright_browser, playwright_context=playwright_context)
         async with scraper as scraper:
             data = await scraper.get_foreign_ownership_table()
         if save:
             db = next(get_db())
             for item in data:
                 company = Company(symbol=item["symbol"], arabic_name=item["arabicName"], english_name=item["englishName"])
                 db.merge(company)
             db.commit()
             click.echo("Saved (merged) companies into the database.")
         else:
             click.echo("Extracted (foreign ownership) data (companies):")
             for item in data:
                 click.echo(f"Symbol: {item['symbol']} – Arabic Name: {item['arabicName']} – English Name: {item['englishName']} – Ownership %: {item['ownershipPercentage']}%")
    asyncio.run(_extract_ownership_async())

if __name__ == '__main__':
    cli() 