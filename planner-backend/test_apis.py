#!/usr/bin/env python3
"""
Test script for Preauth Agent APIs
"""

import asyncio
import httpx
import json
from datetime import datetime

BASE_URL = "http://host.docker.internal:8001"

async def test_health_check():
    """Test health check endpoint"""
    print("🔍 Testing health check...")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{BASE_URL}/health")
            print(f"✅ Health check: {response.status_code} - {response.json()}")
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Health check failed: {e}")
            return False

async def test_preauth_initiate():
    """Test preauth initiation"""
    print("\n🔍 Testing preauth initiation...")
    
    test_request = {
        "user_id": "test_user_001",
        "payer_id": "PAYER001",
        "patient_id": "PAT001",
        "patient_name": "John Doe",
        "prompt": "Request preauth for MRI scan of lower back"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{BASE_URL}/api/preauth/initiate",
                json=test_request,
                timeout=30.0
            )
            result = response.json()
            print(f"✅ Preauth initiate: {response.status_code}")
            print(f"   Response: {json.dumps(result, indent=2)}")
            
            if response.status_code in [200, 201]:
                return result.get("request_id")
            return None
        except Exception as e:
            print(f"❌ Preauth initiate failed: {e}")
            return None

async def test_request_status(request_id):
    """Test request status endpoint"""
    if not request_id:
        print("\n⏭️  Skipping status test - no request ID")
        return
    
    print(f"\n🔍 Testing request status for {request_id}...")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{BASE_URL}/api/preauth/status/{request_id}")
            result = response.json()
            print(f"✅ Request status: {response.status_code}")
            print(f"   Status: {result.get('status')}")
            print(f"   Remarks: {result.get('remarks', 'N/A')}")
        except Exception as e:
            print(f"❌ Request status failed: {e}")

async def test_dashboard_stats():
    """Test dashboard statistics"""
    print("\n🔍 Testing dashboard stats...")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{BASE_URL}/api/dashboard/stats?days=7")
            result = response.json()
            print(f"✅ Dashboard stats: {response.status_code}")
            if response.status_code == 200:
                print(f"   Total requests: {result.get('total_requests', 0)}")
                print(f"   Success rate: {result.get('success_rate', 0)}%")
        except Exception as e:
            print(f"❌ Dashboard stats failed: {e}")

async def test_dashboard_requests():
    """Test dashboard requests list"""
    print("\n🔍 Testing dashboard requests...")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{BASE_URL}/api/dashboard/requests?limit=5")
            result = response.json()
            print(f"✅ Dashboard requests: {response.status_code}")
            if response.status_code == 200:
                print(f"   Found {len(result)} requests")
                for req in result[:2]:  # Show first 2
                    print(f"   - {req.get('patient_name', 'Unknown')} ({req.get('status', 'Unknown')})")
        except Exception as e:
            print(f"❌ Dashboard requests failed: {e}")

async def test_n8n_callback(request_id):
    """Test N8N callback endpoint"""
    if not request_id:
        print("\n⏭️  Skipping N8N callback test - no request ID")
        return
    
    print(f"\n🔍 Testing N8N callback for {request_id}...")
    
    callback_data = {
        "request_id": request_id,
        "status": "in_progress",
        "action_type": "FORM_FILL_REQUIRED",
        "message": "Processing authorization form",
        "metadata": {"step": "form_validation"},
        "user_action_required": False,
        "workflow_step": "authorization_processing"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{BASE_URL}/api/n8n/callback",
                json=callback_data
            )
            result = response.json()
            print(f"✅ N8N callback: {response.status_code}")
            print(f"   Success: {result.get('success', False)}")
        except Exception as e:
            print(f"❌ N8N callback failed: {e}")

async def test_payer_validation():
    """Test payer validation"""
    print("\n🔍 Testing payer validation...")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{BASE_URL}/api/payers/PAYER001?request_id=test_request_001"
            )
            result = response.json()
            print(f"✅ Payer validation: {response.status_code}")
            print(f"   Message: {result.get('message', 'N/A')}")
        except Exception as e:
            print(f"❌ Payer validation failed: {e}")

async def test_api_docs():
    """Test API documentation accessibility"""
    print("\n🔍 Testing API docs...")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{BASE_URL}/docs")
            print(f"✅ API docs: {response.status_code}")
        except Exception as e:
            print(f"❌ API docs failed: {e}")

async def main():
    """Run all tests"""
    print("🚀 Starting Preauth Agent API Tests")
    print("=" * 50)
    
    # Test basic connectivity
    if not await test_health_check():
        print("\n❌ Server is not running. Please start the server first:")
        print("   python main.py")
        return
    
    # Test core functionality
    request_id = await test_preauth_initiate()
    await test_request_status(request_id)
    await test_dashboard_stats()
    await test_dashboard_requests()
    await test_n8n_callback(request_id)
    await test_payer_validation()
    await test_api_docs()
    
    print("\n" + "=" * 50)
    print("🎉 Test suite completed!")
    print("\n📖 For complete API documentation, visit:")
    print(f"   {BASE_URL}/docs")
    print("\n💡 To test with frontend dashboard:")
    print("   1. Ensure CORS is configured properly")
    print("   2. Use the dashboard APIs for real-time updates")
    print("   3. Implement polling for status updates")

if __name__ == "__main__":
    asyncio.run(main())
