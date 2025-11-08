"""
Start Marketplace API Server

Run this script to start the marketplace API server.
"""

import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from marketplace.api import start_server

if __name__ == "__main__":
    print("="*70)
    print("🏪 AI AGENT MARKETPLACE API")
    print("="*70)
    print("Starting server on http://localhost:8000")
    print("API Documentation: http://localhost:8000/docs")
    print("Interactive API: http://localhost:8000/redoc")
    print("="*70)
    print()
    
    try:
        start_server(host="0.0.0.0", port=8000)
    except KeyboardInterrupt:
        print("\n\nShutting down marketplace API...")
        print("Goodbye! 👋")
