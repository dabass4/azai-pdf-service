"""
PDF Service Client
Integrates with external PDF processing service (Railway)
"""

import httpx
import os
import base64
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class PDFServiceClient:
    """Client for external PDF processing service"""
    
    def __init__(self):
        self.service_url = os.environ.get("PDF_SERVICE_URL")
        self.api_key = os.environ.get("PDF_SERVICE_API_KEY")
        
        if not self.service_url:
            logger.warning("PDF_SERVICE_URL not set - PDF processing will fail")
        if not self.api_key:
            logger.warning("PDF_SERVICE_API_KEY not set - PDF processing will fail")
    
    def is_configured(self) -> bool:
        """Check if PDF service is properly configured"""
        return bool(self.service_url and self.api_key)
    
    async def health_check(self) -> Dict[str, Any]:
        """Check if PDF service is healthy"""
        if not self.is_configured():
            return {"status": "not_configured"}
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.service_url}/health")
                return response.json()
        except Exception as e:
            logger.error(f"PDF service health check failed: {e}")
            return {"status": "error", "error": str(e)}
    
    async def convert_pdf(
        self,
        pdf_path: str,
        dpi: int = 200
    ) -> List[bytes]:
        """
        Convert PDF to images using external service
        
        Args:
            pdf_path: Path to PDF file
            dpi: DPI for conversion (default: 200)
        
        Returns:
            List of image bytes (one per page)
        
        Raises:
            Exception if conversion fails
        """
        if not self.is_configured():
            raise Exception("PDF service not configured. Set PDF_SERVICE_URL and PDF_SERVICE_API_KEY")
        
        try:
            # Read PDF file
            with open(pdf_path, 'rb') as f:
                pdf_content = f.read()
            
            # Call external service
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.service_url}/api/v1/pdf/convert",
                    files={"file": ("document.pdf", pdf_content, "application/pdf")},
                    params={"dpi": dpi},
                    headers={"Authorization": f"Bearer {self.api_key}"}
                )
            
            # Check response
            if response.status_code != 200:
                error_detail = response.text
                raise Exception(f"PDF service returned {response.status_code}: {error_detail}")
            
            result = response.json()
            
            # Extract images from base64
            images = []
            for page_data in result.get("results", []):
                img_base64 = page_data.get("image_base64")
                if img_base64:
                    img_bytes = base64.b64decode(img_base64)
                    images.append(img_bytes)
            
            logger.info(f"PDF converted successfully: {len(images)} pages")
            return images
            
        except Exception as e:
            logger.error(f"PDF conversion failed: {e}")
            raise
    
    async def get_metadata(self, pdf_path: str) -> Dict[str, Any]:
        """
        Get PDF metadata without converting
        
        Args:
            pdf_path: Path to PDF file
        
        Returns:
            Dict with metadata (pages, file_size, etc.)
        """
        if not self.is_configured():
            raise Exception("PDF service not configured")
        
        try:
            with open(pdf_path, 'rb') as f:
                pdf_content = f.read()
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.service_url}/api/v1/pdf/metadata",
                    files={"file": ("document.pdf", pdf_content, "application/pdf")},
                    headers={"Authorization": f"Bearer {self.api_key}"}
                )
            
            if response.status_code != 200:
                raise Exception(f"Metadata extraction failed: {response.text}")
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Metadata extraction failed: {e}")
            raise

# Singleton instance
pdf_service = PDFServiceClient()
