"""
Clear test authentication data
Removes all test users and organizations except default-org
"""
import asyncio
import os
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

async def clear_test_data():
    print("="*60)
    print("CLEARING TEST AUTHENTICATION DATA")
    print("="*60)
    print()
    
    try:
        # Delete all users
        users_result = await db.users.delete_many({})
        print(f"✅ Deleted {users_result.deleted_count} test users")
        
        # Delete all organizations except default-org
        orgs_result = await db.organizations.delete_many({"id": {"$ne": DEFAULT_ORG_ID}})
        print(f"✅ Deleted {orgs_result.deleted_count} test organizations")
        
        # Delete all EVV credentials
        creds_result = await db.evv_credentials.delete_many({})
        print(f"✅ Deleted {creds_result.deleted_count} EVV credentials")
        
        print()
        print("="*60)
        print("✅ DATABASE RESET COMPLETE!")
        print("="*60)
        print()
        print(f"Preserved: {DEFAULT_ORG_ID} (existing data intact)")
        print("You can now create fresh test accounts")
        
    except Exception as e:
        print(f"❌ Error clearing data: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(clear_test_data())
