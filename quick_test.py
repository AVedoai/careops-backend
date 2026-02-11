#!/usr/bin/env python3
"""
Manual Step-by-Step CareOps Backend Test
This runs one API call at a time to show exactly what's working and what isn't
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_with_output(name, method, url, **kwargs):
    print(f"\n{'='*50}")
    print(f"Testing: {name}")
    print(f"Method: {method}")
    print(f"URL: {url}")
    if 'json' in kwargs:
        print(f"JSON Data: {kwargs['json']}")
    if 'data' in kwargs:
        print(f"Form Data: {kwargs['data']}")
    if 'headers' in kwargs:
        print(f"Headers: {kwargs['headers']}")
    
    try:
        if method == "GET":
            response = requests.get(url, **kwargs)
        elif method == "POST":
            response = requests.post(url, **kwargs)
        elif method == "PUT":
            response = requests.put(url, **kwargs)
        
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:500]}...")
        
        if response.status_code == 200:
            return response.json()
        else:
            return None
            
    except Exception as e:
        print(f"Error: {e}")
        return None

def manual_test():
    print("🔧 CareOps Backend Manual Test")
    print("Testing each endpoint step by step")
    
    # 1. Health check
    health = test_with_output(
        "Health Check",
        "GET", 
        f"{BASE_URL}/health"
    )
    
    # 2. Login (user should exist from previous tests)
    login_data = {
        "username": "sarah@wellnessspa.com",
        "password": "SecurePass123!"
    }
    
    login_result = test_with_output(
        "User Login",
        "POST",
        f"{BASE_URL}/api/v1/auth/login",
        data=login_data
    )
    
    if not login_result or 'access_token' not in login_result:
        print("❌ Cannot continue without token")
        return
        
    token = login_result['access_token']
    headers = {"Authorization": f"Bearer {token}"}
    
    # 3. Get current workspace
    workspace = test_with_output(
        "Get Workspace",
        "GET",
        f"{BASE_URL}/api/v1/workspaces/me",
        headers=headers
    )
    
    # 4. Create simple service
    service_data = {
        "name": "Test Massage",
        "duration_minutes": 60,
        "description": "Test service"
    }
    
    service = test_with_output(
        "Create Service",
        "POST",
        f"{BASE_URL}/api/v1/services",
        json=service_data,
        headers=headers
    )
    
    # 5. List services
    services = test_with_output(
        "List Services",
        "GET",
        f"{BASE_URL}/api/v1/services",
        headers=headers
    )
    
    # 6. Test public contact form
    contact_data = {
        "full_name": "Test Customer",
        "email": "test@example.com",
        "message": "Test message"
    }
    
    contact = test_with_output(
        "Public Contact Form",
        "POST",
        f"{BASE_URL}/api/v1/public/contact-form/wellness-spa",
        json=contact_data
    )
    
    # 7. List conversations
    conversations = test_with_output(
        "List Conversations",
        "GET",
        f"{BASE_URL}/api/v1/conversations",
        headers=headers
    )
    
    # 8. Get dashboard
    dashboard = test_with_output(
        "Dashboard Data",
        "GET",
        f"{BASE_URL}/api/v1/workspaces/dashboard",
        headers=headers
    )
    
    print("\n" + "="*50)
    print("Manual test complete!")

if __name__ == "__main__":
    manual_test()