"""Create Super Admin User

Run this script once to create the first super admin user.

Usage:
    python create_super_admin.py --email admin@company.com --password yourpassword
"""

import asyncio
import argparse
import uuid
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

from auth import hash_password


async def create_super_admin(email: str, password: str, first_name: str = "Super", last_name: str = "Admin"):
    """Create a super admin user"""
    
    # Connect to MongoDB
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    
    try:
        # Check if super admin already exists
        existing = await db.users.find_one({"email": email})
        if existing:
            print(f"❌ User with email {email} already exists!")
            return False
        
        # Create super admin organization if it doesn't exist
        org_exists = await db.organizations.find_one({"id": "super_admin"})
        if not org_exists:
            org_doc = {
                "id": "super_admin",
                "name": "Platform Administration",
                "contact_email": email,
                "status": "active",
                "plan": "enterprise",
                "subscription_status": "active",
                "features": ["admin_panel", "all_features"],
                "created_at": datetime.now(timezone.utc)
            }
            await db.organizations.insert_one(org_doc)
            print("   ✓ Created super admin organization")
        
        # Create super admin user
        user_id = str(uuid.uuid4())
        hashed_password = hash_password(password)
        
        user_doc = {
            "id": user_id,
            "email": email,
            "password_hash": hashed_password,
            "first_name": first_name,
            "last_name": last_name,
            "organization_id": "super_admin",  # Special org ID for super admins
            "role": "super_admin",  # Required for login
            "is_admin": True,  # Super admin flag
            "is_active": True,
            "created_at": datetime.now(timezone.utc)
        }
        
        await db.users.insert_one(user_doc)
        
        print(f"\n✅ Super admin user created successfully!")
        print(f"   Email: {email}")
        print(f"   User ID: {user_id}")
        print(f"   Name: {first_name} {last_name}")
        print(f"\n⚠️  Please save this information securely!")
        print(f"\n🔐 You can now login with these credentials to access the admin panel.")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating super admin: {str(e)}")
        return False
        
    finally:
        client.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create super admin user")
    parser.add_argument("--email", required=True, help="Admin email address")
    parser.add_argument("--password", required=True, help="Admin password")
    parser.add_argument("--first-name", default="Super", help="First name")
    parser.add_argument("--last-name", default="Admin", help="Last name")
    
    args = parser.parse_args()
    
    print(f"\n🔧 Creating super admin user...")
    print(f"   Email: {args.email}")
    print(f"   Name: {args.first_name} {args.last_name}\n")
    
    asyncio.run(create_super_admin(
        email=args.email,
        password=args.password,
        first_name=args.first_name,
        last_name=args.last_name
    ))
