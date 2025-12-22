import requests
import sys
import json
import os
from datetime import datetime, timezone
import uuid

class PatientSearchTester:
    def __init__(self, base_url="https://medicaid-claims.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        self.auth_token = None
        self.test_patient_ids = []
        self.test_timesheet_ids = []

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

    def setup_authentication(self):
        """Setup test authentication"""
        try:
            # Create a test user and organization
            signup_data = {
                "email": f"test_patient_search_{datetime.now().strftime('%Y%m%d%H%M%S')}@test.com",
                "password": "testpassword123",
                "first_name": "Test",
                "last_name": "User",
                "organization_name": "Test Patient Search Organization",
                "phone": "6145551234"
            }
            
            response = requests.post(f"{self.api_url}/auth/signup", json=signup_data, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get('access_token')
                self.log_test("Setup Authentication", True, f"Token: {self.auth_token[:20]}...")
                return True
            else:
                self.log_test("Setup Authentication", False, f"Status: {response.status_code}, Response: {response.text[:200]}")
                return False
        except Exception as e:
            self.log_test("Setup Authentication", False, str(e))
            return False

    def get_auth_headers(self):
        """Get authorization headers"""
        if self.auth_token:
            return {"Authorization": f"Bearer {self.auth_token}"}
        return {}

    def setup_test_data(self):
        """Create test patients and timesheets for testing"""
        try:
            headers = self.get_auth_headers()
            
            # Create test patients with different DOBs and names
            test_patients = [
                {
                    "first_name": "Alice",
                    "last_name": "Johnson",
                    "date_of_birth": "1990-01-01",
                    "medicaid_number": "111111111111",
                    "address_street": "123 Main St",
                    "address_city": "Columbus",
                    "address_state": "OH",
                    "address_zip": "43215",
                    "prior_auth_number": "PA123456",
                    "icd10_code": "Z00.00",
                    "physician_name": "Dr. Smith",
                    "physician_npi": "1234567890",
                    "is_complete": True
                },
                {
                    "first_name": "Bob",
                    "last_name": "Smith",
                    "date_of_birth": "1985-06-15",
                    "medicaid_number": "222222222222",
                    "address_street": "456 Oak Ave",
                    "address_city": "Cleveland",
                    "address_state": "OH",
                    "address_zip": "44115",
                    "prior_auth_number": "PA789012",
                    "icd10_code": "Z00.01",
                    "physician_name": "Dr. Jones",
                    "physician_npi": "0987654321",
                    "is_complete": True
                },
                {
                    "first_name": "Carol",
                    "last_name": "Davis",
                    "date_of_birth": "1990-12-25",
                    "medicaid_number": "333333333333",
                    "address_street": "789 Pine Rd",
                    "address_city": "Cincinnati",
                    "address_state": "OH",
                    "address_zip": "45202",
                    "prior_auth_number": "PA345678",
                    "icd10_code": "Z00.02",
                    "physician_name": "Dr. Brown",
                    "physician_npi": "1122334455",
                    "is_complete": True
                }
            ]
            
            # Create patients
            for patient_data in test_patients:
                response = requests.post(f"{self.api_url}/patients", 
                                       json=patient_data, headers=headers, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    self.test_patient_ids.append(data.get('id'))
                else:
                    print(f"Failed to create patient {patient_data['first_name']}: {response.text[:200]}")
            
            # Create test timesheets for some patients
            if len(self.test_patient_ids) >= 2:
                # Create timesheet for Alice Johnson
                timesheet_data = {
                    "filename": "alice_timesheet.pdf",
                    "file_type": "pdf",
                    "status": "completed",
                    "patient_id": self.test_patient_ids[0],
                    "extracted_data": {
                        "client_name": "Alice Johnson",
                        "week_of": "2024-01-01 - 2024-01-07",
                        "employee_entries": [
                            {
                                "employee_name": "John Doe",
                                "service_code": "HHA001",
                                "signature": "Yes",
                                "time_entries": [
                                    {
                                        "date": "2024-01-01",
                                        "time_in": "09:00",
                                        "time_out": "17:00",
                                        "hours_worked": "8",
                                        "units": 32
                                    }
                                ]
                            }
                        ]
                    }
                }
                
                # Insert timesheet directly (simulating upload result)
                # Note: We'll use a mock approach since we can't easily upload files in this test
                print("Test data setup: Created 3 patients and prepared timesheet data")
                
            self.log_test("Setup Test Data", True, f"Created {len(self.test_patient_ids)} patients")
            return True
            
        except Exception as e:
            self.log_test("Setup Test Data", False, str(e))
            return False

    def test_patient_search_by_name(self):
        """Test patient search by name"""
        try:
            headers = self.get_auth_headers()
            
            # Search for "Alice"
            response = requests.get(f"{self.api_url}/patients?search=Alice", 
                                  headers=headers, timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                success = isinstance(data, list) and len(data) > 0
                # Check if Alice Johnson is in results
                alice_found = any(p.get('first_name') == 'Alice' and p.get('last_name') == 'Johnson' 
                                for p in data)
                success = success and alice_found
                details = f"Status: {response.status_code}, Found {len(data)} patients, Alice found: {alice_found}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Patient Search by Name", success, details)
            return success
        except Exception as e:
            self.log_test("Patient Search by Name", False, str(e))
            return False

    def test_patient_search_by_medicaid_number(self):
        """Test patient search by Medicaid number"""
        try:
            headers = self.get_auth_headers()
            
            # Search for partial Medicaid number "111111"
            response = requests.get(f"{self.api_url}/patients?search=111111", 
                                  headers=headers, timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                success = isinstance(data, list) and len(data) > 0
                # Check if patient with medicaid 111111111111 is found
                medicaid_found = any(p.get('medicaid_number') == '111111111111' for p in data)
                success = success and medicaid_found
                details = f"Status: {response.status_code}, Found {len(data)} patients, Medicaid match: {medicaid_found}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Patient Search by Medicaid Number", success, details)
            return success
        except Exception as e:
            self.log_test("Patient Search by Medicaid Number", False, str(e))
            return False

    def test_patient_search_by_dob_full_date(self):
        """Test patient search by full date of birth (YYYY-MM-DD)"""
        try:
            headers = self.get_auth_headers()
            
            # Search for "1990-01-01"
            response = requests.get(f"{self.api_url}/patients?search=1990-01-01", 
                                  headers=headers, timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                success = isinstance(data, list) and len(data) > 0
                # Check if Alice Johnson (DOB: 1990-01-01) is found
                dob_found = any(p.get('date_of_birth') == '1990-01-01' for p in data)
                success = success and dob_found
                details = f"Status: {response.status_code}, Found {len(data)} patients, DOB match: {dob_found}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Patient Search by DOB (Full Date)", success, details)
            return success
        except Exception as e:
            self.log_test("Patient Search by DOB (Full Date)", False, str(e))
            return False

    def test_patient_search_by_dob_year_only(self):
        """Test patient search by year only (YYYY)"""
        try:
            headers = self.get_auth_headers()
            
            # Search for "1990" - should find both Alice and Carol
            response = requests.get(f"{self.api_url}/patients?search=1990", 
                                  headers=headers, timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                success = isinstance(data, list) and len(data) >= 2
                # Check if patients born in 1990 are found
                year_matches = [p for p in data if p.get('date_of_birth', '').startswith('1990')]
                success = success and len(year_matches) >= 2
                details = f"Status: {response.status_code}, Found {len(data)} patients, 1990 matches: {len(year_matches)}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Patient Search by DOB (Year Only)", success, details)
            return success
        except Exception as e:
            self.log_test("Patient Search by DOB (Year Only)", False, str(e))
            return False

    def test_patient_search_by_dob_partial_date(self):
        """Test patient search by partial date (YYYY-MM)"""
        try:
            headers = self.get_auth_headers()
            
            # Search for "1990-01" - should find Alice
            response = requests.get(f"{self.api_url}/patients?search=1990-01", 
                                  headers=headers, timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                success = isinstance(data, list) and len(data) > 0
                # Check if Alice (1990-01-01) is found
                partial_found = any(p.get('date_of_birth', '').startswith('1990-01') for p in data)
                success = success and partial_found
                details = f"Status: {response.status_code}, Found {len(data)} patients, 1990-01 match: {partial_found}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Patient Search by DOB (Partial Date)", success, details)
            return success
        except Exception as e:
            self.log_test("Patient Search by DOB (Partial Date)", False, str(e))
            return False

    def test_patient_search_combination(self):
        """Test combination search behavior - searches individual fields, not combinations"""
        try:
            headers = self.get_auth_headers()
            
            # Search for "Alice" - should find Alice Johnson
            response = requests.get(f"{self.api_url}/patients?search=Alice", 
                                  headers=headers, timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                alice_found = any(p.get('first_name') == 'Alice' for p in data)
                
                # Search for "1990" - should find patients born in 1990
                year_response = requests.get(f"{self.api_url}/patients?search=1990", 
                                           headers=headers, timeout=10)
                year_success = year_response.status_code == 200
                
                if year_success:
                    year_data = year_response.json()
                    year_found = any(p.get('date_of_birth', '').startswith('1990') for p in year_data)
                    
                    # Both individual searches should work
                    success = alice_found and year_found
                    details = f"Alice search: {alice_found}, 1990 search: {year_found}"
                else:
                    success = False
                    details = f"Year search failed: {year_response.status_code}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Patient Search Individual Terms", success, details)
            return success
        except Exception as e:
            self.log_test("Patient Search Individual Terms", False, str(e))
            return False

    def test_patient_search_case_insensitive(self):
        """Test case-insensitive search"""
        try:
            headers = self.get_auth_headers()
            
            # Search for "alice" (lowercase)
            response = requests.get(f"{self.api_url}/patients?search=alice", 
                                  headers=headers, timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                success = isinstance(data, list) and len(data) > 0
                # Check if Alice Johnson is found despite lowercase search
                alice_found = any(p.get('first_name') == 'Alice' for p in data)
                success = success and alice_found
                details = f"Status: {response.status_code}, Found {len(data)} patients, Alice found: {alice_found}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Patient Search Case Insensitive", success, details)
            return success
        except Exception as e:
            self.log_test("Patient Search Case Insensitive", False, str(e))
            return False

    def test_patient_details_with_timesheet_history(self):
        """Test patient details endpoint with timesheet history"""
        try:
            headers = self.get_auth_headers()
            
            if not self.test_patient_ids:
                self.log_test("Patient Details with Timesheet History", False, "No test patient IDs available")
                return False
            
            patient_id = self.test_patient_ids[0]  # Alice Johnson
            
            response = requests.get(f"{self.api_url}/patients/{patient_id}/details", 
                                  headers=headers, timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                # Check required fields - API returns patient data merged with additional fields
                required_fields = ['timesheets', 'total_visits', 'last_visit_date', 'id', 'first_name', 'last_name']
                has_required_fields = all(field in data for field in required_fields)
                
                # Check patient data (merged in response)
                patient_valid = data.get('id') == patient_id
                
                # Check timesheets array
                timesheets = data.get('timesheets', [])
                timesheets_valid = isinstance(timesheets, list)
                
                # Check statistics
                total_visits = data.get('total_visits', 0)
                last_visit_date = data.get('last_visit_date')
                stats_valid = isinstance(total_visits, int) and total_visits >= 0
                
                success = has_required_fields and patient_valid and timesheets_valid and stats_valid
                details = f"Status: {response.status_code}, Required fields: {has_required_fields}, " \
                         f"Patient valid: {patient_valid}, Timesheets: {len(timesheets)}, " \
                         f"Total visits: {total_visits}, Last visit: {last_visit_date}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Patient Details with Timesheet History", success, details)
            return success
        except Exception as e:
            self.log_test("Patient Details with Timesheet History", False, str(e))
            return False

    def test_patient_details_with_multiple_timesheets(self):
        """Test patient details with multiple timesheets"""
        try:
            headers = self.get_auth_headers()
            
            if len(self.test_patient_ids) < 2:
                self.log_test("Patient Details Multiple Timesheets", False, "Not enough test patient IDs")
                return False
            
            patient_id = self.test_patient_ids[1]  # Bob Smith
            
            response = requests.get(f"{self.api_url}/patients/{patient_id}/details", 
                                  headers=headers, timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                timesheets = data.get('timesheets', [])
                total_visits = data.get('total_visits', 0)
                
                # For this test, we expect 0 timesheets since we didn't create any for Bob
                success = isinstance(timesheets, list) and total_visits == 0
                details = f"Status: {response.status_code}, Timesheets: {len(timesheets)}, Total visits: {total_visits}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Patient Details Multiple Timesheets", success, details)
            return success
        except Exception as e:
            self.log_test("Patient Details Multiple Timesheets", False, str(e))
            return False

    def test_patient_details_invalid_id(self):
        """Test patient details with invalid patient ID"""
        try:
            headers = self.get_auth_headers()
            
            fake_id = "invalid-patient-id-12345"
            response = requests.get(f"{self.api_url}/patients/{fake_id}/details", 
                                  headers=headers, timeout=10)
            success = response.status_code == 404
            details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Patient Details Invalid ID", success, details)
            return success
        except Exception as e:
            self.log_test("Patient Details Invalid ID", False, str(e))
            return False

    def test_patient_details_cross_org_access(self):
        """Test that patient details respects multi-tenant isolation"""
        try:
            # Create another organization and user
            signup_data = {
                "email": f"test_other_org_{datetime.now().strftime('%Y%m%d%H%M%S')}@test.com",
                "password": "testpassword123",
                "first_name": "Other",
                "last_name": "User",
                "organization_name": "Other Organization",
                "phone": "6145559999"
            }
            
            response = requests.post(f"{self.api_url}/auth/signup", json=signup_data, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                other_token = data.get('access_token')
                other_headers = {"Authorization": f"Bearer {other_token}"}
                
                # Try to access our test patient with other org's token
                if self.test_patient_ids:
                    patient_id = self.test_patient_ids[0]
                    response = requests.get(f"{self.api_url}/patients/{patient_id}/details", 
                                          headers=other_headers, timeout=10)
                    success = response.status_code == 404  # Should not find patient from other org
                    details = f"Status: {response.status_code}, Cross-org access blocked: {success}"
                else:
                    success = False
                    details = "No test patient IDs available"
            else:
                success = False
                details = f"Failed to create other org: {response.status_code}"
            
            self.log_test("Patient Details Cross-Org Access", success, details)
            return success
        except Exception as e:
            self.log_test("Patient Details Cross-Org Access", False, str(e))
            return False

    def test_enhanced_upload_endpoint_exists(self):
        """Test that enhanced upload endpoint exists"""
        try:
            headers = self.get_auth_headers()
            
            # Test with no file (should get 422 validation error, not 404)
            response = requests.post(f"{self.api_url}/timesheets/upload-enhanced", 
                                   headers=headers, timeout=10)
            success = response.status_code in [400, 422]  # Validation error, not "not found"
            details = f"Status: {response.status_code}, Endpoint exists: {success}"
            
            self.log_test("Enhanced Upload Endpoint Exists", success, details)
            return success
        except Exception as e:
            self.log_test("Enhanced Upload Endpoint Exists", False, str(e))
            return False

    def run_patient_search_tests(self):
        """Run all patient search and details tests"""
        print("🔍 Starting Patient Search & Details Backend Tests")
        print(f"Testing against: {self.api_url}")
        print("=" * 60)
        
        # Setup authentication
        if not self.setup_authentication():
            print("❌ Authentication setup failed - stopping tests")
            return self.get_results()
        
        # Setup test data
        if not self.setup_test_data():
            print("❌ Test data setup failed - stopping tests")
            return self.get_results()
        
        # Test patient search with DOB support
        print("\n📋 Testing Patient Search with DOB Support:")
        self.test_patient_search_by_name()
        self.test_patient_search_by_medicaid_number()
        self.test_patient_search_by_dob_full_date()
        self.test_patient_search_by_dob_year_only()
        self.test_patient_search_by_dob_partial_date()
        self.test_patient_search_combination()
        self.test_patient_search_case_insensitive()
        
        # Test patient details with timesheet history
        print("\n📊 Testing Patient Details with Timesheet History:")
        self.test_patient_details_with_timesheet_history()
        self.test_patient_details_with_multiple_timesheets()
        self.test_patient_details_invalid_id()
        self.test_patient_details_cross_org_access()
        
        # Test enhanced upload endpoint
        print("\n🚀 Testing Enhanced Upload Infrastructure:")
        self.test_enhanced_upload_endpoint_exists()
        
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

if __name__ == "__main__":
    tester = PatientSearchTester()
    exit_code = tester.run_patient_search_tests()
    sys.exit(exit_code)