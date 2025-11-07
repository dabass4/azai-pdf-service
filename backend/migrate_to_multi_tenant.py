"""
Migration script to add organization_id to all existing data
Run this once to migrate existing data to multi-tenant structure
"""
import asyncio
import os
import uuid
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

DEFAULT_ORG_ID = "default-org"

async def create_default_organization():
    """Create a default organization for existing data"""
    print("Creating default organization...")
    
    # Check if it already exists
    existing = await db.organizations.find_one({"id": DEFAULT_ORG_ID})
    if existing:
        print(f"Default organization already exists: {DEFAULT_ORG_ID}")
        return
    
    default_org = {
        "id": DEFAULT_ORG_ID,
        "name": "Default Organization",
        "plan": "professional",
        "subscription_status": "active",
        "stripe_customer_id": None,
        "stripe_subscription_id": None,
        "admin_email": "admin@example.com",
        "admin_name": "Admin User",
        "phone": None,
        "address_street": None,
        "address_city": None,
        "address_state": None,
        "address_zip": None,
        "max_timesheets": -1,  # Unlimited
        "max_employees": -1,
        "max_patients": -1,
        "features": ["sandata_submission", "evv_submission", "bulk_operations", "advanced_reporting", "api_access"],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "trial_ends_at": None,
        "last_payment_at": None
    }
    
    await db.organizations.insert_one(default_org)
    print(f"✅ Created default organization: {DEFAULT_ORG_ID}")

async def migrate_collection(collection_name):
    """Migrate a collection to add organization_id"""
    print(f"\nMigrating collection: {collection_name}")
    
    # Count documents without organization_id
    count = await db[collection_name].count_documents({"organization_id": {"$exists": False}})
    
    if count == 0:
        print(f"  ✅ {collection_name}: No documents to migrate")
        return
    
    print(f"  Found {count} documents to migrate")
    
    # Update all documents without organization_id
    result = await db[collection_name].update_many(
        {"organization_id": {"$exists": False}},
        {"$set": {"organization_id": DEFAULT_ORG_ID}}
    )
    
    print(f"  ✅ {collection_name}: Migrated {result.modified_count} documents")

async def main():
    print("="*60)
    print("MULTI-TENANT MIGRATION SCRIPT")
    print("="*60)
    print()
    
    try:
        # Step 1: Create default organization
        await create_default_organization()
        
        # Step 2: Migrate all collections
        collections_to_migrate = [
            "patients",
            "employees",
            "timesheets",
            "claims",
            "servicecodes",
            "business_entities",
            "payers"
        ]
        
        for collection in collections_to_migrate:
            await migrate_collection(collection)
        
        print()
        print("="*60)
        print("✅ MIGRATION COMPLETE!")
        print("="*60)
        print()
        print(f"All existing data has been assigned to: {DEFAULT_ORG_ID}")
        print()
        print("Next steps:")
        print("1. Restart your backend server")
        print("2. Test API endpoints with X-Organization-ID header")
        print("3. Create new organizations for new customers")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(main())
