#!/usr/bin/env python3
"""
Flask API for serving evidence screenshots and extraction metadata
"""

from flask import Flask, send_file, jsonify, request
from flask_cors import CORS
import json
import os
from pathlib import Path
import logging
import subprocess

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_app():
    app = Flask(__name__)
    # Allow CORS from React frontend
    CORS(app, origins=["http://localhost:3000", "http://127.0.0.1:3000"])

    # Always resolve paths relative to the project root
    PROJECT_ROOT = Path(__file__).parent.parent.parent.resolve()
    SCREENSHOTS_DIR = PROJECT_ROOT / "output/screenshots"
    RESULTS_FILE = PROJECT_ROOT / "data/results/retained_earnings_results.json"
    METADATA_FILE = SCREENSHOTS_DIR / "evidence_metadata.json"
    CSV_FILE = PROJECT_ROOT / "data/results/reinvested_earnings_results.csv"

    @app.route('/api/evidence/<company_symbol>.png')
    def get_evidence_screenshot(company_symbol):
        """
        Serve evidence screenshot for a specific company
        """
        try:
            screenshot_path = SCREENSHOTS_DIR / f"{company_symbol}_evidence.png"
            
            if not screenshot_path.exists():
                return jsonify({"error": "Evidence screenshot not found"}), 404
            
            return send_file(str(screenshot_path), mimetype='image/png')
            
        except Exception as e:
            logger.error(f"Error serving screenshot for {company_symbol}: {e}")
            return jsonify({"error": "Internal server error"}), 500

    @app.route('/api/extractions')
    def get_extractions():
        """
        Get all extraction results with evidence information
        """
        try:
            # Load extraction results
            with open(RESULTS_FILE, 'r', encoding='utf-8') as f:
                results = json.load(f)
            
            # Load evidence metadata if available
            evidence_metadata = {}
            if METADATA_FILE.exists():
                with open(METADATA_FILE, 'r', encoding='utf-8') as f:
                    evidence_data = json.load(f)
                    for item in evidence_data:
                        evidence_metadata[item['company_symbol']] = {
                            'has_evidence': True,
                            'screenshot_path': item['screenshot_path']
                        }
            
            # Add evidence information to results
            for result in results:
                company_symbol = result['company_symbol']
                if company_symbol in evidence_metadata:
                    result['evidence'] = evidence_metadata[company_symbol]
                else:
                    result['evidence'] = {'has_evidence': False}
            
            return jsonify({
                'extractions': results,
                'total': len(results),
                'successful': len([r for r in results if r['success']])
            })
            
        except Exception as e:
            logger.error(f"Error serving extractions: {e}")
            return jsonify({"error": "Internal server error"}), 500

    @app.route('/api/extractions/<company_symbol>')
    def get_extraction_by_company(company_symbol):
        """
        Get extraction result for a specific company
        """
        try:
            # Load extraction results
            with open(RESULTS_FILE, 'r', encoding='utf-8') as f:
                results = json.load(f)
            
            # Find the specific company
            company_result = None
            for result in results:
                if result['company_symbol'] == company_symbol:
                    company_result = result
                    break
            
            if not company_result:
                return jsonify({"error": "Company not found"}), 404
            
            # Add evidence information
            evidence_metadata = {}
            if METADATA_FILE.exists():
                with open(METADATA_FILE, 'r', encoding='utf-8') as f:
                    evidence_data = json.load(f)
                    for item in evidence_data:
                        if item['company_symbol'] == company_symbol:
                            company_result['evidence'] = {
                                'has_evidence': True,
                                'screenshot_path': item['screenshot_path']
                            }
                            break
                    else:
                        company_result['evidence'] = {'has_evidence': False}
            
            return jsonify(company_result)
            
        except Exception as e:
            logger.error(f"Error serving extraction for {company_symbol}: {e}")
            return jsonify({"error": "Internal server error"}), 500

    @app.route('/api/evidence/metadata')
    def get_evidence_metadata():
        """
        Get metadata about all available evidence screenshots
        """
        try:
            if not METADATA_FILE.exists():
                return jsonify({"evidence_screenshots": []})
            
            with open(METADATA_FILE, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            return jsonify({
                "evidence_screenshots": metadata,
                "total_screenshots": len(metadata)
            })
            
        except Exception as e:
            logger.error(f"Error serving evidence metadata: {e}")
            return jsonify({"error": "Internal server error"}), 500

    @app.route('/api/evidence/<company_symbol>')
    def get_evidence(company_symbol):
        """
        Get evidence data for a specific company
        """
        try:
            # Load extraction results
            with open(RESULTS_FILE, 'r', encoding='utf-8') as f:
                results = json.load(f)
            
            # Find the specific company
            company_result = None
            for result in results:
                if result['company_symbol'] == company_symbol:
                    company_result = result
                    break
            
            if not company_result:
                return jsonify({"error": "Company not found"}), 404
            
            # Load evidence metadata
            evidence_data = None
            if METADATA_FILE.exists():
                with open(METADATA_FILE, 'r', encoding='utf-8') as f:
                    evidence_list = json.load(f)
                    for item in evidence_list:
                        if item['company_symbol'] == company_symbol:
                            evidence_data = item
                            break
            
            # Prepare response
            response = {
                'company_symbol': company_symbol,
                'extracted_value': company_result.get('numeric_value'),
                'method': company_result.get('method', 'regex'),
                'confidence': company_result.get('confidence', 'medium'),
                'screenshot_url': None,
                'context': company_result.get('raw_match', '')
            }
            
            # Add screenshot URL if available
            if evidence_data:
                screenshot_filename = f"{company_symbol}_evidence.png"
                response['screenshot_url'] = f"/api/evidence/{company_symbol}.png"
            
            return jsonify(response)
            
        except Exception as e:
            logger.error(f"Error serving evidence for {company_symbol}: {e}")
            return jsonify({"error": "Internal server error"}), 500

    @app.route('/api/reinvested_earnings_results.csv')
    def get_reinvested_earnings_csv():
        """
        Serve the latest reinvested earnings CSV data
        """
        try:
            if not CSV_FILE.exists():
                return jsonify({"error": "CSV file not found"}), 404
            
            return send_file(str(CSV_FILE), mimetype='text/csv')
            
        except Exception as e:
            logger.error(f"Error serving CSV file: {e}")
            return jsonify({"error": "Internal server error"}), 500

    @app.route('/api/refresh', methods=['POST'])
    def refresh_data():
        """
        Refreshes the ownership data, recalculates reinvested earnings, and regenerates evidence screenshots.
        """
        try:
            # 1. Scrape latest ownership data
            subprocess.run(['python', 'src/scrapers/ownership.py'], check=True)
            # 2. Recalculate reinvested earnings
            subprocess.run(['python', 'src/calculators/calculate_reinvested_earnings.py'], check=True)
            # 3. Regenerate evidence screenshots
            subprocess.run(['python', 'src/utils/generate_evidence_screenshots.py'], check=True)
            return jsonify({"status": "success", "message": "Data refreshed and evidence regenerated"}), 200
        except subprocess.CalledProcessError as e:
            return jsonify({"status": "error", "message": str(e)}), 500
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500

    @app.route('/api/health')
    def health_check():
        """
        Health check endpoint
        """
        return jsonify({
            "status": "healthy",
            "screenshots_dir": str(SCREENSHOTS_DIR),
            "screenshots_available": SCREENSHOTS_DIR.exists()
        })

    return app

if __name__ == '__main__':
    app = create_app()
    
    # Ensure screenshots directory exists (use absolute path)
    PROJECT_ROOT = Path(__file__).parent.parent.parent.resolve()
    (PROJECT_ROOT / "output/screenshots").mkdir(parents=True, exist_ok=True)
    
    print(f"Starting Evidence API server...")
    print(f"Screenshots directory: {PROJECT_ROOT / 'output/screenshots'}")
    print(f"API will be available at: http://localhost:5002")
    
    app.run(debug=True, host='0.0.0.0', port=5002) 