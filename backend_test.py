import requests
import sys
import json
import os
from datetime import datetime
from pathlib import Path
import tempfile

class TimesheetAPITester:
    def __init__(self, base_url="https://sandata-upload.preview.emergentagent.com"):
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

    def test_root_endpoint(self):
        """Test root API endpoint"""
        try:
            response = requests.get(f"{self.api_url}/", timeout=10)
            success = response.status_code == 200
            details = f"Status: {response.status_code}, Response: {response.text[:100]}"
            self.log_test("Root API Endpoint", success, details)
            return success
        except Exception as e:
            self.log_test("Root API Endpoint", False, str(e))
            return False

    def test_get_timesheets_empty(self):
        """Test getting timesheets when none exist"""
        try:
            response = requests.get(f"{self.api_url}/timesheets", timeout=10)
            success = response.status_code == 200
            if success:
                data = response.json()
                success = isinstance(data, list)
                details = f"Status: {response.status_code}, Count: {len(data) if isinstance(data, list) else 'N/A'}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            self.log_test("Get Timesheets (Empty)", success, details)
            return success
        except Exception as e:
            self.log_test("Get Timesheets (Empty)", False, str(e))
            return False

    def create_test_pdf(self):
        """Create a simple test PDF file"""
        try:
            # Create a simple text file that we'll treat as PDF for testing
            test_content = """TIMESHEET
Employee: John Doe
Date: 2024-01-15
Time In: 9:00 AM
Time Out: 5:00 PM
Hours: 8
Client: ABC Healthcare
Service Code: HHA001
Signature: [Signed]"""
            
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf', mode='w')
            temp_file.write(test_content)
            temp_file.close()
            return temp_file.name
        except Exception as e:
            print(f"Error creating test file: {e}")
            return None

    def test_upload_invalid_file_type(self):
        """Test uploading invalid file type"""
        try:
            # Create a test file with invalid extension
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.txt', mode='w')
            temp_file.write("Invalid file type")
            temp_file.close()
            
            with open(temp_file.name, 'rb') as f:
                files = {'file': ('test.txt', f, 'text/plain')}
                response = requests.post(f"{self.api_url}/timesheets/upload", files=files, timeout=30)
            
            success = response.status_code == 400
            details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            self.log_test("Upload Invalid File Type", success, details)
            
            # Cleanup
            os.unlink(temp_file.name)
            return success
        except Exception as e:
            self.log_test("Upload Invalid File Type", False, str(e))
            return False

    def test_upload_pdf_timesheet(self):
        """Test uploading a PDF timesheet"""
        try:
            test_file = self.create_test_pdf()
            if not test_file:
                self.log_test("Upload PDF Timesheet", False, "Could not create test file")
                return False, None
            
            with open(test_file, 'rb') as f:
                files = {'file': ('test_timesheet.pdf', f, 'application/pdf')}
                response = requests.post(f"{self.api_url}/timesheets/upload", files=files, timeout=60)
            
            success = response.status_code == 200
            timesheet_id = None
            
            if success:
                try:
                    data = response.json()
                    timesheet_id = data.get('id')
                    has_required_fields = all(key in data for key in ['id', 'filename', 'status'])
                    success = success and has_required_fields
                    details = f"Status: {response.status_code}, ID: {timesheet_id}, Status: {data.get('status')}"
                except json.JSONDecodeError:
                    success = False
                    details = f"Status: {response.status_code}, Invalid JSON response"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Upload PDF Timesheet", success, details)
            
            # Cleanup
            os.unlink(test_file)
            return success, timesheet_id
        except Exception as e:
            self.log_test("Upload PDF Timesheet", False, str(e))
            return False, None

    def test_get_specific_timesheet(self, timesheet_id):
        """Test getting a specific timesheet by ID"""
        if not timesheet_id:
            self.log_test("Get Specific Timesheet", False, "No timesheet ID provided")
            return False
        
        try:
            response = requests.get(f"{self.api_url}/timesheets/{timesheet_id}", timeout=10)
            success = response.status_code == 200
            
            if success:
                try:
                    data = response.json()
                    has_required_fields = all(key in data for key in ['id', 'filename', 'status'])
                    success = success and has_required_fields
                    details = f"Status: {response.status_code}, Found timesheet: {data.get('filename')}"
                except json.JSONDecodeError:
                    success = False
                    details = f"Status: {response.status_code}, Invalid JSON response"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Get Specific Timesheet", success, details)
            return success
        except Exception as e:
            self.log_test("Get Specific Timesheet", False, str(e))
            return False

    def test_get_timesheets_with_data(self):
        """Test getting timesheets when data exists"""
        try:
            response = requests.get(f"{self.api_url}/timesheets", timeout=10)
            success = response.status_code == 200
            
            if success:
                try:
                    data = response.json()
                    success = isinstance(data, list) and len(data) > 0
                    details = f"Status: {response.status_code}, Count: {len(data) if isinstance(data, list) else 'N/A'}"
                except json.JSONDecodeError:
                    success = False
                    details = f"Status: {response.status_code}, Invalid JSON response"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Get Timesheets (With Data)", success, details)
            return success
        except Exception as e:
            self.log_test("Get Timesheets (With Data)", False, str(e))
            return False

    def test_delete_timesheet(self, timesheet_id):
        """Test deleting a timesheet"""
        if not timesheet_id:
            self.log_test("Delete Timesheet", False, "No timesheet ID provided")
            return False
        
        try:
            response = requests.delete(f"{self.api_url}/timesheets/{timesheet_id}", timeout=10)
            success = response.status_code == 200
            
            if success:
                try:
                    data = response.json()
                    success = "message" in data
                    details = f"Status: {response.status_code}, Message: {data.get('message', 'N/A')}"
                except json.JSONDecodeError:
                    success = False
                    details = f"Status: {response.status_code}, Invalid JSON response"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Delete Timesheet", success, details)
            return success
        except Exception as e:
            self.log_test("Delete Timesheet", False, str(e))
            return False

    def test_delete_nonexistent_timesheet(self):
        """Test deleting a non-existent timesheet"""
        try:
            fake_id = "nonexistent-id-12345"
            response = requests.delete(f"{self.api_url}/timesheets/{fake_id}", timeout=10)
            success = response.status_code == 404
            details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            self.log_test("Delete Non-existent Timesheet", success, details)
            return success
        except Exception as e:
            self.log_test("Delete Non-existent Timesheet", False, str(e))
            return False

    def run_all_tests(self):
        """Run all backend API tests"""
        print("🚀 Starting Timesheet API Backend Tests")
        print(f"Testing against: {self.api_url}")
        print("=" * 60)
        
        # Test basic connectivity
        if not self.test_root_endpoint():
            print("❌ Root endpoint failed - stopping tests")
            return self.get_results()
        
        # Test empty state
        self.test_get_timesheets_empty()
        
        # Test file validation
        self.test_upload_invalid_file_type()
        
        # Test file upload and processing
        upload_success, timesheet_id = self.test_upload_pdf_timesheet()
        
        if upload_success and timesheet_id:
            # Test getting specific timesheet
            self.test_get_specific_timesheet(timesheet_id)
            
            # Test getting all timesheets with data
            self.test_get_timesheets_with_data()
            
            # Test deletion
            self.test_delete_timesheet(timesheet_id)
        
        # Test deleting non-existent timesheet
        self.test_delete_nonexistent_timesheet()
        
        return self.get_results()

    def get_results(self):
        """Get test results summary"""
        print("\n" + "=" * 60)
        print(f"📊 Test Results: {self.tests_passed}/{self.tests_run} passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed!")
            return 0
        else:
            print("❌ Some tests failed")
            failed_tests = [r for r in self.test_results if not r['success']]
            print("\nFailed tests:")
            for test in failed_tests:
                print(f"  - {test['test']}: {test['details']}")
            return 1

def main():
    tester = TimesheetAPITester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())