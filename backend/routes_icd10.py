"""
ICD-10 Code Lookup Service
Fetches ICD-10 code information from icd10data.com including billability status
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import aiohttp
from bs4 import BeautifulSoup
import re
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/icd10", tags=["ICD-10 Lookup"])


class ICD10LookupResponse(BaseModel):
    """Response model for ICD-10 code lookup"""
    code: str
    description: str
    is_billable: bool
    billable_text: str  # "Billable/Specific Code" or "Non-Billable/Non-Specific Code"
    source_url: str
    error: Optional[str] = None


class ICD10SearchResult(BaseModel):
    """Individual search result"""
    code: str
    description: str
    is_billable: bool
    url: str


class ICD10SearchResponse(BaseModel):
    """Response model for ICD-10 search"""
    results: list[ICD10SearchResult]
    total_count: int
    query: str
    error: Optional[str] = None


async def fetch_icd10_page(url: str) -> str:
    """Fetch HTML content from icd10data.com"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=15)) as response:
            if response.status != 200:
                raise HTTPException(status_code=502, detail=f"Failed to fetch ICD-10 data: HTTP {response.status}")
            return await response.text()


def parse_billability(html_content: str, target_code: str) -> tuple[bool, str]:
    """
    Parse the billability status from the HTML content for a specific code.
    Returns (is_billable, billable_text)
    
    The icd10data.com search page format shows each code like:
    "ICD-10-CM Diagnosis Code F32.8 ... 20162017...Non-Billable/Non-Specific Code"
    or
    "ICD-10-CM Diagnosis Code F32.9 ... 20162017...Billable/Specific Code"
    """
    import re
    target_code_upper = target_code.upper()
    text_content = html_content
    
    # Strategy 1: Look for the exact pattern where code is followed by billability
    # Pattern: "ICD-10-CM Diagnosis Code {CODE}\n{description}\n{years}Billable" or "Non-Billable"
    # We need to find the CODE then look for the NEXT billability marker before another code appears
    
    # Find all occurrences of our code (case insensitive)
    code_pattern = rf'ICD-10-CM Diagnosis Code {re.escape(target_code)}\b'
    code_matches = list(re.finditer(code_pattern, text_content, re.IGNORECASE))
    
    if code_matches:
        for match in code_matches:
            # Get text after this code until the next ICD-10-CM Diagnosis Code or end
            start_pos = match.end()
            
            # Find next code marker
            next_code_match = re.search(r'ICD-10-CM Diagnosis Code [A-Z]\d{2}', text_content[start_pos:], re.IGNORECASE)
            if next_code_match:
                section_text = text_content[start_pos:start_pos + next_code_match.start()]
            else:
                section_text = text_content[start_pos:start_pos + 2000]  # Take next 2000 chars
            
            # Look for billability in this section
            if "Non-Billable" in section_text:
                return False, "Non-Billable/Non-Specific Code"
            elif "Billable/Specific Code" in section_text or "Billable" in section_text:
                return True, "Billable/Specific Code"
    
    # Strategy 2: Look in the full text for pattern with exact code boundaries
    # Pattern like "F32.820162017...Non-Billable" (years concatenated)
    pattern = rf'{re.escape(target_code)}(?:\s|[0-9])*?(Non-Billable|Billable/Specific Code)'
    match = re.search(pattern, text_content, re.IGNORECASE)
    if match:
        if "Non-Billable" in match.group(1):
            return False, "Non-Billable/Non-Specific Code"
        return True, "Billable/Specific Code"
    
    # Strategy 3: Parse HTML more carefully to find the code's entry
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Find all bold or strong tags that might contain our code
    for bold_tag in soup.find_all(['strong', 'b', 'a']):
        tag_text = bold_tag.get_text()
        if target_code_upper in tag_text.upper():
            # Look at siblings and parents for billability info
            parent = bold_tag.find_parent(['div', 'li', 'p', 'td'])
            if parent:
                parent_text = parent.get_text()
                if "Non-Billable" in parent_text:
                    return False, "Non-Billable/Non-Specific Code"
                elif "Billable/Specific Code" in parent_text or "Billable" in parent_text:
                    return True, "Billable/Specific Code"
    
    # Default - if we can't determine, return unknown
    return True, "Unknown"


def parse_code_description(html_content: str, code: str) -> str:
    """
    Parse the description for a specific ICD-10 code from HTML content.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Try to find the main heading which contains the description
    # Format: "2026 ICD-10-CM Diagnosis Code {CODE}\n{DESCRIPTION}"
    h1_tags = soup.find_all('h1')
    for h1 in h1_tags:
        text = h1.get_text(strip=True)
        if code.upper() in text.upper():
            # The description usually follows the code
            # Try to extract just the description part
            break
    
    # Look for the description in h2 tags (usually contains the actual description)
    h2_tags = soup.find_all('h2')
    for h2 in h2_tags:
        text = h2.get_text(strip=True)
        # Filter out navigation and meta content
        if text and len(text) > 5 and not text.startswith('ICD-10'):
            return text
    
    # Try meta description
    meta_desc = soup.find('meta', attrs={'name': 'description'})
    if meta_desc and meta_desc.get('content'):
        content = meta_desc['content']
        # Extract description from "ICD 10 code for {description}..."
        if 'ICD 10 code for' in content:
            desc = content.split('ICD 10 code for')[1].split('.')[0].strip()
            return desc
    
    # Fallback: try title
    title = soup.find('title')
    if title:
        title_text = title.get_text()
        # Format: "2026 ICD-10-CM Diagnosis Code {CODE}: {DESCRIPTION}"
        if ':' in title_text:
            return title_text.split(':')[1].strip()
    
    return "Description not found"


def parse_search_results(html_content: str) -> list[ICD10SearchResult]:
    """
    Parse search results from icd10data.com search page
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    results = []
    
    # Find all links that point to ICD codes
    code_pattern = re.compile(r'/ICD10CM/Codes/[^"]+')
    
    # Look for code entries in the search results
    # The format typically shows code followed by description
    for link in soup.find_all('a', href=code_pattern):
        href = link.get('href', '')
        text = link.get_text(strip=True)
        
        # Skip navigation links and empty text
        if not text or 'convert to' in text.lower():
            continue
        
        # Extract the code from the URL
        # URL format: /ICD10CM/Codes/F01-F99/F30-F39/F32-/F32.9
        code_match = re.search(r'/([A-Z][0-9]{2}(?:\.[A-Z0-9]{1,4})?)$', href)
        if code_match:
            code = code_match.group(1)
            
            # Check if it's a billable code by looking at nearby text
            parent = link.parent
            if parent:
                parent_text = parent.get_text()
                is_billable = "Billable" in parent_text and "Non-Billable" not in parent_text
            else:
                is_billable = True  # Default assumption
            
            # Get description from the h2 inside the link's context or the link text itself
            description = text if text != code else "No description"
            
            # Only add if we found a valid code
            if code and not any(r.code == code for r in results):
                results.append(ICD10SearchResult(
                    code=code,
                    description=description,
                    is_billable=is_billable,
                    url=f"https://www.icd10data.com{href}"
                ))
    
    return results


@router.get("/lookup/{code}", response_model=ICD10LookupResponse)
async def lookup_icd10_code(code: str):
    """
    Look up a specific ICD-10 code and return its details including billability status.
    
    Args:
        code: The ICD-10 code to look up (e.g., F32.9, Z99.89)
    
    Returns:
        ICD10LookupResponse with code details and billability status
    """
    # Clean and format the code
    code = code.strip().upper()
    
    # Validate code format (basic check)
    if not re.match(r'^[A-Z][0-9]{2}(?:\.[A-Z0-9]{1,4})?$', code):
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid ICD-10 code format: {code}. Expected format: A00.0 or A00"
        )
    
    try:
        # Use the search endpoint which is more reliable
        search_url = f"https://www.icd10data.com/search?s={code}"
        html_content = await fetch_icd10_page(search_url)
        
        # First try to get data from parsed search results (most accurate)
        results = parse_search_results(html_content)
        
        # Look for exact code match in results
        exact_match = None
        for result in results:
            if result.code.upper() == code.upper():
                exact_match = result
                break
        
        if exact_match:
            # Use the exact match data
            return ICD10LookupResponse(
                code=code,
                description=exact_match.description,
                is_billable=exact_match.is_billable,
                billable_text="Billable/Specific Code" if exact_match.is_billable else "Non-Billable/Non-Specific Code",
                source_url=exact_match.url,
                error=None
            )
        
        # Fallback: parse from raw HTML
        is_billable, billable_text = parse_billability(html_content, code)
        description = parse_code_description(html_content, code)
        
        return ICD10LookupResponse(
            code=code,
            description=description,
            is_billable=is_billable,
            billable_text=billable_text if is_billable else "Non-Billable/Non-Specific Code",
            source_url=search_url,
            error=None
        )
        
    except aiohttp.ClientError as e:
        logger.error(f"Network error fetching ICD-10 data for {code}: {e}")
        raise HTTPException(status_code=502, detail=f"Network error: {str(e)}")
    except Exception as e:
        logger.error(f"Error looking up ICD-10 code {code}: {e}")
        raise HTTPException(status_code=500, detail=f"Error looking up code: {str(e)}")


@router.get("/search", response_model=ICD10SearchResponse)
async def search_icd10_codes(q: str):
    """
    Search for ICD-10 codes by keyword or partial code.
    
    Args:
        q: Search query (code or description keywords)
    
    Returns:
        ICD10SearchResponse with list of matching codes
    """
    if not q or len(q) < 2:
        raise HTTPException(status_code=400, detail="Search query must be at least 2 characters")
    
    try:
        search_url = f"https://www.icd10data.com/search?s={q}"
        html_content = await fetch_icd10_page(search_url)
        
        results = parse_search_results(html_content)
        
        return ICD10SearchResponse(
            results=results[:20],  # Limit to 20 results
            total_count=len(results),
            query=q,
            error=None
        )
        
    except aiohttp.ClientError as e:
        logger.error(f"Network error searching ICD-10: {e}")
        raise HTTPException(status_code=502, detail=f"Network error: {str(e)}")
    except Exception as e:
        logger.error(f"Error searching ICD-10 codes: {e}")
        raise HTTPException(status_code=500, detail=f"Error searching codes: {str(e)}")
