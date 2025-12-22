#!/usr/bin/env python3
"""
PDF Timesheet Upload Test - Focused test for poppler-utils fix verification
Tests the PDF upload functionality after poppler-utils installation
"""

import requests
import sys
import json
import os
import tempfile
import uuid
from datetime import datetime
from pathlib import Path
import time

class PDFUploadTester:
    def __init__(self, base_url="https://medicaid-claims.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.auth_token = None
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

    def login_admin(self):
        """Login with admin credentials to get authentication token"""
        try:
            login_data = {
                "email": "admin@medicaidservices.com",
                "password": "Admin2024!"
            }
            
            response = requests.post(f"{self.api_url}/auth/login", json=login_data, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get('access_token')
                success = self.auth_token is not None
                details = f"Status: {response.status_code}, Token received: {success}"
                self.log_test("Admin Login", success, details)
                return success
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
                self.log_test("Admin Login", False, details)
                return False
        except Exception as e:
            self.log_test("Admin Login", False, str(e))
            return False

    def create_realistic_test_pdf(self):
        """Create a realistic test PDF content that mimics a timesheet using ReportLab"""
        try:
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import letter
            
            # Create temporary PDF file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
            temp_file.close()  # Close so ReportLab can write to it
            
            # Create PDF with ReportLab
            c = canvas.Canvas(temp_file.name, pagesize=letter)
            width, height = letter
            
            # Title
            c.setFont("Helvetica-Bold", 16)
            c.drawString(50, height - 50, "TIMESHEET - HEALTHCARE SERVICES")
            
            # Employee Information
            c.setFont("Helvetica-Bold", 12)
            c.drawString(50, height - 100, "Employee Information:")
            c.setFont("Helvetica", 10)
            c.drawString(50, height - 120, "Name: Sarah Johnson")
            c.drawString(50, height - 135, "Employee ID: EMP001")
            c.drawString(50, height - 150, "Service Code: HHA001")
            
            # Client Information
            c.setFont("Helvetica-Bold", 12)
            c.drawString(50, height - 180, "Client Information:")
            c.setFont("Helvetica", 10)
            c.drawString(50, height - 200, "Client Name: Mary Williams")
            c.drawString(50, height - 215, "Week of: 12/16/2024 - 12/22/2024")
            
            # Daily Time Entries
            c.setFont("Helvetica-Bold", 12)
            c.drawString(50, height - 245, "Daily Time Entries:")
            c.setFont("Helvetica", 10)
            
            entries = [
                "Monday 12/16/2024    8:00 AM - 4:00 PM    8.0 hours",
                "Tuesday 12/17/2024   9:00 AM - 5:00 PM    8.0 hours",
                "Wednesday 12/18/2024 8:30 AM - 4:30 PM    8.0 hours", 
                "Thursday 12/19/2024  8:00 AM - 4:00 PM    8.0 hours",
                "Friday 12/20/2024    8:00 AM - 3:00 PM    7.0 hours"
            ]
            
            y_pos = height - 265
            for entry in entries:
                c.drawString(50, y_pos, entry)
                y_pos -= 15
            
            # Total and Signature
            c.setFont("Helvetica-Bold", 10)
            c.drawString(50, y_pos - 20, "Total Hours: 39.0")
            c.drawString(50, y_pos - 40, "Signature: [Signed] Sarah Johnson")
            c.drawString(50, y_pos - 55, "Date: 12/22/2024")
            
            # Service Details
            c.setFont("Helvetica-Bold", 12)
            c.drawString(50, y_pos - 85, "Service Details:")
            c.setFont("Helvetica", 10)
            c.drawString(50, y_pos - 105, "- Personal Care Services")
            c.drawString(50, y_pos - 120, "- Home Health Aide")
            c.drawString(50, y_pos - 135, "- Medicaid Approved Services")
            
            # Save the PDF
            c.save()
            
            print(f"📄 Created test PDF: {temp_file.name}")
            return temp_file.name
        except Exception as e:
            print(f"❌ Error creating test PDF: {e}")
            return None

    def test_pdf_upload_with_auth(self):
        """Test PDF upload with authentication"""
        try:
            if not self.auth_token:
                self.log_test("PDF Upload with Auth", False, "No authentication token available")
                return False, None

            test_file = self.create_realistic_test_pdf()
            if not test_file:
                self.log_test("PDF Upload with Auth", False, "Could not create test PDF")
                return False, None
            
            headers = {
                'Authorization': f'Bearer {self.auth_token}'
            }
            
            with open(test_file, 'rb') as f:
                files = {'file': ('healthcare_timesheet.pdf', f, 'application/pdf')}
                response = requests.post(
                    f"{self.api_url}/timesheets/upload", 
                    files=files, 
                    headers=headers,
                    timeout=60
                )
            
            success = response.status_code == 200
            timesheet_id = None
            
            if success:
                try:
                    data = response.json()
                    timesheet_id = data.get('id')
                    status = data.get('status')
                    filename = data.get('filename')
                    error_message = data.get('error_message')
                    
                    # Check for poppler-related errors
                    poppler_error = False
                    if error_message and 'poppler' in error_message.lower():
                        poppler_error = True
                    
                    has_required_fields = all(key in data for key in ['id', 'filename', 'status'])
                    success = success and has_required_fields and not poppler_error
                    
                    details = f"Status: {response.status_code}, ID: {timesheet_id}, " \
                             f"Timesheet Status: {status}, Filename: {filename}, " \
                             f"Poppler Error: {poppler_error}"
                    
                    if error_message:
                        details += f", Error: {error_message[:100]}"
                        
                except json.JSONDecodeError:
                    success = False
                    details = f"Status: {response.status_code}, Invalid JSON response"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:300]}"
            
            self.log_test("PDF Upload with Auth", success, details)
            
            # Cleanup
            os.unlink(test_file)
            return success, timesheet_id
        except Exception as e:
            self.log_test("PDF Upload with Auth", False, str(e))
            return False, None

    def test_pdf_processing_status(self, timesheet_id):
        """Test PDF processing status and check for completion"""
        if not timesheet_id:
            self.log_test("PDF Processing Status", False, "No timesheet ID provided")
            return False
        
        try:
            if not self.auth_token:
                self.log_test("PDF Processing Status", False, "No authentication token")
                return False

            headers = {
                'Authorization': f'Bearer {self.auth_token}'
            }
            
            # Wait a moment for processing
            print("⏳ Waiting for PDF processing...")
            time.sleep(3)
            
            response = requests.get(
                f"{self.api_url}/timesheets/{timesheet_id}", 
                headers=headers,
                timeout=10
            )
            
            success = response.status_code == 200
            
            if success:
                try:
                    data = response.json()
                    status = data.get('status')
                    error_message = data.get('error_message')
                    extracted_data = data.get('extracted_data')
                    
                    # Check for poppler-related errors
                    poppler_error = False
                    pdf_conversion_failed = False
                    
                    if error_message:
                        if 'poppler' in error_message.lower():
                            poppler_error = True
                        if 'pdf conversion failed' in error_message.lower():
                            pdf_conversion_failed = True
                    
                    # Check if processing completed successfully
                    processing_success = (status == "completed" and not poppler_error and 
                                        not pdf_conversion_failed)
                    
                    # Check if extracted data exists
                    has_extracted_data = extracted_data is not None
                    
                    success = processing_success
                    
                    details = f"Status: {response.status_code}, Processing Status: {status}, " \
                             f"Poppler Error: {poppler_error}, PDF Conversion Failed: {pdf_conversion_failed}, " \
                             f"Has Extracted Data: {has_extracted_data}"
                    
                    if error_message:
                        details += f", Error: {error_message[:150]}"
                        
                except json.JSONDecodeError:
                    success = False
                    details = f"Status: {response.status_code}, Invalid JSON response"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("PDF Processing Status", success, details)
            return success
        except Exception as e:
            self.log_test("PDF Processing Status", False, str(e))
            return False

    def test_extracted_data_quality(self, timesheet_id):
        """Test the quality of extracted data from PDF"""
        if not timesheet_id:
            self.log_test("Extracted Data Quality", False, "No timesheet ID provided")
            return False
        
        try:
            if not self.auth_token:
                self.log_test("Extracted Data Quality", False, "No authentication token")
                return False

            headers = {
                'Authorization': f'Bearer {self.auth_token}'
            }
            
            response = requests.get(
                f"{self.api_url}/timesheets/{timesheet_id}", 
                headers=headers,
                timeout=10
            )
            
            success = response.status_code == 200
            
            if success:
                try:
                    data = response.json()
                    extracted_data = data.get('extracted_data')
                    
                    if extracted_data:
                        client_name = extracted_data.get('client_name')
                        employee_entries = extracted_data.get('employee_entries', [])
                        
                        # Check if basic data was extracted
                        has_client = client_name is not None and len(str(client_name).strip()) > 0
                        has_employees = len(employee_entries) > 0
                        
                        employee_data_quality = False
                        if has_employees:
                            first_employee = employee_entries[0]
                            employee_name = first_employee.get('employee_name')
                            time_entries = first_employee.get('time_entries', [])
                            
                            has_employee_name = employee_name is not None and len(str(employee_name).strip()) > 0
                            has_time_entries = len(time_entries) > 0
                            
                            employee_data_quality = has_employee_name and has_time_entries
                        
                        success = has_client and has_employees and employee_data_quality
                        
                        details = f"Status: {response.status_code}, Has Client: {has_client}, " \
                                 f"Has Employees: {has_employees}, Employee Data Quality: {employee_data_quality}, " \
                                 f"Client: {client_name}, Employees Count: {len(employee_entries)}"
                    else:
                        success = False
                        details = f"Status: {response.status_code}, No extracted data found"
                        
                except json.JSONDecodeError:
                    success = False
                    details = f"Status: {response.status_code}, Invalid JSON response"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Extracted Data Quality", success, details)
            return success
        except Exception as e:
            self.log_test("Extracted Data Quality", False, str(e))
            return False

    def check_backend_logs(self):
        """Check backend logs for poppler-related errors"""
        try:
            print("\n🔍 Checking backend logs for poppler errors...")
            
            # Check supervisor backend logs
            import subprocess
            result = subprocess.run(
                ['tail', '-n', '50', '/var/log/supervisor/backend.err.log'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                log_content = result.stdout
                
                # Look for poppler-related errors
                poppler_errors = []
                pdf_errors = []
                
                for line in log_content.split('\n'):
                    if 'poppler' in line.lower():
                        poppler_errors.append(line.strip())
                    if 'pdf conversion failed' in line.lower():
                        pdf_errors.append(line.strip())
                
                has_poppler_errors = len(poppler_errors) > 0
                has_pdf_errors = len(pdf_errors) > 0
                
                success = not has_poppler_errors and not has_pdf_errors
                
                details = f"Poppler Errors: {len(poppler_errors)}, PDF Errors: {len(pdf_errors)}"
                
                if poppler_errors:
                    details += f", Recent Poppler Error: {poppler_errors[-1][:100]}"
                if pdf_errors:
                    details += f", Recent PDF Error: {pdf_errors[-1][:100]}"
                
                self.log_test("Backend Logs Check", success, details)
                
                # Print recent errors for debugging
                if poppler_errors or pdf_errors:
                    print("\n🚨 Recent errors found in logs:")
                    for error in (poppler_errors + pdf_errors)[-3:]:
                        print(f"   {error}")
                
                return success
            else:
                self.log_test("Backend Logs Check", False, "Could not read backend logs")
                return False
                
        except Exception as e:
            self.log_test("Backend Logs Check", False, str(e))
            return False

    def test_poppler_installation(self):
        """Test if poppler-utils is properly installed"""
        try:
            print("\n🔧 Checking poppler-utils installation...")
            
            import subprocess
            
            # Check if pdftoppm is available
            result = subprocess.run(['which', 'pdftoppm'], capture_output=True, text=True)
            pdftoppm_available = result.returncode == 0
            
            # Check if pdfinfo is available  
            result = subprocess.run(['which', 'pdfinfo'], capture_output=True, text=True)
            pdfinfo_available = result.returncode == 0
            
            # Get poppler version if available
            poppler_version = "Unknown"
            if pdftoppm_available:
                try:
                    result = subprocess.run(['pdftoppm', '-v'], capture_output=True, text=True, stderr=subprocess.STDOUT)
                    if result.stdout:
                        # Extract version from output
                        for line in result.stdout.split('\n'):
                            if 'version' in line.lower():
                                poppler_version = line.strip()
                                break
                except:
                    pass
            
            success = pdftoppm_available and pdfinfo_available
            
            details = f"pdftoppm: {pdftoppm_available}, pdfinfo: {pdfinfo_available}, Version: {poppler_version}"
            
            self.log_test("Poppler Installation Check", success, details)
            
            if success:
                print(f"✅ Poppler-utils detected: {poppler_version}")
            else:
                print("❌ Poppler-utils not properly installed")
            
            return success
        except Exception as e:
            self.log_test("Poppler Installation Check", False, str(e))
            return False

    def run_pdf_upload_tests(self):
        """Run comprehensive PDF upload tests"""
        print("🚀 Starting PDF Timesheet Upload Tests (Poppler-utils Fix Verification)")
        print(f"Testing against: {self.api_url}")
        print("=" * 80)
        
        # Step 1: Check poppler installation
        poppler_installed = self.test_poppler_installation()
        
        # Step 2: Login with admin credentials
        if not self.login_admin():
            print("❌ Admin login failed - stopping tests")
            return self.get_results()
        
        # Step 3: Test PDF upload
        upload_success, timesheet_id = self.test_pdf_upload_with_auth()
        
        if upload_success and timesheet_id:
            # Step 4: Check processing status
            processing_success = self.test_pdf_processing_status(timesheet_id)
            
            # Step 5: Check extracted data quality
            if processing_success:
                self.test_extracted_data_quality(timesheet_id)
        
        # Step 6: Check backend logs for errors
        self.check_backend_logs()
        
        return self.get_results()

    def get_results(self):
        """Get test results summary"""
        print("\n" + "=" * 80)
        print(f"📊 PDF Upload Test Results: {self.tests_passed}/{self.tests_run} passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All PDF upload tests passed! Poppler-utils fix verified.")
            return 0
        else:
            print("❌ Some PDF upload tests failed")
            failed_tests = [r for r in self.test_results if not r['success']]
            print("\nFailed tests:")
            for test in failed_tests:
                print(f"  - {test['test']}: {test['details']}")
            return 1

if __name__ == "__main__":
    tester = PDFUploadTester()
    exit_code = tester.run_pdf_upload_tests()
    sys.exit(exit_code)