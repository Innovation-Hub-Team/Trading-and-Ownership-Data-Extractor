#!/usr/bin/env python3
"""
Enhanced Retained Earnings Extraction from Financial Statement PDFs
Using PyMuPDF for layout-aware extraction + LLM for context validation
"""

import fitz  # PyMuPDF
import re
import json
from pathlib import Path
import sqlite3
from datetime import datetime
import openai
import os
from typing import Dict, List, Optional, Tuple
import logging
import sys
sys.path.append('.')
from src.utils.generate_evidence_screenshots import EvidenceScreenshotGenerator
import pdfplumber
import pprint
import base64

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

# Set OpenAI API key directly (for vision)
openai.api_key = "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"

def extract_retained_earnings_from_image_openai(image_path):
    with open(image_path, "rb") as image_file:
        image_base64 = base64.b64encode(image_file.read()).decode()
    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "What is the value of 'Retained earnings' in this table? Return only the number."},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_base64}"}}
                ]
            }
        ],
        max_tokens=20,
    )
    return response.choices[0].message.content.strip()

class EnhancedRetainedEarningsExtractor:
    def __init__(self, use_llm: bool = True):
        self.use_llm = use_llm
        self.keywords = [
            "retained earnings",
            "statement of changes in equity", 
            "financial position",
            "shareholders' equity",
            "equity",
            "accumulated earnings",
            "undistributed profits",
            "retainedearnings",
            "retained",
            "earnings",
            "profit",
            "loss"
        ]
        self.target_years = ["2024", "2023", "2022"]  # Prioritize latest year
        
    def extract_blocks_with_keywords(self, pdf_path: str) -> List[Dict]:
        """
        Extract text blocks containing relevant keywords using PyMuPDF
        """
        relevant_blocks = []
        
        try:
            doc = fitz.open(pdf_path)
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                
                # Get text blocks with coordinates
                blocks = page.get_text("blocks")
                
                for block in blocks:
                    if block[6] == 0:  # Text block (not image)
                        text = block[4].lower()
                        
                        # Check if block contains any relevant keywords
                        if any(keyword in text for keyword in self.keywords):
                            # Prioritize blocks that contain 2024
                            priority = 0
                            if '2024' in text:
                                priority = 100  # Highest priority for 2024
                            elif '2023' in text:
                                priority = 50   # Medium priority for 2023
                            elif '2022' in text:
                                priority = 25   # Lower priority for 2022
                            else:
                                priority = 10   # Default priority
                            
                            relevant_blocks.append({
                                'page': page_num + 1,
                                'text': block[4],
                                'bbox': block[:4],  # x0, y0, x1, y1
                                'block_type': 'text',
                                'priority': priority
                            })
            
            # Sort blocks by priority (2024 first, then 2023, etc.)
            relevant_blocks.sort(key=lambda x: x['priority'], reverse=True)
            
            doc.close()
            return relevant_blocks
            
        except Exception as e:
            logger.error(f"Error extracting blocks from {pdf_path}: {e}")
            return []
    
    def extract_with_regex_fallback(self, text: str) -> Optional[Dict]:
        """
        Enhanced regex extraction with multiple patterns and validation
        """
        patterns = [
            # 2024-specific patterns (highest priority)
            r'Retained\s+Earnings.*2024[:\s]*([\d,]+\.?\d*)',
            r'([\d,]+\.?\d*).*Retained\s+Earnings.*2024',
            r'2024.*Retained\s+Earnings[:\s]*([\d,]+\.?\d*)',
            r'([\d,]+\.?\d*).*2024.*Retained\s+Earnings',
            
            # More precise patterns that require the number to be on the same line or very close
            r'Retained\s+Earnings[:\s]*([\d,]+\.?\d*)',
            r'Retained\s+Earnings\s+([\d,]+\.?\d*)',
            r'([\d,]+\.?\d*)\s+Retained\s+Earnings',
            r'Retained\s+earnings[:\s]*([\d,]+\.?\d*)',
            r'Retainedearnings[:\s]*([\d,]+\.?\d*)',
            r'Retainedearnings\s+([\d,]+\.?\d*)',
            r'([\d,]+\.?\d*)\s+Retainedearnings',
            r'Retained\s+earnings\s+([\d,]+\.?\d*)',
            r'([\d,]+\.?\d*)\s+Retained\s+earnings',
            
            # Patterns with currency indicators
            r'Retained\s+Earnings\s*SAR\s*([\d,]+\.?\d*)',
            r'SAR\s*([\d,]+\.?\d*)\s*Retained\s+Earnings',
            r'Retained\s+earnings\s*SAR\s*([\d,]+\.?\d*)',
            r'SAR\s*([\d,]+\.?\d*)\s*Retained\s+earnings',
            
            # Patterns with parentheses (often used for negative values)
            r'Retained\s+Earnings\s*\(([\d,]+\.?\d*)\)',
            r'\(([\d,]+\.?\d*)\)\s*Retained\s+Earnings',
            
            # Patterns with specific financial statement context
            r'Retained\s+Earnings\s*[:\-]?\s*([\d,]+\.?\d*)\s*(?:SAR|million|thousand)?',
            r'([\d,]+\.?\d*)\s*[:\-]?\s*Retained\s+Earnings\s*(?:SAR|million|thousand)?',
        ]
        
        candidates = []
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                value = match.group(1)
                clean_value = value.replace(',', '')
                if clean_value:
                    try:
                        numeric_value = float(clean_value)
                        if numeric_value > 999:  # Filter out small numbers
                            # Get context around the match
                            context = text[max(0, match.start()-200):match.end()+200]
                            
                            # Skip if this appears to be a page number, year, or other non-financial number
                            if (numeric_value > 999999999 or  # Too large to be realistic
                                'page' in context.lower() or
                                'note' in context.lower()):
                                continue
                            
                            # Check for year indicators in context with more patterns
                            year_score = 0
                            year_found = None
                            
                            # Look for various year patterns
                            year_patterns = [
                                r'2024', r'2023', r'2022', r'2021',
                                r'31\s*December\s*2024', r'31\s*December\s*2023',
                                r'December\s*31,\s*2024', r'December\s*31,\s*2023',
                                r'31/12/2024', r'31/12/2023',
                                r'2024-12-31', r'2023-12-31'
                            ]
                            
                            for pattern in year_patterns:
                                year_matches = re.finditer(pattern, context, re.IGNORECASE)
                                for year_match in year_matches:
                                    year_found = year_match.group(0)
                                    if '2024' in year_found:
                                        year_score = 100  # Highest priority for 2024
                                        break
                                    elif '2023' in year_found:
                                        year_score = 50   # Medium priority for 2023
                                    elif '2022' in year_found:
                                        year_score = 25   # Lower priority for 2022
                                    elif '2021' in year_found:
                                        year_score = 10   # Lowest priority for 2021
                                if year_score == 100:  # Found 2024, highest priority
                                    break
                            
                            # If no specific year found, check if this is likely 2024 data
                            if year_score == 0:
                                # Check for indicators that this might be 2024 data
                                if any(indicator in context.lower() for indicator in ['current year', 'latest', 'most recent', 'ending 2024']):
                                    year_score = 80  # High confidence it's 2024
                                elif any(indicator in context.lower() for indicator in ['previous year', 'prior year', 'ending 2023']):
                                    year_score = 40  # Medium confidence it's 2023
                                else:
                                    year_score = 30  # Default score if no year found
                                
                            candidates.append({
                                'value': value,
                                'numeric_value': numeric_value,
                                'raw_match': match.group(0),
                                'pattern': pattern,
                                'position': match.start(),
                                'context': context,
                                'year_score': year_score,
                                'year_found': year_found
                            })
                    except ValueError:
                        continue
        
        # Sort by year score first (highest priority for 2024), then by numeric value
        if candidates:
            candidates.sort(key=lambda x: (x['year_score'], x['numeric_value']), reverse=True)
            best_match = candidates[0]
            year_info = f" (year_score: {best_match['year_score']}"
            if best_match.get('year_found'):
                year_info += f", year_found: {best_match['year_found']}"
            year_info += ")"
            logger.info(f"[REGEX] Used regex fallback, found value: {best_match['value']}{year_info}")
            return best_match
        
        return None
    
    def extract_with_full_text_fallback(self, pdf_path: str) -> Optional[Dict]:
        """
        Fallback to full text extraction when block-based fails
        """
        try:
            doc = fitz.open(pdf_path)
            full_text = ""
            
            for page in doc:
                full_text += page.get_text() + "\n"
            
            doc.close()
            
            # Use the same regex patterns on full text
            return self.extract_with_regex_fallback(full_text)
            
        except Exception as e:
            logger.error(f"Error in full text extraction: {e}")
            return None
    
    def extract_with_llm(self, blocks: List[Dict]) -> Optional[Dict]:
        """
        Extract retained earnings using LLM with structured output
        """
        if not self.use_llm:
            return None
            
        try:
            # Combine relevant blocks into context
            context = "\n\n".join([f"Page {block['page']}: {block['text']}" for block in blocks[:5]])  # Limit to first 5 blocks
            
            prompt = f"""
            Extract retained earnings information from the following financial statement text.
            
            IMPORTANT: Prioritize the MOST RECENT year (2024) over older years (2023, 2022, etc.).
            If multiple years are present, always return the 2024 value.
            
            Context:
            {context}
            
            Please extract the retained earnings information and return it in the following JSON format:
            {{
                "retained_earnings": {{
                    "value": "4509836",
                    "currency": "SAR", 
                    "date": "2024-12-31",
                    "source_section": "Statement of Financial Position",
                    "note": "End of year balance for 2024",
                    "confidence": "high/medium/low"
                }}
            }}
            
            If no retained earnings are found, return:
            {{
                "retained_earnings": null,
                "reason": "No retained earnings found in the provided text"
            }}
            
            Focus on:
            1. The final retained earnings balance for 2024 (most recent year)
            2. The currency (usually SAR for Saudi companies)
            3. The date (usually 2024-12-31)
            4. The source section where it was found
            5. If 2024 data is not available, then use 2023, but clearly indicate this
            """
            
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            content = response.choices[0].message.content
            logger.info("[LLM] Used GPT-4 for extraction.")
            try:
                result = json.loads(content)
                if result.get('retained_earnings'):
                    return result['retained_earnings']
            except Exception as e:
                logger.error(f"[LLM] Failed to parse LLM output: {e}\nRaw output: {content}")
            return None
            
        except Exception as e:
            logger.error(f"Error in LLM extraction: {e}")
            return None

    def extract_from_tables(self, pdf_path: str) -> dict:
        """
        Try to extract retained earnings from tables using Camelot, but only on pages containing 'Retained earnings'.
        Returns a dict with extraction info if successful, else None.
        """
        import camelot
        import pandas as pd
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    page_text = page.extract_text() or ""
                    if "retained earnings" in page_text.lower():
                        # Use Camelot to extract tables from this page
                        tables = camelot.read_pdf(pdf_path, pages=str(page_num+1), flavor="stream")
                        for t_idx, table in enumerate(tables):
                            df = table.df
                            # Try to find header row with years
                            header_idx = None
                            for i, row in df.iterrows():
                                if any(str(y) in map(str, row) for y in self.target_years):
                                    header_idx = i
                                    break
                            if header_idx is None:
                                continue  # No header row found, try next table
                            df.columns = df.iloc[header_idx]
                            df = df.iloc[header_idx+1:]
                            # Now look for the 'Retained earnings' row
                            retained_row = df[df.iloc[:,0].str.contains("Retained earnings", case=False, na=False)]
                            if not retained_row.empty:
                                for year in self.target_years:
                                    if year in df.columns:
                                        value = retained_row[year].values[0]
                                        if value and str(value).replace(",", "").replace(" ", "").replace("-", "").replace(".", "").isdigit():
                                            return {
                                                'success': True,
                                                'value': str(value),
                                                'numeric_value': float(str(value).replace(',', '')),
                                                'method': 'table_camelot',
                                                'year': year,
                                                'page': page_num+1,
                                                'raw_match': f"Retained earnings {year}: {value}",
                                                'total_blocks': 0
                                            }
            return None
        except Exception as e:
            logger.error(f"[TABLE] Error extracting from tables: {e}")
            return None

    def extract_retained_earnings(self, pdf_path: str) -> dict:
        """
        Main extraction method: table -> LLM -> regex fallback
        """
        logger.info(f"Processing: {pdf_path}")
        # 1. Try table extraction first
        table_result = self.extract_from_tables(pdf_path)
        if table_result:
            logger.info(f"[TABLE] Extraction succeeded: {table_result.get('value')} for {table_result.get('year')}")
            return table_result
        # 2. Try LLM extraction (if enabled)
        blocks = self.extract_blocks_with_keywords(pdf_path)
        logger.info(f"Found {len(blocks)} relevant blocks")
        if self.use_llm and blocks:
            llm_result = self.extract_with_llm(blocks)
            if llm_result and llm_result.get('value'):
                logger.info(f"[LLM] Extraction succeeded: {llm_result.get('value')}")
                return {
                    'success': True,
                    'value': llm_result.get('value'),
                    'numeric_value': float(llm_result.get('value', '0').replace(',', '')),
                    'currency': llm_result.get('currency', 'SAR'),
                    'date': llm_result.get('date'),
                    'source_section': llm_result.get('source_section'),
                    'confidence': llm_result.get('confidence', 'medium'),
                    'method': 'llm',
                    'total_blocks': len(blocks)
                }
            else:
                logger.info("[LLM] LLM extraction failed or returned no value, falling back to regex.")
        # 3. Try regex extraction on relevant blocks
        if blocks:
            combined_text = "\n".join([block['text'] for block in blocks])
            regex_result = self.extract_with_regex_fallback(combined_text)
            if regex_result:
                return {
                    'success': True,
                    'value': regex_result['value'],
                    'numeric_value': regex_result['numeric_value'],
                    'raw_match': regex_result['raw_match'],
                    'method': 'regex_blocks',
                    'total_blocks': len(blocks)
                }
        # 4. Fallback to full text extraction
        full_text_result = self.extract_with_full_text_fallback(pdf_path)
        if full_text_result:
            return {
                'success': True,
                'value': full_text_result['value'],
                'numeric_value': full_text_result['numeric_value'],
                'raw_match': full_text_result['raw_match'],
                'method': 'regex_full_text',
                'total_blocks': len(blocks) if blocks else 0
            }
        # 5. Fallback to OpenAI Vision on screenshot
        company_symbol = get_company_symbol_from_filename(Path(pdf_path).name)
        screenshot_path = f"output/screenshots/{company_symbol}_evidence.png"
        if os.path.exists(screenshot_path):
            try:
                logger.info(f"[VISION] Trying OpenAI Vision on screenshot for {company_symbol}...")
                vision_value = extract_retained_earnings_from_image_openai(screenshot_path)
                if vision_value and vision_value.replace(',', '').replace(' ', '').isdigit():
                    numeric_value = float(vision_value.replace(',', ''))
                    logger.info(f"[VISION] OpenAI Vision extracted: {vision_value}")
                    return {
                        'success': True,
                        'value': vision_value,
                        'numeric_value': numeric_value,
                        'raw_match': vision_value,
                        'method': 'openai_vision',
                        'total_blocks': len(blocks) if blocks else 0
                    }
                else:
                    logger.warning(f"[VISION] OpenAI Vision did not return a valid number: {vision_value}")
            except Exception as e:
                logger.error(f"[VISION] OpenAI Vision extraction failed: {e}")
        return {
            'success': False,
            'error': 'No retained earnings found using any method',
            'method': 'all_methods_failed',
            'total_blocks': len(blocks) if blocks else 0
        }

def get_company_symbol_from_filename(filename):
    """Extract company symbol from PDF filename (e.g., '2010_annual_2024.pdf' -> '2010')"""
    return filename.split('_')[0]

def save_to_database(results):
    """Save results to SQLite database with enhanced schema"""
    conn = sqlite3.connect('data/financial_analysis.db')
    cursor = conn.cursor()
    
    # Drop existing table if it exists and recreate with enhanced schema
    cursor.execute('DROP TABLE IF EXISTS retained_earnings')
    
    # Create enhanced table schema
    cursor.execute('''
        CREATE TABLE retained_earnings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_symbol TEXT,
            pdf_filename TEXT,
            retained_earnings_value REAL,
            currency TEXT DEFAULT 'SAR',
            date TEXT,
            source_section TEXT,
            confidence TEXT,
            method TEXT,
            raw_match TEXT,
            total_blocks INTEGER,
            extraction_date TIMESTAMP,
            success BOOLEAN,
            error_message TEXT
        )
    ''')
    
    # Insert results
    for result in results:
        cursor.execute('''
            INSERT INTO retained_earnings 
            (company_symbol, pdf_filename, retained_earnings_value, currency, date,
             source_section, confidence, method, raw_match, total_blocks, 
             extraction_date, success, error_message)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            result['company_symbol'],
            result['pdf_filename'],
            result.get('numeric_value'),
            result.get('currency', 'SAR'),
            result.get('date'),
            result.get('source_section'),
            result.get('confidence', 'medium'),
            result.get('method', 'regex'),
            result.get('raw_match'),
            result.get('total_blocks'),
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
    
    # DEBUG: Print tables from the first PDF
    sample_pdf = str(pdf_files[0])
    print(f"\n[DEBUG] Printing tables extracted by pdfplumber from: {sample_pdf}")
    import pdfplumber
    with pdfplumber.open(sample_pdf) as pdf:
        for page_num, page in enumerate(pdf.pages):
            tables = page.extract_tables()
            print(f"\n[DEBUG] Page {page_num+1} - {len(tables)} tables found")
            for t_idx, table in enumerate(tables):
                print(f"[DEBUG] Table {t_idx+1}:")
                pprint.pprint(table)
            if page_num == 0:
                break  # Only print first page for now
    print("\n[DEBUG] End of table printout.\n")
    
    # DEBUG: Print tables from the first PDF using Camelot
    import camelot
    print(f"\n[DEBUG] Printing tables extracted by Camelot from: {sample_pdf}")
    try:
        tables = camelot.read_pdf(sample_pdf, pages="1", flavor="stream")
        print(f"[DEBUG] Camelot found {tables.n} tables on page 1.")
        for i, table in enumerate(tables):
            print(f"[DEBUG] Table {i+1} (shape {table.shape}):")
            print(table.df)
    except Exception as e:
        print(f"[DEBUG] Camelot extraction error: {e}")
    print("\n[DEBUG] End of Camelot table printout.\n")
    
    # Initialize enhanced extractor
    extractor = EnhancedRetainedEarningsExtractor(use_llm=True)  # LLM enabled by default
    
    # Initialize evidence screenshot generator
    evidence_generator = EvidenceScreenshotGenerator()
    
    # Ensure screenshots directory exists
    screenshots_dir = Path("output/screenshots")
    screenshots_dir.mkdir(parents=True, exist_ok=True)
    
    results = []
    successful_extractions = 0
    evidence_metadata = []
    
    for i, pdf_file in enumerate(pdf_files, 1):
        print(f"\n[{i}/{len(pdf_files)}] Processing: {pdf_file.name}")
        company_symbol = get_company_symbol_from_filename(pdf_file.name)
        # Run all extraction methods and collect their results
        table_result = extractor.extract_from_tables(str(pdf_file))
        blocks = extractor.extract_blocks_with_keywords(str(pdf_file))
        regex_result = None
        if blocks:
            combined_text = "\n".join([block['text'] for block in blocks])
            regex_result = extractor.extract_with_regex_fallback(combined_text)
        vision_result = None
        screenshot_path = f"output/screenshots/{company_symbol}_evidence.png"
        if os.path.exists(screenshot_path):
            try:
                vision_value = extract_retained_earnings_from_image_openai(screenshot_path)
                if vision_value and vision_value.replace(',', '').replace(' ', '').isdigit():
                    numeric_value = float(vision_value.replace(',', ''))
                    vision_result = {'value': vision_value, 'numeric_value': numeric_value}
            except Exception as e:
                print(f"  ⚠️ OpenAI Vision extraction failed: {e}")
        # Collect all non-empty results
        values = set()
        method_values = {}
        if table_result and table_result.get('success'):
            values.add(str(table_result['numeric_value']))
            method_values['table'] = table_result['numeric_value']
        if regex_result:
            values.add(str(regex_result['numeric_value']))
            method_values['regex'] = regex_result['numeric_value']
        if vision_result:
            values.add(str(vision_result['numeric_value']))
            method_values['vision'] = vision_result['numeric_value']
        # Confidence logic
        if len(values) == 1 and values:
            confidence = 'high'
            flag_for_review = False
        else:
            confidence = 'low'
            flag_for_review = True
        # Pick the best available result (table > vision > regex)
        if table_result and table_result.get('success'):
            result = table_result
            result['method'] = 'table_camelot'
        elif vision_result:
            result = {
                'success': True,
                'value': vision_result['value'],
                'numeric_value': vision_result['numeric_value'],
                'raw_match': vision_result['value'],
                'method': 'openai_vision',
                'total_blocks': len(blocks) if blocks else 0
            }
        elif regex_result:
            result = {
                'success': True,
                'value': regex_result['value'],
                'numeric_value': regex_result['numeric_value'],
                'raw_match': regex_result['raw_match'],
                'method': 'regex_blocks',
                'total_blocks': len(blocks) if blocks else 0
            }
        else:
            result = {
                'success': False,
                'error': 'No retained earnings found using any method',
                'method': 'all_methods_failed',
                'total_blocks': len(blocks) if blocks else 0
            }
        # Add confidence and flag fields
        result['confidence'] = confidence
        result['flag_for_review'] = flag_for_review
        result['method_values'] = method_values
        result['company_symbol'] = company_symbol
        result['pdf_filename'] = pdf_file.name
        
        if result['success']:
            successful_extractions += 1
            print(f"  ✓ Found: {result['value']} (numeric: {result['numeric_value']:,.0f})")
            print(f"  ✓ Method: {result.get('method', 'unknown')}")
            if result.get('source_section'):
                print(f"  ✓ Source: {result['source_section']}")
            
            # Generate evidence screenshot
            try:
                print(f"  📸 Generating evidence screenshot...")
                
                screenshot_path = evidence_generator.generate_highlight_screenshot(
                    pdf_path=str(pdf_file),
                    search_value=result['value'],
                    company_symbol=company_symbol
                )
                
                if screenshot_path:
                    print(f"  ✓ Evidence screenshot saved: {screenshot_path}")
                    evidence_metadata.append({
                        "company_symbol": company_symbol,
                        "value": result['value'],
                        "screenshot_path": screenshot_path,
                        "pdf_filename": pdf_file.name
                    })
                else:
                    print(f"  ⚠️ Failed to generate evidence screenshot")
                    
            except Exception as e:
                print(f"  ⚠️ Error generating evidence screenshot: {e}")
        else:
            print(f"  ✗ Error: {result.get('error', 'Unknown error')}")
        
        results.append(result)
    
    # Save results to JSON
    # Ensure data/results directory exists
    results_dir = Path("data/results")
    results_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = results_dir / "retained_earnings_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    # Save evidence metadata
    evidence_metadata_file = screenshots_dir / "evidence_metadata.json"
    with open(evidence_metadata_file, 'w', encoding='utf-8') as f:
        json.dump(evidence_metadata, f, ensure_ascii=False, indent=2)
    
    # Save to database
    save_to_database(results)
    
    # Print summary
    print(f"\n{'='*50}")
    print(f"ENHANCED EXTRACTION SUMMARY")
    print(f"{'='*50}")
    print(f"Total PDFs processed: {len(pdf_files)}")
    print(f"Successful extractions: {successful_extractions}")
    print(f"Evidence screenshots generated: {len(evidence_metadata)}")
    print(f"Success rate: {successful_extractions/len(pdf_files)*100:.1f}%")
    print(f"Results saved to: {output_file}")
    print(f"Evidence metadata saved to: {evidence_metadata_file}")
    print(f"Results also saved to database: data/financial_analysis.db")
    
    # Show successful extractions
    if successful_extractions > 0:
        print(f"\nSuccessful extractions:")
        for result in results:
            if result['success']:
                method = result.get('method', 'unknown')
                source = result.get('source_section', 'N/A')
                print(f"  {result['company_symbol']}: {result['value']} ({result['numeric_value']:,.0f}) [{method}]")

if __name__ == "__main__":
    main() 