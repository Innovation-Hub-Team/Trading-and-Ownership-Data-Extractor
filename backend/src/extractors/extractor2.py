#!/usr/bin/env python3
import argparse
import json
import re
import os
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

# Separate detection for pdfium/PIL and pytesseract
try:
    import pypdfium2 as pdfium  # type: ignore
    from PIL import Image, ImageOps  # type: ignore
    has_pdfium = True
except Exception:  # pragma: no cover - optional deps
    has_pdfium = False

try:
    import pytesseract  # type: ignore
    from pytesseract import Output  # type: ignore
    has_tesseract = True
except Exception:  # pragma: no cover - optional deps
    has_tesseract = False

# Text extraction (optional fast path for text PDFs)
try:
    import pdfplumber  # type: ignore
    has_pdfplumber = True
except Exception:
    has_pdfplumber = False

# Gemini Vision API for advanced OCR
try:
    import google.generativeai as genai
    has_gemini = True
except Exception:
    has_gemini = False


def extract_text_with_pdfplumber(pdf_path: str, page_index: int) -> str:
    if not has_pdfplumber:
        return ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            if 0 <= page_index < len(pdf.pages):
                text = pdf.pages[page_index].extract_text(x_tolerance=2, y_tolerance=2) or ""
                return text
    except Exception:
        return ""
    return ""

# -------------------------
# Configuration
# -------------------------
DEFAULT_TARGET_TITLES = [
    "Main Market Value Traded Breakdown - By Nationality, Investor Type and Classification",
    "Main Market Ownership Breakdown - By Nationality, Investor Type and Classification",
    "Main Market Value Traded Breakdown - By Nationality and Investor Type",
    "Main Market Ownership Breakdown - By Nationality and Investor Type"
]

# -------------------------
# Utilities
# -------------------------

def configure_gemini(api_key: str) -> None:
    """Configure Gemini API with the provided key."""
    if not has_gemini:
        raise RuntimeError("google-generativeai is required. Install via: pip install google-generativeai")
    genai.configure(api_key=api_key)

def extract_financial_metrics_with_gemini(pdf_path: str, page_num: int = 5, page_type: str = "value_traded") -> Optional[dict]:
    """
    Extract multiple financial metrics using Gemini Vision API.
    page_type: "value_traded" or "ownership_value"
    Returns a dictionary with all extracted values or None if failed.
    """
    try:
        if not has_gemini:
            print("❌ Gemini Vision API not available")
            return None
            
        # Convert PDF page to image
        doc = pdfium.PdfDocument(pdf_path)
        page = doc[page_num - 1]  # Convert to 0-based index
        
        # Render page to high-quality image
        image = page.render(scale=3.0)  # High resolution for better recognition
        pil_image = image.to_pil()
        
        # Save temporary image for Gemini
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
            pil_image.save(tmp_file.name, 'PNG')
            temp_path = tmp_file.name
        
        try:
            # Upload image to Gemini
            uploaded_file = genai.upload_file(temp_path)
            
            # Create the model
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            # Craft a comprehensive prompt for multiple metrics
            if page_type == "value_traded":
                prompt = """
                This is a financial table showing trading data by nationality and investor type.
                
                CRITICAL: You are analyzing page {page_num} of this specific PDF. Focus ONLY on this page.
                
                FIRST: Look for the report date at the top of the page. Common formats:
                - "Weekly Trading and Ownership Report [DATE]"
                - "Report as of [DATE]"
                - "Period ending [DATE]"
                - Look for dates in formats like: DD Month YYYY, MM/DD/YYYY, YYYY-MM-DD
                
                THEN: Please find these specific rows and extract the Net Value Traded number from each:
                
                1. "Sub Total (Individuals)" - Net Value Traded
                2. "Sub Total (Institutions)" - Net Value Traded  
                3. "Total GCC Investors" - Net Value Traded
                4. "Total Foreign Investors" - Net Value Traded
                
                Each row has this structure:
                [Row Label] [Buy Amount] [Buy %] [Sell Amount] [Sell %] [Net Value Traded] [Net %]
                
                Before extracting, confirm you found the correct row by showing: "FOUND ROW: [exact row label]"
                
                Return ONLY in this exact format (numbers without commas):
                REPORT_DATE: [date in YYYY-MM-DD format]
                INDIVIDUALS: [number]
                INSTITUTIONS: [number]
                GCC: [number]
                FOREIGN: [number]
                
                If you cannot find a specific row, use "NOT_FOUND" for that value.
                If you cannot find the date, use "NOT_FOUND" for REPORT_DATE.
                """
            else:  # ownership_value
                prompt = """
                This is a financial table showing ownership data by nationality and investor type.
                
                CRITICAL: You are analyzing page {page_num} of this specific PDF. Focus ONLY on this page.
                
                FIRST: Look for the report date at the top of the page. Common formats:
                - "Weekly Trading and Ownership Report [DATE]"
                - "Report as of [DATE]"
                - "Period ending [DATE]"
                - Look for dates in formats like: DD Month YYYY, MM/DD/YYYY, YYYY-MM-DD
                
                THEN: Please find these specific rows and extract the Weekly Change number from each:
                
                1. "Sub Total (Individuals)" - Weekly Change
                2. "Sub Total (Institutions)" - Weekly Change  
                3. "Total GCC Investors" - Weekly Change
                4. "Total Foreign Investors" - Weekly Change
                
                IMPORTANT: 
                - Look for the "Weekly Change" column specifically (usually second numeric column from left)
                - Make sure you are reading from the correct "Weekly Change" column
                - Verify you are reading the correct row by checking the row label matches exactly
                
                Each row has this structure:
                [Row Label] [Weekly Change] [Weekly Change %]
                
                Before extracting, confirm you found the correct row by showing: "FOUND ROW: [exact row label]"
                
                Return ONLY in this exact format (numbers without commas):
                REPORT_DATE: [date in YYYY-MM-DD format]
                INDIVIDUALS: [number]
                INSTITUTIONS: [number]
                GCC: [number]
                FOREIGN: [number]
                
                If you cannot find a specific row, use "NOT_FOUND" for that value.
                If you cannot find the date, use "NOT_FOUND" for REPORT_DATE.
                """
            
            # Generate response
            formatted_prompt = prompt.format(page_num=page_num)
            response = model.generate_content([formatted_prompt, uploaded_file])
            
            # Clean up temporary file
            import os
            os.unlink(temp_path)
            
            # Parse the response
            result_text = response.text.strip()
            print(f"🤖 Gemini response: '{result_text}'")
            
            # Parse the structured response
            metrics = {}
            lines = result_text.split('\n')
            
            for line in lines:
                line = line.strip()
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip().upper()
                    value = value.strip()
                    
                    if value == "NOT_FOUND":
                        metrics[key] = None
                    elif key == "REPORT_DATE":
                        # Keep the date as is, we'll process it later
                        metrics[key] = value
                    else:
                        # Extract number from value (handle negative numbers)
                        numbers = re.findall(r'-?\d+', value)
                        if numbers:
                            metrics[key] = int(numbers[0])
                        else:
                            metrics[key] = None
            
            print(f"📊 Extracted metrics: {metrics}")
            return metrics
                
        except Exception as e:
            print(f"❌ Gemini API error: {e}")
            # Clean up temporary file on error
            try:
                os.unlink(temp_path)
            except:
                pass
            return None
            
    except Exception as e:
        print(f"❌ Gemini extraction error: {e}")
        return None


@dataclass
class HeadingResult:
    heading: str
    page_number: int
    score: float
    matched_text_snippet: str


def normalize_text(text: str) -> str:
    """Normalize text for comparison."""
    if not text:
        return ""
    
    # Replace hyphen-newline breaks
    text = re.sub(r'-\s*\n\s*', '', text)
    
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove extra punctuation and normalize
    text = re.sub(r'[^\w\s-]', ' ', text)
    
    return text.strip().lower()


def simplify_text(text: str) -> str:
    """Simplify text for relaxed exact matching."""
    if not text:
        return ""
    
    # Remove punctuation and extra spaces
    text = re.sub(r'[^\w\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip().lower()


def find_headings_in_pdf(
    pdf_path: str,
    target_headings: List[str],
    exact_relaxed: bool = False,
    include_terms: Optional[List[str]] = None,
    exclude_terms: Optional[List[str]] = None,
) -> List[HeadingResult]:
    """Find pages containing target headings in PDF."""
    results = []
    
    if not has_pdfplumber:
        print("Falling back to OCR for all pages...")
        # If no pdfplumber, use OCR for all pages
        doc = pdfium.PdfDocument(pdf_path)
        for page_num in range(len(doc)):
            page_num_1_indexed = page_num + 1
            for heading in target_headings:
                # For OCR fallback, assume all pages might contain headings
                results.append(HeadingResult(
                    heading=heading,
                    page_number=page_num_1_indexed,
                    score=100.0,  # High score for OCR fallback
                    matched_text_snippet="OCR fallback - page processed"
                ))
        return results
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                page_num_1_indexed = page_num + 1
                
                # Extract text from page
                text = page.extract_text(x_tolerance=2, y_tolerance=2) or ""
                
                # If no text extracted, skip this page
                if not text.strip():
                    continue
                
                # Normalize text
                normalized_text = normalize_text(text)
                
                # Check include/exclude filters
                if include_terms:
                    if not any(term.lower() in normalized_text for term in include_terms):
                        continue
                
                if exclude_terms:
                    if any(term.lower() in normalized_text for term in exclude_terms):
                        continue
                
                # Check each target heading
                for heading in target_headings:
                    if exact_relaxed:
                        # Relaxed exact matching
                        simplified_heading = simplify_text(heading)
                        simplified_text = simplify_text(text)
                        
                        if simplified_heading in simplified_text:
                            # Find the best match snippet
                            snippet = find_best_match_snippet(text, heading)
                            results.append(HeadingResult(
                                heading=heading,
                                page_number=page_num_1_indexed,
                                score=100.0,
                                matched_text_snippet=snippet
                            ))
                    else:
                        # Exact matching
                        if heading.lower() in text.lower():
                            # Find the best match snippet
                            snippet = find_best_match_snippet(text, heading)
                            results.append(HeadingResult(
                                heading=heading,
                                page_number=page_num_1_indexed,
                                score=100.0,
                                matched_text_snippet=snippet
                            ))
    
    except Exception as e:
        print(f"Error processing PDF: {e}")
        return []
    
    return results


def find_best_match_snippet(text: str, heading: str, context_chars: int = 100) -> str:
    """Find the best snippet around the matched heading."""
    try:
        # Find the heading in the text (case-insensitive)
        heading_lower = heading.lower()
        text_lower = text.lower()
        
        start_idx = text_lower.find(heading_lower)
        if start_idx == -1:
            return heading
        
        # Calculate snippet boundaries
        snippet_start = max(0, start_idx - context_chars)
        snippet_end = min(len(text), start_idx + len(heading) + context_chars)
        
        snippet = text[snippet_start:snippet_end]
        
        # Clean up snippet
        snippet = snippet.strip()
        if len(snippet) > 200:
            snippet = snippet[:200] + "..."
        
        return snippet
    
    except Exception:
        return heading


def export_pages_to_png(pdf_path: str, page_numbers: List[int], export_dir: str, scale: float = 2.0) -> List[str]:
    """Export specific PDF pages as PNG images."""
    if not has_pdfium:
        raise RuntimeError("pypdfium2 is required for PNG export")
    
    # Create export directory
    os.makedirs(export_dir, exist_ok=True)
    
    exported_paths = []
    doc = pdfium.PdfDocument(pdf_path)
    
    for page_num in page_numbers:
        try:
            page = doc[page_num - 1]  # Convert to 0-based index
            
            # Render page to image
            image = page.render(scale=scale)
            pil_image = image.to_pil()
            
            # Save as PNG
            filename = f"page_{page_num:03d}.png"
            filepath = os.path.join(export_dir, filename)
            pil_image.save(filepath, "PNG")
            
            exported_paths.append(filepath)
            
        except Exception as e:
            print(f"Failed to export page {page_num}: {e}")
    
    return exported_paths


def main():
    parser = argparse.ArgumentParser(description="Find PDF pages containing specific headings")
    parser.add_argument("--pdf", default="2025_06__REPORT.pdf", help="PDF file path")
    parser.add_argument("--headings", nargs="+", help="Headings to search for")
    parser.add_argument("--exact-relaxed", action="store_true", help="Use relaxed exact matching")
    parser.add_argument("--include", nargs="*", default=["main market"], help="Terms that must be present")
    parser.add_argument("--exclude", nargs="*", default=["nomu"], help="Terms that must not be present")
    parser.add_argument("--export-png-dir", default="./final_main_market", help="Directory for PNG exports")
    parser.add_argument("--export-crop-dir", help="Directory for cropped cell exports")
    parser.add_argument("--save-position", help="Save learned position to JSON file")
    parser.add_argument("--load-position", help="Load position from JSON file")
    parser.add_argument("--json", action="store_true", help="Output results as JSON")
    parser.add_argument("--render-scale", type=float, default=2.0, help="Render scale for OCR")
    parser.add_argument("--tesseract-psm", type=int, help="Tesseract PSM mode")
    
    args = parser.parse_args()
    
    # Use default headings if none specified
    headings = args.headings or DEFAULT_TARGET_TITLES
    
    # Handle empty include/exclude lists (disable filters)
    include_terms = args.include if args.include else None
    exclude_terms = args.exclude if args.exclude else None
    
    print(f"Searching for headings: {headings}")
    print(f"Include terms: {include_terms}")
    print(f"Exclude terms: {exclude_terms}")
    
    # Find headings
    results = find_headings_in_pdf(
        args.pdf,
        headings,
        exact_relaxed=args.exact_relaxed,
        include_terms=include_terms,
        exclude_terms=exclude_terms,
    )
    
    # Export PNGs if requested
    unique_pages = sorted({r.page_number for r in results})
    if unique_pages:
        try:
            paths = export_pages_to_png(args.pdf, unique_pages, args.export_png_dir, scale=args.render_scale)
        except Exception as e:
            print(f"PNG export failed: {e}")
            paths = []
    else:
        paths = []
    
    # Learn position if requested
    saved_pos = None
    if args.save_position:
        print("Position learning not implemented in this version")
    
    # Configure Gemini API
    gemini_api_key = "AIzaSyCBPEa1qNq_wT-4ehE5Y7KL9kP2-D1N0NM"
    try:
        configure_gemini(gemini_api_key)
        print("✅ Gemini API configured successfully")
    except Exception as e:
        print(f"⚠️ Gemini API configuration failed: {e}")

    # Attempt to extract financial metrics
    extracted_value = None
    
    # Try Gemini first (most accurate) - now extracts from both pages
    extracted_metrics = None
    ownership_metrics = None
    
    if unique_pages and has_gemini:
        try:
            # Extract from Value Traded page (first found page)
            page_to_extract = unique_pages[0]
            print(f"🤖 Trying Gemini extraction on page {page_to_extract} (Value Traded)...")
            extracted_metrics = extract_financial_metrics_with_gemini(args.pdf, page_to_extract, "value_traded")
            
            # For backward compatibility, set extracted_value to Individuals if available
            if extracted_metrics and 'INDIVIDUALS' in extracted_metrics and extracted_metrics['INDIVIDUALS'] is not None:
                extracted_value = extracted_metrics['INDIVIDUALS']
            else:
                extracted_value = None
                
        except Exception as e:
            print(f"❌ Gemini extraction failed: {e}")
            extracted_value = None
            
        # Try to extract from Ownership page if it exists
        try:
            ownership_pages = [p for p in unique_pages if p != page_to_extract]
            if ownership_pages:
                ownership_page = ownership_pages[0]
                print(f"🤖 Trying Gemini extraction on page {ownership_page} (Ownership Value)...")
                ownership_metrics = extract_financial_metrics_with_gemini(args.pdf, ownership_page, "ownership_value")
        except Exception as e:
            print(f"❌ Gemini ownership extraction failed: {e}")
            ownership_metrics = None
    
    # Fallback to position-based extraction
    if extracted_value is None and args.load_position:
        print("Position-based extraction not implemented in this version")
    
    # Final fallback to Tesseract OCR
    if extracted_value is None:
        print("⚠️ Tesseract OCR fallback not implemented in this version")
    
    if args.json:
        payload = {
            "pdf": args.pdf,
            "exact_relaxed": bool(args.exact_relaxed),
            "include": args.include,
            "exclude": args.exclude,
            "png_export": {
                "dir": args.export_png_dir,
                "pages": unique_pages,
                "paths": paths,
            },
            "results": [
                {
                    "heading": r.heading,
                    "page": r.page_number,
                    "score": r.score,
                    "snippet": r.matched_text_snippet,
                }
                for r in results
            ],
            "extraction": {
                "saudi_subtotal_individuals_net_value_traded": extracted_value,
                "value_traded_metrics": extracted_metrics,
                "ownership_metrics": ownership_metrics,
                "saved_position": saved_pos,
            },
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return
    
    # Human-readable
    if not results:
        print(f"No matches found in {args.pdf}. OCR is used on all pages.")
        return
    
    print(f"PDF: {args.pdf}\nMode: exact\nOCR: on")
    for heading in headings:
        matches = [r for r in results if r.heading == heading]
        if not matches:
            print(f"- {heading}: no pages found")
            continue
        pages = ", ".join(str(m.page_number) for m in sorted(matches, key=lambda x: x.page_number))
        best = max(matches, key=lambda x: x.score)
        print(f"- {heading}: pages {pages} (best score {best.score})")
    if paths:
        print("Exported PNGs:")
        for p in paths:
            print(f"  - {p}")
    
    # Display all extracted metrics
    if extracted_metrics:
        print("\n📊 **Value Traded Metrics:**")
        if extracted_metrics.get('INDIVIDUALS'):
            print(f"✅ Saudi → Sub Total (Individuals) → Net Value Traded: {extracted_metrics['INDIVIDUALS']:,}")
        else:
            print("❌ Saudi → Sub Total (Individuals) → Net Value Traded: not found")
            
        if extracted_metrics.get('INSTITUTIONS'):
            print(f"✅ Saudi → Sub Total (Institutions) → Net Value Traded: {extracted_metrics['INSTITUTIONS']:,}")
        else:
            print("❌ Saudi → Sub Total (Institutions) → Net Value Traded: not found")
            
        if extracted_metrics.get('GCC'):
            print(f"✅ Total GCC Investors → Net Value Traded: {extracted_metrics['GCC']:,}")
        else:
            print("❌ Total GCC Investors → Net Value Traded: not found")
            
        if extracted_metrics.get('FOREIGN'):
            print(f"✅ Total Foreign Investors → Net Value Traded: {extracted_metrics['FOREIGN']:,}")
        else:
            print("❌ Total Foreign Investors → Net Value Traded: not found")
    
    if ownership_metrics:
        print("\n📊 **Ownership Value Metrics:**")
        if ownership_metrics.get('INDIVIDUALS'):
            print(f"✅ Saudi → Sub Total (Individuals) → Ownership Value: {ownership_metrics['INDIVIDUALS']:,}")
        else:
            print("❌ Saudi → Sub Total (Individuals) → Ownership Value: not found")
            
        if ownership_metrics.get('INSTITUTIONS'):
            print(f"✅ Saudi → Sub Total (Institutions) → Ownership Value: {ownership_metrics['INSTITUTIONS']:,}")
        else:
            print("❌ Saudi → Sub Total (Institutions) → Ownership Value: not found")
            
        if ownership_metrics.get('GCC'):
            print(f"✅ Total GCC Investors → Ownership Value: {ownership_metrics['GCC']:,}")
        else:
            print("❌ Total GCC Investors → Ownership Value: not found")
            
        if ownership_metrics.get('FOREIGN'):
            print(f"✅ Total Foreign Investors → Ownership Value: {ownership_metrics['FOREIGN']:,}")
        else:
            print("❌ Total Foreign Investors → Ownership Value: not found")
    
    elif extracted_value:
        print(f"Saudi → Sub Total (Individuals) → Net Value Traded: {extracted_value}")
    else:
        print("Saudi → Sub Total (Individuals) → Net Value Traded: not found")


if __name__ == "__main__":
    main()
