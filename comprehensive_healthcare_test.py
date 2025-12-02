#!/usr/bin/env python3
"""
Comprehensive Healthcare Timesheet Management API Test Suite

Tests all backend endpoints for:
- Authentication (signup, login)
- Patient management (CRUD)
- Employee management (CRUD)
- Timesheet management (upload, processing)
- Claims connection tests (OMES SOAP, OMES SFTP, Availity)
- Claims management (list)
- Admin endpoints (organizations, system health)
"""

import requests
import json
import uuid
import tempfile
import os
from datetime import datetime, timezone
from typing import Optional, Dict, Any


class HealthcareAPITester:
    def __init__(self, base_url="https://caresheet.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        self.auth_token = None
        self.test_user_email = None
        self.test_organization_id = None
        self.test_patient_id = None
        self.test_employee_id = None
        self.test_timesheet_id = None

    def log_test(self, name: str, success: bool, details: str = ""):
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

    def make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Make authenticated request"""
        headers = kwargs.get('headers', {})
        if self.auth_token:
            headers['Authorization'] = f"Bearer {self.auth_token}"
        kwargs['headers'] = headers
        kwargs['timeout'] = kwargs.get('timeout', 30)
        
        url = f"{self.api_url}{endpoint}"
        return requests.request(method, url, **kwargs)

    # ==================== AUTHENTICATION TESTS ====================
    
    def test_user_signup(self) -> bool:
        """Test user signup endpoint"""
        try:
            # Generate unique test user
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            self.test_user_email = f"test_healthcare_{timestamp}@example.com"
            
            signup_data = {
                "email": self.test_user_email,
                "password": "SecurePassword123!",
                "first_name": "Dr. Sarah",
                "last_name": "Johnson",
                "organization_name": "Johnson Healthcare Services",
                "phone": "614-555-0123"
            }
            
            response = self.make_request('POST', '/auth/signup', json=signup_data)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                self.auth_token = data.get('access_token')
                user_info = data.get('user', {})
                org_info = data.get('organization', {})
                self.test_organization_id = org_info.get('id')
                
                # Verify response structure
                required_fields = ['access_token', 'token_type', 'user', 'organization']
                has_required = all(field in data for field in required_fields)
                success = success and has_required and self.auth_token is not None
                
                details = f"Status: {response.status_code}, Token: {'✓' if self.auth_token else '✗'}, Org ID: {self.test_organization_id}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("User Signup", success, details)
            return success
            
        except Exception as e:
            self.log_test("User Signup", False, str(e))
            return False

    def test_user_login(self) -> bool:
        """Test user login endpoint"""
        try:
            if not self.test_user_email:
                self.log_test("User Login", False, "No test user email available")
                return False
            
            login_data = {
                "email": self.test_user_email,
                "password": "SecurePassword123!"
            }
            
            response = self.make_request('POST', '/auth/login', json=login_data)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                new_token = data.get('access_token')
                
                # Verify response structure
                required_fields = ['access_token', 'token_type', 'user', 'organization']
                has_required = all(field in data for field in required_fields)
                success = success and has_required and new_token is not None
                
                details = f"Status: {response.status_code}, Token received: {'✓' if new_token else '✗'}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("User Login", success, details)
            return success
            
        except Exception as e:
            self.log_test("User Login", False, str(e))
            return False

    def test_invalid_login(self) -> bool:
        """Test login with invalid credentials"""
        try:
            login_data = {
                "email": "invalid@example.com",
                "password": "wrongpassword"
            }
            
            response = self.make_request('POST', '/auth/login', json=login_data)
            success = response.status_code == 401  # Should fail with 401
            
            details = f"Status: {response.status_code} (expected 401)"
            self.log_test("Invalid Login Rejection", success, details)
            return success
            
        except Exception as e:
            self.log_test("Invalid Login Rejection", False, str(e))
            return False

    # ==================== PATIENT MANAGEMENT TESTS ====================
    
    def test_create_patient(self) -> bool:
        """Test creating a patient"""
        try:
            if not self.auth_token:
                self.log_test("Create Patient", False, "No authentication token")
                return False
            
            patient_data = {
                "first_name": "Maria",
                "last_name": "Rodriguez",
                "sex": "Female",
                "date_of_birth": "1985-03-15",
                "address_street": "123 Healthcare Ave",
                "address_city": "Columbus",
                "address_state": "OH",
                "address_zip": "43215",
                "address_latitude": 39.9612,
                "address_longitude": -82.9988,
                "timezone": "America/New_York",
                "prior_auth_number": "PA123456789",
                "icd10_code": "Z51.11",
                "icd10_description": "Encounter for antineoplastic chemotherapy",
                "physician_name": "Dr. Robert Smith",
                "physician_npi": "1234567890",
                "medicaid_number": "123456789012",
                "patient_other_id": "PAT001",
                "phone_numbers": [
                    {
                        "phone_type": "Mobile",
                        "phone_number": "6145551234",
                        "is_primary": True
                    }
                ]
            }
            
            response = self.make_request('POST', '/patients', json=patient_data)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                self.test_patient_id = data.get('id')
                
                # Verify required fields
                required_fields = ['id', 'first_name', 'last_name', 'medicaid_number']
                has_required = all(field in data for field in required_fields)
                success = success and has_required and self.test_patient_id is not None
                
                details = f"Status: {response.status_code}, Patient ID: {self.test_patient_id}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Create Patient", success, details)
            return success
            
        except Exception as e:
            self.log_test("Create Patient", False, str(e))
            return False

    def test_list_patients(self) -> bool:
        """Test listing patients"""
        try:
            if not self.auth_token:
                self.log_test("List Patients", False, "No authentication token")
                return False
            
            response = self.make_request('GET', '/patients')
            success = response.status_code == 200
            
            if success:
                data = response.json()
                success = isinstance(data, list)
                patient_count = len(data) if isinstance(data, list) else 0
                details = f"Status: {response.status_code}, Patient count: {patient_count}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("List Patients", success, details)
            return success
            
        except Exception as e:
            self.log_test("List Patients", False, str(e))
            return False

    def test_get_patient(self) -> bool:
        """Test getting specific patient"""
        try:
            if not self.auth_token or not self.test_patient_id:
                self.log_test("Get Patient", False, "No auth token or patient ID")
                return False
            
            response = self.make_request('GET', f'/patients/{self.test_patient_id}')
            success = response.status_code == 200
            
            if success:
                data = response.json()
                required_fields = ['id', 'first_name', 'last_name']
                has_required = all(field in data for field in required_fields)
                success = success and has_required
                details = f"Status: {response.status_code}, Patient: {data.get('first_name')} {data.get('last_name')}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Get Patient", success, details)
            return success
            
        except Exception as e:
            self.log_test("Get Patient", False, str(e))
            return False

    # ==================== EMPLOYEE MANAGEMENT TESTS ====================
    
    def test_create_employee(self) -> bool:
        """Test creating an employee"""
        try:
            if not self.auth_token:
                self.log_test("Create Employee", False, "No authentication token")
                return False
            
            employee_data = {
                "first_name": "John",
                "last_name": "Smith",
                "ssn": "123-45-6789",
                "date_of_birth": "1990-05-20",
                "sex": "Male",
                "email": "john.smith@healthcare.com",
                "phone": "6145559876",
                "address_street": "456 Oak Avenue",
                "address_city": "Columbus",
                "address_state": "OH",
                "address_zip": "43215",
                "employee_id": "EMP001",
                "hire_date": "2023-01-15",
                "job_title": "Home Health Aide",
                "employment_status": "Full-time",
                "staff_pin": "123456789",
                "staff_other_id": "STAFF001",
                "staff_position": "HHA",
                "emergency_contact_name": "Jane Smith",
                "emergency_contact_phone": "6145555555",
                "emergency_contact_relation": "Spouse"
            }
            
            response = self.make_request('POST', '/employees', json=employee_data)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                self.test_employee_id = data.get('id')
                
                # Verify required fields
                required_fields = ['id', 'first_name', 'last_name', 'employee_id']
                has_required = all(field in data for field in required_fields)
                success = success and has_required and self.test_employee_id is not None
                
                details = f"Status: {response.status_code}, Employee ID: {self.test_employee_id}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Create Employee", success, details)
            return success
            
        except Exception as e:
            self.log_test("Create Employee", False, str(e))
            return False

    def test_list_employees(self) -> bool:
        """Test listing employees"""
        try:
            if not self.auth_token:
                self.log_test("List Employees", False, "No authentication token")
                return False
            
            response = self.make_request('GET', '/employees')
            success = response.status_code == 200
            
            if success:
                data = response.json()
                success = isinstance(data, list)
                employee_count = len(data) if isinstance(data, list) else 0
                details = f"Status: {response.status_code}, Employee count: {employee_count}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("List Employees", success, details)
            return success
            
        except Exception as e:
            self.log_test("List Employees", False, str(e))
            return False

    # ==================== TIMESHEET MANAGEMENT TESTS ====================
    
    def test_list_timesheets(self) -> bool:
        """Test listing timesheets"""
        try:
            if not self.auth_token:
                self.log_test("List Timesheets", False, "No authentication token")
                return False
            
            response = self.make_request('GET', '/timesheets')
            success = response.status_code == 200
            
            if success:
                data = response.json()
                success = isinstance(data, list)
                timesheet_count = len(data) if isinstance(data, list) else 0
                details = f"Status: {response.status_code}, Timesheet count: {timesheet_count}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("List Timesheets", success, details)
            return success
            
        except Exception as e:
            self.log_test("List Timesheets", False, str(e))
            return False

    def create_test_timesheet_file(self) -> str:
        """Create a test timesheet file"""
        try:
            test_content = """HEALTHCARE TIMESHEET
Patient: Maria Rodriguez
Employee: John Smith
Date: 2024-01-15
Time In: 9:00 AM
Time Out: 5:00 PM
Hours: 8
Service Code: HHA001
Signature: [Signed]"""
            
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf', mode='w')
            temp_file.write(test_content)
            temp_file.close()
            return temp_file.name
        except Exception as e:
            print(f"Error creating test file: {e}")
            return None

    def test_upload_timesheet(self) -> bool:
        """Test uploading a timesheet"""
        try:
            if not self.auth_token:
                self.log_test("Upload Timesheet", False, "No authentication token")
                return False
            
            test_file = self.create_test_timesheet_file()
            if not test_file:
                self.log_test("Upload Timesheet", False, "Could not create test file")
                return False
            
            with open(test_file, 'rb') as f:
                files = {'file': ('healthcare_timesheet.pdf', f, 'application/pdf')}
                response = self.make_request('POST', '/timesheets/upload', files=files)
            
            success = response.status_code == 200
            
            if success:
                try:
                    data = response.json()
                    self.test_timesheet_id = data.get('id')
                    has_required_fields = all(key in data for key in ['id', 'filename', 'status'])
                    success = success and has_required_fields
                    details = f"Status: {response.status_code}, ID: {self.test_timesheet_id}, Status: {data.get('status')}"
                except json.JSONDecodeError:
                    success = False
                    details = f"Status: {response.status_code}, Invalid JSON response"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            # Cleanup
            os.unlink(test_file)
            
            self.log_test("Upload Timesheet", success, details)
            return success
            
        except Exception as e:
            self.log_test("Upload Timesheet", False, str(e))
            return False

    # ==================== CLAIMS CONNECTION TESTS ====================
    
    def test_omes_soap_connection(self) -> bool:
        """Test OMES SOAP connection"""
        try:
            if not self.auth_token:
                self.log_test("OMES SOAP Connection", False, "No authentication token")
                return False
            
            response = self.make_request('GET', '/claims/test/omes-soap')
            success = response.status_code == 200
            
            if success:
                data = response.json()
                has_success_field = 'success' in data
                details = f"Status: {response.status_code}, Success: {data.get('success')}, Message: {data.get('message', 'N/A')[:50]}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("OMES SOAP Connection Test", success, details)
            return success
            
        except Exception as e:
            self.log_test("OMES SOAP Connection Test", False, str(e))
            return False

    def test_omes_sftp_connection(self) -> bool:
        """Test OMES SFTP connection"""
        try:
            if not self.auth_token:
                self.log_test("OMES SFTP Connection", False, "No authentication token")
                return False
            
            response = self.make_request('GET', '/claims/test/omes-sftp')
            success = response.status_code == 200
            
            if success:
                data = response.json()
                has_success_field = 'success' in data
                details = f"Status: {response.status_code}, Success: {data.get('success')}, Message: {data.get('message', 'N/A')[:50]}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("OMES SFTP Connection Test", success, details)
            return success
            
        except Exception as e:
            self.log_test("OMES SFTP Connection Test", False, str(e))
            return False

    def test_availity_connection(self) -> bool:
        """Test Availity connection"""
        try:
            if not self.auth_token:
                self.log_test("Availity Connection", False, "No authentication token")
                return False
            
            response = self.make_request('GET', '/claims/test/availity')
            success = response.status_code == 200
            
            if success:
                data = response.json()
                has_success_field = 'success' in data
                details = f"Status: {response.status_code}, Success: {data.get('success')}, Message: {data.get('message', 'N/A')[:50]}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Availity Connection Test", success, details)
            return success
            
        except Exception as e:
            self.log_test("Availity Connection Test", False, str(e))
            return False

    def test_list_claims(self) -> bool:
        """Test listing claims"""
        try:
            if not self.auth_token:
                self.log_test("List Claims", False, "No authentication token")
                return False
            
            response = self.make_request('GET', '/claims/list')
            success = response.status_code == 200
            
            if success:
                data = response.json()
                has_success_field = 'success' in data and data.get('success') == True
                claims_count = len(data.get('claims', [])) if 'claims' in data else 0
                details = f"Status: {response.status_code}, Success: {has_success_field}, Claims count: {claims_count}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("List Claims", success, details)
            return success
            
        except Exception as e:
            self.log_test("List Claims", False, str(e))
            return False

    # ==================== ADMIN ENDPOINT TESTS ====================
    
    def test_admin_organizations_unauthorized(self) -> bool:
        """Test admin organizations endpoint without admin role (should fail)"""
        try:
            if not self.auth_token:
                self.log_test("Admin Organizations (Unauthorized)", False, "No authentication token")
                return False
            
            response = self.make_request('GET', '/admin/organizations')
            success = response.status_code == 403  # Should be forbidden for non-admin users
            
            details = f"Status: {response.status_code} (expected 403 for non-admin user)"
            self.log_test("Admin Organizations Access Control", success, details)
            return success
            
        except Exception as e:
            self.log_test("Admin Organizations Access Control", False, str(e))
            return False

    def test_system_health_unauthorized(self) -> bool:
        """Test system health endpoint without admin role (should fail)"""
        try:
            if not self.auth_token:
                self.log_test("System Health (Unauthorized)", False, "No authentication token")
                return False
            
            response = self.make_request('GET', '/admin/system/health')
            success = response.status_code == 403  # Should be forbidden for non-admin users
            
            details = f"Status: {response.status_code} (expected 403 for non-admin user)"
            self.log_test("System Health Access Control", success, details)
            return success
            
        except Exception as e:
            self.log_test("System Health Access Control", False, str(e))
            return False

    # ==================== ERROR HANDLING TESTS ====================
    
    def test_invalid_endpoints(self) -> bool:
        """Test invalid endpoints return proper errors"""
        try:
            response = self.make_request('GET', '/nonexistent-endpoint')
            success = response.status_code == 404
            
            details = f"Status: {response.status_code} (expected 404)"
            self.log_test("Invalid Endpoint Handling", success, details)
            return success
            
        except Exception as e:
            self.log_test("Invalid Endpoint Handling", False, str(e))
            return False

    def test_unauthorized_access(self) -> bool:
        """Test endpoints that require authentication"""
        try:
            # Test claims eligibility endpoint which requires get_current_user
            headers = {}
            eligibility_data = {
                "member_id": "123456789012",
                "first_name": "Test",
                "last_name": "Patient",
                "date_of_birth": "1990-01-01",
                "provider_npi": "1234567890"
            }
            response = requests.post(f"{self.api_url}/claims/eligibility/verify", 
                                   json=eligibility_data, headers=headers, timeout=30)
            success = response.status_code == 401  # Should be unauthorized
            
            # Log actual response for debugging
            response_text = response.text[:200] if response.text else "No response body"
            details = f"Status: {response.status_code} (expected 401), Response: {response_text}"
            self.log_test("Unauthorized Access Handling", success, details)
            return success
            
        except Exception as e:
            self.log_test("Unauthorized Access Handling", False, str(e))
            return False

    # ==================== MAIN TEST RUNNER ====================
    
    def run_comprehensive_tests(self) -> int:
        """Run all healthcare API tests"""
        print("🏥 Starting Comprehensive Healthcare Timesheet API Tests")
        print(f"Testing against: {self.api_url}")
        print("=" * 80)
        
        # Test basic connectivity
        try:
            response = requests.get(f"{self.api_url}/", timeout=10)
            if response.status_code != 200:
                print("❌ Root endpoint failed - stopping tests")
                return 1
            print("✅ Root endpoint connectivity - PASSED")
        except Exception as e:
            print(f"❌ Root endpoint failed: {e}")
            return 1
        
        # 1. Authentication Tests
        print("\n🔐 Authentication Tests")
        print("-" * 40)
        if not self.test_user_signup():
            print("❌ Signup failed - stopping tests")
            return 1
        
        self.test_user_login()
        self.test_invalid_login()
        
        # 2. Patient Management Tests
        print("\n👥 Patient Management Tests")
        print("-" * 40)
        self.test_create_patient()
        self.test_list_patients()
        self.test_get_patient()
        
        # 3. Employee Management Tests
        print("\n👨‍⚕️ Employee Management Tests")
        print("-" * 40)
        self.test_create_employee()
        self.test_list_employees()
        
        # 4. Timesheet Management Tests
        print("\n📋 Timesheet Management Tests")
        print("-" * 40)
        self.test_list_timesheets()
        self.test_upload_timesheet()
        
        # 5. Claims Connection Tests
        print("\n🏥 Claims Connection Tests")
        print("-" * 40)
        self.test_omes_soap_connection()
        self.test_omes_sftp_connection()
        self.test_availity_connection()
        self.test_list_claims()
        
        # 6. Admin Endpoint Tests
        print("\n🔧 Admin Endpoint Tests")
        print("-" * 40)
        self.test_admin_organizations_unauthorized()
        self.test_system_health_unauthorized()
        
        # 7. Error Handling Tests
        print("\n⚠️ Error Handling Tests")
        print("-" * 40)
        self.test_invalid_endpoints()
        self.test_unauthorized_access()
        
        return self.get_results()

    def get_results(self) -> int:
        """Get test results summary"""
        print("\n" + "=" * 80)
        print(f"📊 Healthcare API Test Results: {self.tests_passed}/{self.tests_run} passed")
        
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
    tester = HealthcareAPITester()
    exit_code = tester.run_comprehensive_tests()
    exit(exit_code)