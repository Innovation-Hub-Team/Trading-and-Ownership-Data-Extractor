# Foreign Investment Analysis Tool

A backend system for analyzing foreign investment in Saudi companies by calculating reinvested earnings based on retained earnings and foreign ownership percentages.

## Features

- Scrapes foreign ownership data from Tadawul
- Downloads and processes financial statements (PDFs)
- Extracts retained earnings data using text extraction and OCR
- Calculates reinvested earnings for foreign shareholders
- Stores all data in a SQL database

## Project Structure

```
.
├── alembic/                  # Database migrations
├── app/
│   ├── models/              # SQLAlchemy models
│   ├── scrapers/           # Web scrapers for Tadawul
│   ├── pdf/                # PDF processing and extraction
│   ├── calculator/         # Earnings calculation logic
│   └── cli/                # Command-line interface
├── data/                   # Data storage
│   ├── pdfs/              # Downloaded PDFs
│   └── raw/               # Raw scraped data
├── tests/                  # Test suite
├── .env                    # Environment variables
├── requirements.txt        # Project dependencies
└── README.md              # This file
```

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. Initialize the database:
```bash
alembic upgrade head
```

## Usage

Run the full pipeline:
```bash
python -m app.cli.main run-pipeline
```

## Development

- Database migrations: `alembic revision --autogenerate -m "description"`
- Run tests: `pytest`
- Format code: `black .`
- Type checking: `mypy .` 