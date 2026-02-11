#!/usr/bin/env python3
"""
Quick Manual Test Commands for CareOps Platform
Run these commands individually to test specific features
"""

import requests
import json

BASE_URL = "http://localhost:8000"

# Get a token first
def get_token():
    response = requests.post(f"{BASE_URL}/api/v1/auth/register", json={
        "email": "test@wellnessspa.com",
        "password": "SecurePass123!",
        "full_name": "Test User"
    })
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print("Failed to get token")
        return None

# Test commands
if __name__ == "__main__":
    print("🔧 CareOps Manual Test Commands")
    print("=" * 40)
    
    # Health check
    print("1. Health Check:")
    print(f"curl {BASE_URL}/health")
    
    # Register user  
    print("\n2. Register User:")
    print(f'curl -X POST {BASE_URL}/api/v1/auth/register -H "Content-Type: application/json" -d \'{{"email":"sarah@wellnessspa.com","password":"SecurePass123!","full_name":"Sarah Johnson"}}\'')
    
    # Login
    print("\n3. Login:")
    print(f'curl -X POST {BASE_URL}/api/v1/auth/login -H "Content-Type: application/json" -d \'{{"email":"sarah@wellnessspa.com","password":"SecurePass123!"}}\'')
    
    # Get token and show authenticated requests
    token = get_token()
    if token:
        print(f"\n🔑 Your token: {token}")
        
        print("\n4. Onboard Workspace:")
        print(f'curl -X POST {BASE_URL}/api/v1/workspaces/onboarding -H "Authorization: Bearer {token}" -H "Content-Type: application/json" -d \'{{"business_name":"Wellness Spa","address":"123 Main St, Austin, TX","timezone":"America/Chicago","contact_email":"hello@wellnessspa.com"}}\'')
        
        print(f"\n5. Activate Workspace:")
        print(f'curl -X POST {BASE_URL}/api/v1/workspaces/activate -H "Authorization: Bearer {token}"')
        
        print(f"\n6. Create Service:")
        print(f'curl -X POST {BASE_URL}/api/v1/services -H "Authorization: Bearer {token}" -H "Content-Type: application/json" -d \'{{"name":"60-Min Massage","duration":60,"price":120.00,"location":"123 Main St, Austin, TX"}}\'')
        
        print(f"\n7. List Conversations (Inbox):")
        print(f'curl -X GET {BASE_URL}/api/v1/conversations -H "Authorization: Bearer {token}"')
        
        print(f"\n8. Get Dashboard:")
        print(f'curl -X GET {BASE_URL}/api/v1/workspaces/dashboard -H "Authorization: Bearer {token}"')
        
        print(f"\n9. List Forms:")
        print(f'curl -X GET {BASE_URL}/api/v1/forms -H "Authorization: Bearer {token}"')
        
        print(f"\n10. List Contacts:")
        print(f'curl -X GET {BASE_URL}/api/v1/contacts -H "Authorization: Bearer {token}"')
    
    print(f"\n📞 Public Endpoints (No Auth Required):")
    print(f"11. Submit Contact Form:")