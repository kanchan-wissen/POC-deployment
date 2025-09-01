"""
Simple test to verify API structure and imports
"""

try:
    print("Testing imports...")
    
    # Test basic FastAPI imports
    from fastapi import FastAPI
    print("✅ FastAPI imported")
    
    # Test database imports
    from db.config.connection import init_db, get_db
    print("✅ Database connection imported")
    
    # Test model imports
    from db.models.dbmodels.requestProgress import RequestProgress, RequestStatus
    print("✅ RequestProgress model imported")
    
    from db.models.dbmodels.priorAuthRequest import priorAuthRequest
    print("✅ priorAuthRequest model imported")
    
    # Test API imports
    from api.agent_tools import router as agent_tools_router
    print("✅ Agent tools router imported")
    
    from api.n8nRequestListener import router as n8n_listener_router
    print("✅ N8N listener router imported")
    
    from api.dashboard_api import router as dashboard_router
    print("✅ Dashboard router imported")
    
    # Test the main app
    from main import app
    print("✅ Main app imported")
    
    print("\n🎉 All imports successful!")
    print("\nTo run the server:")
    print("python main.py")
    print("\nOr use the startup scripts:")
    print("Windows: start.bat") 
    print("Linux/Mac: bash start.sh")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("\nThis usually means:")
    print("1. Missing dependencies - run: pip install -r requirements.txt")
    print("2. Python environment not activated") 
    print("3. Missing database models or API files")
    
except Exception as e:
    print(f"❌ Other error: {e}")
    
print("\n" + "="*50)
print("Quick API Test - Available Endpoints:")
print("="*50)

endpoints = [
    ("POST", "/api/tools/start-request", "Start new preauth request"),
    ("GET", "/api/tools/check-payer/{payer_id}", "Check payer onboarding"),
    ("POST", "/api/tools/get-patient-details", "Get patient JSON data"),
    ("POST", "/api/tools/validate-json", "Validate patient JSON"),
    ("POST", "/api/tools/trigger-n8n", "Trigger N8N workflow"),
    ("GET", "/api/tools/request-status/{request_id}", "Get request status"),
    ("POST", "/api/tools/handle-user-action", "Handle user action response"),
    ("POST", "/api/n8n/action-required", "N8N action required callback"),
    ("GET", "/api/dashboard/stats", "Dashboard statistics"),
    ("GET", "/api/dashboard/requests", "Recent requests"),
    ("GET", "/health", "Health check"),
]

for method, endpoint, description in endpoints:
    print(f"{method:6} {endpoint:35} - {description}")

print("\n📖 Full documentation: http://host.docker.internal:8001/docs")
print("📊 Dashboard APIs: http://host.docker.internal:8001/api/dashboard/")
print("🔧 Agent Tools: http://host.docker.internal:8001/api/tools/")
