"""
Initialize MongoDB with sample data for testing
Run this after the MongoDB container is up
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import os

async def init_sample_data():
    """Initialize MongoDB with sample data"""
    print("🔄 Connecting to MongoDB...")
    
    # Connect to MongoDB
    client = AsyncIOMotorClient("mongodb://host.docker.internal:27017")
    db = client["unified_db"]
    
    try:
        # Sample payers data
        sample_payers = [
            {
                "id": "PAYER001",
                "name": "Aetna Health",
                "status": "active",
                "onboarded_date": datetime.now(),
                "supported_procedures": ["MRI", "CT_SCAN", "X_RAY"],
                "contact_info": {
                    "email": "preauth@aetna.com",
                    "phone": "1-800-AETNA-01"
                }
            },
            {
                "id": "PAYER002", 
                "name": "Blue Cross Blue Shield",
                "status": "active",
                "onboarded_date": datetime.now(),
                "supported_procedures": ["MRI", "CT_SCAN", "ULTRASOUND"],
                "contact_info": {
                    "email": "auth@bcbs.com",
                    "phone": "1-800-BCBS-001"
                }
            },
            {
                "id": "PAYER003",
                "name": "United Healthcare",
                "status": "active", 
                "onboarded_date": datetime.now(),
                "supported_procedures": ["MRI", "CT_SCAN", "PET_SCAN"],
                "contact_info": {
                    "email": "preauth@uhc.com",
                    "phone": "1-800-UHC-0001"
                }
            }
        ]
        
        # Insert sample payers
        print("📝 Inserting sample payers...")
        await db.priorAuthPayers.delete_many({})  # Clear existing
        await db.priorAuthPayers.insert_many(sample_payers)
        print(f"✅ Inserted {len(sample_payers)} payers")
        
        # Sample validation rules (basic structure)
        print("📝 Creating indexes and sample data...")
        
        # Create indexes for better performance
        await db.requestProgress.create_index("requestId")
        await db.priorAuthRequest.create_index("requestId")
        await db.priorAuthUserAction.create_index("requestId")
        await db.priorAuthPayers.create_index("id")
        
        print("✅ Database initialization completed!")
        
        # Display summary
        payers_count = await db.priorAuthPayers.count_documents({})
        print(f"📊 Database Summary:")
        print(f"   - Payers: {payers_count}")
        print(f"   - Collections created with indexes")
        
        print("\n🎉 Ready to use! Available payers:")
        for payer in sample_payers:
            print(f"   - {payer['id']}: {payer['name']}")
            
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(init_sample_data())
