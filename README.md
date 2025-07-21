# Financial Analysis System - Foreign Investment

python src/api/evidence_api.py
npm start


A comprehensive system for analyzing foreign investment in Saudi companies by scraping ownership data, extracting financial information from PDFs, and calculating reinvested earnings with evidence-based verification.

## 🏗️ System Architecture

```
Financial Analysis System
├── 📊 Data Collection (Scrapers)
│   ├── Foreign ownership data from Tadawul
│   └── Financial reports (PDFs) from company profiles
├── 🔍 Data Extraction (Extractors)
│   └── Retained earnings from PDF financial statements
├── 🧮 Calculations (Calculators)
│   └── Reinvested earnings = Retained earnings × Foreign ownership %
├── 🌐 Evidence System (API + Frontend)
│   ├── Evidence screenshots with highlighted values
│   └── React frontend for data visualization
```

## 📁 Project Structure

```
Foreign Investment/
├── src/                          # Main source code
│   ├── scrapers/                 # Web scraping modules
│   │   ├── ownership.py         # Tadawul ownership scraper
│   │   └── hybrid_financial_downloader.py  # PDF downloader
│   ├── extractors/              # PDF processing modules
│   │   └── extract_retained_earnings_all_pdfs.py
│   ├── calculators/             # Financial calculations
│   │   └── calculate_reinvested_earnings.py
│   ├── api/                     # Evidence API server
│   │   └── evidence_api.py
│   └── utils/                   # Utility modules
│       └── generate_evidence_screenshots.py
├── data/                        # Data storage
│   ├── pdfs/                   # Downloaded financial reports
│   ├── ownership/              # Scraped ownership data
│   └── results/                # Extraction results
├── output/                      # Generated outputs
│   └── screenshots/            # Evidence screenshots
├── frontend/                    # React frontend
│   └── src/
├── main.py                      # Main orchestration script
└── requirements.txt             # Python dependencies
```

## 🚀 Quick Start

### 1. Setup Environment
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Run Complete Workflow
```bash
# Run the entire system
python main.py --full
```

### 3. Start Frontend
```bash
cd frontend
npm install
npm start
```

## 🔄 Workflow Steps

### Step 1: Scrape Ownership Data
Scrapes foreign ownership percentages from Tadawul website.
```bash
python main.py --scrape-ownership
```

### Step 2: Download Financial Reports
Downloads annual financial reports (PDFs) from company profiles.
```bash
python main.py --download-pdfs
```

### Step 3: Extract Retained Earnings
Processes PDFs to extract retained earnings using LLM + regex.
```bash
python main.py --extract-earnings
```

### Step 4: Calculate Reinvested Earnings
Combines ownership data with retained earnings to calculate reinvested amounts.
```bash
python main.py --calculate
```

### Step 5: Evidence System
Generates evidence screenshots and starts API server.
```bash
python main.py --evidence-api
```

## 📊 Data Flow

1. **Scrape Ownership Data** → `data/ownership/foreign_ownership_data.csv`
2. **Download PDFs** → `data/pdfs/`
3. **Extract Retained Earnings** → `data/results/retained_earnings_results.json`
4. **Calculate Reinvested Earnings** → `frontend/public/reinvested_earnings_results.csv`
5. **Generate Evidence** → `output/screenshots/`
6. **Display Results** → React frontend with evidence API

## 🛠️ Key Features

### 🔍 Advanced PDF Extraction
- **LLM-powered extraction** using GPT-4 for context understanding
- **Regex fallback** for reliable pattern matching
- **Layout-aware processing** using PyMuPDF
- **Evidence generation** with highlighted screenshots

### 📊 Comprehensive Data Collection
- **Foreign ownership scraping** from Tadawul website
- **Financial report downloading** from company profiles
- **Stealth browser automation** to avoid detection

### 🧮 Financial Calculations
- **Reinvested earnings calculation**: `Retained Earnings × Foreign Ownership %`
- **Data validation** and error handling
- **CSV export** for further analysis

### 🌐 Evidence System
- **Evidence API** serving screenshots and metadata
- **React frontend** with evidence modal
- **Real-time data** with confidence scores
- **Excel Export** with formatted multi-sheet reports

## 📈 Sample Output

The system produces:
- **Foreign ownership data** with percentages
- **Retained earnings** extracted from financial statements
- **Reinvested earnings** calculated for foreign shareholders
- **Evidence screenshots** showing highlighted values
- **Interactive dashboard** with evidence verification
- **Excel reports** with multiple formatted sheets

## 📊 Excel Export Features

The system includes comprehensive Excel export functionality:

### **Multiple Sheets**
- **ملخص النتائج (Summary)**: Key metrics and statistics
- **البيانات الرئيسية (Main Data)**: Complete dataset with all companies
- **الاستخراج الناجح (Successful Extractions)**: Only successful extractions
- **الاستخراج الفاشل (Failed Extractions)**: Failed extractions for review
- **تحليل حسب السنة (Year Analysis)**: Statistics grouped by year

### **Professional Formatting**
- **Arabic headers** and right-to-left text alignment
- **Color-coded headers** with green theme
- **Number formatting** with thousands separators
- **Auto-sized columns** for optimal readability
- **Borders and styling** for professional appearance

### **Export Methods**
1. **Frontend Button**: Click "تصدير Excel" in the web interface
2. **API Endpoint**: `GET /api/export_excel`
3. **Command Line**: `python src/utils/export_to_excel.py`
4. **Demo Script**: `python export_excel_demo.py`

### **Sample Excel Structure**
```
ملخص النتائج:
- إجمالي الشركات: 53
- الاستخراج الناجح: 25
- نسبة النجاح: 47.2%
- إجمالي الأرباح المبقاة: 8,234,567,890
- إجمالي الأرباح المعاد استثمارها: 1,234,567,890

البيانات الرئيسية:
- رمز الشركة | اسم الشركة | السنة | الأرباح المبقاة | نسبة ملكية الأجانب | الأرباح المعاد استثمارها
```

## 🔧 Configuration

### Environment Variables
```bash
export OPENAI_API_KEY="your-openai-api-key"  # For LLM extraction
```

### API Endpoints
- `GET /api/health` - Health check
- `GET /api/extractions` - All extraction results
- `GET /api/evidence/{company}` - Evidence for specific company
- `GET /api/evidence/{company}.png` - Evidence screenshot

## 🛡️ Error Handling

- **Graceful degradation** from LLM to regex extraction
- **Comprehensive logging** for debugging
- **Data validation** at each step
- **Evidence generation** for verification

## 📝 Dependencies

### Python Packages
- `playwright` - Web scraping and automation
- `fitz` (PyMuPDF) - PDF processing
- `openai` - LLM integration
- `flask` - API server
- `pandas` - Data manipulation

### Frontend
- React with modern UI components
- Evidence modal with screenshot display
- Real-time data updates

## 🤝 Contributing

1. Follow the modular structure
2. Add tests for new features
3. Update documentation
4. Use type hints and docstrings

## 📄 License

This project is for financial analysis and research purposes. 