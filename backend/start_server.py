#!/usr/bin/env python3
"""
Start the Trading and Ownership Data Extractor API Server
"""

import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent / 'src'))

def main():
    """Start the Flask API server"""
    try:
        from api.evidence_api import create_app
        
        # Create the Flask app
        app = create_app()
        
        # Get port from environment or use default
        port = int(os.getenv('API_PORT', 5003))
        
        print("🚀 Trading and Ownership Data Extractor - API Server")
        print("=" * 60)
        print(f"   Port: {port}")
        print(f"   Extractor: Gemini Vision API")
        print()
        print("📡 Available Endpoints:")
        print("   • POST /api/upload_pdf - Upload single PDF")
        print("   • POST /api/upload_multiple_pdfs - Upload multiple PDFs")
        print("   • GET  /api/get_extracted_data - Get all data")
        print("   • GET  /api/get_screenshots - Get screenshots")
        print("   • GET  /api/health - Health check")
        print()
        print("📁 Data Directories:")
        print(f"   • Uploads: {Path('uploads').absolute()}")
        print(f"   • Data: {Path('data').absolute()}")
        print(f"   • Screenshots: {Path('output/screenshots').absolute()}")
        print()
        print(f"🌐 Server URL: http://localhost:{port}")
        print(f"🔗 Frontend: http://localhost:3000")
        print()
        print("Press Ctrl+C to stop the server")
        print("=" * 60)
        
        # Start the server
        app.run(
            host='0.0.0.0',
            port=port,
            debug=False,
            use_reloader=False
        )
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure you're in the backend directory and dependencies are installed:")
        print("   pip install -r requirements.txt")
        return 1
        
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
