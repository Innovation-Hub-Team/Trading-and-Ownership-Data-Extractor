#!/usr/bin/env python3
"""
Test script to extract Retained Earnings from a single PDF using full-text search and regex.
This is a faster alternative to chunking and sending everything to an LLM.
"""

import pdfplumber
import re
import json
from pathlib import Path

def extract_retained_earnings_from_pdf(pdf_path):
    """
    Extract Retained Earnings from a PDF using full-text search and regex patterns.
    """
    print(f"Processing: {pdf_path}")
    
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
            for page_num, page in enumerate(pdf.pages):
                print(f"  Processing page {page_num + 1}/{len(pdf.pages)}")
                page_text = page.extract_text()
                if page_text:
                    full_text += page_text + "\n"
            
            print(f"  Total text length: {len(full_text)} characters")
            
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
                        print(f"    Could not convert '{value}' to number")
            
            # Also search for lines containing "Retained Earnings" for context
            retained_earnings_lines = []
            for line in full_text.split('\n'):
                if re.search(r'retained\s+earnings', line, re.IGNORECASE) or \
                   re.search(r'الأرباح\s+المحتجزة', line, re.IGNORECASE):
                    retained_earnings_lines.append(line.strip())
            
            return {
                'pdf_path': str(pdf_path),
                'total_pages': len(pdf.pages),
                'total_text_length': len(full_text),
                'regex_matches': results,
                'context_lines': retained_earnings_lines[:10],  # First 10 lines for context
                'best_match': results[0] if results else None
            }
            
    except Exception as e:
        print(f"Error processing {pdf_path}: {e}")
        return {
            'pdf_path': str(pdf_path),
            'error': str(e)
        }

def main():
    # Test on one PDF
    pdf_dir = Path("data/pdfs")
    pdf_files = list(pdf_dir.glob("*.pdf"))
    
    if not pdf_files:
        print("No PDF files found in data/pdfs/")
        return
    
    # Use the first PDF for testing
    test_pdf = pdf_files[0]
    print(f"Testing on: {test_pdf}")
    
    result = extract_retained_earnings_from_pdf(test_pdf)
    
    # Save results
    output_file = "test_retained_earnings_result.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print(f"\nResults saved to: {output_file}")
    
    # Print summary
    if 'error' in result:
        print(f"Error: {result['error']}")
    else:
        print(f"\nSummary:")
        print(f"  PDF: {result['pdf_path']}")
        print(f"  Pages: {result['total_pages']}")
        print(f"  Text length: {result['total_text_length']:,} characters")
        print(f"  Regex matches found: {len(result['regex_matches'])}")
        
        if result['best_match']:
            print(f"  Best match: {result['best_match']['raw_match']}")
            print(f"  Value: {result['best_match']['value']}")
            print(f"  Numeric value: {result['best_match']['numeric_value']}")
        else:
            print("  No Retained Earnings found with regex patterns")
        
        if result['context_lines']:
            print(f"\nContext lines containing 'Retained Earnings':")
            for i, line in enumerate(result['context_lines'], 1):
                print(f"  {i}. {line}")

if __name__ == "__main__":
    main() 