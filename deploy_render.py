#!/usr/bin/env python3
"""Deploy the AI Dev Studio platform to Render using their API."""
import os
import requests
import json
import time

RENDER_API_KEY = os.environ.get("RENDER_API_KEY")
if not RENDER_API_KEY:
    raise ValueError("RENDER_API_KEY environment variable is required")

RENDER_OWNER_ID = os.environ.get("RENDER_OWNER_ID")
if not RENDER_OWNER_ID:
    raise ValueError("RENDER_OWNER_ID environment variable is required")

HEADERS = {
    "Authorization": f"Bearer {RENDER_API_KEY}",
    "Content-Type": "application/json",
    "Accept": "application/json"
}

def create_web_service():
    """Create a web service on Render."""
    url = "https://api.render.com/v1/services"

    payload = {
        "service": {
            "name": "ai-dev-studio",
            "type": "web_service",
            "runtime": "python",
            "region": "oregon",
            "plan": "free",
            "serviceDetails": {
                "buildCommand": "pip install -r requirements.txt",
                "startCommand": "cd desktop_app && python app.py",
                "healthCheckPath": "/",
                "numInstances": 1
            }
        },
        "ownerId": RENDER_OWNER_ID
    }
    
    print(f"Creating web service with payload: {json.dumps(payload, indent=2)}")
    
    response = requests.post(url, headers=HEADERS, json=payload)
    print(f"Response status: {response.status_code}")
    print(f"Response body: {response.text}")
    
    return response.json()

def get_services():
    """Get all services."""
    url = f"https://api.render.com/v1/services?ownerId={RENDER_OWNER_ID}"
    response = requests.get(url, headers=HEADERS)
    print(f"Services response: {response.text}")
    return response.json()

if __name__ == "__main__":
    print("Checking existing services...")
    get_services()
    print("\n" + "="*50)
    print("Creating new web service...")
    result = create_web_service()
    print(f"\nResult: {json.dumps(result, indent=2)}")
