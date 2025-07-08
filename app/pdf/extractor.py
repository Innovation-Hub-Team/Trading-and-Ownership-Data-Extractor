"""Module for extracting retained earnings data from PDF financial statements."""
import logging
import re
from decimal import Decimal
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
import PyPDF2
import pytesseract
from pdf2image import convert_from_path
from sqlalchemy.orm import Session

from app.models.models import Company, RetainedEarnings

logger = logging.getLogger(__name__)

class PDFExtractor:
    """Extractor for retained earnings data from PDF financial statements."""
    
    def __init__(self, tesseract_cmd: str, ocr_language: str = 'ara+eng'):
        self.tesseract_cmd = tesseract_cmd
        self.ocr_language = ocr_language
        pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
        
        # Regular expression for finding retained earnings in Arabic
        self.re_arabic = re.compile(r'الأرباح المبقاة\s*:?\s*([\d,]+\.?\d*)')
        # Regular expression for finding retained earnings in English
        self.re_english = re.compile(r'Retained Earnings\s*:?\s*([\d,]+\.?\d*)')

    def extract_retained_earnings(self, pdf_path: str) -> Tuple[Decimal, str, float]:
        """Extract retained earnings from a PDF file.
        
        Returns:
            Tuple containing:
            - The extracted amount as Decimal
            - The extraction method used ('text_extraction' or 'ocr')
            - Confidence score (0-100)
        """
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        # Try text extraction first
        try:
            amount, confidence = self._extract_from_text(pdf_path)
            if amount is not None:
                return amount, 'text_extraction', confidence
        except Exception as e:
            logger.warning(f"Text extraction failed for {pdf_path}: {e}")

        # Fall back to OCR
        try:
            amount, confidence = self._extract_from_ocr(pdf_path)
            if amount is not None:
                return amount, 'ocr', confidence
        except Exception as e:
            logger.error(f"OCR extraction failed for {pdf_path}: {e}")
            raise

        raise ValueError(f"Could not extract retained earnings from {pdf_path}")

    def _extract_from_text(self, pdf_path: Path) -> Tuple[Optional[Decimal], float]:
        """Extract retained earnings using PyPDF2 text extraction."""
        with open(pdf_path, 'rb') as f:
            pdf = PyPDF2.PdfReader(f)
            text = ''
            for page in pdf.pages:
                text += page.extract_text()

        # Try Arabic first
        match = self.re_arabic.search(text)
        if match:
            amount = self._parse_amount(match.group(1))
            return amount, 100.0  # High confidence for direct text extraction

        # Try English
        match = self.re_english.search(text)
        if match:
            amount = self._parse_amount(match.group(1))
            return amount, 100.0

        return None, 0.0

    def _extract_from_ocr(self, pdf_path: Path) -> Tuple[Optional[Decimal], float]:
        """Extract retained earnings using OCR."""
        # Convert PDF to images
        images = convert_from_path(pdf_path)
        
        for image in images:
            # Extract text using OCR
            text = pytesseract.image_to_string(image, lang=self.ocr_language)
            
            # Try Arabic first
            match = self.re_arabic.search(text)
            if match:
                amount = self._parse_amount(match.group(1))
                return amount, 80.0  # Lower confidence for OCR

            # Try English
            match = self.re_english.search(text)
            if match:
                amount = self._parse_amount(match.group(1))
                return amount, 80.0

        return None, 0.0

    def _parse_amount(self, amount_str: str) -> Decimal:
        """Parse amount string to Decimal, handling different formats."""
        # Remove commas and convert to Decimal
        amount_str = amount_str.replace(',', '')
        try:
            return Decimal(amount_str)
        except Exception as e:
            logger.error(f"Error parsing amount '{amount_str}': {e}")
            raise ValueError(f"Invalid amount format: {amount_str}")

    def save_retained_earnings(self, db: Session, company_id: int, year: int,
                             amount: Decimal, source_file: str,
                             extraction_method: str, confidence_score: float) -> RetainedEarnings:
        """Save extracted retained earnings to the database."""
        retained_earnings = RetainedEarnings(
            company_id=company_id,
            year=year,
            amount=amount,
            source_file=source_file,
            extraction_method=extraction_method,
            confidence_score=confidence_score
        )

        db.add(retained_earnings)
        db.commit()
        db.refresh(retained_earnings)
        
        return retained_earnings 