#!/bin/bash
# ============================================================
# AZAI PDF Dependencies & Scan Configuration
# ============================================================
# This script ensures poppler-utils is installed and displays
# all scan parameters that are permanently configured in code.
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
echo "SCAN CONFIGURATION (Permanently Applied)"
echo "=========================================="

echo ""
echo "📄 PDF CONVERSION:"
echo "   DPI: 300 (high quality OCR)"
echo "   JPEG Quality: 98"
echo "   Color Mode: RGB (for signature detection)"
echo "   Thread Count: 2"

echo ""
echo "🕐 TIME FORMAT:"
echo "   Display: 24-hour (HH:MM)"
echo "   Examples: 09:00, 17:30, 14:45"
echo "   OCR Fixes:"
echo "     • Decimal to colon: 6.70 → 06:10"
echo "     • Invalid minutes: 6:70 → 06:10"
echo "     • Smart AM/PM: 7-11 = AM, 1-6 = PM"

echo ""
echo "📅 DATE FORMAT:"
echo "   Output: MM/DD/YYYY"
echo "   Examples: 12/30/2024, 01/04/2025"
echo "   Features:"
echo "     • Week inference from week_of field"
echo "     • Day name to date: Monday → 12/30/2024"
echo "     • Cross-timesheet comparison"

echo ""
echo "🔢 UNIT CALCULATION:"
echo "   1 unit = 15 minutes"
echo "   Rounding: nearest unit"
echo "   Examples:"
echo "     • 8 hours (480 min) = 32 units"
echo "     • 4 hours (240 min) = 16 units"

echo ""
echo "🔍 EXTRACTION FEATURES:"
echo "   • Service Codes: T1019, T1020, T1021, S5125, S5126, S5130, S5131"
echo "   • Signature Detection: Enabled"
echo "   • Similar Employee Matching: Enabled"
echo "   • Name Correction: Enabled"

echo ""
echo "=========================================="
echo "All settings are permanently configured"
echo "in code and auto-applied to every scan."
echo "=========================================="
