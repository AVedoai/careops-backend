#!/usr/bin/env python3
"""
Script to start the development server with hot reloading

Usage:
    python scripts/dev_server.py [--host HOST] [--port PORT]

Examples:
    python scripts/dev_server.py
    python scripts/dev_server.py --host 0.0.0.0 --port 8001
"""

import os
import sys
import argparse
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def main():
    parser = argparse.ArgumentParser(description='Start development server')
    parser.add_argument(
        '--host',
        default='127.0.0.1',
        help='Host to bind to (default: 127.0.0.1)'
    )
    parser.add_argument(
        '--port', '-p',
        type=int,
        default=8000,
        help='Port to bind to (default: 8000)'
    )
    parser.add_argument(
        '--reload',
        action='store_true',
        default=True,
        help='Enable auto-reload on code changes (default: True)'
    )
    parser.add_argument(
        '--log-level',
        default='info',
        choices=['critical', 'error', 'warning', 'info', 'debug', 'trace'],
        help='Log level (default: info)'
    )
    
    args = parser.parse_args()
    
    print(f"🚀 Starting CareOps development server...")
    print(f"🌍 Server: http://{args.host}:{args.port}")
    print(f"📚 API Docs: http://{args.host}:{args.port}/docs")
    print(f"💬 ReDoc: http://{args.host}:{args.port}/redoc")
    print(f"❤️ Health Check: http://{args.host}:{args.port}/health")
    print()
    
    try:
        import uvicorn
        uvicorn.run(
            "app.main:app",
            host=args.host,
            port=args.port,
            reload=args.reload,
            log_level=args.log_level,
            access_log=True
        )
    except ImportError:
        print("❌ uvicorn not installed. Please run: pip install uvicorn[standard]")
        sys.exit(1)
    except KeyboardInterrupt:
        print("✋ Development server stopped.")
        sys.exit(0)


if __name__ == '__main__':
    main()