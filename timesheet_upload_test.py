#!/usr/bin/env python3
"""
Focused Timesheet Upload Test
Tests the /api/timesheets/upload endpoint specifically
"""

import requests
import sys
import json
import os
import tempfile
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

class TimesheetUploadTester:
    def __init__(self, base_url="https://healthcare-tracking.preview.emergentagent.com"):
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

    def create_timesheet_pdf(self):
        """Create a realistic timesheet PDF"""
        try:
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
            temp_file.close()
            
            c = canvas.Canvas(temp_file.name, pagesize=letter)
            width, height = letter
            
            # Header
            c.setFont("Helvetica-Bold", 16)
            c.drawString(50, height - 50, "HEALTHCARE TIMESHEET")
            
            # Week info
            c.setFont("Helvetica", 12)
            c.drawString(50, height - 80, "Week of: 01/15/2024 - 01/21/2024")
            
            # Client
            c.drawString(50, height - 110, "Client Name: Maria Rodriguez")
            
            # Employee
            c.setFont("Helvetica-Bold", 12)
            c.drawString(50, height - 140, "Employee: John Smith")
            c.setFont("Helvetica", 10)
            c.drawString(50, height - 160, "Service Code: T1019")
            
            # Time entries
            entries = [
                ("01/15", "9:00 AM", "5:00 PM", "8.0"),
                ("01/16", "8:30 AM", "4:30 PM", "8.0"),
                ("01/17", "9:00 AM", "5:00 PM", "8.0")
            ]
            
            y_pos = height - 190
            c.drawString(50, y_pos, "Date    Time In    Time Out    Hours")
            
            for i, (date, time_in, time_out, hours) in enumerate(entries):
                y_pos = height - 210 - (i * 20)
                c.drawString(50, y_pos, f"{date}    {time_in}    {time_out}    {hours}")
            
            # Signature
            c.drawString(50, height - 300, "Employee Signature: [Signed]")
            
            c.save()
            return temp_file.name
        except Exception as e:
            print(f"Error creating PDF: {e}")
            return None

    def test_timesheet_upload_basic(self):
        """Test basic timesheet upload functionality"""
        try:
            pdf_file = self.create_timesheet_pdf()
            if not pdf_file:
                self.log_test("Timesheet Upload Basic", False, "Could not create test PDF")
                return False, None
            
            with open(pdf_file, 'rb') as f:
                files = {'file': ('test_timesheet.pdf', f, 'application/pdf')}
                response = requests.post(f"{self.api_url}/timesheets/upload", files=files, timeout=120)
            
            success = response.status_code == 200
            timesheet_id = None
            
            if success:
                try:
                    data = response.json()
                    timesheet_id = data.get('id')
                    
                    # Check basic response structure
                    has_id = 'id' in data
                    has_filename = 'filename' in data
                    has_status = 'status' in data
                    
                    # Check if processing was attempted
                    status = data.get('status', 'unknown')
                    processing_attempted = status in ['completed', 'failed', 'processing']
                    
                    success = has_id and has_filename and has_status and processing_attempted
                    details = f"Status: {response.status_code}, ID: {timesheet_id}, " \
                             f"Processing Status: {status}, Has required fields: {has_id and has_filename and has_status}"
                    
                except json.JSONDecodeError:
                    success = False
                    details = f"Status: {response.status_code}, Invalid JSON response"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            os.unlink(pdf_file)
            
            self.log_test("Timesheet Upload Basic", success, details)
            return success, timesheet_id
        except Exception as e:
            self.log_test("Timesheet Upload Basic", False, str(e))
            return False, None

    def test_timesheet_list(self):
        """Test getting timesheet list"""
        try:
            response = requests.get(f"{self.api_url}/timesheets", timeout=30)
            success = response.status_code == 200
            
            if success:
                try:
                    data = response.json()
                    is_list = isinstance(data, list)
                    success = is_list
                    details = f"Status: {response.status_code}, Is list: {is_list}, Count: {len(data) if is_list else 'N/A'}"
                except json.JSONDecodeError:
                    success = False
                    details = f"Status: {response.status_code}, Invalid JSON response"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Timesheet List", success, details)
            return success
        except Exception as e:
            self.log_test("Timesheet List", False, str(e))
            return False

    def test_timesheet_get_specific(self, timesheet_id):
        """Test getting specific timesheet"""
        if not timesheet_id:
            self.log_test("Timesheet Get Specific", False, "No timesheet ID provided")
            return False
        
        try:
            response = requests.get(f"{self.api_url}/timesheets/{timesheet_id}", timeout=30)
            success = response.status_code == 200
            
            if success:
                try:
                    data = response.json()
                    has_id = data.get('id') == timesheet_id
                    has_filename = 'filename' in data
                    success = has_id and has_filename
                    details = f"Status: {response.status_code}, Correct ID: {has_id}, Has filename: {has_filename}"
                except json.JSONDecodeError:
                    success = False
                    details = f"Status: {response.status_code}, Invalid JSON response"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Timesheet Get Specific", success, details)
            return success
        except Exception as e:
            self.log_test("Timesheet Get Specific", False, str(e))
            return False

    def test_invalid_file_upload(self):
        """Test uploading invalid file type"""
        try:
            # Create text file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.txt', mode='w')
            temp_file.write("This is not a PDF")
            temp_file.close()
            
            with open(temp_file.name, 'rb') as f:
                files = {'file': ('test.txt', f, 'text/plain')}
                response = requests.post(f"{self.api_url}/timesheets/upload", files=files, timeout=30)
            
            # Should reject invalid file type
            success = response.status_code == 400
            details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            os.unlink(temp_file.name)
            
            self.log_test("Invalid File Upload", success, details)
            return success
        except Exception as e:
            self.log_test("Invalid File Upload", False, str(e))
            return False

    def run_all_tests(self):
        """Run all timesheet upload tests"""
        print("📋 Testing Timesheet Upload Functionality")
        print(f"Testing against: {self.api_url}")
        print("=" * 60)
        
        # Test 1: Basic upload
        upload_success, timesheet_id = self.test_timesheet_upload_basic()
        
        # Test 2: List timesheets
        self.test_timesheet_list()
        
        # Test 3: Get specific timesheet (if upload succeeded)
        if timesheet_id:
            self.test_timesheet_get_specific(timesheet_id)
        
        # Test 4: Invalid file upload
        self.test_invalid_file_upload()
        
        return self.get_results()

    def get_results(self):
        """Get test results summary"""
        print("\n" + "=" * 60)
        print(f"📊 Timesheet Upload Test Results: {self.tests_passed}/{self.tests_run} passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All timesheet upload tests passed!")
            return 0
        else:
            print("❌ Some timesheet upload tests failed")
            failed_tests = [r for r in self.test_results if not r['success']]
            print("\nFailed tests:")
            for test in failed_tests:
                print(f"  - {test['test']}: {test['details']}")
            return 1

if __name__ == "__main__":
    tester = TimesheetUploadTester()
    exit_code = tester.run_all_tests()
    sys.exit(exit_code)