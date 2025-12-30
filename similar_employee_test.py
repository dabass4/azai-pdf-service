#!/usr/bin/env python3
"""
Similar Employee Suggestion Feature Test
Tests the fuzzy matching and employee linking functionality for timesheet scanning workflow.
"""

import requests
import json
import sys
from datetime import datetime, timezone

class SimilarEmployeeFeatureTester:
    def __init__(self, base_url="https://claim-tracker-21.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        self.auth_token = None
        self.test_organization_id = None
        self.created_employees = []  # Track created employees for cleanup

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
                self.test_organization_id = data.get('organization_id')
                self.log_test("Admin Authentication", True, f"Successfully authenticated")
                return True
            else:
                self.log_test("Admin Authentication", False, f"Status: {response.status_code}, Response: {response.text[:200]}")
                return False
        except Exception as e:
            self.log_test("Admin Authentication", False, str(e))
            return False

    def get_auth_headers(self):
        """Get authorization headers for authenticated requests"""
        if self.auth_token:
            return {"Authorization": f"Bearer {self.auth_token}"}
        return {}

    def create_test_employee(self, first_name, last_name, email_suffix="", categories=None):
        """Create a test employee and track for cleanup"""
        try:
            if categories is None:
                categories = ["HHA"]
                
            employee_data = {
                "first_name": first_name,
                "last_name": last_name,
                "email": f"{first_name.lower()}.{last_name.lower()}{email_suffix}@test.com",
                "phone": "6145551234",
                "ssn": "123-45-6789",
                "date_of_birth": "1990-01-01",
                "sex": "Male",
                "categories": categories,
                "is_complete": True
            }
            
            headers = self.get_auth_headers()
            response = requests.post(f"{self.api_url}/employees", json=employee_data, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                employee_id = data.get('id')
                self.created_employees.append(employee_id)
                return employee_id, f"{first_name} {last_name}"
            else:
                print(f"Failed to create employee {first_name} {last_name}: {response.status_code} - {response.text[:200]}")
                return None, None
        except Exception as e:
            print(f"Error creating employee {first_name} {last_name}: {e}")
            return None, None

    def test_similar_employee_exact_match(self):
        """Test 1: Search for exact name match should return 100% similarity"""
        try:
            # Create a test employee
            emp_id, emp_name = self.create_test_employee("Test", "Employee")
            if not emp_id:
                self.log_test("Similar Employee - Exact Match", False, "Failed to create test employee")
                return False

            # Search for exact match
            headers = self.get_auth_headers()
            response = requests.get(f"{self.api_url}/employees/similar/Test Employee", headers=headers, timeout=10)
            
            success = response.status_code == 200
            
            if success:
                data = response.json()
                
                # Verify response structure
                required_fields = ['search_name', 'similar_employees', 'total_found', 'has_exact_match', 'has_close_match']
                has_required_fields = all(field in data for field in required_fields)
                
                if has_required_fields:
                    search_name = data.get('search_name')
                    similar_employees = data.get('similar_employees', [])
                    has_exact_match = data.get('has_exact_match')
                    
                    # Should find the exact match
                    found_exact = len(similar_employees) > 0 and has_exact_match
                    
                    if found_exact:
                        # Check first result
                        first_result = similar_employees[0]
                        expected_fields = ['id', 'first_name', 'last_name', 'full_name', 'categories', 'is_complete', 'similarity_score', 'match_type']
                        has_employee_fields = all(field in first_result for field in expected_fields)
                        
                        # Should be 100% similarity for exact match
                        similarity_score = first_result.get('similarity_score', 0)
                        is_exact_score = similarity_score >= 0.95
                        match_type = first_result.get('match_type')
                        is_exact_type = match_type == "exact"
                        
                        success = has_employee_fields and is_exact_score and is_exact_type
                        details = f"Status: {response.status_code}, Found: {len(similar_employees)}, " \
                                f"Exact match: {has_exact_match}, Score: {similarity_score}, Type: {match_type}"
                    else:
                        success = False
                        details = f"Status: {response.status_code}, No exact match found for 'Test Employee'"
                else:
                    success = False
                    details = f"Status: {response.status_code}, Missing required fields: {[f for f in required_fields if f not in data]}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Similar Employee - Exact Match", success, details)
            return success
        except Exception as e:
            self.log_test("Similar Employee - Exact Match", False, str(e))
            return False

    def test_similar_employee_fuzzy_match(self):
        """Test 2: Search for fuzzy match (Jon Smith should find John Smith)"""
        try:
            # Create John Smith
            emp_id, emp_name = self.create_test_employee("John", "Smith")
            if not emp_id:
                self.log_test("Similar Employee - Fuzzy Match", False, "Failed to create test employee")
                return False

            # Search for "Jon Smith" (typo)
            headers = self.get_auth_headers()
            response = requests.get(f"{self.api_url}/employees/similar/Jon Smith", headers=headers, timeout=10)
            
            success = response.status_code == 200
            
            if success:
                data = response.json()
                
                # Verify response structure
                similar_employees = data.get('similar_employees', [])
                has_close_match = data.get('has_close_match')
                
                # Should find John Smith with high similarity
                found_match = len(similar_employees) > 0
                
                if found_match:
                    # Check if John Smith is in results
                    john_smith_found = False
                    best_score = 0
                    best_match_type = None
                    
                    for emp in similar_employees:
                        full_name = emp.get('full_name', '')
                        if 'John Smith' in full_name:
                            john_smith_found = True
                            best_score = emp.get('similarity_score', 0)
                            best_match_type = emp.get('match_type')
                            break
                    
                    # Should find John Smith with 85-90% similarity
                    good_similarity = best_score >= 0.8 and best_score < 0.95
                    correct_type = best_match_type == "similar"
                    
                    success = john_smith_found and good_similarity and correct_type
                    details = f"Status: {response.status_code}, Found John Smith: {john_smith_found}, " \
                            f"Score: {best_score}, Type: {best_match_type}, Close match flag: {has_close_match}"
                else:
                    success = False
                    details = f"Status: {response.status_code}, No similar employees found for 'Jon Smith'"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Similar Employee - Fuzzy Match", success, details)
            return success
        except Exception as e:
            self.log_test("Similar Employee - Fuzzy Match", False, str(e))
            return False

    def test_similar_employee_partial_name(self):
        """Test 3: Search for partial name (Smith should find Jane Smith)"""
        try:
            # Create Jane Smith
            emp_id, emp_name = self.create_test_employee("Jane", "Smith")
            if not emp_id:
                self.log_test("Similar Employee - Partial Name", False, "Failed to create test employee")
                return False

            # Search for just "Smith"
            headers = self.get_auth_headers()
            response = requests.get(f"{self.api_url}/employees/similar/Smith", headers=headers, timeout=10)
            
            success = response.status_code == 200
            
            if success:
                data = response.json()
                
                similar_employees = data.get('similar_employees', [])
                
                # Should find Jane Smith
                found_match = len(similar_employees) > 0
                
                if found_match:
                    # Check if Jane Smith is in results
                    jane_smith_found = False
                    best_score = 0
                    
                    for emp in similar_employees:
                        full_name = emp.get('full_name', '')
                        if 'Jane Smith' in full_name:
                            jane_smith_found = True
                            best_score = emp.get('similarity_score', 0)
                            break
                    
                    # Should find with reasonable similarity
                    reasonable_similarity = best_score >= 0.5
                    
                    success = jane_smith_found and reasonable_similarity
                    details = f"Status: {response.status_code}, Found Jane Smith: {jane_smith_found}, " \
                            f"Score: {best_score}, Total found: {len(similar_employees)}"
                else:
                    success = False
                    details = f"Status: {response.status_code}, No similar employees found for 'Smith'"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Similar Employee - Partial Name", success, details)
            return success
        except Exception as e:
            self.log_test("Similar Employee - Partial Name", False, str(e))
            return False

    def test_similar_employee_typo_match(self):
        """Test 4: Search for name with typo (Jane Smyth should find Jane Smith)"""
        try:
            # Create Jane Smith (if not already created)
            emp_id, emp_name = self.create_test_employee("Jane", "Smith", "_typo_test")
            if not emp_id:
                self.log_test("Similar Employee - Typo Match", False, "Failed to create test employee")
                return False

            # Search for "Jane Smyth" (typo in last name)
            headers = self.get_auth_headers()
            response = requests.get(f"{self.api_url}/employees/similar/Jane Smyth", headers=headers, timeout=10)
            
            success = response.status_code == 200
            
            if success:
                data = response.json()
                
                similar_employees = data.get('similar_employees', [])
                
                # Should find Jane Smith
                found_match = len(similar_employees) > 0
                
                if found_match:
                    # Check if Jane Smith is in results
                    jane_smith_found = False
                    best_score = 0
                    
                    for emp in similar_employees:
                        full_name = emp.get('full_name', '')
                        if 'Jane Smith' in full_name:
                            jane_smith_found = True
                            best_score = emp.get('similarity_score', 0)
                            break
                    
                    # Should find with ~80% similarity
                    good_similarity = best_score >= 0.7 and best_score <= 0.9
                    
                    success = jane_smith_found and good_similarity
                    details = f"Status: {response.status_code}, Found Jane Smith: {jane_smith_found}, " \
                            f"Score: {best_score}, Total found: {len(similar_employees)}"
                else:
                    success = False
                    details = f"Status: {response.status_code}, No similar employees found for 'Jane Smyth'"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Similar Employee - Typo Match", success, details)
            return success
        except Exception as e:
            self.log_test("Similar Employee - Typo Match", False, str(e))
            return False

    def test_similarity_scores_ranking(self):
        """Test 5: Verify similarity scores make sense and are ranked properly"""
        try:
            # Create multiple employees with varying similarity to "John Smith"
            john_id, _ = self.create_test_employee("John", "Smith", "_exact")
            jon_id, _ = self.create_test_employee("Jon", "Smith", "_close")
            johnny_id, _ = self.create_test_employee("Johnny", "Smith", "_partial")
            jane_id, _ = self.create_test_employee("Jane", "Doe", "_different")
            
            if not all([john_id, jon_id, johnny_id, jane_id]):
                self.log_test("Similarity Scores - Ranking", False, "Failed to create test employees")
                return False

            # Search for "John Smith"
            headers = self.get_auth_headers()
            response = requests.get(f"{self.api_url}/employees/similar/John Smith", headers=headers, timeout=10)
            
            success = response.status_code == 200
            
            if success:
                data = response.json()
                
                similar_employees = data.get('similar_employees', [])
                
                if len(similar_employees) >= 3:
                    # Verify scores are in descending order
                    scores = [emp.get('similarity_score', 0) for emp in similar_employees]
                    is_sorted = all(scores[i] >= scores[i+1] for i in range(len(scores)-1))
                    
                    # Verify John Smith has highest score (should be first)
                    first_employee = similar_employees[0]
                    is_john_first = 'John Smith' in first_employee.get('full_name', '')
                    first_score = first_employee.get('similarity_score', 0)
                    
                    # Verify scores are in 0-1 range
                    valid_scores = all(0 <= score <= 1 for score in scores)
                    
                    # Verify match types are correct
                    exact_matches = [emp for emp in similar_employees if emp.get('match_type') == 'exact']
                    similar_matches = [emp for emp in similar_employees if emp.get('match_type') == 'similar']
                    
                    has_exact = len(exact_matches) > 0
                    has_similar = len(similar_matches) > 0
                    
                    success = is_sorted and is_john_first and valid_scores and has_exact
                    details = f"Status: {response.status_code}, Sorted: {is_sorted}, John first: {is_john_first}, " \
                            f"First score: {first_score}, Valid scores: {valid_scores}, Exact matches: {len(exact_matches)}"
                else:
                    success = False
                    details = f"Status: {response.status_code}, Not enough results: {len(similar_employees)}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Similarity Scores - Ranking", success, details)
            return success
        except Exception as e:
            self.log_test("Similarity Scores - Ranking", False, str(e))
            return False

    def test_link_to_existing_employee(self):
        """Test 6: Link scanned employee to existing employee"""
        try:
            # Create two employees - one "scanned" and one "existing"
            existing_id, existing_name = self.create_test_employee("Michael", "Johnson", "_existing", ["RN"])
            scanned_id, scanned_name = self.create_test_employee("Mike", "Johnson", "_scanned", ["HHA"])
            
            if not all([existing_id, scanned_id]):
                self.log_test("Link to Existing Employee", False, "Failed to create test employees")
                return False

            # Test the link endpoint - parameters should be query params, not JSON body
            headers = self.get_auth_headers()
            params = {
                "scanned_employee_id": scanned_id,
                "existing_employee_id": existing_id
            }
            
            response = requests.post(f"{self.api_url}/employees/link-to-existing", 
                                   params=params, headers=headers, timeout=10)
            
            success = response.status_code == 200
            
            if success:
                data = response.json()
                
                # Verify response structure
                required_fields = ['status', 'message', 'scanned_employee_deleted', 'linked_to', 'timesheets_updated']
                has_required_fields = all(field in data for field in required_fields)
                
                # Verify status is success
                status_success = data.get('status') == 'success'
                
                # Verify linked_to structure
                linked_to = data.get('linked_to', {})
                linked_id_correct = linked_to.get('id') == existing_id
                
                # Verify scanned employee was deleted
                headers = self.get_auth_headers()
                check_response = requests.get(f"{self.api_url}/employees/{scanned_id}", headers=headers, timeout=10)
                scanned_deleted = check_response.status_code == 404
                
                # Verify existing employee still exists
                check_response = requests.get(f"{self.api_url}/employees/{existing_id}", headers=headers, timeout=10)
                existing_still_exists = check_response.status_code == 200
                
                success = (has_required_fields and status_success and linked_id_correct and 
                          scanned_deleted and existing_still_exists)
                details = f"Status: {response.status_code}, Fields: {has_required_fields}, " \
                        f"Status OK: {status_success}, Linked ID: {linked_id_correct}, " \
                        f"Scanned deleted: {scanned_deleted}, Existing exists: {existing_still_exists}"
                
                # Remove scanned_id from cleanup list since it was deleted
                if scanned_id in self.created_employees:
                    self.created_employees.remove(scanned_id)
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Link to Existing Employee", success, details)
            return success
        except Exception as e:
            self.log_test("Link to Existing Employee", False, str(e))
            return False

    def test_link_nonexistent_employees(self):
        """Test 7: Try to link non-existent employees (should fail gracefully)"""
        try:
            fake_scanned_id = "fake-scanned-id-12345"
            fake_existing_id = "fake-existing-id-67890"
            
            headers = self.get_auth_headers()
            link_data = {
                "scanned_employee_id": fake_scanned_id,
                "existing_employee_id": fake_existing_id
            }
            
            response = requests.post(f"{self.api_url}/employees/link-to-existing", 
                                   json=link_data, headers=headers, timeout=10)
            
            # Should return 404 for non-existent employee
            success = response.status_code == 404
            
            if success:
                # Should have error message
                try:
                    data = response.json()
                    has_error_detail = 'detail' in data
                    details = f"Status: {response.status_code}, Has error detail: {has_error_detail}, " \
                            f"Detail: {data.get('detail', 'N/A')}"
                except:
                    details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            else:
                details = f"Status: {response.status_code}, Expected 404 for non-existent employees"
            
            self.log_test("Link Non-existent Employees", success, details)
            return success
        except Exception as e:
            self.log_test("Link Non-existent Employees", False, str(e))
            return False

    def cleanup_test_employees(self):
        """Clean up created test employees"""
        print(f"\n🧹 Cleaning up {len(self.created_employees)} test employees...")
        
        headers = self.get_auth_headers()
        cleaned_count = 0
        
        for emp_id in self.created_employees:
            try:
                response = requests.delete(f"{self.api_url}/employees/{emp_id}", headers=headers, timeout=10)
                if response.status_code == 200:
                    cleaned_count += 1
            except Exception as e:
                print(f"Failed to delete employee {emp_id}: {e}")
        
        print(f"✅ Cleaned up {cleaned_count}/{len(self.created_employees)} test employees")
        self.created_employees = []

    def run_all_tests(self):
        """Run all Similar Employee Suggestion tests"""
        print("🔍 Starting Similar Employee Suggestion Feature Tests")
        print(f"Testing against: {self.api_url}")
        print("=" * 60)
        
        # Step 1: Authenticate as admin
        if not self.authenticate_admin():
            print("❌ Admin authentication failed - stopping tests")
            return self.get_results()
        
        # Step 2: Run all test cases
        print("\n📝 Running test cases...")
        
        self.test_similar_employee_exact_match()
        self.test_similar_employee_fuzzy_match()
        self.test_similar_employee_partial_name()
        self.test_similar_employee_typo_match()
        self.test_similarity_scores_ranking()
        self.test_link_to_existing_employee()
        self.test_link_nonexistent_employees()
        
        # Step 3: Cleanup
        self.cleanup_test_employees()
        
        return self.get_results()

    def get_results(self):
        """Get test results summary"""
        print("\n" + "=" * 60)
        print(f"📊 Test Results: {self.tests_passed}/{self.tests_run} passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All Similar Employee Suggestion tests passed!")
            return 0
        else:
            print("❌ Some tests failed")
            failed_tests = [r for r in self.test_results if not r['success']]
            print("\nFailed tests:")
            for test in failed_tests:
                print(f"  - {test['test']}: {test['details']}")
            return 1


if __name__ == "__main__":
    tester = SimilarEmployeeFeatureTester()
    exit_code = tester.run_all_tests()
    sys.exit(exit_code)