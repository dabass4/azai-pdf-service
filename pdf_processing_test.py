#!/usr/bin/env python3
"""
PDF Processing Test Suite
Tests PDF processing functionality with poppler-utils integration
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
import uuid

class PDFProcessingTester:
    def __init__(self, base_url="https://odm-claims-hub.preview.emergentagent.com"):
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

    def test_system_dependencies(self):
        """Test that poppler-utils dependencies are available"""
        try:
            # Test pdftoppm
            result = subprocess.run(['which', 'pdftoppm'], capture_output=True, text=True)
            pdftoppm_available = result.returncode == 0
            
            # Test pdfinfo
            result = subprocess.run(['which', 'pdfinfo'], capture_output=True, text=True)
            pdfinfo_available = result.returncode == 0
            
            # Test pdftoppm version
            pdftoppm_version = ""
            if pdftoppm_available:
                result = subprocess.run(['pdftoppm', '-v'], capture_output=True, text=True)
                pdftoppm_version = result.stderr.strip() if result.stderr else "Unknown"
            
            # Test pdf2image import
            pdf2image_available = False
            try:
                from pdf2image import convert_from_path
                pdf2image_available = True
            except ImportError:
                pass
            
            success = pdftoppm_available and pdfinfo_available and pdf2image_available
            details = f"pdftoppm: {pdftoppm_available}, pdfinfo: {pdfinfo_available}, pdf2image: {pdf2image_available}, version: {pdftoppm_version}"
            
            self.log_test("System Dependencies Check", success, details)
            return success
        except Exception as e:
            self.log_test("System Dependencies Check", False, str(e))
            return False

    def create_realistic_timesheet_pdf(self):
        """Create a realistic timesheet PDF for testing"""
        try:
            # Create a temporary PDF file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
            temp_file.close()
            
            # Create PDF with reportlab
            c = canvas.Canvas(temp_file.name, pagesize=letter)
            width, height = letter
            
            # Title
            c.setFont("Helvetica-Bold", 16)
            c.drawString(50, height - 50, "HEALTHCARE TIMESHEET")
            
            # Week information
            c.setFont("Helvetica", 12)
            c.drawString(50, height - 80, "Week of: 01/15/2024 - 01/21/2024")
            
            # Client information
            c.drawString(50, height - 110, "Client Name: Maria Rodriguez")
            c.drawString(50, height - 130, "Service Code: T1019")
            
            # Employee section
            c.setFont("Helvetica-Bold", 12)
            c.drawString(50, height - 170, "Employee: John Smith")
            
            # Time entries table header
            c.setFont("Helvetica-Bold", 10)
            y_pos = height - 200
            c.drawString(50, y_pos, "Date")
            c.drawString(150, y_pos, "Time In")
            c.drawString(250, y_pos, "Time Out")
            c.drawString(350, y_pos, "Hours")
            
            # Time entries
            c.setFont("Helvetica", 10)
            entries = [
                ("01/15", "9:00 AM", "5:00 PM", "8.0"),
                ("01/16", "8:30 AM", "4:30 PM", "8.0"),
                ("01/17", "9:00 AM", "5:00 PM", "8.0"),
                ("01/18", "8:00 AM", "4:00 PM", "8.0"),
                ("01/19", "9:30 AM", "5:30 PM", "8.0")
            ]
            
            for i, (date, time_in, time_out, hours) in enumerate(entries):
                y_pos = height - 220 - (i * 20)
                c.drawString(50, y_pos, date)
                c.drawString(150, y_pos, time_in)
                c.drawString(250, y_pos, time_out)
                c.drawString(350, y_pos, hours)
            
            # Signature
            c.setFont("Helvetica", 10)
            c.drawString(50, height - 350, "Employee Signature: [Signed]")
            
            c.save()
            
            return temp_file.name
        except Exception as e:
            print(f"Error creating realistic PDF: {e}")
            return None

    def test_pdf2image_conversion(self):
        """Test pdf2image conversion with poppler-utils"""
        try:
            pdf_file = self.create_realistic_timesheet_pdf()
            if not pdf_file:
                self.log_test("PDF2Image Conversion", False, "Could not create test PDF")
                return False
            
            # Test pdf2image conversion
            from pdf2image import convert_from_path
            
            # Convert PDF to images
            images = convert_from_path(pdf_file, dpi=200)
            
            success = len(images) > 0
            if success:
                # Save first image to verify conversion worked
                temp_image = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
                temp_image.close()
                images[0].save(temp_image.name, 'JPEG')
                
                # Check if image file was created and has content
                image_size = os.path.getsize(temp_image.name)
                success = image_size > 1000  # Should be at least 1KB for a real image
                
                details = f"Converted {len(images)} pages, first image size: {image_size} bytes"
                
                # Cleanup
                os.unlink(temp_image.name)
            else:
                details = "No images returned from PDF conversion"
            
            # Cleanup
            os.unlink(pdf_file)
            
            self.log_test("PDF2Image Conversion", success, details)
            return success
        except Exception as e:
            self.log_test("PDF2Image Conversion", False, str(e))
            return False

    def test_timesheet_upload_pdf_processing(self):
        """Test the actual timesheet upload endpoint with PDF processing"""
        try:
            pdf_file = self.create_realistic_timesheet_pdf()
            if not pdf_file:
                self.log_test("Timesheet PDF Upload Processing", False, "Could not create test PDF")
                return False, None
            
            # Upload the PDF to the timesheet endpoint
            with open(pdf_file, 'rb') as f:
                files = {'file': ('realistic_timesheet.pdf', f, 'application/pdf')}
                response = requests.post(f"{self.api_url}/timesheets/upload", files=files, timeout=120)
            
            success = response.status_code == 200
            timesheet_id = None
            
            if success:
                try:
                    data = response.json()
                    timesheet_id = data.get('id')
                    
                    # Check if extraction was successful
                    has_extracted_data = 'extracted_data' in data and data['extracted_data'] is not None
                    status = data.get('status', 'unknown')
                    
                    # Check if client name was extracted
                    client_extracted = False
                    if has_extracted_data and data['extracted_data']:
                        client_name = data['extracted_data'].get('client_name', '')
                        client_extracted = 'Maria' in client_name or 'Rodriguez' in client_name
                    
                    # Check if employee data was extracted
                    employee_extracted = False
                    if has_extracted_data and data['extracted_data']:
                        employee_entries = data['extracted_data'].get('employee_entries', [])
                        if employee_entries:
                            employee_name = employee_entries[0].get('employee_name', '')
                            employee_extracted = 'John' in employee_name or 'Smith' in employee_name
                    
                    # Check if time entries were extracted
                    time_entries_extracted = False
                    if has_extracted_data and data['extracted_data']:
                        employee_entries = data['extracted_data'].get('employee_entries', [])
                        if employee_entries and employee_entries[0].get('time_entries'):
                            time_entries_extracted = len(employee_entries[0]['time_entries']) > 0
                    
                    # Overall success if PDF was processed without poppler errors
                    pdf_processing_success = status != 'failed' and 'poppler' not in data.get('error_message', '').lower()
                    
                    success = success and pdf_processing_success
                    details = f"Status: {response.status_code}, ID: {timesheet_id}, Status: {status}, " \
                             f"Client: {client_extracted}, Employee: {employee_extracted}, " \
                             f"TimeEntries: {time_entries_extracted}, PDF Processing: {pdf_processing_success}"
                    
                except json.JSONDecodeError:
                    success = False
                    details = f"Status: {response.status_code}, Invalid JSON response"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:300]}"
            
            # Cleanup
            os.unlink(pdf_file)
            
            self.log_test("Timesheet PDF Upload Processing", success, details)
            return success, timesheet_id
        except Exception as e:
            self.log_test("Timesheet PDF Upload Processing", False, str(e))
            return False, None

    def test_multi_page_pdf_processing(self):
        """Test multi-page PDF processing"""
        try:
            # Create a multi-page PDF
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
            temp_file.close()
            
            c = canvas.Canvas(temp_file.name, pagesize=letter)
            width, height = letter
            
            # Page 1
            c.setFont("Helvetica-Bold", 16)
            c.drawString(50, height - 50, "TIMESHEET - PAGE 1")
            c.setFont("Helvetica", 12)
            c.drawString(50, height - 80, "Client: Alice Johnson")
            c.drawString(50, height - 100, "Employee: Sarah Wilson")
            c.drawString(50, height - 120, "Date: 01/15 Time In: 9:00 AM Time Out: 5:00 PM")
            c.showPage()
            
            # Page 2
            c.setFont("Helvetica-Bold", 16)
            c.drawString(50, height - 50, "TIMESHEET - PAGE 2")
            c.setFont("Helvetica", 12)
            c.drawString(50, height - 80, "Client: Bob Martinez")
            c.drawString(50, height - 100, "Employee: Mike Davis")
            c.drawString(50, height - 120, "Date: 01/16 Time In: 8:00 AM Time Out: 4:00 PM")
            c.showPage()
            
            c.save()
            
            # Upload the multi-page PDF
            with open(temp_file.name, 'rb') as f:
                files = {'file': ('multi_page_timesheet.pdf', f, 'application/pdf')}
                response = requests.post(f"{self.api_url}/timesheets/upload", files=files, timeout=120)
            
            success = response.status_code == 200
            
            if success:
                try:
                    data = response.json()
                    
                    # Check if it's a batch response (multi-page)
                    is_batch = 'timesheets' in data and isinstance(data['timesheets'], list)
                    
                    if is_batch:
                        timesheets = data['timesheets']
                        success = len(timesheets) == 2  # Should create 2 timesheet records
                        
                        # Check if both pages were processed
                        page1_processed = any('Page 1' in ts.get('filename', '') for ts in timesheets)
                        page2_processed = any('Page 2' in ts.get('filename', '') for ts in timesheets)
                        
                        success = success and page1_processed and page2_processed
                        details = f"Status: {response.status_code}, Pages: {len(timesheets)}, " \
                                 f"Page1: {page1_processed}, Page2: {page2_processed}"
                    else:
                        # Single timesheet response - check if it indicates multi-page processing
                        success = 'Page 1' in data.get('filename', '') or data.get('status') == 'completed'
                        details = f"Status: {response.status_code}, Single response for multi-page PDF"
                    
                except json.JSONDecodeError:
                    success = False
                    details = f"Status: {response.status_code}, Invalid JSON response"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:300]}"
            
            # Cleanup
            os.unlink(temp_file.name)
            
            self.log_test("Multi-page PDF Processing", success, details)
            return success
        except Exception as e:
            self.log_test("Multi-page PDF Processing", False, str(e))
            return False

    def test_pdf_error_handling(self):
        """Test PDF error handling with corrupted/invalid PDFs"""
        try:
            # Create a fake PDF (just text file with .pdf extension)
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf', mode='w')
            temp_file.write("This is not a real PDF file")
            temp_file.close()
            
            # Upload the fake PDF
            with open(temp_file.name, 'rb') as f:
                files = {'file': ('fake.pdf', f, 'application/pdf')}
                response = requests.post(f"{self.api_url}/timesheets/upload", files=files, timeout=60)
            
            # Should either reject the file or handle the error gracefully
            success = response.status_code in [200, 400, 422, 500]  # Any valid response
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    # If it accepts the file, it should mark it as failed or have an error message
                    status = data.get('status', 'unknown')
                    error_message = data.get('error_message', '')
                    
                    # Success if it detected the error
                    success = status == 'failed' or 'error' in error_message.lower() or 'pdf' in error_message.lower()
                    details = f"Status: {response.status_code}, Processing Status: {status}, Error: {error_message[:100]}"
                except json.JSONDecodeError:
                    success = False
                    details = f"Status: {response.status_code}, Invalid JSON response"
            else:
                details = f"Status: {response.status_code}, Rejected invalid PDF"
            
            # Cleanup
            os.unlink(temp_file.name)
            
            self.log_test("PDF Error Handling", success, details)
            return success
        except Exception as e:
            self.log_test("PDF Error Handling", False, str(e))
            return False

    def run_all_pdf_tests(self):
        """Run all PDF processing tests"""
        print("🔍 Starting PDF Processing Tests with Poppler-utils")
        print(f"Testing against: {self.api_url}")
        print("=" * 60)
        
        # Test 1: System dependencies
        if not self.test_system_dependencies():
            print("❌ System dependencies failed - stopping tests")
            return self.get_results()
        
        # Test 2: PDF2Image conversion
        if not self.test_pdf2image_conversion():
            print("❌ PDF2Image conversion failed - stopping tests")
            return self.get_results()
        
        # Test 3: Timesheet PDF upload and processing
        upload_success, timesheet_id = self.test_timesheet_upload_pdf_processing()
        
        # Test 4: Multi-page PDF processing
        self.test_multi_page_pdf_processing()
        
        # Test 5: Error handling
        self.test_pdf_error_handling()
        
        return self.get_results()

    def get_results(self):
        """Get test results summary"""
        print("\n" + "=" * 60)
        print(f"📊 PDF Processing Test Results: {self.tests_passed}/{self.tests_run} passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All PDF processing tests passed!")
            return 0
        else:
            print("❌ Some PDF processing tests failed")
            failed_tests = [r for r in self.test_results if not r['success']]
            print("\nFailed tests:")
            for test in failed_tests:
                print(f"  - {test['test']}: {test['details']}")
            return 1

if __name__ == "__main__":
    tester = PDFProcessingTester()
    exit_code = tester.run_all_pdf_tests()
    sys.exit(exit_code)