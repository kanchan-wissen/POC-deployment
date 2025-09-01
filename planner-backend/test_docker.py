"""
Test script for Docker-based Preauth Agent APIs
Tests all agent tool endpoints with MongoDB
"""

import asyncio
import httpx
import json
from datetime import datetime

BASE_URL = "http://host.docker.internal:8001"

async def wait_for_service(url, max_retries=30, delay=2):
    """Wait for service to be ready"""
    for i in range(max_retries):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=5.0)
                if response.status_code == 200:
                    return True
        except:
            pass
        print(f"⏳ Waiting for service... ({i+1}/{max_retries})")
        await asyncio.sleep(delay)
    return False

async def test_agent_tools_workflow():
    """Test the complete agent tools workflow"""
    print("🔧 Testing Agent Tools Workflow")
    print("=" * 50)
    
    # Wait for service to be ready
    if not await wait_for_service(f"{BASE_URL}/health"):
        print("❌ Service not ready after waiting")
        return
    
    async with httpx.AsyncClient() as client:
        try:
            # Step 1: Start new request
            print("\\n1️⃣ Testing: Start New Request")
            start_request = {
                "user_id": "USER123",
                "prompt": "Please process preauth for patient PAT123 with Aetna (PAYER001) for MRI scan"
            }
            response = await client.post(f"{BASE_URL}/api/tools/start-request", json=start_request)
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                request_id = result["request_id"]
                print(f"   ✅ Request ID: {request_id}")
            else:
                print(f"   ❌ Failed: {response.text}")
                return
            
            # Step 2: Check payer onboarding
            print("\\n2️⃣ Testing: Check Payer Onboarding")
            response = await client.get(f"{BASE_URL}/api/tools/check-payer/PAYER001?request_id={request_id}")
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ Payer onboarded: {result['is_onboarded']}")
                if result.get('payer_details'):
                    print(f"   📋 Payer: {result['payer_details']['name']}")
            else:
                print(f"   ❌ Failed: {response.text}")
            
            # Step 3: Get patient details
            print("\\n3️⃣ Testing: Get Patient Details")
            patient_request = {
                "patient_id": "PAT123",
                "payer_id": "PAYER001",
                "request_id": request_id
            }
            response = await client.post(f"{BASE_URL}/api/tools/get-patient-details", json=patient_request)
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ Patient data retrieved: {result['success']}")
                if not result['success']:
                    print(f"   ⚠️ Message: {result['message']}")
            else:
                print(f"   ❌ Failed: {response.text}")
                
            # Step 4: Validate JSON
            print("\\n4️⃣ Testing: Validate Patient JSON")
            validate_request = {
                "json_data": {"patient_id": "PAT123", "procedure": "MRI", "payer_id": "PAYER001"}
            }
            response = await client.post(f"{BASE_URL}/api/validate-json", json=validate_request)
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ JSON valid: {result['is_valid']}")
                print(f"   ⚠️  Missing fields: {result.get('missing_fields', [])}")
            else:
                print(f"   ❌ Failed: {response.text}")
            
            # Step 5: Get request status
            print("\\n5️⃣ Testing: Get Request Status")
            response = await client.get(f"{BASE_URL}/api/tools/request-status/{request_id}")
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ Current status: {result['status']}")
                print(f"   📝 Remarks: {result.get('remarks', 'N/A')}")
            else:
                print(f"   ❌ Failed: {response.text}")
            
            # Step 6: Test N8N callback (simulation)
            print("\\n6️⃣ Testing: N8N Callback")
            callback_request = {
                "request_id": request_id,
                "payer_id": "PAYER001",
                "status": "waiting_for_user",
                "message": "Need additional patient insurance information",
                "user_action_required": True,
                "action_type": "INSURANCE_INFO_REQUIRED",
                "action_details": {
                    "required_fields": ["secondary_insurance", "group_number"]
                },
                "workflow_step": "insurance_verification"
            }
            response = await client.post(f"{BASE_URL}/api/n8n/callback", json=callback_request)
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ Action created: {result['success']}")
                print(f"   👤 User action required: {result.get('user_action_created', False)}")
            else:
                print(f"   ❌ Failed: {response.text}")
                
        except Exception as e:
            print(f"❌ Test failed with error: {str(e)}")

async def test_dashboard_apis():
    """Test dashboard endpoints"""
    print("\\n📊 Testing Dashboard APIs")
    print("=" * 30)
    
    async with httpx.AsyncClient() as client:
        # Test dashboard stats
        print("📈 Testing: Dashboard Stats")
        response = await client.get(f"{BASE_URL}/api/dashboard/stats")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Total requests: {result['total_requests']}")
            print(f"   📊 Success rate: {result['success_rate']:.1%}")
        
        # Test recent requests
        print("📋 Testing: Recent Requests")
        response = await client.get(f"{BASE_URL}/api/dashboard/requests?limit=5")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Found {len(result)} requests")
            
        # Test user actions
        print("👤 Testing: User Actions")
        response = await client.get(f"{BASE_URL}/api/dashboard/user-actions?limit=5")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Found {len(result)} user actions")

async def main():
    """Main test function"""
    print("🚀 Starting Docker-based Preauth Agent API Tests")
    print("=" * 60)
    
    # Test health first
    print("🔍 Testing service health...")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{BASE_URL}/health", timeout=10.0)
            if response.status_code == 200:
                print("✅ Service is healthy!")
            else:
                print(f"❌ Service unhealthy: {response.status_code}")
                return
        except Exception as e:
            print(f"❌ Cannot reach service: {str(e)}")
            return
    
    # Run tests
    await test_agent_tools_workflow()
    await test_dashboard_apis()
    
    # Summary
    print("\\n" + "=" * 60)
    print("🎉 Test suite completed!")
    print("📖 Available Resources:")
    print("   🌐 API Documentation: http://host.docker.internal:8001/docs")
    print("   🔍 Health Check: http://host.docker.internal:8001/health")
    print("   🗄️  MongoDB Admin: http://host.docker.internal:8081")
    print("   🔧 Agent Tools: http://host.docker.internal:8001/api/tools/")
    print("   📊 Dashboard: http://host.docker.internal:8001/api/dashboard/")
    print("💡 Next Steps:")
    print("   1. Connect your Planner Agent to use these tool endpoints")
    print("   2. Set up your frontend dashboard to poll dashboard APIs")
    print("   3. Configure N8N to use the callback endpoints")
    print("   4. Initialize sample data: python init_db.py")

if __name__ == "__main__":
    asyncio.run(main())
