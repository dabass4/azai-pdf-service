"""OMES EDI Integration for Ohio Medicaid

Provides:
- SOAP client for real-time transactions (270/271, 276/277, 278)
- SFTP client for batch submissions (837, receive 835)
- X12 builders and parsers
"""

from .soap_client import OMESSOAPClient
from .sftp_client import OMESSFTPClient
from .models import (
    EligibilityRequest,
    EligibilityResponse,
    ClaimStatusRequest,
    ClaimStatusResponse
)

__all__ = [
    'OMESSOAPClient',
    'OMESSFTPClient',
    'EligibilityRequest',
    'EligibilityResponse',
    'ClaimStatusRequest',
    'ClaimStatusResponse'
]
