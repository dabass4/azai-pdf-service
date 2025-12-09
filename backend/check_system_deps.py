#!/usr/bin/env python3
"""
Check if all system dependencies are installed
Run this to verify the environment before starting the application
"""

import subprocess
import sys
import shutil

def check_command(command, package_name):
    """Check if a command exists in PATH"""
    if shutil.which(command):
        print(f"✅ {command} found")
        return True
    else:
        print(f"❌ {command} NOT found - install {package_name}")
        return False

def check_poppler():
    """Check poppler-utils installation and version"""
    try:
        result = subprocess.run(
            ['pdftoppm', '-v'],
            capture_output=True,
            text=True,
            stderr=subprocess.STDOUT
        )
        version_line = result.stdout.split('\n')[0]
        print(f"✅ poppler-utils: {version_line}")
        return True
    except FileNotFoundError:
        print("❌ poppler-utils NOT installed")
        return False

def main():
    print("Checking system dependencies...\n")
    
    dependencies = [
        ("pdftoppm", "poppler-utils"),
        ("pdfinfo", "poppler-utils"),
    ]
    
    all_ok = True
    for cmd, pkg in dependencies:
        if not check_command(cmd, pkg):
            all_ok = False
    
    print()
    if not check_poppler():
        all_ok = False
    
    print("\n" + "="*60)
    if all_ok:
        print("✅ ALL SYSTEM DEPENDENCIES INSTALLED")
        print("="*60)
        return 0
    else:
        print("❌ MISSING DEPENDENCIES")
        print("Run: sudo bash /app/backend/install_system_deps.sh")
        print("="*60)
        return 1

if __name__ == "__main__":
    sys.exit(main())
