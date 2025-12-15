#!/bin/bash
# Install System Dependencies Script
# This script ensures required system packages are installed
# Run this on container startup or after environment reset

set -e

echo "🔧 Checking system dependencies..."

# Check if poppler-utils is installed
if ! command -v pdftoppm &> /dev/null; then
    echo "📦 Installing poppler-utils..."
    sudo apt-get update -qq
    sudo apt-get install -y poppler-utils
    echo "✅ poppler-utils installed successfully"
else
    echo "✅ poppler-utils already installed"
    pdftoppm -v 2>&1 | head -1
fi

# Verify installation
if command -v pdftoppm &> /dev/null; then
    echo "✅ System dependencies check passed"
    exit 0
else
    echo "❌ System dependencies check failed"
    exit 1
fi
