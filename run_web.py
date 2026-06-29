#!/usr/bin/env python3
"""
Quick start script for Rover Mission Control Web App
"""

import sys
import os
from pathlib import Path

# Ensure we can import from the project
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def main():
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║          🚀 Rover Mission Control Web Server 🚀          ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
    """)

    print("Checking dependencies...")

    try:
        import flask
        import flask_cors
        import flask_socketio
        print("✓ Flask dependencies installed")
    except ImportError as e:
        print(f"✗ Missing dependency: {e}")
        print("\nInstall dependencies with:")
        print("  pip install -r requirements.txt")
        sys.exit(1)

    print("✓ All dependencies available")
    print("\nStarting server...\n")

    try:
        from app import app, socketio
        print("=" * 60)
        print("🌐 Server running at: http://localhost:5000")
        print("📊 Open this URL in your web browser to access Mission Control")
        print("=" * 60 + "\n")
        socketio.run(app, debug=True, host="0.0.0.0", port=5000)
    except ImportError as e:
        print(f"✗ Error importing app: {e}")
        print("\nMake sure you're in the AI-Lab-Robot directory")
        sys.exit(1)

if __name__ == "__main__":
    main()
