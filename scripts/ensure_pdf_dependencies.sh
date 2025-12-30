#!/bin/bash
# Ensure PDF Dependencies Script
# This script ensures poppler-utils is installed and scan parameters are configured
# Run this whenever the container restarts or before processing PDFs

echo "=========================================="
echo "AZAI PDF Dependencies Check"
echo "=========================================="

# Check if poppler-utils is installed
if ! command -v pdftoppm &> /dev/null; then
    echo "⚠️  poppler-utils not found. Installing..."
    apt-get update -qq
    apt-get install -y poppler-utils > /dev/null 2>&1
    
    if command -v pdftoppm &> /dev/null; then
        echo "✅ poppler-utils installed successfully"
    else
        echo "❌ Failed to install poppler-utils"
        exit 1
    fi
else
    echo "✅ poppler-utils already installed"
fi

# Display version info
echo ""
echo "PDF Processing Configuration:"
echo "  - pdftoppm: $(pdftoppm -v 2>&1 | head -1)"
echo "  - DPI: 300 (high quality OCR)"
echo "  - JPEG Quality: 98"
echo "  - Color Mode: RGB (for signature detection)"
echo ""

# Scan Parameters Summary
echo "Scan Parameters Applied:"
echo "  ✓ Enhanced OCR prompt with service codes"
echo "  ✓ Signature detection (handwritten, initials, stamps)"
echo "  ✓ Name extraction with similar matching"
echo "  ✓ Date inference from week context"
echo "  ✓ MM/DD/YYYY date format"
echo "  ✓ Ohio Medicaid codes: T1019, T1020, T1021, S5125, S5126, S5130, S5131"
echo ""
echo "=========================================="
echo "PDF Dependencies Ready"
echo "=========================================="
