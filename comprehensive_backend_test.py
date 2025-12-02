#!/usr/bin/env python3
"""
Comprehensive Backend Testing Suite for Timesheet SaaS
Tests authentication, multi-tenancy, CRUD operations, search/filter, bulk operations, and Stripe integration
"""

import requests
import json
import sys
from datetime import datetime
from typing import Dict, List, Optional, Tuple

class ComprehensiveBackendTester:
    def __init__(self, base_url="https://caresheet.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        
        # Test user credentials with timestamp to ensure uniqueness
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        self.test_user1_email = f"testuser1_{timestamp}@test.com"
        self.test_user1_password = "SecurePass123!"
        self.test_user1_token = None
        self.test_user1_org_id = None
        
        self.test_user2_email = f"testuser2_{timestamp}@test.com"
        self.test_user2_password = "SecurePass456!"
        self.test_user2_token = None
        self.test_user2_org_id = None
        
        # Store created resource IDs for cleanup
        self.created_resources = {
            'user1': {'patients': [], 'employees': [], 'timesheets': [], 'claims': [], 'payers': [], 'service_codes': []},
            'user2': {'patients': [], 'employees': [], 'timesheets': [], 'claims': [], 'payers': [], 'service_codes': []}
        }

    def log_test(self, name: str, success: bool, details: str = ""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}")
        else:
            print(f"❌ {name} - FAILED: {details}")
        
        self.test_results.append({
            "test": name,
            "success": success,
            "details": details
        })

    def get_auth_headers(self, token: str) -> Dict:
        """Get authorization headers"""
        return {"Authorization": f"Bearer {token}"}

    # ========================================
    # 1. AUTHENTICATION TESTS
    # ========================================
    
    def test_auth_signup_user1(self) -> bool:
        """Test user signup for user 1"""
        try:
            signup_data = {
                "email": self.test_user1_email,
                "password": self.test_user1_password,
                "first_name": "Test",
                "last_name": "User1",
                "organization_name": "Test Organization 1"
            }
            
            response = requests.post(f"{self.api_url}/auth/signup", json=signup_data, timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                self.test_user1_token = data.get('access_token')
                user_data = data.get('user', {})
                self.test_user1_org_id = user_data.get('organization_id')
                success = self.test_user1_token is not None and self.test_user1_org_id is not None
                details = f"Token: {self.test_user1_token[:20]}..., Org ID: {self.test_user1_org_id}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Auth: Signup User 1", success, details)
            return success
        except Exception as e:
            self.log_test("Auth: Signup User 1", False, str(e))
            return False

    def test_auth_signup_user2(self) -> bool:
        """Test user signup for user 2"""
        try:
            signup_data = {
                "email": self.test_user2_email,
                "password": self.test_user2_password,
                "first_name": "Test",
                "last_name": "User2",
                "organization_name": "Test Organization 2"
            }
            
            response = requests.post(f"{self.api_url}/auth/signup", json=signup_data, timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                self.test_user2_token = data.get('access_token')
                user_data = data.get('user', {})
                self.test_user2_org_id = user_data.get('organization_id')
                success = self.test_user2_token is not None and self.test_user2_org_id is not None
                details = f"Token: {self.test_user2_token[:20]}..., Org ID: {self.test_user2_org_id}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Auth: Signup User 2", success, details)
            return success
        except Exception as e:
            self.log_test("Auth: Signup User 2", False, str(e))
            return False

    def test_auth_login_user1(self) -> bool:
        """Test user login for user 1"""
        try:
            login_data = {
                "email": self.test_user1_email,
                "password": self.test_user1_password
            }
            
            response = requests.post(f"{self.api_url}/auth/login", json=login_data, timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                token = data.get('access_token')
                user_data = data.get('user', {})
                org_id = user_data.get('organization_id')
                success = token is not None and org_id == self.test_user1_org_id
                details = f"Login successful, Org ID matches: {org_id == self.test_user1_org_id}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Auth: Login User 1", success, details)
            return success
        except Exception as e:
            self.log_test("Auth: Login User 1", False, str(e))
            return False

    def test_auth_me_user1(self) -> bool:
        """Test /auth/me endpoint for user 1"""
        try:
            headers = self.get_auth_headers(self.test_user1_token)
            response = requests.get(f"{self.api_url}/auth/me", headers=headers, timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                success = (data.get('email') == self.test_user1_email and 
                          data.get('organization_id') == self.test_user1_org_id)
                details = f"Email: {data.get('email')}, Org: {data.get('organization_id')}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Auth: /auth/me User 1", success, details)
            return success
        except Exception as e:
            self.log_test("Auth: /auth/me User 1", False, str(e))
            return False

    def test_auth_invalid_credentials(self) -> bool:
        """Test login with invalid credentials"""
        try:
            login_data = {
                "email": self.test_user1_email,
                "password": "WrongPassword123!"
            }
            
            response = requests.post(f"{self.api_url}/auth/login", json=login_data, timeout=10)
            success = response.status_code == 401
            details = f"Status: {response.status_code} (expected 401)"
            
            self.log_test("Auth: Invalid Credentials", success, details)
            return success
        except Exception as e:
            self.log_test("Auth: Invalid Credentials", False, str(e))
            return False

    # ========================================
    # 2. PATIENT CRUD TESTS
    # ========================================
    
    def test_create_patient_user1(self) -> Optional[str]:
        """Create patient for user 1"""
        try:
            patient_data = {
                "first_name": "John",
                "last_name": "Doe",
                "sex": "Male",
                "date_of_birth": "1980-05-15",
                "address_street": "123 Main St",
                "address_city": "Columbus",
                "address_state": "OH",
                "address_zip": "43215",
                "medicaid_number": "123456789012",
                "prior_auth_number": "PA123456",
                "icd10_code": "Z00.00",
                "physician_name": "Dr. Smith",
                "physician_npi": "1234567890",
                "is_complete": True
            }
            
            headers = self.get_auth_headers(self.test_user1_token)
            response = requests.post(f"{self.api_url}/patients", json=patient_data, headers=headers, timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                patient_id = data.get('id')
                org_id = data.get('organization_id')
                success = patient_id is not None and org_id == self.test_user1_org_id
                self.created_resources['user1']['patients'].append(patient_id)
                details = f"Patient ID: {patient_id}, Org ID: {org_id}"
                self.log_test("Patient: Create for User 1", success, details)
                return patient_id if success else None
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
                self.log_test("Patient: Create for User 1", success, details)
                return None
        except Exception as e:
            self.log_test("Patient: Create for User 1", False, str(e))
            return None

    def test_create_patient_user2(self) -> Optional[str]:
        """Create patient for user 2"""
        try:
            patient_data = {
                "first_name": "Jane",
                "last_name": "Smith",
                "sex": "Female",
                "date_of_birth": "1985-08-20",
                "address_street": "456 Oak Ave",
                "address_city": "Cleveland",
                "address_state": "OH",
                "address_zip": "44115",
                "medicaid_number": "987654321098",
                "prior_auth_number": "PA987654",
                "icd10_code": "Z00.01",
                "physician_name": "Dr. Johnson",
                "physician_npi": "0987654321",
                "is_complete": True
            }
            
            headers = self.get_auth_headers(self.test_user2_token)
            response = requests.post(f"{self.api_url}/patients", json=patient_data, headers=headers, timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                patient_id = data.get('id')
                org_id = data.get('organization_id')
                success = patient_id is not None and org_id == self.test_user2_org_id
                self.created_resources['user2']['patients'].append(patient_id)
                details = f"Patient ID: {patient_id}, Org ID: {org_id}"
                self.log_test("Patient: Create for User 2", success, details)
                return patient_id if success else None
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
                self.log_test("Patient: Create for User 2", success, details)
                return None
        except Exception as e:
            self.log_test("Patient: Create for User 2", False, str(e))
            return None

    def test_get_patients_user1(self) -> bool:
        """Get patients for user 1 - should only see their own"""
        try:
            headers = self.get_auth_headers(self.test_user1_token)
            response = requests.get(f"{self.api_url}/patients", headers=headers, timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                # Check all patients belong to user1's organization
                all_belong_to_user1 = all(p.get('organization_id') == self.test_user1_org_id for p in data)
                # Check user2's patient is NOT in the list
                user2_patient_ids = self.created_resources['user2']['patients']
                no_user2_data = all(p.get('id') not in user2_patient_ids for p in data)
                
                success = all_belong_to_user1 and no_user2_data
                details = f"Count: {len(data)}, All belong to User1: {all_belong_to_user1}, No User2 data: {no_user2_data}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Patient: Get Patients User 1 (Isolation Check)", success, details)
            return success
        except Exception as e:
            self.log_test("Patient: Get Patients User 1 (Isolation Check)", False, str(e))
            return False

    def test_get_patients_user2(self) -> bool:
        """Get patients for user 2 - should only see their own"""
        try:
            headers = self.get_auth_headers(self.test_user2_token)
            response = requests.get(f"{self.api_url}/patients", headers=headers, timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                # Check all patients belong to user2's organization
                all_belong_to_user2 = all(p.get('organization_id') == self.test_user2_org_id for p in data)
                # Check user1's patient is NOT in the list
                user1_patient_ids = self.created_resources['user1']['patients']
                no_user1_data = all(p.get('id') not in user1_patient_ids for p in data)
                
                success = all_belong_to_user2 and no_user1_data
                details = f"Count: {len(data)}, All belong to User2: {all_belong_to_user2}, No User1 data: {no_user1_data}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Patient: Get Patients User 2 (Isolation Check)", success, details)
            return success
        except Exception as e:
            self.log_test("Patient: Get Patients User 2 (Isolation Check)", False, str(e))
            return False

    def test_patient_cross_org_access(self, patient_id: str) -> bool:
        """Test that user 2 cannot access user 1's patient"""
        try:
            headers = self.get_auth_headers(self.test_user2_token)
            response = requests.get(f"{self.api_url}/patients/{patient_id}", headers=headers, timeout=10)
            # Should return 404 or empty, not the patient data
            success = response.status_code == 404
            details = f"Status: {response.status_code} (expected 404 for cross-org access)"
            
            self.log_test("Patient: Cross-Org Access Prevention", success, details)
            return success
        except Exception as e:
            self.log_test("Patient: Cross-Org Access Prevention", False, str(e))
            return False

    def test_update_patient(self, patient_id: str, token: str) -> bool:
        """Test updating a patient"""
        try:
            headers = self.get_auth_headers(token)
            # First get the patient
            response = requests.get(f"{self.api_url}/patients/{patient_id}", headers=headers, timeout=10)
            if response.status_code != 200:
                self.log_test("Patient: Update", False, "Could not fetch patient")
                return False
            
            patient_data = response.json()
            patient_data['address_city'] = "Updated City"
            
            response = requests.put(f"{self.api_url}/patients/{patient_id}", json=patient_data, headers=headers, timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                success = data.get('address_city') == "Updated City"
                details = f"City updated: {data.get('address_city')}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Patient: Update", success, details)
            return success
        except Exception as e:
            self.log_test("Patient: Update", False, str(e))
            return False

    def test_delete_patient(self, patient_id: str, token: str) -> bool:
        """Test deleting a patient"""
        try:
            headers = self.get_auth_headers(token)
            response = requests.delete(f"{self.api_url}/patients/{patient_id}", headers=headers, timeout=10)
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            
            self.log_test("Patient: Delete", success, details)
            return success
        except Exception as e:
            self.log_test("Patient: Delete", False, str(e))
            return False

    # ========================================
    # 3. EMPLOYEE CRUD TESTS
    # ========================================
    
    def test_create_employee_user1(self) -> Optional[str]:
        """Create employee for user 1"""
        try:
            employee_data = {
                "first_name": "Alice",
                "last_name": "Worker",
                "ssn": "123456789",
                "date_of_birth": "1990-03-10",
                "sex": "Female",
                "email": "alice.worker@test.com",
                "phone": "6145551234",
                "address_street": "789 Elm St",
                "address_city": "Columbus",
                "address_state": "OH",
                "address_zip": "43215",
                "employee_id": "EMP001",
                "hire_date": "2023-01-15",
                "job_title": "Home Health Aide",
                "employment_status": "Full-time",
                "is_complete": True
            }
            
            headers = self.get_auth_headers(self.test_user1_token)
            response = requests.post(f"{self.api_url}/employees", json=employee_data, headers=headers, timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                employee_id = data.get('id')
                org_id = data.get('organization_id')
                success = employee_id is not None and org_id == self.test_user1_org_id
                self.created_resources['user1']['employees'].append(employee_id)
                details = f"Employee ID: {employee_id}, Org ID: {org_id}"
                self.log_test("Employee: Create for User 1", success, details)
                return employee_id if success else None
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
                self.log_test("Employee: Create for User 1", success, details)
                return None
        except Exception as e:
            self.log_test("Employee: Create for User 1", False, str(e))
            return None

    def test_create_employee_user2(self) -> Optional[str]:
        """Create employee for user 2"""
        try:
            employee_data = {
                "first_name": "Bob",
                "last_name": "Helper",
                "ssn": "987654321",
                "date_of_birth": "1988-07-22",
                "sex": "Male",
                "email": "bob.helper@test.com",
                "phone": "2165559876",
                "address_street": "321 Pine Ave",
                "address_city": "Cleveland",
                "address_state": "OH",
                "address_zip": "44115",
                "employee_id": "EMP002",
                "hire_date": "2022-06-01",
                "job_title": "Personal Care Assistant",
                "employment_status": "Part-time",
                "is_complete": True
            }
            
            headers = self.get_auth_headers(self.test_user2_token)
            response = requests.post(f"{self.api_url}/employees", json=employee_data, headers=headers, timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                employee_id = data.get('id')
                org_id = data.get('organization_id')
                success = employee_id is not None and org_id == self.test_user2_org_id
                self.created_resources['user2']['employees'].append(employee_id)
                details = f"Employee ID: {employee_id}, Org ID: {org_id}"
                self.log_test("Employee: Create for User 2", success, details)
                return employee_id if success else None
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
                self.log_test("Employee: Create for User 2", success, details)
                return None
        except Exception as e:
            self.log_test("Employee: Create for User 2", False, str(e))
            return None

    def test_get_employees_isolation(self) -> bool:
        """Test employee data isolation between organizations"""
        try:
            # User 1 should only see their employees
            headers1 = self.get_auth_headers(self.test_user1_token)
            response1 = requests.get(f"{self.api_url}/employees", headers=headers1, timeout=10)
            
            # User 2 should only see their employees
            headers2 = self.get_auth_headers(self.test_user2_token)
            response2 = requests.get(f"{self.api_url}/employees", headers=headers2, timeout=10)
            
            success = response1.status_code == 200 and response2.status_code == 200
            
            if success:
                data1 = response1.json()
                data2 = response2.json()
                
                # Check isolation
                all_user1_belong = all(e.get('organization_id') == self.test_user1_org_id for e in data1)
                all_user2_belong = all(e.get('organization_id') == self.test_user2_org_id for e in data2)
                
                # Check no cross-contamination
                user2_emp_ids = self.created_resources['user2']['employees']
                user1_emp_ids = self.created_resources['user1']['employees']
                no_user2_in_user1 = all(e.get('id') not in user2_emp_ids for e in data1)
                no_user1_in_user2 = all(e.get('id') not in user1_emp_ids for e in data2)
                
                success = all_user1_belong and all_user2_belong and no_user2_in_user1 and no_user1_in_user2
                details = f"User1 count: {len(data1)}, User2 count: {len(data2)}, Isolation: {success}"
            else:
                details = f"Status: {response1.status_code}, {response2.status_code}"
            
            self.log_test("Employee: Data Isolation", success, details)
            return success
        except Exception as e:
            self.log_test("Employee: Data Isolation", False, str(e))
            return False

    # ========================================
    # 4. PAYER/INSURANCE CONTRACT TESTS
    # ========================================
    
    def test_create_payer_user1(self) -> Optional[str]:
        """Create insurance contract for user 1"""
        try:
            payer_data = {
                "payer_name": "Ohio Department of Medicaid",
                "insurance_type": "Medicaid",
                "contract_number": "ODM-2024-001",
                "start_date": "2024-01-01",
                "contact_person": "John Contract",
                "contact_phone": "6145551111",
                "contact_email": "contracts@odm.ohio.gov",
                "is_active": True,
                "billable_services": [
                    {
                        "service_code": "T1019",
                        "service_name": "Personal Care Services",
                        "is_active": True
                    }
                ]
            }
            
            headers = self.get_auth_headers(self.test_user1_token)
            response = requests.post(f"{self.api_url}/insurance-contracts", json=payer_data, headers=headers, timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                payer_id = data.get('id')
                self.created_resources['user1']['payers'].append(payer_id)
                details = f"Payer ID: {payer_id}"
                self.log_test("Payer: Create for User 1", success, details)
                return payer_id if success else None
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
                self.log_test("Payer: Create for User 1", success, details)
                return None
        except Exception as e:
            self.log_test("Payer: Create for User 1", False, str(e))
            return None

    def test_get_payers_isolation(self) -> bool:
        """Test payer data isolation"""
        try:
            headers1 = self.get_auth_headers(self.test_user1_token)
            response1 = requests.get(f"{self.api_url}/insurance-contracts", headers=headers1, timeout=10)
            
            headers2 = self.get_auth_headers(self.test_user2_token)
            response2 = requests.get(f"{self.api_url}/insurance-contracts", headers=headers2, timeout=10)
            
            success = response1.status_code == 200 and response2.status_code == 200
            
            if success:
                data1 = response1.json()
                data2 = response2.json()
                
                # User 1 should have payers, User 2 should have none (we didn't create any)
                user1_has_payers = len(data1) > 0
                user2_has_no_payers = len(data2) == 0
                
                success = user1_has_payers and user2_has_no_payers
                details = f"User1 payers: {len(data1)}, User2 payers: {len(data2)}"
            else:
                details = f"Status: {response1.status_code}, {response2.status_code}"
            
            self.log_test("Payer: Data Isolation", success, details)
            return success
        except Exception as e:
            self.log_test("Payer: Data Isolation", False, str(e))
            return False

    # ========================================
    # 5. CLAIMS MANAGEMENT TESTS
    # ========================================
    
    def test_create_claim_user1(self, patient_id: str, payer_id: str) -> Optional[str]:
        """Create claim for user 1"""
        try:
            claim_data = {
                "claim_number": f"CLM-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "patient_id": patient_id,
                "patient_name": "John Doe",
                "patient_medicaid_number": "123456789012",
                "payer_id": payer_id,
                "payer_name": "Ohio Department of Medicaid",
                "service_period_start": "2024-01-01",
                "service_period_end": "2024-01-31",
                "line_items": [
                    {
                        "date_of_service": "2024-01-15",
                        "employee_name": "Alice Worker",
                        "service_code": "T1019",
                        "service_name": "Personal Care Services",
                        "units": 32,
                        "rate_per_unit": 15.50,
                        "amount": 496.00
                    }
                ],
                "total_units": 32,
                "total_amount": 496.00,
                "status": "draft"
            }
            
            headers = self.get_auth_headers(self.test_user1_token)
            response = requests.post(f"{self.api_url}/claims", json=claim_data, headers=headers, timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                claim_id = data.get('id')
                org_id = data.get('organization_id')
                success = claim_id is not None and org_id == self.test_user1_org_id
                self.created_resources['user1']['claims'].append(claim_id)
                details = f"Claim ID: {claim_id}, Org ID: {org_id}"
                self.log_test("Claim: Create for User 1", success, details)
                return claim_id if success else None
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
                self.log_test("Claim: Create for User 1", success, details)
                return None
        except Exception as e:
            self.log_test("Claim: Create for User 1", False, str(e))
            return None

    def test_get_claims_isolation(self) -> bool:
        """Test claims data isolation"""
        try:
            headers1 = self.get_auth_headers(self.test_user1_token)
            response1 = requests.get(f"{self.api_url}/claims", headers=headers1, timeout=10)
            
            headers2 = self.get_auth_headers(self.test_user2_token)
            response2 = requests.get(f"{self.api_url}/claims", headers=headers2, timeout=10)
            
            success = response1.status_code == 200 and response2.status_code == 200
            
            if success:
                data1 = response1.json()
                data2 = response2.json()
                
                # Check isolation
                all_user1_belong = all(c.get('organization_id') == self.test_user1_org_id for c in data1)
                user1_has_claims = len(data1) > 0
                user2_has_no_claims = len(data2) == 0
                
                success = all_user1_belong and user1_has_claims and user2_has_no_claims
                details = f"User1 claims: {len(data1)}, User2 claims: {len(data2)}, Isolation: {success}"
            else:
                details = f"Status: {response1.status_code}, {response2.status_code}"
            
            self.log_test("Claim: Data Isolation", success, details)
            return success
        except Exception as e:
            self.log_test("Claim: Data Isolation", False, str(e))
            return False

    # ========================================
    # 6. SERVICE CODES TESTS
    # ========================================
    
    def test_create_service_code_user1(self) -> Optional[str]:
        """Create service code for user 1"""
        try:
            service_code_data = {
                "service_name": "Home Health Aide - State Plan",
                "service_code_internal": "HHA-SP",
                "payer": "ODM",
                "payer_program": "SP",
                "procedure_code": "T1019",
                "service_description": "Personal care services provided by HHA",
                "service_category": "Personal Care",
                "billable_unit_type": "15_minutes",
                "requires_evv": True,
                "is_active": True,
                "effective_start_date": "2024-01-01"
            }
            
            headers = self.get_auth_headers(self.test_user1_token)
            response = requests.post(f"{self.api_url}/service-codes", json=service_code_data, headers=headers, timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                service_code_id = data.get('id')
                org_id = data.get('organization_id')
                success = service_code_id is not None and org_id == self.test_user1_org_id
                self.created_resources['user1']['service_codes'].append(service_code_id)
                details = f"Service Code ID: {service_code_id}, Org ID: {org_id}"
                self.log_test("Service Code: Create for User 1", success, details)
                return service_code_id if success else None
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
                self.log_test("Service Code: Create for User 1", success, details)
                return None
        except Exception as e:
            self.log_test("Service Code: Create for User 1", False, str(e))
            return None

    def test_get_service_codes_isolation(self) -> bool:
        """Test service codes data isolation"""
        try:
            headers1 = self.get_auth_headers(self.test_user1_token)
            response1 = requests.get(f"{self.api_url}/service-codes", headers=headers1, timeout=10)
            
            headers2 = self.get_auth_headers(self.test_user2_token)
            response2 = requests.get(f"{self.api_url}/service-codes", headers=headers2, timeout=10)
            
            success = response1.status_code == 200 and response2.status_code == 200
            
            if success:
                data1 = response1.json()
                data2 = response2.json()
                
                # Check isolation
                all_user1_belong = all(sc.get('organization_id') == self.test_user1_org_id for sc in data1)
                user1_has_codes = len(data1) > 0
                user2_has_no_codes = len(data2) == 0
                
                success = all_user1_belong and user1_has_codes and user2_has_no_codes
                details = f"User1 codes: {len(data1)}, User2 codes: {len(data2)}, Isolation: {success}"
            else:
                details = f"Status: {response1.status_code}, {response2.status_code}"
            
            self.log_test("Service Code: Data Isolation", success, details)
            return success
        except Exception as e:
            self.log_test("Service Code: Data Isolation", False, str(e))
            return False

    # ========================================
    # 7. SEARCH AND FILTER TESTS
    # ========================================
    
    def test_patient_search(self) -> bool:
        """Test patient search functionality"""
        try:
            headers = self.get_auth_headers(self.test_user1_token)
            response = requests.get(f"{self.api_url}/patients?search=John", headers=headers, timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                # Should find John Doe
                found_john = any(p.get('first_name') == 'John' for p in data)
                success = found_john
                details = f"Found John: {found_john}, Count: {len(data)}"
            else:
                details = f"Status: {response.status_code}"
            
            self.log_test("Search: Patient by Name", success, details)
            return success
        except Exception as e:
            self.log_test("Search: Patient by Name", False, str(e))
            return False

    def test_patient_filter_by_completion(self) -> bool:
        """Test patient filter by completion status"""
        try:
            headers = self.get_auth_headers(self.test_user1_token)
            response = requests.get(f"{self.api_url}/patients?is_complete=true", headers=headers, timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                all_complete = all(p.get('is_complete') == True for p in data)
                success = all_complete
                details = f"All complete: {all_complete}, Count: {len(data)}"
            else:
                details = f"Status: {response.status_code}"
            
            self.log_test("Filter: Patient by Completion", success, details)
            return success
        except Exception as e:
            self.log_test("Filter: Patient by Completion", False, str(e))
            return False

    def test_employee_search(self) -> bool:
        """Test employee search functionality"""
        try:
            headers = self.get_auth_headers(self.test_user1_token)
            response = requests.get(f"{self.api_url}/employees?search=Alice", headers=headers, timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                found_alice = any(e.get('first_name') == 'Alice' for e in data)
                success = found_alice
                details = f"Found Alice: {found_alice}, Count: {len(data)}"
            else:
                details = f"Status: {response.status_code}"
            
            self.log_test("Search: Employee by Name", success, details)
            return success
        except Exception as e:
            self.log_test("Search: Employee by Name", False, str(e))
            return False

    # ========================================
    # 8. BULK OPERATIONS TESTS
    # ========================================
    
    def test_bulk_update_patients(self, patient_ids: List[str]) -> bool:
        """Test bulk update patients"""
        if not patient_ids:
            self.log_test("Bulk: Update Patients", False, "No patient IDs provided")
            return False
        
        try:
            bulk_data = {
                "ids": patient_ids,
                "updates": {
                    "address_city": "Bulk Updated City"
                }
            }
            
            headers = self.get_auth_headers(self.test_user1_token)
            response = requests.post(f"{self.api_url}/patients/bulk-update", json=bulk_data, headers=headers, timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                modified_count = data.get('modified_count', 0)
                success = modified_count > 0
                details = f"Modified: {modified_count}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Bulk: Update Patients", success, details)
            return success
        except Exception as e:
            self.log_test("Bulk: Update Patients", False, str(e))
            return False

    def test_bulk_delete_employees(self, employee_ids: List[str]) -> bool:
        """Test bulk delete employees"""
        if not employee_ids:
            self.log_test("Bulk: Delete Employees", False, "No employee IDs provided")
            return False
        
        try:
            bulk_data = {
                "ids": employee_ids
            }
            
            headers = self.get_auth_headers(self.test_user1_token)
            response = requests.post(f"{self.api_url}/employees/bulk-delete", json=bulk_data, headers=headers, timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                deleted_count = data.get('deleted_count', 0)
                success = deleted_count > 0
                details = f"Deleted: {deleted_count}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Bulk: Delete Employees", success, details)
            return success
        except Exception as e:
            self.log_test("Bulk: Delete Employees", False, str(e))
            return False

    def test_csv_export(self) -> bool:
        """Test CSV export functionality"""
        try:
            headers = self.get_auth_headers(self.test_user1_token)
            response = requests.post(f"{self.api_url}/timesheets/export", headers=headers, timeout=10)
            success = response.status_code == 200
            
            if success:
                content_type = response.headers.get('content-type', '')
                is_csv = 'text/csv' in content_type
                has_content = len(response.content) > 0
                success = is_csv and has_content
                details = f"Content-Type: {content_type}, Size: {len(response.content)} bytes"
            else:
                details = f"Status: {response.status_code}"
            
            self.log_test("Export: CSV Timesheets", success, details)
            return success
        except Exception as e:
            self.log_test("Export: CSV Timesheets", False, str(e))
            return False

    # ========================================
    # 9. STRIPE INTEGRATION TESTS
    # ========================================
    
    def test_stripe_create_checkout(self) -> bool:
        """Test Stripe checkout session creation"""
        try:
            checkout_data = {
                "plan": "professional",
                "success_url": f"{self.base_url}/success",
                "cancel_url": f"{self.base_url}/cancel"
            }
            
            headers = self.get_auth_headers(self.test_user1_token)
            response = requests.post(f"{self.api_url}/payments/create-checkout", json=checkout_data, headers=headers, timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                has_session_id = 'session_id' in data
                has_url = 'url' in data
                success = has_session_id and has_url
                details = f"Session ID: {data.get('session_id', 'N/A')[:20]}..."
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Stripe: Create Checkout Session", success, details)
            return success
        except Exception as e:
            self.log_test("Stripe: Create Checkout Session", False, str(e))
            return False

    def test_stripe_webhook_endpoint_exists(self) -> bool:
        """Test that Stripe webhook endpoint exists"""
        try:
            # Just check if the endpoint exists (will fail without proper signature, but that's expected)
            response = requests.post(f"{self.api_url}/payments/webhook", data=b"test", timeout=10)
            # Should return 400 (bad signature) not 404 (not found)
            success = response.status_code in [400, 401, 403]  # Any auth/validation error means endpoint exists
            details = f"Status: {response.status_code} (endpoint exists)"
            
            self.log_test("Stripe: Webhook Endpoint Exists", success, details)
            return success
        except Exception as e:
            self.log_test("Stripe: Webhook Endpoint Exists", False, str(e))
            return False

    def test_get_plans(self) -> bool:
        """Test getting available plans"""
        try:
            response = requests.get(f"{self.api_url}/payments/plans", timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                has_plans = 'plans' in data and len(data['plans']) > 0
                success = has_plans
                details = f"Plans available: {len(data.get('plans', []))}"
            else:
                details = f"Status: {response.status_code}"
            
            self.log_test("Stripe: Get Plans", success, details)
            return success
        except Exception as e:
            self.log_test("Stripe: Get Plans", False, str(e))
            return False

    # ========================================
    # 10. EVV SYSTEM VERIFICATION
    # ========================================
    
    def test_evv_business_entity(self) -> bool:
        """Test EVV business entity endpoint"""
        try:
            headers = self.get_auth_headers(self.test_user1_token)
            response = requests.get(f"{self.api_url}/evv/business-entity", headers=headers, timeout=10)
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            
            self.log_test("EVV: Business Entity Endpoint", success, details)
            return success
        except Exception as e:
            self.log_test("EVV: Business Entity Endpoint", False, str(e))
            return False

    def test_evv_visits_endpoint(self) -> bool:
        """Test EVV visits endpoint"""
        try:
            headers = self.get_auth_headers(self.test_user1_token)
            response = requests.get(f"{self.api_url}/evv/visits", headers=headers, timeout=10)
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            
            self.log_test("EVV: Visits Endpoint", success, details)
            return success
        except Exception as e:
            self.log_test("EVV: Visits Endpoint", False, str(e))
            return False

    def test_evv_export_individuals(self) -> bool:
        """Test EVV export individuals endpoint"""
        try:
            headers = self.get_auth_headers(self.test_user1_token)
            response = requests.get(f"{self.api_url}/evv/export/individuals", headers=headers, timeout=10)
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            
            self.log_test("EVV: Export Individuals", success, details)
            return success
        except Exception as e:
            self.log_test("EVV: Export Individuals", False, str(e))
            return False

    def test_evv_reference_data(self) -> bool:
        """Test EVV reference data endpoints"""
        try:
            response = requests.get(f"{self.api_url}/evv/reference/payers", timeout=10)
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            
            self.log_test("EVV: Reference Data", success, details)
            return success
        except Exception as e:
            self.log_test("EVV: Reference Data", False, str(e))
            return False

    # ========================================
    # MAIN TEST RUNNER
    # ========================================
    
    def run_comprehensive_tests(self):
        """Run all comprehensive backend tests"""
        print("=" * 80)
        print("🚀 COMPREHENSIVE BACKEND TESTING SUITE")
        print("=" * 80)
        print(f"Testing against: {self.api_url}")
        print(f"Test Stripe Key: sk_test_51SQfPv3AlN52R5kIbg7TqOZOCpBRUBQm5b1wWxtqaYnIcUQnB2Mx6xKZ6aYeH41WuHFeJQanDECcQkUPW6qjGMKE00ASHzhODC")
        print("=" * 80)
        
        # 1. AUTHENTICATION TESTS
        print("\n📝 1. AUTHENTICATION TESTS")
        print("-" * 80)
        if not self.test_auth_signup_user1():
            print("❌ User 1 signup failed - stopping tests")
            return self.get_results()
        
        if not self.test_auth_signup_user2():
            print("❌ User 2 signup failed - stopping tests")
            return self.get_results()
        
        self.test_auth_login_user1()
        self.test_auth_me_user1()
        self.test_auth_invalid_credentials()
        
        # 2. PATIENT CRUD & MULTI-TENANCY
        print("\n👥 2. PATIENT CRUD & MULTI-TENANCY TESTS")
        print("-" * 80)
        patient_id_user1 = self.test_create_patient_user1()
        patient_id_user2 = self.test_create_patient_user2()
        
        if patient_id_user1 and patient_id_user2:
            self.test_get_patients_user1()
            self.test_get_patients_user2()
            self.test_patient_cross_org_access(patient_id_user1)
            self.test_update_patient(patient_id_user1, self.test_user1_token)
        
        # 3. EMPLOYEE CRUD & MULTI-TENANCY
        print("\n👷 3. EMPLOYEE CRUD & MULTI-TENANCY TESTS")
        print("-" * 80)
        employee_id_user1 = self.test_create_employee_user1()
        employee_id_user2 = self.test_create_employee_user2()
        
        if employee_id_user1 and employee_id_user2:
            self.test_get_employees_isolation()
        
        # 4. PAYER/INSURANCE CONTRACTS
        print("\n💳 4. PAYER/INSURANCE CONTRACT TESTS")
        print("-" * 80)
        payer_id_user1 = self.test_create_payer_user1()
        self.test_get_payers_isolation()
        
        # 5. CLAIMS MANAGEMENT
        print("\n📋 5. CLAIMS MANAGEMENT TESTS")
        print("-" * 80)
        if patient_id_user1 and payer_id_user1:
            claim_id_user1 = self.test_create_claim_user1(patient_id_user1, payer_id_user1)
            self.test_get_claims_isolation()
        
        # 6. SERVICE CODES
        print("\n🔧 6. SERVICE CODES TESTS")
        print("-" * 80)
        service_code_id_user1 = self.test_create_service_code_user1()
        self.test_get_service_codes_isolation()
        
        # 7. SEARCH & FILTER
        print("\n🔍 7. SEARCH & FILTER TESTS")
        print("-" * 80)
        self.test_patient_search()
        self.test_patient_filter_by_completion()
        self.test_employee_search()
        
        # 8. BULK OPERATIONS
        print("\n📦 8. BULK OPERATIONS TESTS")
        print("-" * 80)
        if patient_id_user1:
            self.test_bulk_update_patients([patient_id_user1])
        if employee_id_user1:
            # Create another employee for bulk delete test
            extra_emp = self.test_create_employee_user1()
            if extra_emp:
                self.test_bulk_delete_employees([extra_emp])
        self.test_csv_export()
        
        # 9. STRIPE INTEGRATION
        print("\n💰 9. STRIPE INTEGRATION TESTS")
        print("-" * 80)
        self.test_stripe_create_checkout()
        self.test_stripe_webhook_endpoint_exists()
        self.test_get_plans()
        
        # 10. EVV SYSTEM VERIFICATION
        print("\n🏥 10. EVV SYSTEM VERIFICATION")
        print("-" * 80)
        self.test_evv_business_entity()
        self.test_evv_visits_endpoint()
        self.test_evv_export_individuals()
        self.test_evv_reference_data()
        
        return self.get_results()

    def get_results(self):
        """Get test results summary"""
        print("\n" + "=" * 80)
        print(f"📊 TEST RESULTS: {self.tests_passed}/{self.tests_run} PASSED")
        print("=" * 80)
        
        if self.tests_passed == self.tests_run:
            print("🎉 ALL TESTS PASSED!")
            return 0
        else:
            print(f"❌ {self.tests_run - self.tests_passed} TESTS FAILED")
            failed_tests = [r for r in self.test_results if not r['success']]
            print("\n❌ FAILED TESTS:")
            for test in failed_tests:
                print(f"  • {test['test']}")
                if test['details']:
                    print(f"    └─ {test['details']}")
            return 1


if __name__ == "__main__":
    tester = ComprehensiveBackendTester()
    exit_code = tester.run_comprehensive_tests()
    sys.exit(exit_code)
