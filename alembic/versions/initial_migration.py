"""Initial migration

Revision ID: 001
Revises: 
Create Date: 2024-03-19 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create companies table
    op.create_table(
        'companies',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('symbol', sa.String(length=10), nullable=False),
        sa.Column('arabic_name', sa.String(length=255), nullable=False),
        sa.Column('english_name', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('symbol')
    )
    op.create_index(op.f('ix_companies_symbol'), 'companies', ['symbol'], unique=True)

    # Create ownership_data table
    op.create_table(
        'ownership_data',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('scrape_date', sa.Date(), nullable=False),
        sa.Column('ownership_percentage', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('source_url', sa.String(length=512), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create retained_earnings table
    op.create_table(
        'retained_earnings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('amount', sa.Numeric(precision=20, scale=2), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=True),
        sa.Column('source_file', sa.String(length=512), nullable=True),
        sa.Column('extraction_method', sa.String(length=50), nullable=True),
        sa.Column('confidence_score', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create reinvested_earnings table
    op.create_table(
        'reinvested_earnings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('retained_earnings_id', sa.Integer(), nullable=False),
        sa.Column('ownership_data_id', sa.Integer(), nullable=False),
        sa.Column('amount', sa.Numeric(precision=20, scale=2), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=True),
        sa.Column('calculation_date', sa.Date(), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
        sa.ForeignKeyConstraint(['ownership_data_id'], ['ownership_data.id'], ),
        sa.ForeignKeyConstraint(['retained_earnings_id'], ['retained_earnings.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('reinvested_earnings')
    op.drop_table('retained_earnings')
    op.drop_table('ownership_data')
    op.drop_index(op.f('ix_companies_symbol'), table_name='companies')
    op.drop_table('companies') 