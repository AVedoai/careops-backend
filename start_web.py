#!/usr/bin/env python3
"""
Railway-compatible startup script for FastAPI
Handles PORT environment variable properly
"""
import os
import subprocess
import sys

def main():
    # Get port from environment or default to 8000
    port = os.getenv('PORT', '8000')
    
    # Start uvicorn with the correct port
    cmd = [
        'uvicorn', 
        'app.main:app', 
        '--host', '0.0.0.0', 
        '--port', port
    ]
    
    print(f"Starting FastAPI on port {port}")
    subprocess.run(cmd)

if __name__ == "__main__":
    main()