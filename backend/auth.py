"""
JWT-based authentication system
Simple, secure, and production-ready
"""
import os
import jwt
import bcrypt
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict
from fastapi import HTTPException, Header

JWT_SECRET = os.environ.get('JWT_SECRET', 'your-secret-key-change-in-production')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_HOURS = 24 * 7  # 7 days

def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_access_token(user_id: str, email: str, organization_id: str, role: str, is_admin: bool = False) -> str:
    """Create a JWT access token"""
    expiration = datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS)
    
    payload = {
        'user_id': user_id,
        'email': email,
        'organization_id': organization_id,
        'role': role,
        'is_admin': is_admin,
        'exp': expiration,
        'iat': datetime.now(timezone.utc)
    }
    
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token

def decode_access_token(token: str) -> Dict:
    """Decode and verify a JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

def get_token_from_header(authorization: Optional[str] = Header(None)) -> str:
    """Extract JWT token from Authorization header"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != 'bearer':
        raise HTTPException(status_code=401, detail="Invalid authorization header format. Use: Bearer <token>")
    
    return parts[1]

async def get_current_user(authorization: Optional[str] = Header(None)) -> Dict:
    """Dependency to get current authenticated user from JWT"""
    token = get_token_from_header(authorization)
    payload = decode_access_token(token)
    return payload

async def get_organization_from_token(authorization: Optional[str] = Header(None)) -> str:
    """Extract organization_id from JWT token"""
    try:
        token = get_token_from_header(authorization)
        payload = decode_access_token(token)
        return payload.get('organization_id')
    except HTTPException:
        # Fallback to default organization if no auth provided
        return "default-org"
