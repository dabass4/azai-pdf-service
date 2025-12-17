# Integration Guide - Connect Main App to PDF Service

## Overview

After deploying PDF service to Railway, follow these steps to integrate it with your main AZAI application.

---

## Step 1: Update Environment Variables

Add these to `/app/backend/.env`:

```bash
# External PDF Processing Service
PDF_SERVICE_URL=https://your-railway-url.railway.app
PDF_SERVICE_API_KEY=your-api-key-from-railway
```

**Get these values from:**
- Railway dashboard → Your service → Settings → Domain
- Railway dashboard → Your service → Variables → PDF_SERVICE_API_KEY

---

## Step 2: Install Required Package

```bash
cd /app/backend
pip install httpx
pip freeze > requirements.txt
sudo supervisorctl restart backend
```

---

## Step 3: Update Your Upload Endpoint

### Option A: Quick Integration (Minimal Changes)

Replace the PDF conversion part in `server.py`:

**Find this code** (around line 963-990):
```python
# OLD CODE - In-process conversion
if file_type == 'pdf':
    try:
        logger.info(f"Converting PDF page {page_number} to image: {file_path}")
        images = convert_from_path(file_path, first_page=page_number, last_page=page_number, dpi=200)
        # ... rest of conversion
```

**Replace with:**
```python
# NEW CODE - External service
if file_type == 'pdf':
    try:
        from pdf_service_client import pdf_service
        
        logger.info(f"Converting PDF page {page_number} using external service")
        
        # Convert entire PDF at once (external service handles pages)
        image_bytes_list = await pdf_service.convert_pdf(file_path, dpi=200)
        
        # Get the specific page we need
        if page_number <= len(image_bytes_list):
            # Save the image bytes to a temporary file
            import tempfile
            page_image_path = str(file_path).replace('.pdf', f'_page{page_number}.jpg')
            
            with open(page_image_path, 'wb') as img_file:
                img_file.write(image_bytes_list[page_number - 1])
            
            processing_file_path = page_image_path
            temp_image_created = True
            logger.info(f"PDF page {page_number} converted successfully")
        else:
            raise Exception(f"Page {page_number} not found in PDF")
            
    except Exception as e:
        logger.error(f"External PDF conversion error for page {page_number}: {e}")
        logger.warning(f"Falling back to in-process conversion")
        # Fallback to old method if external service fails
        try:
            images = convert_from_path(file_path, first_page=page_number, last_page=page_number, dpi=200)
            # ... existing fallback code
        except:
            # ... existing error handling
```

### Option B: Complete Refactor (Recommended)

Create a new helper function in `server.py`:

```python
async def convert_pdf_page_to_image(
    file_path: str,
    file_type: str,
    page_number: int
) -> str:
    """
    Convert PDF page to image using external service (with fallback)
    
    Returns:
        Path to the converted image file
    """
    from pdf_service_client import pdf_service
    
    # For non-PDF files, return as-is
    if file_type != 'pdf':
        return file_path
    
    try:
        # Try external service first
        if pdf_service.is_configured():
            logger.info(f"Converting PDF page {page_number} using external service")
            
            # Convert PDF
            image_bytes_list = await pdf_service.convert_pdf(file_path, dpi=200)
            
            # Save specific page
            if page_number <= len(image_bytes_list):
                page_image_path = str(file_path).replace('.pdf', f'_page{page_number}.jpg')
                with open(page_image_path, 'wb') as img_file:
                    img_file.write(image_bytes_list[page_number - 1])
                
                logger.info(f"PDF page {page_number} converted via external service")
                return page_image_path
            else:
                raise Exception(f"Page {page_number} not found")
        else:
            logger.warning("External PDF service not configured, using in-process conversion")
            raise Exception("Service not configured")
            
    except Exception as e:
        # Fallback to in-process conversion
        logger.warning(f"External service failed, falling back to in-process: {e}")
        
        try:
            from pdf2image import convert_from_path
            images = convert_from_path(
                file_path,
                first_page=page_number,
                last_page=page_number,
                dpi=200
            )
            
            if images:
                page_image_path = str(file_path).replace('.pdf', f'_page{page_number}.jpg')
                images[0].save(page_image_path, 'JPEG', quality=95)
                logger.info(f"PDF page {page_number} converted via fallback method")
                return page_image_path
            else:
                raise Exception("No images returned from fallback conversion")
                
        except Exception as fallback_error:
            logger.error(f"Fallback conversion also failed: {fallback_error}")
            raise Exception(f"PDF conversion failed: {fallback_error}")
```

Then in your `extract_timesheet_data` function, replace the conversion logic:

```python
# Around line 963
if file_type == 'pdf':
    processing_file_path = await convert_pdf_page_to_image(
        file_path,
        file_type,
        page_number
    )
    mime_type = "image/jpeg"
    temp_image_created = True
```

---

## Step 4: Test the Integration

### Test 1: Check PDF Service Connection

Add a test endpoint to verify connectivity:

```python
@api_router.get("/test/pdf-service")
async def test_pdf_service():
    """Test external PDF service connection"""
    from pdf_service_client import pdf_service
    
    if not pdf_service.is_configured():
        return {
            "configured": False,
            "message": "PDF service not configured. Check environment variables."
        }
    
    health = await pdf_service.health_check()
    return {
        "configured": True,
        "health": health,
        "service_url": pdf_service.service_url,
        "api_key_set": bool(pdf_service.api_key)
    }
```

Test it:
```bash
curl https://timesheet-claims.preview.emergentagent.com/api/test/pdf-service
```

### Test 2: Upload a Real Timesheet

Use your existing upload endpoint:
```bash
# Upload a test PDF
curl -X POST https://timesheet-claims.preview.emergentagent.com/api/timesheets/upload \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@test_timesheet.pdf"
```

Check logs:
```bash
tail -f /var/log/supervisor/backend.err.log | grep -i "pdf\|conversion"
```

You should see:
```
INFO - Converting PDF page 1 using external service
INFO - PDF page 1 converted via external service
```

---

## Step 5: Gradual Migration Strategy

### Phase 1: External Service with Fallback (Current)
```python
try:
    # Use external service
    result = await pdf_service.convert_pdf(file_path)
except:
    # Fallback to in-process
    result = convert_from_path(file_path)
```

**Status:** Safe, both methods available

### Phase 2: External Service Only (After Testing)
```python
# Only use external service
result = await pdf_service.convert_pdf(file_path)
```

**When to switch:**
- After 100+ successful PDF uploads
- No errors in logs for 7 days
- External service uptime > 99%

### Phase 3: Remove Old Code (Final)
```python
# Remove pdf2image and convert_from_path entirely
# Remove poppler-utils from requirements (not needed anymore)
```

**When to do this:**
- After Phase 2 runs for 30+ days
- External service proven reliable
- Team comfortable with architecture

---

## Step 6: Monitoring & Alerts

### Add Logging

```python
# Log every PDF service call
logger.info(
    "pdf_service_call",
    extra={
        "filename": filename,
        "pages": page_count,
        "method": "external_service",
        "success": True
    }
)
```

### Track Metrics

Add to your monitoring:
```python
# Count external service usage
external_service_calls = 0
external_service_failures = 0

# Track in database
await db.metrics.insert_one({
    "type": "pdf_service_call",
    "status": "success",
    "duration_ms": duration,
    "timestamp": datetime.now(timezone.utc)
})
```

### Set Up Alerts

Monitor these:
- External service error rate > 5%
- External service response time > 10s
- Fallback usage > 10% of calls

---

## Troubleshooting

### Issue: "PDF service not configured"
**Solution:**
```bash
# Check environment variables
echo $PDF_SERVICE_URL
echo $PDF_SERVICE_API_KEY

# If empty, add to .env and restart
sudo supervisorctl restart backend
```

### Issue: "Connection timeout"
**Solution:**
```python
# Increase timeout in pdf_service_client.py
async with httpx.AsyncClient(timeout=120.0) as client:  # Increase from 60
```

### Issue: "Authorization failed"
**Solution:**
- Verify API key matches Railway environment variable
- Check Railway logs for authentication errors
- Regenerate API key if needed

### Issue: "Service unavailable"
**Solution:**
1. Check Railway dashboard - is service running?
2. Check Railway deployment logs
3. Verify Railway domain is correct
4. Test health endpoint directly

---

## Performance Optimization

### Cache PDF Metadata
```python
# Cache page counts to avoid repeated calls
@lru_cache(maxsize=1000)
async def get_pdf_page_count_cached(file_hash: str) -> int:
    # Use external service metadata endpoint
    metadata = await pdf_service.get_metadata(file_path)
    return metadata["pages"]
```

### Batch Processing
```python
# If processing multiple PDFs, use async
import asyncio

async def process_multiple_pdfs(pdf_paths: List[str]):
    tasks = [pdf_service.convert_pdf(path) for path in pdf_paths]
    results = await asyncio.gather(*tasks)
    return results
```

---

## Rollback Plan

If external service has issues:

### Immediate (< 1 minute):
```python
# In pdf_service_client.py, add at top:
FORCE_FALLBACK = True  # Set to True to disable external service

def is_configured(self) -> bool:
    if FORCE_FALLBACK:
        return False
    return bool(self.service_url and self.api_key)
```

### Full Rollback (< 5 minutes):
```bash
# Revert to old upload_timesheet function
git log --oneline  # Find commit before integration
git revert <commit-hash>
git push
sudo supervisorctl restart backend
```

---

## Success Metrics

Track these to measure success:

- ✅ **Poppler incidents**: Should be 0
- ✅ **PDF processing success rate**: Should be > 99%
- ✅ **Average processing time**: Should be < 10s per page
- ✅ **External service uptime**: Should be > 99.5%
- ✅ **Cost per PDF**: Should be < $0.01

---

## Next Steps

1. ✅ Complete Step 1-3 (environment, client code)
2. ⏳ Deploy and test with 10 PDFs
3. ⏳ Monitor for 24 hours
4. ⏳ Gradually increase traffic to external service
5. ⏳ After 7 days of stability, remove fallback code

**Estimated Time: 30 minutes for full integration**

---

Ready to integrate! Start with Step 1. 🚀
