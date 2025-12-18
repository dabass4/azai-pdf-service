#!/usr/bin/env python3
"""
Focused PDF Processing Test with Poppler-utils
Tests specifically the PDF processing pipeline and poppler integration
"""

import requests
import sys
import json
import os
import tempfile
import subprocess
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

class PDFPopplerTester:
    def __init__(self, base_url="https://azai-healthcare.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED")
        else:
            print(f"❌ {name} - FAILED: {details}")
        
        self.test_results.append({
            "test": name,
            "success": success,
            "details": details
        })

    def test_poppler_dependencies(self):
        """Test that poppler-utils dependencies are available and working"""
        try:
            # Test pdftoppm availability and version
            result = subprocess.run(['pdftoppm', '-v'], capture_output=True, text=True)
            pdftoppm_success = result.returncode == 0
            pdftoppm_version = result.stderr.strip() if result.stderr else "Unknown"
            
            # Test pdfinfo availability
            result = subprocess.run(['which', 'pdfinfo'], capture_output=True, text=True)
            pdfinfo_success = result.returncode == 0
            
            # Test pdf2image can import and use poppler
            pdf2image_success = False
            try:
                from pdf2image import convert_from_path
                pdf2image_success = True
            except ImportError:
                pass
            
            success = pdftoppm_success and pdfinfo_success and pdf2image_success
            details = f"pdftoppm: {pdftoppm_success} ({pdftoppm_version}), pdfinfo: {pdfinfo_success}, pdf2image: {pdf2image_success}"
            
            self.log_test("Poppler Dependencies Available", success, details)
            return success
        except Exception as e:
            self.log_test("Poppler Dependencies Available", False, str(e))
            return False

    def create_simple_pdf(self):
        """Create a simple valid PDF for testing"""
        try:
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
            temp_file.close()
            
            c = canvas.Canvas(temp_file.name, pagesize=letter)
            width, height = letter
            
            c.setFont("Helvetica-Bold", 16)
            c.drawString(50, height - 50, "TIMESHEET")
            c.setFont("Helvetica", 12)
            c.drawString(50, height - 80, "Client: John Doe")
            c.drawString(50, height - 100, "Employee: Jane Smith")
            c.drawString(50, height - 120, "Date: 01/15/2024")
            c.drawString(50, height - 140, "Time In: 9:00 AM")
            c.drawString(50, height - 160, "Time Out: 5:00 PM")
            c.drawString(50, height - 180, "Hours: 8.0")
            
            c.save()
            return temp_file.name
        except Exception as e:
            print(f"Error creating PDF: {e}")
            return None

    def test_pdf2image_with_poppler(self):
        """Test pdf2image conversion using poppler-utils"""
        try:
            pdf_file = self.create_simple_pdf()
            if not pdf_file:
                self.log_test("PDF2Image with Poppler", False, "Could not create test PDF")
                return False
            
            from pdf2image import convert_from_path
            
            # Convert PDF to images using poppler
            images = convert_from_path(pdf_file, dpi=150)
            
            success = len(images) > 0
            if success:
                # Verify the image has reasonable dimensions
                img = images[0]
                width, height = img.size
                success = width > 100 and height > 100  # Should be reasonable size
                details = f"Converted 1 page, image size: {width}x{height}"
            else:
                details = "No images returned from conversion"
            
            os.unlink(pdf_file)
            
            self.log_test("PDF2Image with Poppler", success, details)
            return success
        except Exception as e:
            self.log_test("PDF2Image with Poppler", False, str(e))
            return False

    def test_timesheet_upload_no_poppler_errors(self):
        """Test timesheet upload doesn't have poppler dependency errors"""
        try:
            pdf_file = self.create_simple_pdf()
            if not pdf_file:
                self.log_test("Timesheet Upload - No Poppler Errors", False, "Could not create test PDF")
                return False
            
            # Upload PDF to timesheet endpoint
            with open(pdf_file, 'rb') as f:
                files = {'file': ('test_timesheet.pdf', f, 'application/pdf')}
                response = requests.post(f"{self.api_url}/timesheets/upload", files=files, timeout=90)
            
            success = response.status_code == 200
            
            if success:
                try:
                    data = response.json()
                    
                    # Check for poppler-related errors
                    error_message = data.get('error_message', '')
                    poppler_error = 'poppler' in error_message.lower()
                    
                    # Check if processing completed (even if extraction failed)
                    status = data.get('status', 'unknown')
                    processing_attempted = status in ['completed', 'failed', 'processing']
                    
                    # Success if no poppler errors and processing was attempted
                    success = not poppler_error and processing_attempted
                    details = f"Status: {response.status_code}, Processing Status: {status}, Poppler Error: {poppler_error}"
                    
                    if poppler_error:
                        details += f", Error: {error_message[:100]}"
                    
                except json.JSONDecodeError:
                    success = False
                    details = f"Status: {response.status_code}, Invalid JSON response"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            os.unlink(pdf_file)
            
            self.log_test("Timesheet Upload - No Poppler Errors", success, details)
            return success
        except Exception as e:
            self.log_test("Timesheet Upload - No Poppler Errors", False, str(e))
            return False

    def test_multi_page_pdf_poppler(self):
        """Test multi-page PDF processing with poppler"""
        try:
            # Create multi-page PDF
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
            temp_file.close()
            
            c = canvas.Canvas(temp_file.name, pagesize=letter)
            width, height = letter
            
            # Page 1
            c.setFont("Helvetica-Bold", 16)
            c.drawString(50, height - 50, "TIMESHEET PAGE 1")
            c.setFont("Helvetica", 12)
            c.drawString(50, height - 80, "Client: Alice Johnson")
            c.showPage()
            
            # Page 2
            c.setFont("Helvetica-Bold", 16)
            c.drawString(50, height - 50, "TIMESHEET PAGE 2")
            c.setFont("Helvetica", 12)
            c.drawString(50, height - 80, "Client: Bob Smith")
            c.showPage()
            
            c.save()
            
            # Test with pdf2image first
            from pdf2image import convert_from_path
            images = convert_from_path(temp_file.name)
            
            pdf2image_success = len(images) == 2
            
            # Test upload
            with open(temp_file.name, 'rb') as f:
                files = {'file': ('multi_page.pdf', f, 'application/pdf')}
                response = requests.post(f"{self.api_url}/timesheets/upload", files=files, timeout=90)
            
            upload_success = response.status_code == 200
            
            if upload_success:
                try:
                    data = response.json()
                    
                    # Check if it handled multi-page (batch response or single with page info)
                    is_batch = 'timesheets' in data
                    has_page_info = 'Page' in data.get('filename', '') if not is_batch else False
                    
                    # Check for poppler errors
                    error_message = data.get('error_message', '')
                    poppler_error = 'poppler' in error_message.lower()
                    
                    success = pdf2image_success and upload_success and not poppler_error
                    details = f"PDF2Image: {pdf2image_success} (pages: {len(images)}), " \
                             f"Upload: {upload_success}, Batch: {is_batch}, " \
                             f"PageInfo: {has_page_info}, Poppler Error: {poppler_error}"
                    
                except json.JSONDecodeError:
                    success = False
                    details = f"PDF2Image: {pdf2image_success}, Upload failed with invalid JSON"
            else:
                success = False
                details = f"PDF2Image: {pdf2image_success}, Upload failed: {response.status_code}"
            
            os.unlink(temp_file.name)
            
            self.log_test("Multi-page PDF with Poppler", success, details)
            return success
        except Exception as e:
            self.log_test("Multi-page PDF with Poppler", False, str(e))
            return False

    def test_poppler_command_line_tools(self):
        """Test poppler command line tools directly"""
        try:
            pdf_file = self.create_simple_pdf()
            if not pdf_file:
                self.log_test("Poppler Command Line Tools", False, "Could not create test PDF")
                return False
            
            # Test pdfinfo
            result = subprocess.run(['pdfinfo', pdf_file], capture_output=True, text=True)
            pdfinfo_success = result.returncode == 0 and 'Pages:' in result.stdout
            
            # Test pdftoppm
            temp_dir = tempfile.mkdtemp()
            result = subprocess.run(['pdftoppm', '-jpeg', pdf_file, f'{temp_dir}/test'], 
                                  capture_output=True, text=True)
            pdftoppm_success = result.returncode == 0
            
            # Check if image was created
            image_created = False
            if pdftoppm_success:
                image_files = list(Path(temp_dir).glob('test-*.jpg'))
                image_created = len(image_files) > 0
                
                # Cleanup images
                for img_file in image_files:
                    img_file.unlink()
            
            # Cleanup
            os.unlink(pdf_file)
            Path(temp_dir).rmdir()
            
            success = pdfinfo_success and pdftoppm_success and image_created
            details = f"pdfinfo: {pdfinfo_success}, pdftoppm: {pdftoppm_success}, image created: {image_created}"
            
            self.log_test("Poppler Command Line Tools", success, details)
            return success
        except Exception as e:
            self.log_test("Poppler Command Line Tools", False, str(e))
            return False

    def run_all_tests(self):
        """Run all PDF poppler tests"""
        print("🔍 Testing PDF Processing with Poppler-utils Integration")
        print(f"Testing against: {self.api_url}")
        print("=" * 60)
        
        # Test 1: Poppler dependencies
        if not self.test_poppler_dependencies():
            print("❌ Poppler dependencies not available - stopping tests")
            return self.get_results()
        
        # Test 2: Command line tools
        self.test_poppler_command_line_tools()
        
        # Test 3: PDF2Image integration
        self.test_pdf2image_with_poppler()
        
        # Test 4: Timesheet upload without poppler errors
        self.test_timesheet_upload_no_poppler_errors()
        
        # Test 5: Multi-page PDF processing
        self.test_multi_page_pdf_poppler()
        
        return self.get_results()

    def get_results(self):
        """Get test results summary"""
        print("\n" + "=" * 60)
        print(f"📊 PDF Poppler Test Results: {self.tests_passed}/{self.tests_run} passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All PDF poppler tests passed!")
            print("✅ PDF processing pipeline with poppler-utils is working correctly")
            return 0
        else:
            print("❌ Some PDF poppler tests failed")
            failed_tests = [r for r in self.test_results if not r['success']]
            print("\nFailed tests:")
            for test in failed_tests:
                print(f"  - {test['test']}: {test['details']}")
            return 1

if __name__ == "__main__":
    tester = PDFPopplerTester()
    exit_code = tester.run_all_tests()
    sys.exit(exit_code)