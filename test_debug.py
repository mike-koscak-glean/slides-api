#!/usr/bin/env python3
"""
Debug script to test the API locally and identify issues
"""

import requests
import json

# Test the API endpoints
API_URL = "https://slides-content-api-300643503209.us-central1.run.app"

def test_health():
    """Test the health endpoint"""
    print("Testing health endpoint...")
    try:
        response = requests.get(f"{API_URL}/")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return True
    except Exception as e:
        print(f"Health check failed: {e}")
        return False

def test_read_endpoint():
    """Test the read endpoint with a sample document ID"""
    print("\nTesting read endpoint...")
    
    # Use a test document ID - replace with an actual one you have access to
    test_data = {
        "document_id": "1gJ07qLdyubfQjl-VIqM3tle7g4CxtHsexLvLuvu5u0c"  # Replace with real doc ID
    }
    
    try:
        response = requests.post(
            f"{API_URL}/slides/read", 
            json=test_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Success! Document title: {result.get('title', 'Unknown')}")
            print(f"Total slides: {result.get('total_slides', 0)}")
            print(f"Empty cells found: {len(result.get('empty_cells', {}))}")
        else:
            print(f"Error response: {response.text}")
            
    except Exception as e:
        print(f"Request failed: {e}")

def test_with_invalid_doc():
    """Test with an invalid document ID to see error handling"""
    print("\nTesting with invalid document ID...")
    
    test_data = {
        "document_id": "invalid_doc_id"
    }
    
    try:
        response = requests.post(
            f"{API_URL}/slides/read", 
            json=test_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    print("=== API Debug Test ===")
    
    # Test health first
    if not test_health():
        print("Health check failed, stopping tests")
        exit(1)
    
    # Test read endpoint
    test_read_endpoint()
    
    # Test error handling
    test_with_invalid_doc()
    
    print("\n=== Common Issues to Check ===")
    print("1. Service account has access to the document")
    print("2. Document ID is correct and public/shared")
    print("3. Google Slides API is enabled")
    print("4. Service account key is valid")