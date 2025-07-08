from datetime import date
from decimal import Decimal
from typing import Optional

from sqlalchemy import Column, Integer, String, Date, Numeric, ForeignKey, Text
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin

class Company(Base, TimestampMixin):
    """Company information."""
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True)
    symbol = Column(String(10), unique=True, nullable=False, index=True)
    arabic_name = Column(String(255), nullable=False)
    english_name = Column(String(255))
    
    # Relationships
    ownership_data = relationship("OwnershipData", back_populates="company")
    retained_earnings = relationship("RetainedEarnings", back_populates="company")
    reinvested_earnings = relationship("ReinvestedEarnings", back_populates="company")

class OwnershipData(Base, TimestampMixin):
    """Foreign ownership data scraped from Tadawul."""
    __tablename__ = "ownership_data"

    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    year = Column(Integer, nullable=False)  # Year of the ownership data
    scrape_date = Column(Date)  # Made optional since we use year
    ownership_percentage = Column(Numeric(5, 2), nullable=False)  # Stores percentage with 2 decimal places
    source_url = Column(String(512))
    notes = Column(Text)

    # Relationships
    company = relationship("Company", back_populates="ownership_data")

class RetainedEarnings(Base, TimestampMixin):
    """Retained earnings extracted from financial statements."""
    __tablename__ = "retained_earnings"

    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    year = Column(Integer, nullable=False)
    amount = Column(Numeric(20, 2), nullable=False)  # Large numbers with 2 decimal places
    currency = Column(String(3), default="SAR")
    source_file = Column(String(512))  # Path to the PDF file
    extraction_method = Column(String(50))  # e.g., "text_extraction" or "ocr"
    confidence_score = Column(Numeric(5, 2))  # Confidence in the extraction (0-100)
    notes = Column(Text)

    # Relationships
    company = relationship("Company", back_populates="retained_earnings")

class ReinvestedEarnings(Base, TimestampMixin):
    """Calculated reinvested earnings for foreign shareholders."""
    __tablename__ = "reinvested_earnings"

    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    year = Column(Integer, nullable=False)
    retained_earnings_id = Column(Integer, ForeignKey("retained_earnings.id"), nullable=False)
    ownership_data_id = Column(Integer, ForeignKey("ownership_data.id"), nullable=False)
    amount = Column(Numeric(20, 2), nullable=False)  # Calculated amount
    currency = Column(String(3), default="SAR")
    calculation_date = Column(Date, nullable=False)
    notes = Column(Text)

    # Relationships
    company = relationship("Company", back_populates="reinvested_earnings")
    retained_earnings = relationship("RetainedEarnings")
    ownership_data = relationship("OwnershipData") 