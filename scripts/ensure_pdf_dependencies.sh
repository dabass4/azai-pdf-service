#!/bin/bash
# ============================================================
# AZAI PDF Dependencies & Scan Configuration
# ============================================================
# This script ensures poppler-utils is installed.
# All scan settings are loaded from /app/backend/scan_config.py
# which is the SINGLE SOURCE OF TRUTH for configuration.
# ============================================================

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
echo "=========================================="
echo "CONFIGURATION SOURCE: scan_config.py"
echo "=========================================="

echo ""
echo "All scan settings are centralized in:"
echo "  /app/backend/scan_config.py"
echo ""
echo "This is the SINGLE SOURCE OF TRUTH for:"
echo "  • OCR Model (currently: gemini-2.0-flash)"
echo "  • Time Format (currently: 12-hour AM/PM)"
echo "  • Date Format (currently: MM/DD/YYYY)"
echo "  • PDF Settings (DPI, quality, etc.)"
echo "  • Unit Calculation (15 min/unit)"
echo "  • OCR Fixes (decimal→colon, invalid minutes)"
echo ""
echo "To change any setting, edit scan_config.py"
echo "Changes will apply on next server restart."
echo ""
echo "=========================================="
echo "Current Settings Summary:"
echo "=========================================="
echo "🤖 OCR: gemini-2.0-flash (Gemini)"
echo "🕐 Time: 12h (09:00 AM, 05:30 PM)"
echo "📅 Date: MM/DD/YYYY"
echo "📄 PDF: DPI=300, Quality=98, Color=RGB"
echo "🔢 Units: 15 min/unit"
echo "🔧 OCR Fixes: 6.70→06:10, 6:70→06:10"
echo "=========================================="
