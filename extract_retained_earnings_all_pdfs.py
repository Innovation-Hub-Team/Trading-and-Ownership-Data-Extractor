#!/usr/bin/env python3
"""
Extract Retained Earnings from all PDFs using fast regex pattern matching.
This is much faster than chunking and using LLMs.
"""

import pdfplumber
import re
import json
from pathlib import Path
import sqlite3
from datetime import datetime

def extract_retained_earnings_from_lines(text: str):
    """
    Extract the first large number (likely retained earnings) that appears after 'Retained earnings' in the line.
    Skips small numbers (likely note references).
    """
    lines = text.splitlines()
    for line in lines:
        lowered = line.lower()
        for keyword in ["retained earnings", "الأرباح المحتجزة"]:
            pos = lowered.find(keyword)
            if pos != -1:
                # Find all numbers and their positions
                matches = list(re.finditer(r"[\d,]+\.?\d*", line))
                for m in matches:
                    if m.start() > pos:
                        value = float(m.group(0).replace(",", ""))
                        if value > 999:  # likely an actual value, not a footnote
                            return int(value)
    return None

def extract_retained_earnings_from_pdf(pdf_path):
    """
    Extract Retained Earnings from a PDF using regex patterns.
    Returns the best match found.
    """
    # Common patterns for Retained Earnings in financial statements
    patterns = [
        r'Retained\s+Earnings[:\s]*([\d,]+\.?\d*)',  # "Retained Earnings: 1,234.56"
        r'Retained\s+Earnings\s+([\d,]+\.?\d*)',     # "Retained Earnings 1,234.56"
        r'([\d,]+\.?\d*)\s+Retained\s+Earnings',     # "1,234.56 Retained Earnings"
        r'Retained\s+earnings[:\s]*([\d,]+\.?\d*)',  # lowercase variant
        r'الأرباح\s+المحتجزة[:\s]*([\d,]+\.?\d*)',   # Arabic: "الأرباح المحتجزة"
        r'الأرباح\s+المحتجزة\s+([\d,]+\.?\d*)',      # Arabic without colon
    ]
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            full_text = ""
            
            # Extract text from all pages
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    full_text += page_text + "\n"
            
            # Search for Retained Earnings patterns
            results = []
            for pattern in patterns:
                matches = re.finditer(pattern, full_text, re.IGNORECASE)
                for match in matches:
                    value = match.group(1)
                    # Clean the value (remove commas, convert to float)
                    clean_value = value.replace(',', '')
                    try:
                        numeric_value = float(clean_value)
                        results.append({
                            'pattern': pattern,
                            'raw_match': match.group(0),
                            'value': value,
                            'numeric_value': numeric_value,
                            'position': match.start()
                        })
                    except ValueError:
                        continue
            
            # Post-process lines containing 'Retained earnings'
            line_based_value = extract_retained_earnings_from_lines(full_text)
            # Prefer the line-based value if:
            # - regex found nothing, or
            # - regex best match is <= 999, or
            # - line-based value is larger than regex best match
            best_match = results[0] if results else None
            if line_based_value:
                if (not best_match) or (best_match['numeric_value'] <= 999) or (line_based_value > best_match['numeric_value']):
                    return {
                        'success': True,
                        'value': f"{line_based_value:,}",
                        'numeric_value': line_based_value,
                        'raw_match': 'Line-based extraction',
                        'total_matches': len(results),
                        'total_pages': len(pdf.pages),
                        'text_length': len(full_text)
                    }
            if best_match:
                return {
                    'success': True,
                    'value': best_match['value'],
                    'numeric_value': best_match['numeric_value'],
                    'raw_match': best_match['raw_match'],
                    'total_matches': len(results),
                    'total_pages': len(pdf.pages),
                    'text_length': len(full_text)
                }
            else:
                return {
                    'success': False,
                    'error': 'No Retained Earnings found',
                    'total_pages': len(pdf.pages),
                    'text_length': len(full_text)
                }
            
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def get_company_symbol_from_filename(filename):
    """Extract company symbol from PDF filename (e.g., '2010_annual_2024.pdf' -> '2010')"""
    return filename.split('_')[0]

def save_to_database(results):
    """Save results to SQLite database"""
    conn = sqlite3.connect('data/financial_analysis.db')
    cursor = conn.cursor()
    
    # Drop existing table if it exists and recreate with correct schema
    cursor.execute('DROP TABLE IF EXISTS retained_earnings')
    
    # Create table with correct schema
    cursor.execute('''
        CREATE TABLE retained_earnings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_symbol TEXT,
            pdf_filename TEXT,
            retained_earnings_value REAL,
            raw_match TEXT,
            total_matches INTEGER,
            total_pages INTEGER,
            text_length INTEGER,
            extraction_date TIMESTAMP,
            success BOOLEAN,
            error_message TEXT
        )
    ''')
    
    # Insert results
    for result in results:
        cursor.execute('''
            INSERT INTO retained_earnings 
            (company_symbol, pdf_filename, retained_earnings_value, raw_match, 
             total_matches, total_pages, text_length, extraction_date, success, error_message)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            result['company_symbol'],
            result['pdf_filename'],
            result.get('numeric_value'),
            result.get('raw_match'),
            result.get('total_matches'),
            result.get('total_pages'),
            result.get('text_length'),
            datetime.now(),
            result['success'],
            result.get('error')
        ))
    
    conn.commit()
    conn.close()

def main():
    pdf_dir = Path("data/pdfs")
    pdf_files = list(pdf_dir.glob("*.pdf"))
    
    if not pdf_files:
        print("No PDF files found in data/pdfs/")
        return
    
    print(f"Found {len(pdf_files)} PDF files to process")
    
    results = []
    successful_extractions = 0
    
    for i, pdf_file in enumerate(pdf_files, 1):
        print(f"\n[{i}/{len(pdf_files)}] Processing: {pdf_file.name}")
        
        company_symbol = get_company_symbol_from_filename(pdf_file.name)
        result = extract_retained_earnings_from_pdf(pdf_file)
        
        result['company_symbol'] = company_symbol
        result['pdf_filename'] = pdf_file.name
        
        if result['success']:
            successful_extractions += 1
            print(f"  ✓ Found: {result['value']} (numeric: {result['numeric_value']:,.0f})")
            print(f"  ✓ Raw match: {result['raw_match']}")
        else:
            print(f"  ✗ Error: {result.get('error', 'Unknown error')}")
        
        results.append(result)
    
    # Save results to JSON
    output_file = "retained_earnings_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    # Save to database
    save_to_database(results)
    
    # Print summary
    print(f"\n{'='*50}")
    print(f"EXTRACTION SUMMARY")
    print(f"{'='*50}")
    print(f"Total PDFs processed: {len(pdf_files)}")
    print(f"Successful extractions: {successful_extractions}")
    print(f"Success rate: {successful_extractions/len(pdf_files)*100:.1f}%")
    print(f"Results saved to: {output_file}")
    print(f"Results also saved to database: data/financial_analysis.db")
    
    # Show successful extractions
    if successful_extractions > 0:
        print(f"\nSuccessful extractions:")
        for result in results:
            if result['success']:
                print(f"  {result['company_symbol']}: {result['value']} ({result['numeric_value']:,.0f})")

if __name__ == "__main__":
    main() 