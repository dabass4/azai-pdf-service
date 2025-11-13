#!/usr/bin/env python3
"""
System Dependencies Checker
Verifies all required system packages are installed before starting the application.
Run this at container startup to detect missing dependencies early.
"""

import subprocess
import sys
import os
from typing import Dict, List, Tuple

# Color codes for terminal output
RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def check_command(command: str) -> bool:
    """Check if a command is available in PATH"""
    try:
        subprocess.run(['which', command], 
                      stdout=subprocess.PIPE, 
                      stderr=subprocess.PIPE, 
                      check=True)
        return True
    except subprocess.CalledProcessError:
        return False

def check_system_package(package: str) -> bool:
    """Check if a system package is installed"""
    try:
        subprocess.run(['dpkg', '-l', package],
                      stdout=subprocess.PIPE,
                      stderr=subprocess.PIPE,
                      check=True)
        return True
    except subprocess.CalledProcessError:
        return False

def check_python_import(module: str) -> bool:
    """Check if a Python module can be imported"""
    try:
        __import__(module)
        return True
    except ImportError:
        return False

def print_header(text: str):
    """Print a formatted header"""
    print(f"\n{BLUE}{'=' * 70}{RESET}")
    print(f"{BLUE}{text:^70}{RESET}")
    print(f"{BLUE}{'=' * 70}{RESET}\n")

def print_check(name: str, passed: bool, note: str = ""):
    """Print a check result"""
    status = f"{GREEN}✓ PASS{RESET}" if passed else f"{RED}✗ FAIL{RESET}"
    print(f"{name:40} {status}")
    if note and not passed:
        print(f"{' ' * 40} {YELLOW}→ {note}{RESET}")

def main():
    """Run all system dependency checks"""
    print_header("SYSTEM DEPENDENCIES CHECK")
    
    all_passed = True
    critical_failures = []
    
    # Check critical system packages
    print(f"{BLUE}Checking System Packages:{RESET}\n")
    
    system_checks = [
        ("poppler-utils (pdftoppm)", 
         check_command('pdftoppm'),
         "CRITICAL: Required for PDF processing",
         True),  # Critical
        ("poppler-utils (pdfinfo)", 
         check_command('pdfinfo'),
         "CRITICAL: Required for PDF metadata",
         True),  # Critical
        ("libjpeg", 
         check_system_package('libjpeg62-turbo'),
         "Required for image processing",
         False),
        ("libpng", 
         check_system_package('libpng16-16'),
         "Required for image processing",
         False),
        ("libssl", 
         check_system_package('libssl3'),
         "Required for cryptography",
         False),
    ]
    
    for name, passed, note, is_critical in system_checks:
        print_check(name, passed, note if not passed else "")
        if not passed:
            all_passed = False
            if is_critical:
                critical_failures.append((name, note))
    
    # Check Python packages
    print(f"\n{BLUE}Checking Python Packages:{RESET}\n")
    
    python_checks = [
        ("pdf2image", "pdf2image", "Requires poppler-utils", True),
        ("Pillow (PIL)", "PIL", "Image processing", False),
        ("cryptography", "cryptography", "Security", False),
        ("numpy", "numpy", "Numerical computing", False),
        ("pandas", "pandas", "Data processing", False),
    ]
    
    for name, module, note, is_critical in python_checks:
        passed = check_python_import(module)
        print_check(name, passed, note if not passed else "")
        if not passed:
            all_passed = False
            if is_critical:
                critical_failures.append((name, note))
    
    # Print summary
    print_header("SUMMARY")
    
    if all_passed:
        print(f"{GREEN}✓ All system dependencies are installed and working{RESET}\n")
        return 0
    else:
        print(f"{RED}✗ Some dependencies are missing{RESET}\n")
        
        if critical_failures:
            print(f"{RED}CRITICAL FAILURES:{RESET}")
            for name, note in critical_failures:
                print(f"  • {name}: {note}")
            
            print(f"\n{YELLOW}TO FIX IMMEDIATELY:{RESET}")
            print(f"  sudo apt-get update && sudo apt-get install -y poppler-utils")
            
            print(f"\n{YELLOW}PERMANENT FIX NEEDED:{RESET}")
            print(f"  Contact Emergent support to add poppler-utils to base image")
            print(f"  Discord: https://discord.gg/VzKfwCXC4A")
            print(f"  Email: support@emergent.sh")
            print()
        
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
