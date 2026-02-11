#!/usr/bin/env python3
"""
Health check script for Railway deployment
Run this to verify your deployed backend is working correctly
"""

import requests
import sys
import os
from typing import Dict, Any

def test_endpoint(url: str, expected_status: int = 200) -> Dict[str, Any]:
    """Test an endpoint and return results"""
    try:
        response = requests.get(url, timeout=10)
        return {
            "url": url,
            "status": response.status_code,
            "success": response.status_code == expected_status,
            "response": response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text[:200]
        }
    except Exception as e:
        return {
            "url": url,
            "status": 0,
            "success": False,
            "error": str(e)
        }

def main():
    # Get base URL from command line or environment
    base_url = sys.argv[1] if len(sys.argv) > 1 else os.getenv('BACKEND_URL', 'http://localhost:8000')
    
    if not base_url.startswith('http'):
        base_url = f'https://{base_url}'
    
    print(f"🔍 Testing CareOps Backend at: {base_url}")
    print("=" * 50)
    
    # Test endpoints
    tests = [
        f"{base_url}/health",
        f"{base_url}/docs",  # FastAPI auto-docs
    ]
    
    results = []
    for test_url in tests:
        result = test_endpoint(test_url)
        results.append(result)
        
        status_icon = "✅" if result["success"] else "❌"
        print(f"{status_icon} {result['url']}")
        if result["success"]:
            print(f"   Status: {result['status']}")
            print(f"   Response: {result.get('response', 'N/A')}")
        else:
            print(f"   Error: {result.get('error', f'Status {result['status']}')}")
        print()
    
    # Summary
    successful = sum(1 for r in results if r["success"])
    total = len(results)
    
    print("=" * 50)
    if successful == total:
        print(f"🎉 All tests passed! ({successful}/{total})")
        print("Your backend is ready for frontend integration!")
    else:
        print(f"⚠️  Some tests failed ({successful}/{total})")
        print("Check the errors above and verify your deployment.")
        sys.exit(1)

if __name__ == "__main__":
    main()