from fastapi import FastAPI, UploadFile, File, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
import uuid
from datetime import datetime, timezone
from pdf2image import convert_from_bytes
import io
from PIL import Image
import os
import base64
import subprocess

app = FastAPI(
    title="PDF Processing Service",
    description="External service for PDF to image conversion",
    version="1.0.0"
)

# CORS middleware - configure with your actual domain in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to your domain: ["https://timesheet-claims.preview.emergentagent.com"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API key from environment variable
API_KEY = os.environ.get("PDF_SERVICE_API_KEY", "change-this-to-secure-key")

def verify_api_key(authorization: str = Header(None)):
    """Verify API key from Authorization header"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization format")
    
    token = authorization.replace("Bearer ", "")
    if token != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")
    
    return True

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "PDF Processing Service",
        "status": "running",
        "version": "1.0.0",
        "endpoints": [
            "/health",
            "/api/v1/pdf/convert",
            "/api/v1/pdf/metadata"
        ]
    }

@app.get("/health")
async def health_check():
    """Health check with poppler verification"""
    try:
        # Check poppler-utils installation
        result = subprocess.run(
            ["pdfinfo", "-v"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        poppler_version = "unknown"
        if result.stderr:
            # Parse version from stderr
            for line in result.stderr.split('\n'):
                if 'version' in line.lower():
                    parts = line.split()
                    if len(parts) > 0:
                        poppler_version = parts[-1]
                    break
        
        return {
            "status": "healthy",
            "service": "pdf-processing",
            "poppler_installed": True,
            "poppler_version": poppler_version,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "poppler_installed": False,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

@app.post("/api/v1/pdf/convert")
async def convert_pdf(
    file: UploadFile = File(...),
    dpi: int = 200,
    authorization: str = Header(None)
):
    """Convert PDF to images
    
    Args:
        file: PDF file to convert
        dpi: DPI for conversion (default: 200)
        authorization: Bearer token for authentication
    
    Returns:
        JSON with converted images as base64
    """
    
    # Verify API key
    verify_api_key(authorization)
    
    # Validate file type
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    try:
        # Read PDF bytes
        pdf_bytes = await file.read()
        
        # Validate file size (max 50MB)
        max_size = 50 * 1024 * 1024  # 50MB
        if len(pdf_bytes) > max_size:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size: {max_size / 1024 / 1024}MB"
            )
        
        # Convert PDF to images
        images = convert_from_bytes(
            pdf_bytes,
            dpi=dpi,
            fmt='jpeg'
        )
        
        # Process each page
        results = []
        for i, image in enumerate(images):
            # Convert PIL image to bytes
            img_buffer = io.BytesIO()
            image.save(img_buffer, format='JPEG', quality=85)
            img_buffer.seek(0)
            
            # Encode to base64
            img_base64 = base64.b64encode(img_buffer.read()).decode('utf-8')
            
            results.append({
                "page": i + 1,
                "width": image.width,
                "height": image.height,
                "image_base64": img_base64,
                "format": "jpeg"
            })
        
        return {
            "job_id": str(uuid.uuid4()),
            "status": "completed",
            "pages": len(images),
            "results": results,
            "filename": file.filename,
            "dpi": dpi,
            "processing_time_ms": 0,  # Could add timing if needed
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"PDF conversion failed: {str(e)}"
        )

@app.post("/api/v1/pdf/metadata")
async def get_pdf_metadata(
    file: UploadFile = File(...),
    authorization: str = Header(None)
):
    """Extract PDF metadata without conversion
    
    Args:
        file: PDF file
        authorization: Bearer token for authentication
    
    Returns:
        JSON with PDF metadata
    """
    
    # Verify API key
    verify_api_key(authorization)
    
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    import tempfile
    
    try:
        # Save temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name
        
        # Get metadata using pdfinfo
        result = subprocess.run(
            ["pdfinfo", tmp_path],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        # Parse output
        metadata = {}
        for line in result.stdout.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                metadata[key.strip()] = value.strip()
        
        # Clean up temp file
        os.unlink(tmp_path)
        
        return {
            "filename": file.filename,
            "pages": int(metadata.get('Pages', 0)),
            "file_size_bytes": len(content),
            "metadata": metadata,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        # Clean up on error
        if 'tmp_path' in locals():
            try:
                os.unlink(tmp_path)
            except:
                pass
        
        raise HTTPException(
            status_code=500,
            detail=f"Metadata extraction failed: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)