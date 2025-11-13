# System Dependencies Audit Report
**Date:** 2024-11-13  
**Issue:** Packages installed via `apt-get` don't persist across container restarts

---

## Executive Summary

Your application has **1 CRITICAL** dependency that requires Emergent platform intervention:
- **poppler-utils** - Required for PDF processing, currently breaks after each restart

All other system dependencies are already included in the Emergent base image.

---

## Detailed Analysis

### ✅ ALREADY INCLUDED IN BASE IMAGE (Working Fine)

These Python packages require system libraries, but they're **already available** in Emergent's base container:

| Python Package | System Dependencies | Status |
|---------------|---------------------|---------|
| **Pillow** (12.0.0) | libjpeg-dev, libpng-dev, zlib1g-dev | ✅ Pre-installed |
| **cryptography** (46.0.3) | libssl-dev, libffi-dev | ✅ Pre-installed |
| **bcrypt** (4.1.3) | libffi-dev | ✅ Pre-installed |
| **cffi** (2.0.0) | libffi-dev | ✅ Pre-installed |
| **grpcio** (1.76.0) | build-essential | ✅ Pre-installed |
| **google-crc32c** (1.7.1) | build-essential | ✅ Pre-installed |
| **numpy** (2.3.4) | build-essential | ✅ Pre-installed |
| **pandas** (2.3.3) | build-essential | ✅ Pre-installed |
| **reportlab** (4.4.4) | libfreetype6-dev | ✅ Pre-installed |
| **PyYAML** (6.0.3) | libyaml-dev | ✅ Pre-installed |

**Confirmed installed in base image:**
- build-essential
- libffi-dev
- libffi8
- libfreetype6
- libjpeg62-turbo
- libpng16-16
- libssl-dev
- libssl3
- libyaml-0-2
- zlib1g-dev
- zlib1g

---

### ❌ MISSING FROM BASE IMAGE (Needs Emergent Fix)

| Python Package | System Package Needed | Impact | Priority |
|---------------|----------------------|---------|----------|
| **pdf2image** (1.17.0) | **poppler-utils** | **PDF timesheet scanning fails** | **CRITICAL** |

**What breaks without poppler-utils:**
- PDF upload and processing
- Timesheet extraction from PDF files
- Any OCR/image extraction workflows

**Current workaround (temporary):**
```bash
sudo apt-get update && sudo apt-get install -y poppler-utils
```
*Note: Must be run after EVERY container restart*

---

## Frontend Dependencies

**Status:** ✅ All frontend dependencies are pure JavaScript/Node packages

No system-level dependencies required for:
- React and UI libraries (@radix-ui, lucide-react)
- Build tools (craco, webpack, babel)
- Tailwind CSS and PostCSS

**Note:** Node.js itself is pre-installed in the container.

---

## Verification Commands

To verify system dependencies after restart:

```bash
# Check poppler-utils
which pdftoppm pdfinfo  # Should return paths if installed

# Check Python packages
cd /app/backend
python3 -c "from pdf2image import convert_from_path; print('PDF processing: OK')"
python3 -c "from PIL import Image; print('Image processing: OK')"
python3 -c "import grpc; print('gRPC: OK')"
```

---

## Action Items

### For Emergent Platform Team

**REQUEST:** Add `poppler-utils` to base container image

**Justification:**
- Required by pdf2image Python package (in requirements.txt)
- Core functionality: PDF timesheet scanning and OCR
- Currently breaks after every container restart
- Common dependency for document processing applications

**Packages to install:**
```dockerfile
RUN apt-get update && apt-get install -y \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*
```

**Alternative:** Provide mechanism for users to specify system dependencies in project config

---

### For Development Team (Your Team)

**Short-term:**
1. Document the need to reinstall poppler-utils after restarts
2. Create startup script that checks for poppler-utils
3. Monitor for container restart events

**Long-term:**
1. Contact Emergent support to request poppler-utils in base image
2. Once added, remove manual installation workarounds
3. Add system dependency verification to deployment checks

---

## Contact Emergent Support

**Discord:** https://discord.gg/VzKfwCXC4A  
**Email:** support@emergent.sh

**Message Template:**
```
Subject: Request to Add poppler-utils to Base Container Image

Hi Emergent Team,

We're running a healthcare timesheet processing application that uses the 
pdf2image Python library for PDF processing. This requires the system package 
'poppler-utils' to be installed.

Currently, poppler-utils is not included in the base container image, and 
we have to reinstall it after every container restart, which disrupts our 
PDF processing functionality.

Could you please add poppler-utils (and its dependencies) to the base 
container image? This is a common dependency for document processing 
applications.

Required packages:
- poppler-utils
- libpoppler126 (dependency)
- poppler-data (dependency)

Thank you!
```

---

## Testing After Fix

Once Emergent adds poppler-utils, verify with:

```bash
# Should NOT require sudo/manual installation
pdftoppm -v

# Python test
cd /app/backend
python3 -c "
from pdf2image import convert_from_path
print('✅ PDF processing ready')
"

# Full integration test
# Upload a PDF timesheet and verify extraction works
```

---

## Summary

- **Total Python packages with system dependencies:** 11
- **Already working (in base image):** 10 ✅
- **Missing (needs Emergent fix):** 1 ❌ (poppler-utils)
- **Severity:** HIGH - Breaks core PDF processing feature
- **Workaround available:** Yes (temporary, requires manual reinstall)
- **Permanent fix required:** Yes (Emergent platform team)

---

**Last Updated:** 2024-11-13  
**Next Review:** After Emergent implements fix
