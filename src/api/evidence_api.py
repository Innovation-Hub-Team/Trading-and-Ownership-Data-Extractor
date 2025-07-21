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
from datetime import datetime
import pandas as pd

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
        Refreshes the data by recalculating reinvested earnings and regenerating evidence screenshots.
        Note: Ownership data scraping is disabled due to browser issues.
        """
        try:
            logger.info("Starting data refresh...")
            
            # 1. Recalculate reinvested earnings (this is the main step)
            logger.info("Recalculating reinvested earnings...")
            try:
                subprocess.run(['python', 'src/calculators/calculate_reinvested_earnings.py'], 
                             check=True, capture_output=True, text=True)
                logger.info("Reinvested earnings calculation completed successfully")
            except subprocess.CalledProcessError as e:
                logger.error(f"Error in reinvested earnings calculation: {e}")
                return jsonify({
                    "status": "error", 
                    "message": f"Failed to recalculate earnings: {e.stderr}"
                }), 500
            
            # 2. Regenerate evidence screenshots (optional)
            logger.info("Regenerating evidence screenshots...")
            try:
                subprocess.run(['python', 'src/utils/generate_evidence_screenshots.py'], 
                             check=True, capture_output=True, text=True)
                logger.info("Evidence screenshots regeneration completed successfully")
            except subprocess.CalledProcessError as e:
                logger.warning(f"Evidence screenshots regeneration failed: {e}")
                # Don't fail the entire refresh for this step
                pass
            
            logger.info("Data refresh completed successfully")
            return jsonify({
                "status": "success", 
                "message": "Data refreshed successfully. Note: Ownership data was not updated due to browser issues."
            }), 200
            
        except Exception as e:
            logger.error(f"Error during data refresh: {e}")
            return jsonify({
                "status": "error", 
                "message": f"Refresh failed: {str(e)}"
            }), 500

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

    @app.route('/api/correct_retained_earnings', methods=['POST'])
    def correct_retained_earnings():
        data = request.json
        company_symbol = data.get('company_symbol')
        correct_value = data.get('correct_value')
        feedback = data.get('feedback', '')
        if not company_symbol or not correct_value:
            return jsonify({'error': 'Missing company_symbol or correct_value'}), 400

        # Load retained earnings results
        results_file = PROJECT_ROOT / "data/results/retained_earnings_results.json"
        try:
            with open(results_file, 'r', encoding='utf-8') as f:
                results = json.load(f)
        except Exception as e:
            return jsonify({'error': f'Failed to load results: {e}'}), 500

        # Update the value for the company
        updated = False
        for entry in results:
            if entry.get('company_symbol') == company_symbol:
                entry['value'] = correct_value
                entry['numeric_value'] = float(str(correct_value).replace(',', ''))
                entry['method'] = 'manual_correction'
                entry['confidence'] = 'high'
                entry['flag_for_review'] = False
                updated = True
                break
        if not updated:
            # If not found, add a new entry
            results.append({
                'company_symbol': company_symbol,
                'value': correct_value,
                'numeric_value': float(str(correct_value).replace(',', '')),
                'method': 'manual_correction',
                'confidence': 'high',
                'flag_for_review': False,
                'success': True
            })
        # Save back
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        # Log the correction
        corrections_log = PROJECT_ROOT / "data/results/corrections_log.json"
        try:
            if corrections_log.exists():
                with open(corrections_log, 'r', encoding='utf-8') as f:
                    log = json.load(f)
            else:
                log = []
            log.append({
                'company_symbol': company_symbol,
                'correct_value': correct_value,
                'feedback': feedback,
                'timestamp': datetime.now().isoformat()
            })
            with open(corrections_log, 'w', encoding='utf-8') as f:
                json.dump(log, f, ensure_ascii=False, indent=2)
        except Exception as e:
            pass  # Don't block on logging

        # Trigger recalculation
        try:
            subprocess.run(["python", str(PROJECT_ROOT / "src/calculators/calculate_reinvested_earnings.py")], check=True)
        except Exception as e:
            return jsonify({'error': f'Correction saved, but recalculation failed: {e}'}), 500

        # Load updated CSV and return the new values for this company
        csv_file = PROJECT_ROOT / "data/results/reinvested_earnings_results.csv"
        try:
            df = pd.read_csv(csv_file)
            row = df[df['company_symbol'] == int(company_symbol)]
            if not row.empty:
                result = row.iloc[0].to_dict()
                return jsonify({'status': 'success', 'updated': result})
            else:
                return jsonify({'status': 'success', 'updated': None})
        except Exception as e:
            return jsonify({'status': 'success', 'updated': None, 'warning': f'Correction saved, but failed to load updated CSV: {e}'})

    @app.route('/api/export_excel', methods=['GET'])
    def export_excel():
        """
        Export dashboard table data to Excel file
        """
        try:
            import sys
            from pathlib import Path
            import json
            
            # Add project root to Python path
            project_root = Path(__file__).parent.parent.parent
            sys.path.insert(0, str(project_root))
            
            from src.utils.export_to_excel import ExcelExporter
            import pandas as pd
            
            # Create exporter
            exporter = ExcelExporter()
            
            # Load foreign ownership data (JSON)
            ownership_json_path = project_root / "data/ownership/foreign_ownership_data.json"
            if not ownership_json_path.exists():
                return jsonify({"error": "Ownership data file not found"}), 404
            
            with open(ownership_json_path, 'r', encoding='utf-8') as f:
                ownership_data = json.load(f)
            
            # Load reinvested earnings data (CSV)
            csv_path = project_root / "data/results/reinvested_earnings_results.csv"
            if not csv_path.exists():
                return jsonify({"error": "Earnings data file not found"}), 404
            
            earnings_data = pd.read_csv(csv_path)
            
            # Create a map of earnings data by symbol
            earnings_map = {}
            for _, row in earnings_data.iterrows():
                symbol = str(row.get('company_symbol', '')).strip()
                if symbol:
                    earnings_map[symbol] = {
                        'retained_earnings': row.get('retained_earnings', ''),
                        'reinvested_earnings': row.get('reinvested_earnings', ''),
                        'year': row.get('year', ''),
                        'error': row.get('error', '')
                    }
            
            # Merge the data like the frontend does
            merged_data = []
            for ownership_row in ownership_data:
                symbol = str(ownership_row.get('symbol', '')).strip()
                earnings_info = earnings_map.get(symbol, {})
                
                merged_row = {
                    'company_symbol': symbol,
                    'company_name': ownership_row.get('company_name', ''),
                    'foreign_ownership': ownership_row.get('foreign_ownership', ''),
                    'max_allowed': ownership_row.get('max_allowed', ''),
                    'investor_limit': ownership_row.get('investor_limit', ''),
                    'retained_earnings': earnings_info.get('retained_earnings', ''),
                    'reinvested_earnings': earnings_info.get('reinvested_earnings', ''),
                    'year': earnings_info.get('year', ''),
                    'error': earnings_info.get('error', '')
                }
                merged_data.append(merged_row)
            
            # Convert to DataFrame
            data = pd.DataFrame(merged_data)
            
            # Export dashboard table
            output_path = exporter.export_dashboard_table(data)
            
            if output_path:
                # Return the file for download
                return send_file(
                    output_path,
                    as_attachment=True,
                    download_name=f"financial_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )
            else:
                return jsonify({"error": "Failed to create Excel file"}), 500
                
        except Exception as e:
            logger.error(f"Error exporting to Excel: {e}")
            return jsonify({"error": f"Export failed: {str(e)}"}), 500

    @app.route('/api/update_ownership', methods=['POST'])
    def update_ownership_data():
        """
        Manual endpoint to update ownership data (alternative to scraper)
        """
        try:
            logger.info("Manual ownership data update requested...")
            
            # Check if ownership scraper exists and try to run it
            ownership_script = PROJECT_ROOT / "src/scrapers/ownership.py"
            if ownership_script.exists():
                try:
                    logger.info("Attempting to run ownership scraper...")
                    result = subprocess.run(['python', str(ownership_script)], 
                                         check=True, capture_output=True, text=True, timeout=300)
                    logger.info("Ownership data updated successfully")
                    return jsonify({
                        "status": "success", 
                        "message": "Ownership data updated successfully"
                    }), 200
                except subprocess.TimeoutExpired:
                    logger.error("Ownership scraper timed out")
                    return jsonify({
                        "status": "error", 
                        "message": "Ownership scraper timed out. Please try again later."
                    }), 500
                except subprocess.CalledProcessError as e:
                    logger.error(f"Ownership scraper failed: {e.stderr}")
                    return jsonify({
                        "status": "error", 
                        "message": f"Ownership scraper failed: {e.stderr}"
                    }), 500
            else:
                return jsonify({
                    "status": "error", 
                    "message": "Ownership scraper not found"
                }), 404
                
        except Exception as e:
            logger.error(f"Error updating ownership data: {e}")
            return jsonify({
                "status": "error", 
                "message": f"Failed to update ownership data: {str(e)}"
            }), 500

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