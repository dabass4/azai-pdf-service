#!/bin/bash
# Install system dependencies for AZAI backend
# This script ensures poppler-utils is always installed

set -e

echo "Installing system dependencies..."

# Update package list
apt-get update -qq

# Install poppler-utils (required for PDF processing)
if ! command -v pdftoppm &> /dev/null; then
    echo "Installing poppler-utils..."
    apt-get install -y poppler-utils
    echo "✅ poppler-utils installed successfully"
else
    echo "✅ poppler-utils already installed"
fi

# Verify installation
if command -v pdftoppm &> /dev/null && command -v pdfinfo &> /dev/null; then
    echo "✅ All system dependencies verified"
    pdftoppm -v 2>&1 | head -1
else
    echo "❌ ERROR: poppler-utils installation failed"
    exit 1
fi

echo "System dependencies installation complete!"
