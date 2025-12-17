# Deploy PDF Service to Railway.app

## Step-by-Step Guide

### 1. Prepare the Service (5 minutes)

Create a new directory for your PDF service:

```bash
mkdir pdf-service
cd pdf-service
```

Create these files:

**`main.py`** (FastAPI application):
```python
from fastapi import FastAPI, UploadFile, File, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
import uuid
from datetime import datetime, timezone
from pdf2image import convert_from_bytes
import io
from PIL import Image
import os

app = FastAPI(title="PDF Processing Service")

# CORS for your main application
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple API key check
API_KEY = os.environ.get("PDF_SERVICE_API_KEY", "your-secret-key-change-this")

def verify_api_key(authorization: str = Header(None)):
    if not authorization or authorization != f"Bearer {API_KEY}":
        raise HTTPException(status_code=403, detail="Invalid API key")
    return True

@app.get("/")
async def root():
    return {"service": "PDF Processing", "status": "running"}

@app.get("/health")
async def health_check():
    """Health check with poppler verification"""
    import subprocess
    try:
        result = subprocess.run(["pdfinfo", "-v"], capture_output=True, text=True, timeout=5)
        poppler_version = result.stderr.split('\n')[0].split()[-1] if result.stderr else "unknown"
        return {
            "status": "healthy",
            "poppler_version": poppler_version,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

@app.post("/api/v1/pdf/convert")
async def convert_pdf(
    file: UploadFile = File(...),
    dpi: int = 200,
    authorized: bool = Header(default=False, alias="Authorization", include_in_schema=False)
):
    """Convert PDF to images"""
    
    # Validate PDF
    if not file.filename.endswith('.pdf'):
        raise HTTPException(400, "Only PDF files supported")
    
    try:
        # Read PDF bytes
        pdf_bytes = await file.read()
        
        # Convert to images
        images = convert_from_bytes(pdf_bytes, dpi=dpi, fmt='jpeg')
        
        # Convert images to base64 for easy transmission
        results = []
        for i, image in enumerate(images):
            # Convert PIL image to bytes
            img_buffer = io.BytesIO()
            image.save(img_buffer, format='JPEG', quality=85)
            img_buffer.seek(0)
            
            # Encode to base64
            import base64
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
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        raise HTTPException(500, f"PDF conversion failed: {str(e)}")

@app.post("/api/v1/pdf/metadata")
async def get_pdf_metadata(file: UploadFile = File(...)):
    """Get PDF metadata without conversion"""
    import subprocess
    import tempfile
    
    try:
        # Save temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name
        
        # Get page count using pdfinfo
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
        
        # Clean up
        os.unlink(tmp_path)
        
        return {
            "filename": file.filename,
            "pages": int(metadata.get('Pages', 0)),
            "metadata": metadata,
            "file_size_bytes": len(content)
        }
        
    except Exception as e:
        raise HTTPException(500, f"Metadata extraction failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
```

**`requirements.txt`**:
```txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-multipart==0.0.6
pdf2image==1.16.3
Pillow==10.1.0
```

**`Dockerfile`**:
```dockerfile
FROM python:3.11-slim

# Install poppler-utils (critical!)
RUN apt-get update && \
    apt-get install -y poppler-utils && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY main.py .

# Railway uses PORT environment variable
EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**`.gitignore`**:
```
__pycache__/
*.pyc
.env
venv/
.DS_Store
```

### 2. Push to GitHub (3 minutes)

```bash
git init
git add .
git commit -m "Initial PDF service"

# Create repo on GitHub, then:
git remote add origin https://github.com/YOUR_USERNAME/pdf-service.git
git push -u origin main
```

### 3. Deploy to Railway (5 minutes)

1. **Go to** [railway.app](https://railway.app)
2. **Sign up** with GitHub
3. **Click** "New Project" → "Deploy from GitHub repo"
4. **Select** your `pdf-service` repository
5. **Wait** for automatic deployment (2-3 minutes)

### 4. Configure Environment Variables (2 minutes)

In Railway dashboard:
1. Go to your project → Variables tab
2. Add these variables:
   ```
   PDF_SERVICE_API_KEY=your-secure-random-key-here
   PORT=8000
   ```
3. Redeploy (automatic)

### 5. Get Your Service URL

Railway will give you a URL like:
```
https://pdf-service-production-xxxx.up.railway.app
```

Test it:
```bash
curl https://your-railway-url.railway.app/health
```

### 6. Connect to Your Main Application

Update your main app's environment variables:

```bash
# In your main application .env
PDF_SERVICE_URL=https://your-railway-url.railway.app
PDF_SERVICE_API_KEY=your-secure-random-key-here
```

Update your main application code:

```python
# In your main FastAPI app
import httpx
import os

PDF_SERVICE_URL = os.environ.get("PDF_SERVICE_URL")
PDF_SERVICE_API_KEY = os.environ.get("PDF_SERVICE_API_KEY")

@app.post("/api/timesheets/upload")
async def upload_timesheet(file: UploadFile = File(...)):
    """Upload timesheet - now using external PDF service"""
    
    # Save file temporarily
    temp_path = f"/tmp/{uuid.uuid4()}.pdf"
    with open(temp_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    try:
        # Call external PDF service
        async with httpx.AsyncClient(timeout=60.0) as client:
            with open(temp_path, "rb") as pdf_file:
                response = await client.post(
                    f"{PDF_SERVICE_URL}/api/v1/pdf/convert",
                    files={"file": pdf_file},
                    params={"dpi": 200},
                    headers={"Authorization": f"Bearer {PDF_SERVICE_API_KEY}"}
                )
        
        if response.status_code != 200:
            raise HTTPException(500, f"PDF service error: {response.text}")
        
        result = response.json()
        
        # Process each page
        for page_data in result["results"]:
            # Decode base64 image
            import base64
            image_bytes = base64.b64decode(page_data["image_base64"])
            
            # Now send to Gemini Vision API for OCR
            extracted_data = await extract_with_gemini(image_bytes)
            
            # Save to database as before
            await save_timesheet(extracted_data)
        
        return {"status": "completed", "pages": result["pages"]}
        
    finally:
        # Cleanup
        os.unlink(temp_path)
```

### 7. Test End-to-End

```bash
# Upload a test PDF to your main app
curl -X POST https://your-main-app.com/api/timesheets/upload \
  -H "Authorization: Bearer YOUR_USER_TOKEN" \
  -F "file=@test_timesheet.pdf"
```

---

## Troubleshooting

### Issue: "poppler-utils not found"
**Solution:** Make sure Dockerfile includes `apt-get install -y poppler-utils`

### Issue: "Connection timeout"
**Solution:** Increase httpx timeout to 60 seconds or more

### Issue: "Memory limit exceeded"
**Solution:** Upgrade Railway plan or optimize image size (reduce DPI)

### Issue: "CORS errors"
**Solution:** Update `allow_origins` in CORS middleware with your actual domain

---

## Monitoring

Railway provides:
- **Logs**: Real-time logs in dashboard
- **Metrics**: CPU, memory, network usage
- **Deployments**: Automatic deploys on git push

---

## Cost Management

**Free Tier:**
- $5/month credit
- Enough for development/testing
- ~500 PDF conversions/month

**Paid Plan ($5/month per service):**
- More resources
- Custom domains
- Better performance

**Pro Plan ($20/month):**
- Priority support
- More compute
- Ideal for production

---

## Scaling

Railway auto-scales, but you can optimize:

1. **Reduce image size:**
   ```python
   image.save(buffer, format='JPEG', quality=70)  # Lower quality
   ```

2. **Add caching:**
   ```python
   # Cache frequently processed PDFs
   ```

3. **Horizontal scaling:**
   - Railway automatically handles this
   - No configuration needed

---

## Security Checklist

- ✅ Use strong API key (min 32 characters)
- ✅ Enable HTTPS only (Railway does this by default)
- ✅ Restrict CORS origins to your domain
- ✅ Set file size limits (max 50MB)
- ✅ Add rate limiting if needed

---

## Next Steps

1. ✅ Deploy to Railway
2. ⏳ Test with sample PDFs
3. ⏳ Monitor for 24 hours
4. ⏳ Switch main app to use external service
5. ⏳ Remove poppler-utils from main app

**Estimated Total Time: 15 minutes**
**Cost: FREE (development), $5-20/month (production)**
