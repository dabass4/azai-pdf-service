"""OMES EDI SOAP Client for Real-time Transactions

Handles:
- 270/271 Eligibility verification
- 276/277 Claim status inquiry
- 278 Authorization requests
"""

import os
import logging
from typing import Optional
from datetime import datetime
from zeep import Client as ZeepClient
from zeep.transports import Transport
from zeep.wsse.username import UsernameToken
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .models import EligibilityRequest, EligibilityResponse, ClaimStatusRequest, ClaimStatusResponse
from .x12_builders import X12Builder270, X12Builder276
from .x12_parsers import parse_271_response, parse_277_response

logger = logging.getLogger(__name__)


class OMESSOAPClient:
    """Client for OMES EDI SOAP Web Services"""
    
    def __init__(self, 
                 endpoint_url: Optional[str] = None,
                 username: Optional[str] = None,
                 password: Optional[str] = None,
                 cert_path: Optional[str] = None,
                 key_path: Optional[str] = None):
        """
        Initialize OMES SOAP client
        
        Args:
            endpoint_url: SOAP endpoint (defaults to CERT environment)
            username: SOAP username
            password: SOAP password
            cert_path: Path to SSL certificate (.pem)
            key_path: Path to SSL private key (.pem)
        """
        self.endpoint_url = endpoint_url or os.getenv(
            "OMES_SOAP_ENDPOINT",
            "https://dp.cert.oh.healthinteractive.net:993/EDIGateway/v1.0"
        )
        self.username = username or os.getenv("OMES_SOAP_USERNAME", "")
        self.password = password or os.getenv("OMES_SOAP_PASSWORD", "")
        self.cert_path = cert_path or os.getenv("OMES_SOAP_CERT_PATH", "")
        self.key_path = key_path or os.getenv("OMES_SOAP_KEY_PATH", "")
        self.tpid = os.getenv("OMES_TPID", "0000000")
        
        # Configure HTTP session with retries and SSL
        self.session = self._create_session()
        
        # Initialize SOAP client (will be created when needed)
        self._soap_client = None
    
    def _create_session(self) -> requests.Session:
        """Create HTTP session with SSL and retry logic"""
        session = requests.Session()
        
        # Configure SSL certificates if provided
        if self.cert_path and self.key_path:
            session.cert = (self.cert_path, self.key_path)
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["POST"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        
        return session
    
    def _get_soap_client(self) -> ZeepClient:
        """Lazy initialization of SOAP client"""
        if self._soap_client is None:
            transport = Transport(session=self.session)
            
            # Create SOAP client with WS-Security username token
            self._soap_client = ZeepClient(
                wsdl=None,  # Will use endpoint URL directly
                transport=transport,
                wsse=UsernameToken(self.username, self.password)
            )
        
        return self._soap_client
    
    def _create_soap_envelope(self, payload: str, payload_type: str) -> str:
        """
        Create SOAP envelope with X12 payload
        
        Args:
            payload: X12 transaction content
            payload_type: Transaction type (e.g., "X12 270 Request 005010X279A1")
        
        Returns:
            Complete SOAP envelope as string
        """
        timestamp = datetime.utcnow().isoformat() + "Z"
        
        envelope = f'''<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" 
               xmlns:edis="http://omes.ohio.gov/edi">
    <soap:Header>
        <wsse:Security xmlns:wsse="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd">
            <wsse:UsernameToken>
                <wsse:Username>{self.username}</wsse:Username>
                <wsse:Password Type="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-username-token-profile-1.0#PasswordText">{self.password}</wsse:Password>
            </wsse:UsernameToken>
        </wsse:Security>
    </soap:Header>
    <soap:Body>
        <edis:COREEnvelopeRealTimeRequest>
            <PayloadType>{payload_type}</PayloadType>
            <ProcessingMode>RealTime</ProcessingMode>
            <PayloadID>{datetime.utcnow().strftime("%Y%m%d%H%M%S")}</PayloadID>
            <TimeStamp>{timestamp}</TimeStamp>
            <SenderID>{self.tpid}</SenderID>
            <ReceiverID>ODMITS</ReceiverID>
            <CORERuleVersion>2.2.0</CORERuleVersion>
            <Payload><![CDATA[{payload}]]></Payload>
        </edis:COREEnvelopeRealTimeRequest>
    </soap:Body>
</soap:Envelope>'''
        
        return envelope
    
    def _send_soap_request(self, envelope: str) -> str:
        """
        Send SOAP request and return response
        
        Args:
            envelope: SOAP envelope XML
        
        Returns:
            Response payload (X12 format)
        """
        headers = {
            'Content-Type': 'text/xml; charset=utf-8',
            'SOAPAction': ''
        }
        
        try:
            response = self.session.post(
                self.endpoint_url,
                data=envelope.encode('utf-8'),
                headers=headers,
                timeout=30
            )
            response.raise_for_status()
            
            # Extract payload from SOAP response
            # TODO: Parse SOAP response XML and extract CDATA payload
            response_text = response.text
            
            logger.info(f"SOAP response received: {len(response_text)} bytes")
            return response_text
            
        except requests.exceptions.RequestException as e:
            logger.error(f"SOAP request failed: {str(e)}")
            raise Exception(f"OMES SOAP request failed: {str(e)}")
    
    def verify_eligibility(self, request: EligibilityRequest) -> EligibilityResponse:
        """
        Verify patient eligibility (270/271 transaction)
        
        Args:
            request: Eligibility request details
        
        Returns:
            Eligibility response
        """
        try:
            # Build 270 X12 transaction
            builder = X12Builder270(
                sender_id=self.tpid,
                receiver_id="ODMITS"
            )
            x12_payload = builder.build_270(request)
            
            # Create SOAP envelope
            envelope = self._create_soap_envelope(
                payload=x12_payload,
                payload_type="X12 270 Request 005010X279A1"
            )
            
            # Send request
            response_payload = self._send_soap_request(envelope)
            
            # Parse 271 response
            eligibility_response = parse_271_response(response_payload, request)
            
            logger.info(f"Eligibility verified for member {request.member_id}: Active={eligibility_response.is_active}")
            return eligibility_response
            
        except Exception as e:
            logger.error(f"Eligibility verification failed: {str(e)}")
            # Return negative response
            return EligibilityResponse(
                member_id=request.member_id,
                is_active=False,
                rejection_reason=str(e),
                response_raw=None
            )
    
    def check_claim_status(self, request: ClaimStatusRequest) -> ClaimStatusResponse:
        """
        Check claim status (276/277 transaction)
        
        Args:
            request: Claim status request details
        
        Returns:
            Claim status response
        """
        try:
            # Build 276 X12 transaction
            builder = X12Builder276(
                sender_id=self.tpid,
                receiver_id="ODMITS"
            )
            x12_payload = builder.build_276(request)
            
            # Create SOAP envelope
            envelope = self._create_soap_envelope(
                payload=x12_payload,
                payload_type="X12 276 Request 005010X212"
            )
            
            # Send request
            response_payload = self._send_soap_request(envelope)
            
            # Parse 277 response
            status_response = parse_277_response(response_payload, request)
            
            logger.info(f"Claim status checked for {request.claim_number}: {status_response.status_description}")
            return status_response
            
        except Exception as e:
            logger.error(f"Claim status check failed: {str(e)}")
            raise Exception(f"Claim status check failed: {str(e)}")
