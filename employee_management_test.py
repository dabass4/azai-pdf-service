import requests
import json
import sys
from datetime import datetime

class EmployeeManagementTester:
    def __init__(self, base_url="https://medstaff-portal-27.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        self.auth_token = None
        self.created_employee_id = None

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

    def authenticate_admin(self):
        """Authenticate with admin credentials"""
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
                self.log_test("Admin Authentication", success, details)
                return success
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
                self.log_test("Admin Authentication", False, details)
                return False
        except Exception as e:
            self.log_test("Admin Authentication", False, str(e))
            return False

    def get_auth_headers(self):
        """Get authorization headers"""
        if self.auth_token:
            return {"Authorization": f"Bearer {self.auth_token}"}
        return {}

    def test_employee_create_with_categories(self):
        """Test creating new employee with categories field"""
        try:
            employee_data = {
                "first_name": "Sarah",
                "last_name": "Johnson",
                "middle_name": "Marie",
                "ssn": "123-45-6789",
                "date_of_birth": "1990-05-15",
                "sex": "Female",
                "email": "sarah.johnson@test.com",
                "phone": "6145551234",
                "address_street": "123 Main Street",
                "address_city": "Columbus",
                "address_state": "OH",
                "address_zip": "43215",
                "employee_id": "EMP001",
                "hire_date": "2024-01-15",
                "job_title": "Registered Nurse",
                "employment_status": "Full-time",
                "categories": ["RN", "HHA"],  # Test categories field
                "is_complete": True
            }
            
            headers = self.get_auth_headers()
            response = requests.post(f"{self.api_url}/employees", 
                                   json=employee_data, 
                                   headers=headers,
                                   timeout=10)
            
            success = response.status_code == 200
            
            if success:
                try:
                    data = response.json()
                    self.created_employee_id = data.get('id')
                    
                    # Verify categories field is present and correct
                    returned_categories = data.get('categories', [])
                    categories_correct = set(returned_categories) == set(["RN", "HHA"])
                    
                    # Verify no certification fields are present
                    has_cert_fields = any(field in data for field in ['certifications', 'license_number', 'license_expiration'])
                    
                    success = success and categories_correct and not has_cert_fields
                    details = f"Status: {response.status_code}, Employee ID: {self.created_employee_id}, Categories: {returned_categories}, Has cert fields: {has_cert_fields}"
                except json.JSONDecodeError:
                    success = False
                    details = f"Status: {response.status_code}, Invalid JSON response"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:300]}"
            
            self.log_test("Employee Create with Categories", success, details)
            return success
        except Exception as e:
            self.log_test("Employee Create with Categories", False, str(e))
            return False

    def test_employee_update_with_categories(self):
        """Test updating employee with categories field"""
        if not self.created_employee_id:
            self.log_test("Employee Update with Categories", False, "No employee ID available for update")
            return False
        
        try:
            update_data = {
                "first_name": "Sarah",
                "last_name": "Johnson-Smith",  # Changed last name
                "categories": ["RN", "LPN", "DSP"],  # Updated categories
                "job_title": "Senior Registered Nurse",  # Updated title
                "employment_status": "Full-time"
            }
            
            headers = self.get_auth_headers()
            response = requests.put(f"{self.api_url}/employees/{self.created_employee_id}", 
                                  json=update_data, 
                                  headers=headers,
                                  timeout=10)
            
            success = response.status_code == 200
            
            if success:
                try:
                    data = response.json()
                    
                    # Verify categories field is updated correctly
                    returned_categories = data.get('categories', [])
                    categories_correct = set(returned_categories) == set(["RN", "LPN", "DSP"])
                    
                    # Verify other fields are updated
                    last_name_updated = data.get('last_name') == "Johnson-Smith"
                    job_title_updated = data.get('job_title') == "Senior Registered Nurse"
                    
                    # Verify no certification fields are present
                    has_cert_fields = any(field in data for field in ['certifications', 'license_number', 'license_expiration'])
                    
                    success = success and categories_correct and last_name_updated and job_title_updated and not has_cert_fields
                    details = f"Status: {response.status_code}, Categories: {returned_categories}, Last name: {data.get('last_name')}, Job title: {data.get('job_title')}, Has cert fields: {has_cert_fields}"
                except json.JSONDecodeError:
                    success = False
                    details = f"Status: {response.status_code}, Invalid JSON response"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:300]}"
            
            self.log_test("Employee Update with Categories", success, details)
            return success
        except Exception as e:
            self.log_test("Employee Update with Categories", False, str(e))
            return False

    def test_employee_get_after_update(self):
        """Test getting employee after update to verify changes persisted"""
        if not self.created_employee_id:
            self.log_test("Employee Get After Update", False, "No employee ID available")
            return False
        
        try:
            headers = self.get_auth_headers()
            response = requests.get(f"{self.api_url}/employees/{self.created_employee_id}", 
                                  headers=headers,
                                  timeout=10)
            
            success = response.status_code == 200
            
            if success:
                try:
                    data = response.json()
                    
                    # Verify categories field persisted correctly
                    returned_categories = data.get('categories', [])
                    categories_correct = set(returned_categories) == set(["RN", "LPN", "DSP"])
                    
                    # Verify other updated fields persisted
                    last_name_correct = data.get('last_name') == "Johnson-Smith"
                    job_title_correct = data.get('job_title') == "Senior Registered Nurse"
                    
                    # Verify no certification fields are present
                    has_cert_fields = any(field in data for field in ['certifications', 'license_number', 'license_expiration'])
                    
                    success = success and categories_correct and last_name_correct and job_title_correct and not has_cert_fields
                    details = f"Status: {response.status_code}, Categories persisted: {categories_correct}, Last name: {last_name_correct}, Job title: {job_title_correct}, Has cert fields: {has_cert_fields}"
                except json.JSONDecodeError:
                    success = False
                    details = f"Status: {response.status_code}, Invalid JSON response"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:300]}"
            
            self.log_test("Employee Get After Update", success, details)
            return success
        except Exception as e:
            self.log_test("Employee Get After Update", False, str(e))
            return False

    def test_employee_list_categories_display(self):
        """Test listing employees to verify categories are displayed correctly"""
        try:
            headers = self.get_auth_headers()
            response = requests.get(f"{self.api_url}/employees", 
                                  headers=headers,
                                  timeout=10)
            
            success = response.status_code == 200
            
            if success:
                try:
                    data = response.json()
                    
                    if isinstance(data, list) and len(data) > 0:
                        # Find our created employee
                        our_employee = None
                        for emp in data:
                            if emp.get('id') == self.created_employee_id:
                                our_employee = emp
                                break
                        
                        if our_employee:
                            # Verify categories field is present in list view
                            has_categories = 'categories' in our_employee
                            categories_correct = set(our_employee.get('categories', [])) == set(["RN", "LPN", "DSP"])
                            
                            # Verify no certification fields in list view
                            has_cert_fields = any(field in our_employee for field in ['certifications', 'license_number', 'license_expiration'])
                            
                            success = has_categories and categories_correct and not has_cert_fields
                            details = f"Status: {response.status_code}, Employee found: True, Has categories: {has_categories}, Categories correct: {categories_correct}, Has cert fields: {has_cert_fields}"
                        else:
                            success = False
                            details = f"Status: {response.status_code}, Employee not found in list"
                    else:
                        success = False
                        details = f"Status: {response.status_code}, No employees in list or invalid response format"
                except json.JSONDecodeError:
                    success = False
                    details = f"Status: {response.status_code}, Invalid JSON response"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:300]}"
            
            self.log_test("Employee List Categories Display", success, details)
            return success
        except Exception as e:
            self.log_test("Employee List Categories Display", False, str(e))
            return False

    def test_employee_update_invalid_categories(self):
        """Test updating employee with invalid categories to verify validation"""
        if not self.created_employee_id:
            self.log_test("Employee Update Invalid Categories", False, "No employee ID available")
            return False
        
        try:
            update_data = {
                "categories": ["INVALID", "CATEGORY"]  # Invalid categories
            }
            
            headers = self.get_auth_headers()
            response = requests.put(f"{self.api_url}/employees/{self.created_employee_id}", 
                                  json=update_data, 
                                  headers=headers,
                                  timeout=10)
            
            # Should either accept any string values or return validation error
            # For now, we'll accept either 200 (accepts any values) or 422 (validation error)
            success = response.status_code in [200, 422]
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    returned_categories = data.get('categories', [])
                    details = f"Status: {response.status_code}, Accepted invalid categories: {returned_categories}"
                except json.JSONDecodeError:
                    details = f"Status: {response.status_code}, Invalid JSON response"
            elif response.status_code == 422:
                details = f"Status: {response.status_code}, Validation error (expected): {response.text[:200]}"
            else:
                success = False
                details = f"Status: {response.status_code}, Unexpected response: {response.text[:200]}"
            
            self.log_test("Employee Update Invalid Categories", success, details)
            return success
        except Exception as e:
            self.log_test("Employee Update Invalid Categories", False, str(e))
            return False

    def cleanup_test_employee(self):
        """Clean up test employee"""
        if not self.created_employee_id:
            return True
        
        try:
            headers = self.get_auth_headers()
            response = requests.delete(f"{self.api_url}/employees/{self.created_employee_id}", 
                                     headers=headers,
                                     timeout=10)
            
            success = response.status_code in [200, 404]  # 404 is OK if already deleted
            details = f"Status: {response.status_code}"
            
            self.log_test("Cleanup Test Employee", success, details)
            return success
        except Exception as e:
            self.log_test("Cleanup Test Employee", False, str(e))
            return False

    def run_employee_management_tests(self):
        """Run all employee management tests"""
        print("🏥 Starting Employee Management API Tests")
        print(f"Testing against: {self.api_url}")
        print("=" * 60)
        
        # Step 1: Authenticate
        if not self.authenticate_admin():
            print("❌ Authentication failed - stopping tests")
            return self.get_results()
        
        # Step 2: Test employee creation with categories
        self.test_employee_create_with_categories()
        
        # Step 3: Test employee update with categories (should not return 422 error)
        self.test_employee_update_with_categories()
        
        # Step 4: Test getting employee after update
        self.test_employee_get_after_update()
        
        # Step 5: Test employee list view
        self.test_employee_list_categories_display()
        
        # Step 6: Test invalid categories validation
        self.test_employee_update_invalid_categories()
        
        # Step 7: Cleanup
        self.cleanup_test_employee()
        
        return self.get_results()

    def get_results(self):
        """Get test results summary"""
        print("\n" + "=" * 60)
        print(f"📊 Employee Management Test Results: {self.tests_passed}/{self.tests_run} passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All employee management tests passed!")
            return 0
        else:
            print("❌ Some employee management tests failed")
            failed_tests = [r for r in self.test_results if not r['success']]
            print("\nFailed tests:")
            for test in failed_tests:
                print(f"  - {test['test']}: {test['details']}")
            return 1

if __name__ == "__main__":
    tester = EmployeeManagementTester()
    exit_code = tester.run_employee_management_tests()
    sys.exit(exit_code)