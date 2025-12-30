#!/usr/bin/env python3
"""
OCR Model Revert Fix Testing Suite
Tests the specific fix for reverting OCR model from gemini-2.5-pro back to gemini-2.0-flash
and verifying PDF upload performance improvements.

Test Focus:
1. PDF Status Endpoint - Verify gemini-2.0-flash model is active
2. PDF Upload Performance - Verify uploads complete under 30 seconds
3. Timesheet Retrieval - Verify uploaded timesheets are accessible
4. Authentication - Test admin login
5. Employee CRUD - Basic employee operations
"""

import requests
import json
import tempfile
import time
import os
from datetime import datetime
from pathlib import Path

class OCRModelRevertTester:
    def __init__(self, base_url="https://healthcare-tracking.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        self.auth_token = None
        self.admin_email = "admin@medicaidservices.com"
        self.admin_password = "Admin2024!"

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
            "details": details,
            "timestamp": datetime.now().isoformat()
        })

    def authenticate_admin(self):
        """Authenticate with admin credentials"""
        try:
            login_data = {
                "email": self.admin_email,
                "password": self.admin_password
            }
            
            response = requests.post(f"{self.api_url}/auth/login", json=login_data, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get('access_token')
                details = f"Successfully authenticated as {self.admin_email}"
                self.log_test("Admin Authentication", True, details)
                return True
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
                self.log_test("Admin Authentication", False, details)
                return False
        except Exception as e:
            self.log_test("Admin Authentication", False, str(e))
            return False

    def get_auth_headers(self):
        """Get authorization headers for authenticated requests"""
        if self.auth_token:
            return {"Authorization": f"Bearer {self.auth_token}"}
        return {}

    def test_pdf_status_endpoint(self):
        """Test GET /api/system/pdf-status - Priority Test #1"""
        try:
            response = requests.get(f"{self.api_url}/system/pdf-status", timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                
                # Check for required fields
                required_fields = ['ocr_model', 'poppler_utils', 'status']
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    success = False
                    details = f"Missing required fields: {missing_fields}"
                else:
                    # Verify OCR model is gemini-2.0-flash (NOT gemini-2.5-pro)
                    ocr_model = data.get('ocr_model')
                    # Handle both string and object formats
                    if isinstance(ocr_model, dict):
                        model_name = ocr_model.get('model', '')
                        model_correct = model_name == 'gemini-2.0-flash'
                        ocr_model_display = model_name
                    else:
                        model_correct = ocr_model == 'gemini-2.0-flash'
                        ocr_model_display = ocr_model
                    
                    # Verify poppler_utils.installed is true
                    poppler_info = data.get('poppler_utils', {})
                    poppler_installed = poppler_info.get('installed', False)
                    
                    # Verify status is "ready"
                    status_ready = data.get('status') == 'ready'
                    
                    success = model_correct and poppler_installed and status_ready
                    
                    details = f"OCR Model: {ocr_model_display} (Expected: gemini-2.0-flash), " \
                             f"Poppler Installed: {poppler_installed}, " \
                             f"Status: {data.get('status')}"
                    
                    if not model_correct:
                        details += f" ❌ CRITICAL: OCR model should be gemini-2.0-flash, not {ocr_model_display}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("PDF Status Endpoint (OCR Model Check)", success, details)
            return success
        except Exception as e:
            self.log_test("PDF Status Endpoint (OCR Model Check)", False, str(e))
            return False

    def create_realistic_test_pdf(self):
        """Create a realistic test PDF with timesheet content"""
        try:
            # Create a more realistic timesheet content
            timesheet_content = """HEALTHCARE TIMESHEET
            
Client: Mary Johnson
Week of: 12/16/2024 - 12/22/2024
Service Authorization: AUTH123456

Employee: Sarah Williams
Service Code: T1019
Employee ID: EMP001

Date        Time In    Time Out    Hours
12/16/2024  09:00 AM   05:00 PM    8.0
12/17/2024  09:30 AM   05:30 PM    8.0
12/18/2024  10:00 AM   06:00 PM    8.0
12/19/2024  09:00 AM   05:00 PM    8.0
12/20/2024  09:15 AM   05:15 PM    8.0

Total Hours: 40.0
Total Units: 160

Employee Signature: [Signed] Sarah Williams
Date: 12/22/2024

Supervisor: Dr. Robert Smith
NPI: 1234567890
"""
            
            # Create temporary file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf', mode='w')
            temp_file.write(timesheet_content)
            temp_file.close()
            
            return temp_file.name
        except Exception as e:
            print(f"Error creating test PDF: {e}")
            return None

    def test_pdf_upload_performance(self):
        """Test POST /api/timesheets/upload - Priority Test #2"""
        try:
            # Create test PDF
            test_file = self.create_realistic_test_pdf()
            if not test_file:
                self.log_test("PDF Upload Performance", False, "Could not create test PDF")
                return False, None
            
            # Record start time
            start_time = time.time()
            
            # Upload PDF
            headers = self.get_auth_headers()
            with open(test_file, 'rb') as f:
                files = {'file': ('healthcare_timesheet.pdf', f, 'application/pdf')}
                response = requests.post(f"{self.api_url}/timesheets/upload", 
                                       files=files, headers=headers, timeout=60)
            
            # Calculate upload time
            upload_time = time.time() - start_time
            
            success = response.status_code == 200
            timesheet_id = None
            
            if success:
                try:
                    data = response.json()
                    timesheet_id = data.get('id')
                    
                    # Verify response contains required fields
                    required_fields = ['id', 'filename', 'status']
                    has_required_fields = all(field in data for field in required_fields)
                    
                    # Check if extracted_data is present
                    has_extracted_data = 'extracted_data' in data
                    extracted_data = data.get('extracted_data', {})
                    
                    # Verify extracted_data structure
                    has_client_name = 'client_name' in extracted_data
                    has_employee_entries = 'employee_entries' in extracted_data
                    
                    # Verify upload completed under 30 seconds (performance requirement)
                    performance_ok = upload_time < 30.0
                    
                    # Verify status is "completed" (not "processing" or "failed")
                    status_completed = data.get('status') == 'completed'
                    
                    success = (has_required_fields and has_extracted_data and 
                             has_client_name and has_employee_entries and 
                             performance_ok and status_completed)
                    
                    details = f"Upload Time: {upload_time:.2f}s (Limit: 30s), " \
                             f"Status: {data.get('status')}, " \
                             f"Client: {extracted_data.get('client_name', 'N/A')}, " \
                             f"Employees: {len(extracted_data.get('employee_entries', []))}, " \
                             f"ID: {timesheet_id}"
                    
                    if not performance_ok:
                        details += f" ❌ PERFORMANCE ISSUE: Upload took {upload_time:.2f}s (should be < 30s)"
                    
                except json.JSONDecodeError:
                    success = False
                    details = f"Upload Time: {upload_time:.2f}s, Status: {response.status_code}, Invalid JSON response"
            else:
                details = f"Upload Time: {upload_time:.2f}s, Status: {response.status_code}, Response: {response.text[:200]}"
            
            # Cleanup
            os.unlink(test_file)
            
            self.log_test("PDF Upload Performance", success, details)
            return success, timesheet_id
        except Exception as e:
            self.log_test("PDF Upload Performance", False, str(e))
            return False, None

    def test_timesheet_retrieval(self, timesheet_id=None):
        """Test GET /api/timesheets - Priority Test #3"""
        try:
            headers = self.get_auth_headers()
            response = requests.get(f"{self.api_url}/timesheets", headers=headers, timeout=10)
            success = response.status_code == 200
            
            if success:
                try:
                    data = response.json()
                    
                    # Verify response is a list
                    is_list = isinstance(data, list)
                    
                    # Check if we have timesheets
                    has_timesheets = len(data) > 0 if is_list else False
                    
                    # If we have a specific timesheet_id, verify it's in the list
                    timesheet_found = False
                    if timesheet_id and has_timesheets:
                        timesheet_found = any(ts.get('id') == timesheet_id for ts in data)
                    
                    success = is_list and has_timesheets
                    
                    details = f"Status: {response.status_code}, " \
                             f"Timesheets Count: {len(data) if is_list else 'N/A'}"
                    
                    if timesheet_id:
                        details += f", Uploaded Timesheet Found: {timesheet_found}"
                        if not timesheet_found:
                            details += f" ❌ Recently uploaded timesheet {timesheet_id} not found in list"
                    
                except json.JSONDecodeError:
                    success = False
                    details = f"Status: {response.status_code}, Invalid JSON response"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Timesheet Retrieval", success, details)
            return success
        except Exception as e:
            self.log_test("Timesheet Retrieval", False, str(e))
            return False

    def test_employee_crud_basic(self):
        """Test basic employee CRUD operations - Secondary Test #5"""
        try:
            headers = self.get_auth_headers()
            
            # Test POST /api/employees (create)
            employee_data = {
                "first_name": "Test",
                "last_name": "Employee",
                "email": "test.employee@healthcare.com",
                "phone": "6145551234",
                "ssn": "123-45-6789",
                "date_of_birth": "1990-01-01",
                "sex": "Female",
                "categories": ["RN", "HHA"],  # Required field
                "is_complete": True
            }
            
            response = requests.post(f"{self.api_url}/employees", 
                                   json=employee_data, headers=headers, timeout=10)
            create_success = response.status_code == 200
            employee_id = None
            
            if create_success:
                data = response.json()
                employee_id = data.get('id')
                has_categories = 'categories' in data
                create_success = create_success and has_categories
            
            # Test GET /api/employees (list)
            response = requests.get(f"{self.api_url}/employees", headers=headers, timeout=10)
            list_success = response.status_code == 200
            
            # Test PUT /api/employees/{id} (update) if we created an employee
            update_success = True
            if create_success and employee_id:
                update_data = {
                    "categories": ["RN", "LPN", "DSP"]  # Update categories
                }
                response = requests.put(f"{self.api_url}/employees/{employee_id}", 
                                      json=update_data, headers=headers, timeout=10)
                update_success = response.status_code == 200
                
                if update_success:
                    data = response.json()
                    updated_categories = data.get('categories', [])
                    update_success = 'RN' in updated_categories and 'LPN' in updated_categories
            
            success = create_success and list_success and update_success
            
            details = f"Create: {create_success}, List: {list_success}, Update: {update_success}"
            if employee_id:
                details += f", Employee ID: {employee_id}"
            
            self.log_test("Employee CRUD Operations", success, details)
            return success, employee_id
        except Exception as e:
            self.log_test("Employee CRUD Operations", False, str(e))
            return False, None

    def run_priority_tests(self):
        """Run the priority tests as specified in the review request"""
        print("🔧 Starting OCR Model Revert Fix Testing")
        print(f"Testing against: {self.api_url}")
        print("=" * 60)
        
        # Step 1: Authenticate with admin credentials
        if not self.authenticate_admin():
            print("❌ Admin authentication failed - stopping tests")
            return self.get_results()
        
        print("\n📋 PRIORITY TESTS:")
        
        # Priority Test 1: PDF Status Endpoint
        print("\n1️⃣ Testing PDF Status Endpoint...")
        self.test_pdf_status_endpoint()
        
        # Priority Test 2: PDF Upload Performance
        print("\n2️⃣ Testing PDF Upload Performance...")
        upload_success, timesheet_id = self.test_pdf_upload_performance()
        
        # Priority Test 3: Timesheet Retrieval
        print("\n3️⃣ Testing Timesheet Retrieval...")
        self.test_timesheet_retrieval(timesheet_id)
        
        print("\n📋 SECONDARY TESTS:")
        
        # Secondary Test 4: Authentication (already done)
        print("\n4️⃣ Authentication - Already completed ✅")
        
        # Secondary Test 5: Employee CRUD
        print("\n5️⃣ Testing Employee CRUD Operations...")
        self.test_employee_crud_basic()
        
        return self.get_results()

    def get_results(self):
        """Get test results summary"""
        print("\n" + "=" * 60)
        print(f"📊 OCR Model Revert Test Results: {self.tests_passed}/{self.tests_run} passed")
        
        # Categorize results
        priority_tests = [r for r in self.test_results if any(keyword in r['test'] for keyword in 
                         ['PDF Status', 'PDF Upload', 'Timesheet Retrieval', 'Admin Authentication'])]
        secondary_tests = [r for r in self.test_results if r not in priority_tests]
        
        print(f"\n🎯 Priority Tests: {len([t for t in priority_tests if t['success']])}/{len(priority_tests)} passed")
        for test in priority_tests:
            status = "✅" if test['success'] else "❌"
            print(f"  {status} {test['test']}")
        
        if secondary_tests:
            print(f"\n📋 Secondary Tests: {len([t for t in secondary_tests if t['success']])}/{len(secondary_tests)} passed")
            for test in secondary_tests:
                status = "✅" if test['success'] else "❌"
                print(f"  {status} {test['test']}")
        
        if self.tests_passed == self.tests_run:
            print("\n🎉 All tests passed! OCR model revert fix is working correctly.")
            return 0
        else:
            print("\n❌ Some tests failed")
            failed_tests = [r for r in self.test_results if not r['success']]
            print("\nFailed tests:")
            for test in failed_tests:
                print(f"  - {test['test']}: {test['details']}")
            return 1

def main():
    """Main test execution"""
    tester = OCRModelRevertTester()
    return tester.run_priority_tests()

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)