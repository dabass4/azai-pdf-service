"""
NPI Lookup Service
Fetches physician information from NPPES and PECOS certification status
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import aiohttp
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/npi", tags=["NPI Lookup"])


class PhysicianInfo(BaseModel):
    """Response model for NPI lookup"""
    npi: str
    name: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    credential: Optional[str] = None
    specialty: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    phone: Optional[str] = None
    is_pecos_certified: bool = False
    pecos_status: str = "Unknown"
    source: str = "NPPES"
    error: Optional[str] = None


class NPISearchResponse(BaseModel):
    """Response model for NPI search"""
    results: list[PhysicianInfo]
    total_count: int
    query: str
    error: Optional[str] = None


async def fetch_nppes_data(url: str) -> dict:
    """Fetch data from NPPES API"""
    async with aiohttp.ClientSession() as session:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as response:
            if response.status != 200:
                raise HTTPException(status_code=502, detail=f"NPPES API error: HTTP {response.status}")
            return await response.json()


async def check_pecos_status(npi: str) -> tuple[bool, str]:
    """
    Check PECOS certification status for a given NPI.
    
    PECOS (Provider Enrollment, Chain, and Ownership System) is the CMS system
    for Medicare provider enrollment. A provider must be PECOS-enrolled to 
    bill Medicare.
    
    Note: The actual PECOS API requires authentication. This implementation
    uses heuristics based on NPPES data as a proxy. For production, you would
    integrate with the actual CMS PECOS API.
    """
    try:
        # Query NPPES for the provider
        url = f"https://npiregistry.cms.hhs.gov/api/?number={npi}&version=2.1"
        data = await fetch_nppes_data(url)
        
        if data.get("result_count", 0) == 0:
            return False, "NPI not found"
        
        result = data["results"][0]
        
        # Check if provider has Medicare-relevant taxonomy codes
        # Providers enrolled in Medicare typically have specific taxonomy codes
        taxonomies = result.get("taxonomies", [])
        
        # Check for primary taxonomy with Medicare participation indicators
        has_primary_taxonomy = False
        for taxonomy in taxonomies:
            if taxonomy.get("primary", False):
                has_primary_taxonomy = True
                # Check license info which can indicate active practice
                if taxonomy.get("state") and taxonomy.get("license"):
                    # Provider has active state license - likely PECOS enrolled
                    return True, "Enrolled (based on active license)"
        
        # If provider has taxonomies and addresses, likely enrolled
        addresses = result.get("addresses", [])
        practice_address = next((a for a in addresses if a.get("address_purpose") == "LOCATION"), None)
        
        if has_primary_taxonomy and practice_address:
            return True, "Likely Enrolled"
        elif has_primary_taxonomy:
            return False, "Enrollment Uncertain"
        else:
            return False, "Not Enrolled"
            
    except Exception as e:
        logger.error(f"Error checking PECOS status for NPI {npi}: {e}")
        return False, "Unable to verify"


def parse_nppes_result(result: dict) -> PhysicianInfo:
    """Parse a single NPPES result into PhysicianInfo"""
    basic = result.get("basic", {})
    addresses = result.get("addresses", [])
    taxonomies = result.get("taxonomies", [])
    
    # Get practice address
    practice_address = next(
        (a for a in addresses if a.get("address_purpose") == "LOCATION"),
        addresses[0] if addresses else {}
    )
    
    # Get primary taxonomy/specialty
    primary_taxonomy = next(
        (t for t in taxonomies if t.get("primary", False)),
        taxonomies[0] if taxonomies else {}
    )
    
    # Build name
    first_name = basic.get("first_name", "")
    last_name = basic.get("last_name", "")
    credential = basic.get("credential", "")
    
    if basic.get("organization_name"):
        # Organization NPI
        name = basic.get("organization_name", "")
    else:
        # Individual NPI
        name = f"{first_name} {last_name}"
        if credential:
            name += f", {credential}"
    
    return PhysicianInfo(
        npi=result.get("number", ""),
        name=name.strip(),
        first_name=first_name,
        last_name=last_name,
        credential=credential,
        specialty=primary_taxonomy.get("desc", ""),
        address=practice_address.get("address_1", ""),
        city=practice_address.get("city", ""),
        state=practice_address.get("state", ""),
        zip_code=practice_address.get("postal_code", "")[:5] if practice_address.get("postal_code") else "",
        phone=practice_address.get("telephone_number", ""),
        is_pecos_certified=False,  # Will be updated separately
        pecos_status="Checking...",
        source="NPPES"
    )


@router.get("/lookup/{npi}", response_model=PhysicianInfo)
async def lookup_npi(npi: str):
    """
    Look up physician information by NPI number.
    
    Args:
        npi: 10-digit NPI number
    
    Returns:
        PhysicianInfo with provider details and PECOS status
    """
    # Validate NPI format
    if not npi.isdigit() or len(npi) != 10:
        raise HTTPException(
            status_code=400,
            detail="Invalid NPI format. Must be exactly 10 digits."
        )
    
    try:
        # Query NPPES API
        url = f"https://npiregistry.cms.hhs.gov/api/?number={npi}&version=2.1"
        data = await fetch_nppes_data(url)
        
        if data.get("result_count", 0) == 0:
            raise HTTPException(status_code=404, detail=f"NPI {npi} not found in NPPES registry")
        
        result = data["results"][0]
        physician = parse_nppes_result(result)
        
        # Check PECOS status
        is_pecos, pecos_status = await check_pecos_status(npi)
        physician.is_pecos_certified = is_pecos
        physician.pecos_status = pecos_status
        
        return physician
        
    except HTTPException:
        raise
    except aiohttp.ClientError as e:
        logger.error(f"Network error fetching NPI data: {e}")
        raise HTTPException(status_code=502, detail=f"Network error: {str(e)}")
    except Exception as e:
        logger.error(f"Error looking up NPI {npi}: {e}")
        raise HTTPException(status_code=500, detail=f"Error looking up NPI: {str(e)}")


@router.get("/search", response_model=NPISearchResponse)
async def search_npi(
    name: Optional[str] = None,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    state: Optional[str] = None,
    limit: int = 10
):
    """
    Search for physicians by name.
    
    Args:
        name: Full or partial name to search
        first_name: First name
        last_name: Last name  
        state: Two-letter state code
        limit: Maximum results to return (default 10)
    
    Returns:
        NPISearchResponse with list of matching providers
    """
    # Build query parameters
    params = ["version=2.1", "enumeration_type=NPI-1"]  # NPI-1 = Individual providers
    
    if first_name:
        params.append(f"first_name={first_name}*")
    if last_name:
        params.append(f"last_name={last_name}*")
    if name and not (first_name or last_name):
        # Try to split name
        parts = name.strip().split()
        if len(parts) >= 2:
            params.append(f"first_name={parts[0]}*")
            params.append(f"last_name={parts[-1]}*")
        else:
            params.append(f"last_name={name}*")
    if state:
        params.append(f"state={state.upper()}")
    
    params.append(f"limit={min(limit, 50)}")
    
    query_string = "&".join(params)
    
    try:
        url = f"https://npiregistry.cms.hhs.gov/api/?{query_string}"
        data = await fetch_nppes_data(url)
        
        results = []
        for result in data.get("results", [])[:limit]:
            physician = parse_nppes_result(result)
            # Note: We don't check PECOS for search results to keep it fast
            # PECOS is checked when a specific NPI is selected
            physician.pecos_status = "Not checked"
            results.append(physician)
        
        return NPISearchResponse(
            results=results,
            total_count=data.get("result_count", 0),
            query=name or f"{first_name or ''} {last_name or ''}".strip(),
            error=None
        )
        
    except aiohttp.ClientError as e:
        logger.error(f"Network error searching NPI: {e}")
        raise HTTPException(status_code=502, detail=f"Network error: {str(e)}")
    except Exception as e:
        logger.error(f"Error searching NPI: {e}")
        raise HTTPException(status_code=500, detail=f"Error searching: {str(e)}")
