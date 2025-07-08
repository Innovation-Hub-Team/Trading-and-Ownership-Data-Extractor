"""Module for calculating reinvested earnings."""
import logging
from datetime import date
from decimal import Decimal
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.models import (
    Company, OwnershipData, RetainedEarnings, ReinvestedEarnings
)

logger = logging.getLogger(__name__)

class ReinvestedEarningsCalculator:
    """Calculator for reinvested earnings based on retained earnings and ownership."""

    def __init__(self, db: Session):
        self.db = db

    def calculate_reinvested_earnings(self, company_id: int, year: int) -> Optional[ReinvestedEarnings]:
        """Calculate reinvested earnings for a company in a given year."""
        # Get the latest ownership data before or during the year
        ownership_data = self._get_latest_ownership_data(company_id, year)
        if not ownership_data:
            logger.warning(f"No ownership data found for company {company_id} in year {year}")
            return None

        # Get retained earnings for the year
        retained_earnings = self._get_retained_earnings(company_id, year)
        if not retained_earnings:
            logger.warning(f"No retained earnings found for company {company_id} in year {year}")
            return None

        # Calculate reinvested earnings
        amount = retained_earnings.amount * (ownership_data.ownership_percentage / Decimal('100'))
        
        # Create and save the reinvested earnings record
        reinvested = ReinvestedEarnings(
            company_id=company_id,
            year=year,
            retained_earnings_id=retained_earnings.id,
            ownership_data_id=ownership_data.id,
            amount=amount,
            calculation_date=date.today()
        )

        self.db.add(reinvested)
        self.db.commit()
        self.db.refresh(reinvested)
        
        return reinvested

    def calculate_all_reinvested_earnings(self, company_id: Optional[int] = None) -> List[ReinvestedEarnings]:
        """Calculate reinvested earnings for all companies or a specific company."""
        # Get all companies or a specific company
        query = self.db.query(Company)
        if company_id:
            query = query.filter(Company.id == company_id)
        companies = query.all()

        results = []
        for company in companies:
            # Get all years with retained earnings
            years = self.db.query(RetainedEarnings.year)\
                .filter(RetainedEarnings.company_id == company.id)\
                .distinct()\
                .all()
            
            for (year,) in years:
                try:
                    reinvested = self.calculate_reinvested_earnings(company.id, year)
                    if reinvested:
                        results.append(reinvested)
                except Exception as e:
                    logger.error(f"Error calculating reinvested earnings for {company.symbol} in {year}: {e}")

        return results

    def _get_latest_ownership_data(self, company_id: int, year: int) -> Optional[OwnershipData]:
        """Get the latest ownership data before or during the given year."""
        return self.db.query(OwnershipData)\
            .filter(
                and_(
                    OwnershipData.company_id == company_id,
                    OwnershipData.scrape_date <= date(year, 12, 31)
                )
            )\
            .order_by(OwnershipData.scrape_date.desc())\
            .first()

    def _get_retained_earnings(self, company_id: int, year: int) -> Optional[RetainedEarnings]:
        """Get retained earnings for a company in a given year."""
        return self.db.query(RetainedEarnings)\
            .filter(
                and_(
                    RetainedEarnings.company_id == company_id,
                    RetainedEarnings.year == year
                )
            )\
            .first()

    def get_reinvested_earnings_summary(self, company_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get a summary of reinvested earnings for all companies or a specific company."""
        query = self.db.query(
            Company.symbol,
            Company.arabic_name,
            ReinvestedEarnings.year,
            ReinvestedEarnings.amount,
            OwnershipData.ownership_percentage,
            RetainedEarnings.amount.label('retained_earnings_amount')
        ).join(
            ReinvestedEarnings,
            Company.id == ReinvestedEarnings.company_id
        ).join(
            OwnershipData,
            ReinvestedEarnings.ownership_data_id == OwnershipData.id
        ).join(
            RetainedEarnings,
            ReinvestedEarnings.retained_earnings_id == RetainedEarnings.id
        )

        if company_id:
            query = query.filter(Company.id == company_id)

        results = query.order_by(Company.symbol, ReinvestedEarnings.year).all()
        
        return [{
            'symbol': r.symbol,
            'arabic_name': r.arabic_name,
            'year': r.year,
            'retained_earnings': float(r.retained_earnings_amount),
            'ownership_percentage': float(r.ownership_percentage),
            'reinvested_earnings': float(r.amount)
        } for r in results] 