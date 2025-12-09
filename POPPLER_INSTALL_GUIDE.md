# Poppler-utils Installation Guide for AZAI

## Problem: Poppler-utils keeps disappearing

### Why does this happen?

**Root Cause:**
Poppler-utils is a **system package** (installed via `apt-get`), not a Python package. When installed manually during runtime:

1. ✅ Works immediately after installation
2. ❌ Lost when container/environment restarts
3. ❌ Not persisted in the base image

**Why it's not persistent:**
- System packages installed with `apt-get` during runtime are stored in the container's writable layer
- When the container restarts or rebuilds, this layer is reset
- Only packages in the **base image** or **mounted volumes** persist

---

## Solution: Make Poppler Permanent

### Option 1: Install on Container Startup (Automatic)

**Location:** `/app/backend/install_system_deps.sh`

This script runs automatically when the backend starts and ensures poppler-utils is installed.

```bash
#!/bin/bash
# Checks if poppler-utils is installed
# If not, installs it automatically
# Runs on every container startup

sudo bash /app/backend/install_system_deps.sh
```

**Add to supervisor config:**
```ini
[program:backend]
command=/bin/bash -c "bash /app/backend/install_system_deps.sh && uvicorn server:app --host 0.0.0.0 --port 8001"
```

---

### Option 2: Add to Base Docker Image (Recommended)

**For Emergent Platform Team:**

Add to the platform's Dockerfile:

```dockerfile
# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*
```

**Benefits:**
- ✅ Permanent across all restarts
- ✅ No runtime installation overhead
- ✅ Included in base image

---

### Option 3: Manual Installation (Current Method)

**When needed:**
```bash
sudo apt-get update
sudo apt-get install -y poppler-utils
```

**Verification:**
```bash
which pdftoppm
pdftoppm -v
```

**Limitation:** ❌ Lost on restart

---

## Verification Scripts

### Check if Dependencies are Installed

```bash
python3 /app/backend/check_system_deps.py
```

**Output if OK:**
```
✅ pdftoppm found
✅ pdfinfo found
✅ poppler-utils: pdftoppm version 22.12.0

============================================================
✅ ALL SYSTEM DEPENDENCIES INSTALLED
============================================================
```

**Output if Missing:**
```
❌ pdftoppm NOT found - install poppler-utils
❌ pdfinfo NOT found - install poppler-utils

============================================================
❌ MISSING DEPENDENCIES
Run: sudo bash /app/backend/install_system_deps.sh
============================================================
```

---

## System Requirements File

**Location:** `/app/backend/system_requirements.txt`

```
# System packages required for the backend
poppler-utils  # Required for PDF to image conversion (pdf2image)
```

This documents all system-level dependencies needed.

---

## Why Poppler is Critical

**Used By:** `pdf2image` Python library

**Purpose:** Convert PDF pages to images for AI processing

**Without Poppler:**
- ❌ Cannot convert PDFs to images
- ❌ Cannot process timesheet PDFs
- ❌ Scanner functionality broken
- ❌ Error: "Unable to get page count. Is poppler installed and in PATH?"

**With Poppler:**
- ✅ PDFs convert to JPG images
- ✅ AI can analyze timesheet data
- ✅ Scanner extracts information
- ✅ Application fully functional

---

## Technical Details

### What is Poppler?

**Poppler** is a PDF rendering library based on the xpdf-3.0 code base.

**Components Installed:**
- `pdftoppm` - Converts PDF pages to images (PNG, JPEG, etc.)
- `pdfinfo` - Extracts PDF metadata (page count, dimensions)
- `pdftotext` - Extracts text from PDFs
- `pdfimages` - Extracts images from PDFs

**Version:** 22.12.0 (Debian Bookworm)

**Size:** ~20MB installed

---

## How pdf2image Uses Poppler

```python
from pdf2image import convert_from_path

# Internally calls:
# pdftoppm -jpeg -singlefile input.pdf output

images = convert_from_path('timesheet.pdf')
# Returns: List of PIL Image objects
```

**Process:**
1. Python calls `pdftoppm` command
2. Poppler converts PDF to JPEG
3. Python loads JPEG into memory
4. AI processes the image
5. Extracts timesheet data

---

## Installation on Different Environments

### Debian/Ubuntu
```bash
sudo apt-get install poppler-utils
```

### CentOS/RHEL
```bash
sudo yum install poppler-utils
```

### macOS
```bash
brew install poppler
```

### Alpine Linux (Docker)
```dockerfile
RUN apk add --no-cache poppler-utils
```

---

## Troubleshooting

### Issue: "pdftoppm: command not found"

**Diagnosis:**
```bash
which pdftoppm  # Returns nothing if not installed
```

**Fix:**
```bash
sudo bash /app/backend/install_system_deps.sh
```

---

### Issue: "Permission denied" installing poppler

**Cause:** Non-root user

**Fix:**
```bash
sudo apt-get install -y poppler-utils
# or
su -c 'apt-get install -y poppler-utils'
```

---

### Issue: Poppler disappears after restart

**Cause:** Not in base image

**Temporary Fix:**
```bash
# Run on every restart:
sudo bash /app/backend/install_system_deps.sh
```

**Permanent Fix:**
- Add to Dockerfile (Option 2 above)
- Add to startup script in supervisor config

---

## Monitoring

### Add to Application Startup

```python
# In server.py startup
import subprocess
import shutil

if not shutil.which('pdftoppm'):
    logger.error("⚠️ poppler-utils NOT installed!")
    logger.error("Run: sudo bash /app/backend/install_system_deps.sh")
else:
    logger.info("✅ poppler-utils detected")
```

---

## Best Practice

**For Production:**
1. ✅ Add to Dockerfile
2. ✅ Include in base image
3. ✅ Test in CI/CD pipeline
4. ✅ Monitor in health checks

**For Development:**
1. ✅ Document in `system_requirements.txt`
2. ✅ Provide install script
3. ✅ Add verification script
4. ✅ Include in README

---

## Summary

**Problem:** Poppler-utils disappears on restart

**Cause:** System packages not persisted in container

**Solution:** 
1. Add to Dockerfile (permanent)
2. OR run install script on startup (automated)
3. OR install manually as needed (temporary)

**Files Created:**
- `/app/backend/install_system_deps.sh` - Install script
- `/app/backend/check_system_deps.py` - Verification script  
- `/app/backend/system_requirements.txt` - Documentation
- `/app/POPPLER_INSTALL_GUIDE.md` - This guide

**Recommendation:** Contact Emergent platform team to add poppler-utils to base image for permanent solution.
