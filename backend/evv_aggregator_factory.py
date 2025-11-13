"""
EVV Aggregator Factory
Creates appropriate EVV client based on vendor configuration
"""

import os
from typing import Dict, Any, Optional
import logging

from evv_aggregator_base import EVVAggregatorBase
from evv_sandata_client import SandataEVVClient

logger = logging.getLogger(__name__)


class EVVAggregatorFactory:
    """
    Factory for creating EVV aggregator clients
    Supports multiple vendors
    """
    
    # Registry of supported vendors
    VENDORS = {
        'sandata': SandataEVVClient,
        # Add more vendors here as implemented:
        # 'hhax': HHAeXchangeClient,
        # 'wellsky': WellSkyClient,
        # 'santrax': SantraxClient,
    }
    
    @classmethod
    def create_client(
        cls,
        vendor: str,
        config: Optional[Dict[str, Any]] = None
    ) -> EVVAggregatorBase:
        """
        Create EVV client for specified vendor
        
        Args:
            vendor: Vendor name ('sandata', 'hhax', etc.)
            config: Configuration dict (if None, loads from environment)
            
        Returns:
            EVV client instance
            
        Raises:
            ValueError: If vendor not supported
        """
        vendor_lower = vendor.lower()
        
        if vendor_lower not in cls.VENDORS:
            raise ValueError(
                f"Unsupported EVV vendor: {vendor}. "
                f"Supported vendors: {', '.join(cls.VENDORS.keys())}"
            )
        
        # Load config from environment if not provided
        if config is None:
            config = cls._load_config_from_env(vendor_lower)
        
        # Get client class and instantiate
        client_class = cls.VENDORS[vendor_lower]
        
        logger.info(f"Creating {vendor} EVV client...")
        return client_class(config)
    
    @classmethod
    def _load_config_from_env(cls, vendor: str) -> Dict[str, Any]:
        """
        Load vendor configuration from environment variables
        
        Args:
            vendor: Vendor name
            
        Returns:
            Configuration dict
        """
        if vendor == 'sandata':
            return {
                'api_url': os.getenv('SANDATA_API_URL', 'https://api.sandata.com/v1'),
                'api_key': os.getenv('SANDATA_API_KEY'),
                'username': os.getenv('SANDATA_USERNAME'),
                'password': os.getenv('SANDATA_PASSWORD'),
                'company_id': os.getenv('SANDATA_COMPANY_ID'),
                'business_entity_id': os.getenv('SANDATA_BUSINESS_ENTITY_ID'),
                'test_mode': os.getenv('SANDATA_TEST_MODE', 'true').lower() == 'true'
            }
        
        # Add more vendor configurations here
        
        return {}
    
    @classmethod
    def get_supported_vendors(cls) -> list:
        """Get list of supported vendor names"""
        return list(cls.VENDORS.keys())
    
    @classmethod
    def register_vendor(cls, vendor_name: str, client_class):
        """
        Register a new EVV vendor client
        
        Args:
            vendor_name: Name of vendor
            client_class: EVVAggregatorBase subclass
        """
        if not issubclass(client_class, EVVAggregatorBase):
            raise TypeError("Client class must inherit from EVVAggregatorBase")
        
        cls.VENDORS[vendor_name.lower()] = client_class
        logger.info(f"Registered new EVV vendor: {vendor_name}")


def get_default_evv_client() -> EVVAggregatorBase:
    """
    Get EVV client using default configuration from environment
    
    Returns:
        EVV client instance
    """
    # Get vendor from environment (default to Sandata)
    vendor = os.getenv('EVV_VENDOR', 'sandata')
    
    return EVVAggregatorFactory.create_client(vendor)
