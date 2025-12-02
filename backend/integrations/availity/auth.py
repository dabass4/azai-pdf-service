"""Availity OAuth 2.0 Authentication Manager"""

import os
import logging
import httpx
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger(__name__)


class AvailityAuthManager:
    """Manages OAuth 2.0 tokens for Availity API"""
    
    def __init__(self,
                 api_key: Optional[str] = None,
                 client_secret: Optional[str] = None,
                 scope: Optional[str] = None,
                 base_url: Optional[str] = None):
        """
        Initialize Availity auth manager
        
        Args:
            api_key: Availity API key (client_id)
            client_secret: Availity client secret
            scope: Space-separated OAuth scopes
            base_url: Availity base URL
        """
        self.api_key = api_key or os.getenv("AVAILITY_API_KEY", "")
        self.client_secret = client_secret or os.getenv("AVAILITY_CLIENT_SECRET", "")
        self.scope = scope or os.getenv("AVAILITY_SCOPE", "")
        self.base_url = base_url or os.getenv(
            "AVAILITY_BASE_URL",
            "https://api.availity.com"  # Use test: https://tst.api.availity.com
        )
        
        self.token_endpoint = f"{self.base_url}/v1/token"
        
        # Token cache
        self.access_token: Optional[str] = None
        self.token_expires_at: Optional[datetime] = None
    
    def is_token_valid(self) -> bool:
        """Check if cached token is still valid (with 30 second buffer)"""
        if not self.access_token or not self.token_expires_at:
            return False
        return datetime.utcnow() < (self.token_expires_at - timedelta(seconds=30))
    
    def get_access_token(self) -> str:
        """
        Get valid access token, refreshing if necessary
        
        Returns:
            Valid access token
        """
        if self.is_token_valid():
            return self.access_token
        
        # Request new token
        return self._refresh_token()
    
    def _refresh_token(self) -> str:
        """Request new OAuth token from Availity"""
        try:
            payload = {
                "grant_type": "client_credentials",
                "client_id": self.api_key,
                "client_secret": self.client_secret,
                "scope": self.scope
            }
            
            with httpx.Client() as client:
                response = client.post(
                    self.token_endpoint,
                    data=payload,
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                    timeout=30
                )
                response.raise_for_status()
            
            token_data = response.json()
            self.access_token = token_data["access_token"]
            expires_in = token_data.get("expires_in", 300)  # Default 5 minutes
            self.token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
            
            logger.info(f"Availity token refreshed, expires in {expires_in} seconds")
            return self.access_token
            
        except httpx.HTTPError as e:
            logger.error(f"Failed to refresh Availity token: {str(e)}")
            raise Exception(f"Availity authentication failed: {str(e)}")
    
    def get_auth_headers(self) -> dict:
        """
        Get authorization headers for Availity API requests
        
        Returns:
            Dict with Authorization header
        """
        token = self.get_access_token()
        return {"Authorization": f"Bearer {token}"}
