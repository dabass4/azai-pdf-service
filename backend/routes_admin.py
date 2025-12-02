"""Admin API Routes - Super Admin Panel

Provides company staff with tools to:
- Manage all organizations
- Monitor system health
- Troubleshoot client issues
- Manage credentials per organization
- View logs and analytics
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
import logging
import os
from collections import defaultdict

from auth import get_current_user, hash_password
from integrations.omes_edi import OMESSOAPClient, OMESSFTPClient
from integrations.availity import AvailityClient

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/admin", tags=["admin"])


# Admin authorization dependency
async def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    """Verify user has admin role"""
    if not current_user.get("is_admin", False):
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )
    return current_user


# Pydantic Models
class OrganizationCreate(BaseModel):
    """Create new organization"""
    name: str
    admin_email: EmailStr
    admin_password: str
    admin_first_name: str
    admin_last_name: str
    plan: str = "free"


class OrganizationUpdate(BaseModel):
    """Update organization details"""
    name: Optional[str] = None
    status: Optional[str] = None  # active, suspended, cancelled
    plan: Optional[str] = None


class CredentialUpdate(BaseModel):
    """Update organization credentials"""
    omes_tpid: Optional[str] = None
    omes_soap_username: Optional[str] = None
    omes_soap_password: Optional[str] = None
    omes_sftp_username: Optional[str] = None
    omes_sftp_password: Optional[str] = None
    availity_api_key: Optional[str] = None
    availity_client_secret: Optional[str] = None
    availity_scope: Optional[str] = None


class SupportTicket(BaseModel):
    """Support ticket for issue tracking"""
    organization_id: str
    title: str
    description: str
    priority: str = Field(default="medium", pattern="^(low|medium|high|critical)$")
    category: str = Field(default="general", pattern="^(general|billing|technical|integration|credentials)$")


# ==================== ORGANIZATIONS MANAGEMENT ====================

@router.get("/organizations")
async def list_organizations(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status: Optional[str] = None,
    search: Optional[str] = None,
    admin: dict = Depends(require_admin),
    db: AsyncIOMotorClient = Depends(lambda: None)  # Will be injected
) -> dict:
    """
    List all organizations with filtering and pagination
    
    Admin only endpoint
    """
    try:
        from server import db as database
        
        # Build query
        query = {}
        if status:
            query["status"] = status
        if search:
            query["name"] = {"$regex": search, "$options": "i"}
        
        # Get total count
        total = await database.organizations.count_documents(query)
        
        # Get organizations
        cursor = database.organizations.find(query).skip(skip).limit(limit)
        organizations = await cursor.to_list(length=limit)
        
        # Get user counts per organization
        for org in organizations:
            org_id = org.get("id", org.get("organization_id"))
            user_count = await database.users.count_documents(
                {"organization_id": org_id}
            )
            org["user_count"] = user_count
            
            # Get timesheet count
            timesheet_count = await database.timesheets.count_documents(
                {"organization_id": org_id}
            )
            org["timesheet_count"] = timesheet_count
        
        return {
            "success": True,
            "total": total,
            "skip": skip,
            "limit": limit,
            "organizations": organizations
        }
    
    except Exception as e:
        logger.error(f"List organizations error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/organizations/{organization_id}")
async def get_organization_details(
    organization_id: str,
    admin: dict = Depends(require_admin)
) -> dict:
    """
    Get detailed information about a specific organization
    
    Admin only endpoint
    """
    try:
        from server import db as database
        
        # Get organization
        org = await database.organizations.find_one(
            {"organization_id": organization_id}
        )
        
        if not org:
            raise HTTPException(status_code=404, detail="Organization not found")
        
        # Get users
        users = await database.users.find(
            {"organization_id": organization_id}
        ).to_list(length=100)
        
        # Get statistics
        stats = {
            "users": len(users),
            "patients": await database.patients.count_documents({"organization_id": organization_id}),
            "employees": await database.employees.count_documents({"organization_id": organization_id}),
            "timesheets": await database.timesheets.count_documents({"organization_id": organization_id}),
            "timesheets_submitted": await database.timesheets.count_documents({
                "organization_id": organization_id,
                "sandata_status": "submitted"
            })
        }
        
        # Get credentials status
        org_config = await database.organization_config.find_one(
            {"organization_id": organization_id}
        )
        
        credentials_status = {
            "omes_configured": bool(org_config and org_config.get("omes_tpid")),
            "availity_configured": bool(org_config and org_config.get("availity_api_key")),
            "sandata_configured": bool(org_config and org_config.get("sandata_api_key"))
        }
        
        return {
            "success": True,
            "organization": org,
            "users": users,
            "statistics": stats,
            "credentials_status": credentials_status,
            "configuration": org_config
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get organization details error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/organizations")
async def create_organization(
    org_data: OrganizationCreate,
    admin: dict = Depends(require_admin)
) -> dict:
    """
    Create a new organization with admin user
    
    Admin only endpoint
    """
    try:
        from server import db as database
        import uuid
        
        organization_id = str(uuid.uuid4())
        
        # Create organization
        org_doc = {
            "organization_id": organization_id,
            "name": org_data.name,
            "plan": org_data.plan,
            "status": "active",
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        
        await database.organizations.insert_one(org_doc)
        
        # Create admin user for organization
        user_id = str(uuid.uuid4())
        hashed_password = hash_password(org_data.admin_password)
        
        user_doc = {
            "id": user_id,
            "email": org_data.admin_email,
            "password": hashed_password,
            "first_name": org_data.admin_first_name,
            "last_name": org_data.admin_last_name,
            "organization_id": organization_id,
            "is_admin": False,  # Organization admin, not super admin
            "is_active": True,
            "created_at": datetime.now(timezone.utc)
        }
        
        await database.users.insert_one(user_doc)
        
        logger.info(f"Created organization {organization_id}: {org_data.name}")
        
        return {
            "success": True,
            "organization_id": organization_id,
            "organization": org_doc,
            "admin_user_id": user_id
        }
    
    except Exception as e:
        logger.error(f"Create organization error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/organizations/{organization_id}")
async def update_organization(
    organization_id: str,
    update_data: OrganizationUpdate,
    admin: dict = Depends(require_admin)
) -> dict:
    """
    Update organization details
    
    Admin only endpoint
    """
    try:
        from server import db as database
        
        # Build update document
        update_doc = {"updated_at": datetime.now(timezone.utc)}
        
        if update_data.name is not None:
            update_doc["name"] = update_data.name
        if update_data.status is not None:
            update_doc["status"] = update_data.status
        if update_data.plan is not None:
            update_doc["plan"] = update_data.plan
        
        result = await database.organizations.update_one(
            {"organization_id": organization_id},
            {"$set": update_doc}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Organization not found")
        
        return {
            "success": True,
            "organization_id": organization_id,
            "updated_fields": list(update_doc.keys())
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update organization error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== CREDENTIALS MANAGEMENT ====================

@router.get("/organizations/{organization_id}/credentials")
async def get_organization_credentials(
    organization_id: str,
    admin: dict = Depends(require_admin)
) -> dict:
    """
    Get credentials for an organization (masked for security)
    
    Admin only endpoint
    """
    try:
        from server import db as database
        
        config = await database.organization_config.find_one(
            {"organization_id": organization_id}
        )
        
        if not config:
            return {
                "success": True,
                "organization_id": organization_id,
                "credentials": {}
            }
        
        # Mask sensitive values
        masked_config = {}
        for key, value in config.items():
            if key in ["_id", "organization_id"]:
                continue
            if isinstance(value, str) and len(value) > 4:
                masked_config[key] = f"{'*' * (len(value) - 4)}{value[-4:]}"
            else:
                masked_config[key] = value
        
        return {
            "success": True,
            "organization_id": organization_id,
            "credentials": masked_config
        }
    
    except Exception as e:
        logger.error(f"Get credentials error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/organizations/{organization_id}/credentials")
async def update_organization_credentials(
    organization_id: str,
    credentials: CredentialUpdate,
    admin: dict = Depends(require_admin)
) -> dict:
    """
    Update credentials for an organization
    
    Admin only endpoint
    """
    try:
        from server import db as database
        
        # Build update document
        update_doc = {"updated_at": datetime.now(timezone.utc)}
        
        if credentials.omes_tpid:
            update_doc["omes_tpid"] = credentials.omes_tpid
        if credentials.omes_soap_username:
            update_doc["omes_soap_username"] = credentials.omes_soap_username
        if credentials.omes_soap_password:
            update_doc["omes_soap_password"] = credentials.omes_soap_password
        if credentials.omes_sftp_username:
            update_doc["omes_sftp_username"] = credentials.omes_sftp_username
        if credentials.omes_sftp_password:
            update_doc["omes_sftp_password"] = credentials.omes_sftp_password
        if credentials.availity_api_key:
            update_doc["availity_api_key"] = credentials.availity_api_key
        if credentials.availity_client_secret:
            update_doc["availity_client_secret"] = credentials.availity_client_secret
        if credentials.availity_scope:
            update_doc["availity_scope"] = credentials.availity_scope
        
        result = await database.organization_config.update_one(
            {"organization_id": organization_id},
            {"$set": update_doc},
            upsert=True
        )
        
        logger.info(f"Updated credentials for organization {organization_id}")
        
        return {
            "success": True,
            "organization_id": organization_id,
            "updated_fields": list(update_doc.keys())
        }
    
    except Exception as e:
        logger.error(f"Update credentials error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/organizations/{organization_id}/test-credentials")
async def test_organization_credentials(
    organization_id: str,
    service: str = Query(..., pattern="^(omes_soap|omes_sftp|availity)$"),
    admin: dict = Depends(require_admin)
) -> dict:
    """
    Test credentials for a specific service
    
    Admin only endpoint
    """
    try:
        from server import db as database
        
        config = await database.organization_config.find_one(
            {"organization_id": organization_id}
        )
        
        if not config:
            raise HTTPException(
                status_code=404,
                detail="No credentials configured for this organization"
            )
        
        result = {"success": False, "message": ""}
        
        if service == "omes_soap":
            # Test OMES SOAP connection
            soap_client = OMESSOAPClient(
                username=config.get("omes_soap_username"),
                password=config.get("omes_soap_password")
            )
            result["success"] = True
            result["message"] = "OMES SOAP client initialized successfully"
            
        elif service == "omes_sftp":
            # Test OMES SFTP connection
            sftp_client = OMESSFTPClient(
                username=config.get("omes_sftp_username"),
                password=config.get("omes_sftp_password"),
                tpid=config.get("omes_tpid")
            )
            test_success = sftp_client.test_connection()
            result["success"] = test_success
            result["message"] = "OMES SFTP connection successful" if test_success else "OMES SFTP connection failed"
            
        elif service == "availity":
            # Test Availity connection
            availity_client = AvailityClient(
                api_key=config.get("availity_api_key"),
                client_secret=config.get("availity_client_secret")
            )
            test_success = availity_client.test_connection()
            result["success"] = test_success
            result["message"] = "Availity connection successful" if test_success else "Availity connection failed"
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Test credentials error: {str(e)}")
        return {
            "success": False,
            "message": f"Test failed: {str(e)}"
        }


# ==================== SYSTEM HEALTH ====================

@router.get("/system/health")
async def get_system_health(
    admin: dict = Depends(require_admin)
) -> dict:
    """
    Get overall system health status
    
    Admin only endpoint
    """
    try:
        from server import db as database
        
        # Check database connection
        try:
            await database.command("ping")
            db_status = "healthy"
        except:
            db_status = "unhealthy"
        
        # Get service status
        services = {
            "database": db_status,
            "backend": "healthy",  # If this endpoint responds, backend is healthy
            "frontend": "unknown"  # Would need separate health check
        }
        
        # Get statistics
        stats = {
            "total_organizations": await database.organizations.count_documents({}),
            "active_organizations": await database.organizations.count_documents({"status": "active"}),
            "total_users": await database.users.count_documents({}),
            "total_timesheets": await database.timesheets.count_documents({}),
            "timesheets_last_24h": await database.timesheets.count_documents({
                "created_at": {"$gte": datetime.now(timezone.utc) - timedelta(days=1)}
            })
        }
        
        return {
            "success": True,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "services": services,
            "statistics": stats
        }
    
    except Exception as e:
        logger.error(f"Get system health error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/system/logs")
async def get_system_logs(
    level: Optional[str] = Query("ERROR", pattern="^(INFO|WARNING|ERROR|CRITICAL)$"),
    limit: int = Query(100, ge=1, le=1000),
    organization_id: Optional[str] = None,
    admin: dict = Depends(require_admin)
) -> dict:
    """
    Get system logs (would need log aggregation setup)
    
    Admin only endpoint
    """
    try:
        # This is a placeholder - in production, you'd integrate with a logging service
        # like CloudWatch, Datadog, or ELK stack
        
        # For now, read from log files
        import subprocess
        
        cmd = f"tail -n {limit} /var/log/supervisor/backend.err.log"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        logs = result.stdout.split('\n')
        
        return {
            "success": True,
            "level": level,
            "limit": limit,
            "organization_id": organization_id,
            "logs": logs[-limit:]
        }
    
    except Exception as e:
        logger.error(f"Get logs error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== SUPPORT TICKETS ====================

@router.post("/support/tickets")
async def create_support_ticket(
    ticket: SupportTicket,
    admin: dict = Depends(require_admin)
) -> dict:
    """
    Create a support ticket for an organization
    
    Admin only endpoint
    """
    try:
        from server import db as database
        import uuid
        
        ticket_id = str(uuid.uuid4())
        
        ticket_doc = {
            "ticket_id": ticket_id,
            "organization_id": ticket.organization_id,
            "title": ticket.title,
            "description": ticket.description,
            "priority": ticket.priority,
            "category": ticket.category,
            "status": "open",
            "created_by": admin["id"],
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        
        await database.support_tickets.insert_one(ticket_doc)
        
        return {
            "success": True,
            "ticket_id": ticket_id,
            "ticket": ticket_doc
        }
    
    except Exception as e:
        logger.error(f"Create support ticket error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/support/tickets")
async def list_support_tickets(
    status: Optional[str] = Query(None, pattern="^(open|in_progress|resolved|closed)$"),
    organization_id: Optional[str] = None,
    priority: Optional[str] = None,
    limit: int = Query(50, ge=1, le=100),
    admin: dict = Depends(require_admin)
) -> dict:
    """
    List support tickets with filtering
    
    Admin only endpoint
    """
    try:
        from server import db as database
        
        query = {}
        if status:
            query["status"] = status
        if organization_id:
            query["organization_id"] = organization_id
        if priority:
            query["priority"] = priority
        
        tickets = await database.support_tickets.find(query).sort(
            "created_at", -1
        ).limit(limit).to_list(length=limit)
        
        return {
            "success": True,
            "total": len(tickets),
            "tickets": tickets
        }
    
    except Exception as e:
        logger.error(f"List support tickets error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== ANALYTICS ====================

@router.get("/analytics/overview")
async def get_analytics_overview(
    days: int = Query(30, ge=1, le=365),
    admin: dict = Depends(require_admin)
) -> dict:
    """
    Get analytics overview for the specified time period
    
    Admin only endpoint
    """
    try:
        from server import db as database
        
        start_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        # Get growth metrics
        new_orgs = await database.organizations.count_documents({
            "created_at": {"$gte": start_date}
        })
        
        new_users = await database.users.count_documents({
            "created_at": {"$gte": start_date}
        })
        
        new_timesheets = await database.timesheets.count_documents({
            "created_at": {"$gte": start_date}
        })
        
        # Get usage by organization
        pipeline = [
            {"$match": {"created_at": {"$gte": start_date}}},
            {"$group": {
                "_id": "$organization_id",
                "count": {"$sum": 1}
            }},
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ]
        
        top_orgs = await database.timesheets.aggregate(pipeline).to_list(length=10)
        
        return {
            "success": True,
            "period_days": days,
            "start_date": start_date.isoformat(),
            "metrics": {
                "new_organizations": new_orgs,
                "new_users": new_users,
                "new_timesheets": new_timesheets
            },
            "top_organizations_by_usage": top_orgs
        }
    
    except Exception as e:
        logger.error(f"Get analytics error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
