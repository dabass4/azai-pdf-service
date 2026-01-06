"""
Employee Routes for AZAI Healthcare Application
Extracted from server.py for better maintainability

Contains:
- Employee CRUD operations
- Name correction management
- Duplicate detection and resolution
- Billing code management
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timezone
import uuid
import logging

from motor.motor_asyncio import AsyncIOMotorClient
import os

# Import models from the models module
from models import (
    EmployeeProfile,
    EmployeeProfileUpdate,
)

# Import auth dependency
from auth import get_organization_from_token

logger = logging.getLogger(__name__)

# Create router
employees_router = APIRouter(prefix="/employees", tags=["employees"])

# Database connection - will be set by main server
db = None

def set_database(database):
    """Set the database connection for this router"""
    global db
    db = database


# Dependency to get organization ID from auth token
async def get_organization_id(authorization: str = None) -> str:
    """Get organization ID from JWT token or header"""
    if authorization:
        return await get_organization_from_token(authorization)
    return "default-org"


# ============================================================================
# Helper Functions
# ============================================================================

def calculate_name_similarity(name1: str, name2: str) -> float:
    """
    Calculate similarity between two names using Levenshtein distance.
    Returns a score between 0.0 (completely different) and 1.0 (identical).
    """
    if not name1 or not name2:
        return 0.0
    
    name1 = name1.lower().strip()
    name2 = name2.lower().strip()
    
    if name1 == name2:
        return 1.0
    
    # Calculate Levenshtein distance
    len1, len2 = len(name1), len(name2)
    
    if len1 == 0:
        return 0.0 if len2 > 0 else 1.0
    if len2 == 0:
        return 0.0
    
    # Create distance matrix
    distances = [[0] * (len2 + 1) for _ in range(len1 + 1)]
    
    for i in range(len1 + 1):
        distances[i][0] = i
    for j in range(len2 + 1):
        distances[0][j] = j
    
    for i in range(1, len1 + 1):
        for j in range(1, len2 + 1):
            cost = 0 if name1[i-1] == name2[j-1] else 1
            distances[i][j] = min(
                distances[i-1][j] + 1,      # deletion
                distances[i][j-1] + 1,      # insertion
                distances[i-1][j-1] + cost  # substitution
            )
    
    # Convert distance to similarity score
    max_len = max(len1, len2)
    distance = distances[len1][len2]
    similarity = 1.0 - (distance / max_len)
    
    return similarity


async def find_similar_employees(employee_name: str, organization_id: str, threshold: float = 0.6) -> List[Dict[str, Any]]:
    """
    Find employees with similar names to the given name.
    Uses fuzzy matching to find potential matches.
    """
    if not employee_name or employee_name.strip() == "":
        return []
    
    search_name = employee_name.strip().lower()
    search_parts = search_name.split()
    
    employees = await db.employees.find(
        {"organization_id": organization_id},
        {"_id": 0, "id": 1, "first_name": 1, "last_name": 1, "categories": 1, "is_complete": 1}
    ).to_list(10000)
    
    similar_employees = []
    
    for emp in employees:
        emp_first = (emp.get('first_name') or '').lower()
        emp_last = (emp.get('last_name') or '').lower()
        emp_full = f"{emp_first} {emp_last}".strip()
        
        similarity = calculate_name_similarity(search_name, emp_full)
        
        first_match = False
        last_match = False
        
        if len(search_parts) >= 1:
            if search_parts[0] and emp_first:
                first_sim = calculate_name_similarity(search_parts[0], emp_first)
                first_match = first_sim >= 0.8
        
        if len(search_parts) >= 2:
            search_last = ' '.join(search_parts[1:])
            if search_last and emp_last:
                last_sim = calculate_name_similarity(search_last, emp_last)
                last_match = last_sim >= 0.8
        
        if first_match and last_match:
            similarity = max(similarity, 0.95)
        elif first_match or last_match:
            similarity = max(similarity, 0.7)
        
        if similarity >= threshold:
            similar_employees.append({
                "id": emp.get('id'),
                "first_name": emp.get('first_name'),
                "last_name": emp.get('last_name'),
                "full_name": f"{emp.get('first_name', '')} {emp.get('last_name', '')}".strip(),
                "categories": emp.get('categories', []),
                "is_complete": emp.get('is_complete', False),
                "similarity_score": round(similarity, 2),
                "match_type": "exact" if similarity >= 0.95 else "similar"
            })
    
    similar_employees.sort(key=lambda x: x['similarity_score'], reverse=True)
    return similar_employees[:10]


async def apply_name_correction_to_timesheets(
    incorrect_name: str, 
    correct_name: str, 
    organization_id: str
) -> Tuple[int, int]:
    """
    Apply a name correction to all timesheets in an organization.
    Returns: Tuple of (timesheets_updated, entries_corrected)
    """
    timesheets_updated = 0
    entries_corrected = 0
    
    timesheets = await db.timesheets.find(
        {"organization_id": organization_id},
        {"_id": 0}
    ).to_list(10000)
    
    incorrect_lower = incorrect_name.lower()
    
    for ts in timesheets:
        updated = False
        extracted = ts.get('extracted_data', {})
        
        if not isinstance(extracted, dict):
            continue
        
        employee_entries = extracted.get('employee_entries', [])
        for emp in employee_entries:
            if isinstance(emp, dict):
                emp_name = emp.get('employee_name', '')
                if emp_name and emp_name.lower() == incorrect_lower:
                    emp['employee_name'] = correct_name
                    emp['name_corrected_from'] = emp_name
                    emp['name_corrected_at'] = datetime.now(timezone.utc).isoformat()
                    entries_corrected += 1
                    updated = True
        
        reg_results = ts.get('registration_results', {})
        if isinstance(reg_results, dict):
            for emp in reg_results.get('employees', []):
                if isinstance(emp, dict):
                    emp_first = emp.get('first_name', '')
                    emp_last = emp.get('last_name', '')
                    full_name = f"{emp_first} {emp_last}".strip()
                    if full_name.lower() == incorrect_lower:
                        parts = correct_name.split()
                        if len(parts) >= 2:
                            emp['first_name'] = parts[0]
                            emp['last_name'] = ' '.join(parts[1:])
                        else:
                            emp['last_name'] = correct_name
                        emp['name_corrected_from'] = full_name
                        updated = True
        
        if updated:
            await db.timesheets.update_one(
                {"id": ts['id']},
                {"$set": {
                    "extracted_data": extracted,
                    "registration_results": reg_results,
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }}
            )
            timesheets_updated += 1
    
    await db.name_corrections.update_one(
        {"organization_id": organization_id, "incorrect_name": {"$regex": f"^{incorrect_name}$", "$options": "i"}},
        {"$inc": {"times_applied": entries_corrected}}
    )
    
    return timesheets_updated, entries_corrected


# ============================================================================
# Employee CRUD Routes
# ============================================================================

@employees_router.post("", response_model=EmployeeProfile)
async def create_employee(employee: EmployeeProfile, organization_id: str = Depends(get_organization_id)):
    """Create a new employee profile - HIPAA compliant"""
    employee.organization_id = organization_id
    employee.created_at = datetime.now(timezone.utc)
    employee.updated_at = datetime.now(timezone.utc)
    
    doc = employee.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    doc['updated_at'] = doc['updated_at'].isoformat()
    
    await db.employees.insert_one(doc)
    logger.info(f"Employee created: {employee.id} for org {organization_id}")
    
    return employee


@employees_router.get("", response_model=List[EmployeeProfile])
async def get_employees(
    status: Optional[str] = None,
    category: Optional[str] = None,
    is_complete: Optional[bool] = None,
    organization_id: str = Depends(get_organization_id)
):
    """Get all employees with optional filtering - HIPAA compliant"""
    query = {"organization_id": organization_id}
    
    if status:
        query["status"] = status
    if category:
        query["categories"] = category
    if is_complete is not None:
        query["is_complete"] = is_complete
    
    employees = await db.employees.find(query, {"_id": 0}).sort("last_name", 1).to_list(10000)
    
    for emp in employees:
        if isinstance(emp.get('created_at'), str):
            emp['created_at'] = datetime.fromisoformat(emp['created_at'])
        if isinstance(emp.get('updated_at'), str):
            emp['updated_at'] = datetime.fromisoformat(emp['updated_at'])
    
    return employees


@employees_router.get("/{employee_id}", response_model=EmployeeProfile)
async def get_employee(employee_id: str, organization_id: str = Depends(get_organization_id)):
    """Get specific employee by ID - HIPAA compliant"""
    employee = await db.employees.find_one({"id": employee_id, "organization_id": organization_id}, {"_id": 0})
    
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    if isinstance(employee.get('created_at'), str):
        employee['created_at'] = datetime.fromisoformat(employee['created_at'])
    if isinstance(employee.get('updated_at'), str):
        employee['updated_at'] = datetime.fromisoformat(employee['updated_at'])
    
    return employee


@employees_router.put("/{employee_id}", response_model=EmployeeProfile)
async def update_employee(employee_id: str, employee_update: EmployeeProfileUpdate, organization_id: str = Depends(get_organization_id)):
    """Update employee profile and auto-sync with all related timesheets - HIPAA compliant"""
    from validation_utils import validate_employee_required_fields
    
    existing = await db.employees.find_one({"id": employee_id, "organization_id": organization_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    update_data = employee_update.model_dump(exclude_unset=True)
    update_data['updated_at'] = datetime.now(timezone.utc).isoformat()
    
    merged_data = {**existing, **update_data}
    
    if update_data.get('is_complete') == True:
        is_valid, errors = validate_employee_required_fields(merged_data)
        if not is_valid:
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "Cannot mark profile complete. Required fields marked with (*) are missing.",
                    "missing_fields": errors,
                    "required_by": "Ohio Medicaid (ODM) and Electronic Visit Verification (EVV)"
                }
            )
    
    result = await db.employees.update_one(
        {"id": employee_id, "organization_id": organization_id},
        {"$set": update_data}
    )
    
    updated_employee = await db.employees.find_one({"id": employee_id, "organization_id": organization_id}, {"_id": 0})
    
    # AUTO-SYNC: Update all timesheets that reference this employee
    if update_data.get('first_name') or update_data.get('last_name'):
        full_name = f"{updated_employee.get('first_name', '')} {updated_employee.get('last_name', '')}".strip()
        
        timesheets_to_update = await db.timesheets.find({
            "organization_id": organization_id,
            "registration_results.employees.id": employee_id
        }, {"_id": 0}).to_list(1000)
        
        for timesheet in timesheets_to_update:
            if timesheet.get('extracted_data') and isinstance(timesheet['extracted_data'], dict):
                employee_entries = timesheet['extracted_data'].get('employee_entries', [])
                for entry in employee_entries:
                    if isinstance(entry, dict):
                        entry['employee_name'] = full_name
                        entry['auto_corrected'] = True
                        entry['corrected_at'] = datetime.now(timezone.utc).isoformat()
                
                await db.timesheets.update_one(
                    {"id": timesheet['id']},
                    {"$set": {
                        "extracted_data": timesheet['extracted_data'],
                        "updated_at": datetime.now(timezone.utc).isoformat()
                    }}
                )
        
        logger.info(f"Auto-synced {len(timesheets_to_update)} timesheets with updated employee name: {full_name}")
    
    return EmployeeProfile(**updated_employee)


@employees_router.delete("/{employee_id}")
async def delete_employee(employee_id: str, organization_id: str = Depends(get_organization_id)):
    """Delete an employee profile - HIPAA compliant"""
    result = await db.employees.delete_one({"id": employee_id, "organization_id": organization_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    return {"message": "Employee deleted successfully"}


@employees_router.get("/{employee_id}/completion-status")
async def get_employee_completion_status(employee_id: str, organization_id: str = Depends(get_organization_id)):
    """Get profile completion status for employee - HIPAA compliant"""
    from validation_utils import get_profile_completion_status
    
    employee = await db.employees.find_one({"id": employee_id, "organization_id": organization_id}, {"_id": 0})
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    status = get_profile_completion_status('employee', employee)
    return status


# ============================================================================
# Employee Linking Routes
# ============================================================================

@employees_router.post("/link")
async def link_scanned_employee_to_existing(
    scanned_employee_id: str,
    existing_employee_id: str,
    organization_id: str = Depends(get_organization_id)
):
    """
    Link a scanned employee to an existing employee profile.
    This replaces all references to the scanned employee with the existing one.
    HIPAA compliant - org isolated.
    """
    scanned_emp = await db.employees.find_one(
        {"id": scanned_employee_id, "organization_id": organization_id},
        {"_id": 0}
    )
    if not scanned_emp:
        raise HTTPException(status_code=404, detail="Scanned employee not found")
    
    existing_emp = await db.employees.find_one(
        {"id": existing_employee_id, "organization_id": organization_id},
        {"_id": 0}
    )
    if not existing_emp:
        raise HTTPException(status_code=404, detail="Existing employee not found")
    
    scanned_name = f"{scanned_emp.get('first_name', '')} {scanned_emp.get('last_name', '')}".strip()
    existing_name = f"{existing_emp.get('first_name', '')} {existing_emp.get('last_name', '')}".strip()
    
    timesheets_updated = 0
    timesheets = await db.timesheets.find({
        "organization_id": organization_id,
        "registration_results.employees.id": scanned_employee_id
    }, {"_id": 0}).to_list(10000)
    
    for ts in timesheets:
        updated = False
        reg_results = ts.get('registration_results', {})
        
        if 'employees' in reg_results:
            for emp in reg_results['employees']:
                if emp.get('id') == scanned_employee_id:
                    emp['id'] = existing_employee_id
                    emp['first_name'] = existing_emp.get('first_name')
                    emp['last_name'] = existing_emp.get('last_name')
                    emp['linked_from'] = scanned_name
                    updated = True
        
        if ts.get('extracted_data') and isinstance(ts['extracted_data'], dict):
            for entry in ts['extracted_data'].get('employee_entries', []):
                if isinstance(entry, dict):
                    emp_name = entry.get('employee_name', '').lower()
                    if scanned_name.lower() in emp_name or emp_name in scanned_name.lower():
                        entry['employee_name'] = existing_name
                        entry['linked_from_scanned'] = scanned_name
                        updated = True
        
        if updated:
            await db.timesheets.update_one(
                {"id": ts['id']},
                {"$set": {
                    "registration_results": reg_results,
                    "extracted_data": ts.get('extracted_data'),
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }}
            )
            timesheets_updated += 1
    
    await db.employees.delete_one({"id": scanned_employee_id, "organization_id": organization_id})
    
    logger.info(f"Linked scanned employee '{scanned_name}' to existing '{existing_name}', updated {timesheets_updated} timesheets")
    
    return {
        "status": "success",
        "message": f"Linked '{scanned_name}' to existing employee '{existing_name}'",
        "scanned_employee_deleted": scanned_name,
        "linked_to": {
            "id": existing_employee_id,
            "name": existing_name
        },
        "timesheets_updated": timesheets_updated
    }


# ============================================================================
# Name Correction Routes
# ============================================================================

@employees_router.post("/name-corrections")
async def create_name_correction(
    incorrect_name: str,
    correct_name: str,
    apply_to_all: bool = True,
    organization_id: str = Depends(get_organization_id)
):
    """Create a name correction mapping and optionally apply it to all timesheets - HIPAA compliant"""
    if not incorrect_name or not correct_name:
        raise HTTPException(status_code=400, detail="Both incorrect_name and correct_name are required")
    
    incorrect_name = incorrect_name.strip()
    correct_name = correct_name.strip()
    
    if incorrect_name.lower() == correct_name.lower():
        raise HTTPException(status_code=400, detail="Incorrect and correct names cannot be the same")
    
    correction_doc = {
        "id": str(uuid.uuid4()),
        "organization_id": organization_id,
        "incorrect_name": incorrect_name,
        "correct_name": correct_name,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "times_applied": 0
    }
    
    existing = await db.name_corrections.find_one({
        "organization_id": organization_id,
        "incorrect_name": {"$regex": f"^{incorrect_name}$", "$options": "i"}
    })
    
    if existing:
        await db.name_corrections.update_one(
            {"id": existing["id"]},
            {"$set": {"correct_name": correct_name, "updated_at": datetime.now(timezone.utc).isoformat()}}
        )
        correction_id = existing["id"]
    else:
        await db.name_corrections.insert_one(correction_doc)
        correction_id = correction_doc["id"]
    
    timesheets_updated = 0
    entries_corrected = 0
    
    if apply_to_all:
        timesheets_updated, entries_corrected = await apply_name_correction_to_timesheets(
            incorrect_name, correct_name, organization_id
        )
    
    logger.info(f"Name correction created: '{incorrect_name}' → '{correct_name}', applied to {timesheets_updated} timesheets")
    
    return {
        "status": "success",
        "correction_id": correction_id,
        "incorrect_name": incorrect_name,
        "correct_name": correct_name,
        "applied_to_all": apply_to_all,
        "timesheets_updated": timesheets_updated,
        "entries_corrected": entries_corrected,
        "message": f"Name correction saved. Updated {entries_corrected} entries across {timesheets_updated} timesheets."
    }


@employees_router.get("/name-corrections")
async def get_name_corrections(organization_id: str = Depends(get_organization_id)):
    """Get all saved name corrections for the organization - HIPAA compliant"""
    corrections = await db.name_corrections.find(
        {"organization_id": organization_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(1000)
    
    return {
        "corrections": corrections,
        "total": len(corrections)
    }


@employees_router.post("/name-corrections/apply-all")
async def apply_all_name_corrections(organization_id: str = Depends(get_organization_id)):
    """Apply all saved name corrections to all timesheets - HIPAA compliant"""
    corrections = await db.name_corrections.find(
        {"organization_id": organization_id},
        {"_id": 0}
    ).to_list(1000)
    
    if not corrections:
        return {
            "status": "no_corrections",
            "message": "No name corrections found"
        }
    
    total_timesheets = 0
    total_entries = 0
    
    for corr in corrections:
        ts_updated, entries_corrected = await apply_name_correction_to_timesheets(
            corr['incorrect_name'],
            corr['correct_name'],
            organization_id
        )
        total_timesheets += ts_updated
        total_entries += entries_corrected
    
    return {
        "status": "success",
        "corrections_applied": len(corrections),
        "timesheets_updated": total_timesheets,
        "entries_corrected": total_entries,
        "message": f"Applied {len(corrections)} corrections to {total_entries} entries across {total_timesheets} timesheets"
    }


@employees_router.delete("/name-corrections/{correction_id}")
async def delete_name_correction(correction_id: str, organization_id: str = Depends(get_organization_id)):
    """Delete a name correction mapping - HIPAA compliant"""
    result = await db.name_corrections.delete_one({
        "id": correction_id,
        "organization_id": organization_id
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Name correction not found")
    
    return {"message": "Name correction deleted"}


# ============================================================================
# Billing Code Routes
# ============================================================================

@employees_router.get("/{employee_id}/billing-codes")
async def get_employee_billing_codes(employee_id: str, organization_id: str = Depends(get_organization_id)):
    """Get the billing codes assigned to an employee - HIPAA compliant"""
    employee = await db.employees.find_one(
        {"id": employee_id, "organization_id": organization_id},
        {"_id": 0, "id": 1, "first_name": 1, "last_name": 1, "billing_codes": 1, "categories": 1}
    )
    
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    return {
        "employee_id": employee["id"],
        "employee_name": f"{employee.get('first_name', '')} {employee.get('last_name', '')}",
        "billing_codes": employee.get("billing_codes", []),
        "categories": employee.get("categories", [])
    }


@employees_router.get("/by-name/{name}/billing-codes")
async def get_employee_billing_codes_by_name(name: str, organization_id: str = Depends(get_organization_id)):
    """Get billing codes for an employee by name (for timesheet editing) - HIPAA compliant"""
    search_name = name.strip().lower()
    
    employees = await db.employees.find(
        {"organization_id": organization_id},
        {"_id": 0, "id": 1, "first_name": 1, "last_name": 1, "billing_codes": 1, "categories": 1}
    ).to_list(10000)
    
    best_match = None
    best_score = 0.0
    
    for emp in employees:
        full_name = f"{emp.get('first_name', '')} {emp.get('last_name', '')}".strip().lower()
        
        if full_name == search_name:
            best_match = emp
            break
        
        similarity = calculate_name_similarity(search_name, full_name)
        if similarity > best_score and similarity >= 0.8:
            best_score = similarity
            best_match = emp
    
    if not best_match:
        return {
            "employee_found": False,
            "billing_codes": ["T1019", "T1020", "T1021", "G0156"],
            "message": "No matching employee found, showing default codes"
        }
    
    return {
        "employee_found": True,
        "employee_id": best_match["id"],
        "employee_name": f"{best_match.get('first_name', '')} {best_match.get('last_name', '')}",
        "billing_codes": best_match.get("billing_codes", []),
        "categories": best_match.get("categories", [])
    }


# ============================================================================
# Duplicate Detection Routes
# ============================================================================

@employees_router.get("/duplicates/find")
async def find_duplicate_employees(organization_id: str = Depends(get_organization_id)):
    """Find employees with similar/duplicate names - HIPAA compliant"""
    employees = await db.employees.find(
        {"organization_id": organization_id}, 
        {"_id": 0}
    ).to_list(10000)
    
    def normalize_name(first_name, last_name):
        first = (first_name or "").strip().lower()
        last = (last_name or "").strip().lower()
        return f"{first} {last}"
    
    name_groups = {}
    for emp in employees:
        normalized = normalize_name(emp.get('first_name'), emp.get('last_name'))
        if normalized not in name_groups:
            name_groups[normalized] = []
        name_groups[normalized].append(emp)
    
    duplicate_groups = []
    for normalized_name, group in name_groups.items():
        if len(group) > 1:
            sorted_group = sorted(
                group, 
                key=lambda x: x.get('updated_at', '1900-01-01') if isinstance(x.get('updated_at'), str) else x.get('updated_at', datetime.min).isoformat(),
                reverse=True
            )
            
            suggested_keep = sorted_group[0]
            suggested_delete = sorted_group[1:]
            
            duplicate_groups.append({
                "normalized_name": normalized_name,
                "display_name": f"{sorted_group[0].get('first_name', '')} {sorted_group[0].get('last_name', '')}",
                "total_duplicates": len(group),
                "suggested_keep": {
                    "id": suggested_keep.get('id'),
                    "first_name": suggested_keep.get('first_name'),
                    "last_name": suggested_keep.get('last_name'),
                    "email": suggested_keep.get('email'),
                    "phone": suggested_keep.get('phone'),
                    "categories": suggested_keep.get('categories', []),
                    "is_complete": suggested_keep.get('is_complete', False),
                    "updated_at": suggested_keep.get('updated_at'),
                    "reason": "Most recently updated"
                },
                "suggested_delete": [
                    {
                        "id": emp.get('id'),
                        "first_name": emp.get('first_name'),
                        "last_name": emp.get('last_name'),
                        "email": emp.get('email'),
                        "phone": emp.get('phone'),
                        "categories": emp.get('categories', []),
                        "is_complete": emp.get('is_complete', False),
                        "updated_at": emp.get('updated_at'),
                        "reason": "Older record"
                    }
                    for emp in suggested_delete
                ]
            })
    
    duplicate_groups.sort(key=lambda x: x['total_duplicates'], reverse=True)
    
    return {
        "total_duplicate_groups": len(duplicate_groups),
        "total_duplicate_records": sum(g['total_duplicates'] - 1 for g in duplicate_groups),
        "duplicate_groups": duplicate_groups
    }


@employees_router.post("/duplicates/resolve")
async def resolve_duplicate_employees(
    keep_id: str,
    delete_ids: List[str],
    organization_id: str = Depends(get_organization_id)
):
    """Resolve duplicate employees by keeping one and deleting others - HIPAA compliant"""
    keep_employee = await db.employees.find_one(
        {"id": keep_id, "organization_id": organization_id},
        {"_id": 0}
    )
    if not keep_employee:
        raise HTTPException(status_code=404, detail="Employee to keep not found")
    
    deleted_count = 0
    deleted_names = []
    
    for delete_id in delete_ids:
        employee = await db.employees.find_one(
            {"id": delete_id, "organization_id": organization_id},
            {"_id": 0}
        )
        if employee:
            result = await db.employees.delete_one(
                {"id": delete_id, "organization_id": organization_id}
            )
            if result.deleted_count > 0:
                deleted_count += 1
                deleted_names.append(f"{employee.get('first_name', '')} {employee.get('last_name', '')}")
                logger.info(f"Deleted duplicate employee: {delete_id} ({employee.get('first_name')} {employee.get('last_name')})")
    
    return {
        "status": "success",
        "kept_employee": {
            "id": keep_employee.get('id'),
            "name": f"{keep_employee.get('first_name', '')} {keep_employee.get('last_name', '')}"
        },
        "deleted_count": deleted_count,
        "deleted_names": deleted_names,
        "message": f"Kept 1 employee, deleted {deleted_count} duplicate(s)"
    }
