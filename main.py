#!/usr/bin/env python3
"""
Main script for the Financial Analysis System
Orchestrates the complete workflow: scraping → extraction → calculation → evidence
"""

import asyncio
import sys
from pathlib import Path

def main():
    """Main workflow for foreign investment analysis"""
    print("🚀 Starting Foreign Investment Analysis...")
    
    # Step 1: Extract retained earnings from PDFs
    print("\n📄 Step 1: Extracting retained earnings from PDFs...")
    extract_retained_earnings_all_pdfs.main()
    
    # Step 2: Calculate reinvested earnings
    print("\n🧮 Step 2: Calculating reinvested earnings...")
    calculate_reinvested_earnings.main()
    
    # Step 3: Generate evidence screenshots
    print("\n📸 Step 3: Generating evidence screenshots...")
    generate_evidence_screenshots.main()
    
    print("\n✅ Analysis complete! Files saved to:")
    print("   - Data: data/results/reinvested_earnings_results.csv")
    print("   - Screenshots: output/screenshots/")
    print("   - Excel exports: output/excel/")
    print("\n🌐 To view results:")
    print("   1. Start API: python src/api/evidence_api.py")
    print("   2. Start Frontend: cd frontend && npm start")
    print("   3. Open: http://localhost:3000")

if __name__ == "__main__":
    main() 