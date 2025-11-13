"""
Base class for EVV Aggregator implementations
Supports multiple EVV vendors (Sandata, HHAeXchange, WellSky, etc.)
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class EVVSubmissionResult:
    """Result of EVV submission"""
    
    def __init__(
        self,
        success: bool,
        transaction_id: Optional[str] = None,
        message: str = "",
        errors: List[str] = None,
        response_data: Dict = None
    ):
        self.success = success
        self.transaction_id = transaction_id
        self.message = message
        self.errors = errors or []
        self.response_data = response_data or {}
        self.timestamp = datetime.utcnow()
    
    def to_dict(self) -> Dict:
        return {
            "success": self.success,
            "transaction_id": self.transaction_id,
            "message": self.message,
            "errors": self.errors,
            "response_data": self.response_data,
            "timestamp": self.timestamp.isoformat()
        }


class EVVAggregatorBase(ABC):
    """
    Abstract base class for EVV aggregator integrations.
    Each vendor (Sandata, HHAeXchange, etc.) implements this interface.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize aggregator with configuration
        
        Args:
            config: Dict containing vendor-specific configuration
                - api_url: Base API URL
                - api_key: Authentication key
                - business_entity_id: Organization identifier
                - test_mode: Whether in test environment
        """
        self.config = config
        self.api_url = config.get('api_url')
        self.api_key = config.get('api_key')
        self.business_entity_id = config.get('business_entity_id')
        self.test_mode = config.get('test_mode', True)
        
        self._validate_config()
    
    def _validate_config(self):
        """Validate required configuration"""
        required = ['api_url', 'api_key', 'business_entity_id']
        missing = [key for key in required if not self.config.get(key)]
        
        if missing:
            raise ValueError(f"Missing required config: {', '.join(missing)}")
    
    @abstractmethod
    def submit_individuals(self, individuals_data: List[Dict]) -> EVVSubmissionResult:
        """
        Submit individual/patient records
        
        Args:
            individuals_data: List of individual records with EVV fields
            
        Returns:
            EVVSubmissionResult with transaction details
        """
        pass
    
    @abstractmethod
    def submit_direct_care_workers(self, dcw_data: List[Dict]) -> EVVSubmissionResult:
        """
        Submit direct care worker/employee records
        
        Args:
            dcw_data: List of DCW records with credentials
            
        Returns:
            EVVSubmissionResult with transaction details
        """
        pass
    
    @abstractmethod
    def submit_visits(self, visits_data: List[Dict]) -> EVVSubmissionResult:
        """
        Submit visit records (check-in/check-out times)
        
        Args:
            visits_data: List of visit records with service details
            
        Returns:
            EVVSubmissionResult with transaction details
        """
        pass
    
    @abstractmethod
    def get_submission_status(self, transaction_id: str) -> Dict:
        """
        Check status of previous submission
        
        Args:
            transaction_id: Transaction ID from previous submission
            
        Returns:
            Dict with status information
        """
        pass
    
    @abstractmethod
    def test_connection(self) -> bool:
        """
        Test API connectivity and authentication
        
        Returns:
            True if connection successful, False otherwise
        """
        pass
    
    def get_vendor_name(self) -> str:
        """Get name of EVV vendor"""
        return self.__class__.__name__.replace('Client', '').replace('EVV', '')
