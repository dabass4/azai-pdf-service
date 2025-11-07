#!/usr/bin/env python3
"""
Comprehensive Multi-Tenant SaaS Backend Testing
Tests all fixes mentioned in the review request:
1. Data leakage in insurance contracts
2. PatientProfile organization_id field
3. /auth/me endpoint
4. Patient/Employee/Service Code creation with organization_id
5. Multi-tenancy isolation across all endpoints
"""

import requests
import json
import sys
from datetime import datetime

class MultiTenantTester:
    def __init__(self, base_url="https://timesheet-saas.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        
        # Store tokens and IDs for two test organizations
        self.org1_token = None
        self.org1_id = None
        self.org2_token = None
        self.org2_id = None
        
    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}")
        else:
            print(f"❌ {name}")
            print(f"   Details: {details}")
        
        self.test_results.append({
            "test": name,
            "success": success,
            "details": details
        })
        
    def get_results(self):
        """Get test results summary"""
        print("\n" + "=" * 80)
        print(f"📊 Test Results: {self.tests_passed}/{self.tests_run} passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed!")
            return 0
        else:
            print("❌ Some tests failed")
            failed_tests = [r for r in self.test_results if not r['success']]
            print("\n❌ FAILED TESTS:")
            for test in failed_tests:
                print(f"  - {test['test']}")
                if test['details']:
                    print(f"    {test['details']}")
            return 1
    
    # ========================================
    # Authentication Tests
    # ========================================
    
    def test_signup_org1(self):
        """Test signup for organization 1"""
        try:
            signup_data = {
                "email": f"org1_admin_{datetime.now().timestamp()}@test.com",
                "password": "SecurePass123!",
                "first_name": "Org1",
                "last_name": "Admin",
                "organization_name": "Healthcare Org 1"
            }
            
            response = requests.post(f"{self.api_url}/auth/signup", json=signup_data, timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                self.org1_token = data.get('access_token')
                # Extract organization_id from organization object
                org_data = data.get('organization', {})
                self.org1_id = org_data.get('id')
                success = self.org1_token is not None and self.org1_id is not None
                details = f"Token: {self.org1_token[:20]}..., Org ID: {self.org1_id}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Signup Organization 1", success, details)
            return success
        except Exception as e:
            self.log_test("Signup Organization 1", False, str(e))
            return False
    
    def test_signup_org2(self):
        """Test signup for organization 2"""
        try:
            signup_data = {
                "email": f"org2_admin_{datetime.now().timestamp()}@test.com",
                "password": "SecurePass456!",
                "first_name": "Org2",
                "last_name": "Admin",
                "organization_name": "Healthcare Org 2"
            }
            
            response = requests.post(f"{self.api_url}/auth/signup", json=signup_data, timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                self.org2_token = data.get('access_token')
                # Extract organization_id from organization object
                org_data = data.get('organization', {})
                self.org2_id = org_data.get('id')
                success = self.org2_token is not None and self.org2_id is not None
                details = f"Token: {self.org2_token[:20]}..., Org ID: {self.org2_id}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Signup Organization 2", success, details)
            return success
        except Exception as e:
            self.log_test("Signup Organization 2", False, str(e))
            return False
    
    def test_auth_me_org1(self):
        """Test /auth/me endpoint for org1"""
        try:
            headers = {"Authorization": f"Bearer {self.org1_token}"}
            response = requests.get(f"{self.api_url}/auth/me", headers=headers, timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                has_email = data.get('email') is not None and data.get('email') != ""
                has_org = data.get('organization_id') is not None and data.get('organization_id') != ""
                success = has_email and has_org
                details = f"Email: {data.get('email')}, Org: {data.get('organization_id')}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("/auth/me Endpoint (Org1)", success, details)
            return success
        except Exception as e:
            self.log_test("/auth/me Endpoint (Org1)", False, str(e))
            return False
    
    def test_auth_me_org2(self):
        """Test /auth/me endpoint for org2"""
        try:
            headers = {"Authorization": f"Bearer {self.org2_token}"}
            response = requests.get(f"{self.api_url}/auth/me", headers=headers, timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                has_email = data.get('email') is not None and data.get('email') != ""
                has_org = data.get('organization_id') is not None and data.get('organization_id') != ""
                success = has_email and has_org
                details = f"Email: {data.get('email')}, Org: {data.get('organization_id')}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("/auth/me Endpoint (Org2)", success, details)
            return success
        except Exception as e:
            self.log_test("/auth/me Endpoint (Org2)", False, str(e))
            return False
    
    # ========================================
    # Patient CRUD Tests with Multi-Tenancy
    # ========================================
    
    def test_create_patient_org1(self):
        """Test creating patient for org1 (should NOT require organization_id in body)"""
        try:
            headers = {"Authorization": f"Bearer {self.org1_token}"}
            patient_data = {
                "first_name": "John",
                "last_name": "Doe",
                "sex": "Male",
                "date_of_birth": "1980-01-15",
                "address_street": "123 Main St",
                "address_city": "Columbus",
                "address_state": "OH",
                "address_zip": "43215",
                "medicaid_number": "111111111111",
                "prior_auth_number": "PA123",
                "icd10_code": "Z00.00",
                "physician_name": "Dr. Smith",
                "physician_npi": "1234567890"
                # NOTE: NOT including organization_id - should be extracted from JWT
            }
            
            response = requests.post(f"{self.api_url}/patients", json=patient_data, headers=headers, timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                self.org1_patient_id = data.get('id')
                # Verify organization_id was set correctly
                org_id_correct = data.get('organization_id') == self.org1_id
                success = org_id_correct
                details = f"Patient ID: {self.org1_patient_id}, Org ID: {data.get('organization_id')}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:300]}"
            
            self.log_test("Create Patient Org1 (JWT extraction)", success, details)
            return success
        except Exception as e:
            self.log_test("Create Patient Org1 (JWT extraction)", False, str(e))
            return False
    
    def test_create_patient_org2(self):
        """Test creating patient for org2"""
        try:
            headers = {"Authorization": f"Bearer {self.org2_token}"}
            patient_data = {
                "first_name": "Jane",
                "last_name": "Smith",
                "sex": "Female",
                "date_of_birth": "1985-05-20",
                "address_street": "456 Oak Ave",
                "address_city": "Cleveland",
                "address_state": "OH",
                "address_zip": "44115",
                "medicaid_number": "222222222222",
                "prior_auth_number": "PA456",
                "icd10_code": "Z00.01",
                "physician_name": "Dr. Johnson",
                "physician_npi": "9876543210"
            }
            
            response = requests.post(f"{self.api_url}/patients", json=patient_data, headers=headers, timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                self.org2_patient_id = data.get('id')
                org_id_correct = data.get('organization_id') == self.org2_id
                success = org_id_correct
                details = f"Patient ID: {self.org2_patient_id}, Org ID: {data.get('organization_id')}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:300]}"
            
            self.log_test("Create Patient Org2", success, details)
            return success
        except Exception as e:
            self.log_test("Create Patient Org2", False, str(e))
            return False
    
    def test_get_patients_org1_isolation(self):
        """Test that org1 can only see their own patients"""
        try:
            headers = {"Authorization": f"Bearer {self.org1_token}"}
            response = requests.get(f"{self.api_url}/patients", headers=headers, timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                # Should only see org1's patient
                patient_ids = [p.get('id') for p in data]
                has_org1_patient = self.org1_patient_id in patient_ids
                has_org2_patient = self.org2_patient_id in patient_ids
                
                success = has_org1_patient and not has_org2_patient
                details = f"Count: {len(data)}, Has Org1: {has_org1_patient}, Has Org2: {has_org2_patient}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Get Patients Org1 (Data Isolation)", success, details)
            return success
        except Exception as e:
            self.log_test("Get Patients Org1 (Data Isolation)", False, str(e))
            return False
    
    def test_get_patients_org2_isolation(self):
        """Test that org2 can only see their own patients"""
        try:
            headers = {"Authorization": f"Bearer {self.org2_token}"}
            response = requests.get(f"{self.api_url}/patients", headers=headers, timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                patient_ids = [p.get('id') for p in data]
                has_org1_patient = self.org1_patient_id in patient_ids
                has_org2_patient = self.org2_patient_id in patient_ids
                
                success = not has_org1_patient and has_org2_patient
                details = f"Count: {len(data)}, Has Org1: {has_org1_patient}, Has Org2: {has_org2_patient}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Get Patients Org2 (Data Isolation)", success, details)
            return success
        except Exception as e:
            self.log_test("Get Patients Org2 (Data Isolation)", False, str(e))
            return False
    
    # ========================================
    # Employee CRUD Tests with Multi-Tenancy
    # ========================================
    
    def test_create_employee_org1(self):
        """Test creating employee for org1 (should NOT require organization_id in body)"""
        try:
            headers = {"Authorization": f"Bearer {self.org1_token}"}
            employee_data = {
                "first_name": "Alice",
                "last_name": "Worker",
                "ssn": "111223333",
                "date_of_birth": "1990-03-10",
                "sex": "Female",
                "email": "alice.worker@org1.com",
                "phone": "6145551111",
                "address_street": "789 Elm St",
                "address_city": "Columbus",
                "address_state": "OH",
                "address_zip": "43215",
                "employee_id": "EMP001",
                "hire_date": "2023-01-01",
                "job_title": "Home Health Aide",
                "employment_status": "Full-time",
                "emergency_contact_name": "Bob Worker",
                "emergency_contact_phone": "6145552222",
                "emergency_contact_relation": "Spouse"
            }
            
            response = requests.post(f"{self.api_url}/employees", json=employee_data, headers=headers, timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                self.org1_employee_id = data.get('id')
                org_id_correct = data.get('organization_id') == self.org1_id
                success = org_id_correct
                details = f"Employee ID: {self.org1_employee_id}, Org ID: {data.get('organization_id')}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:300]}"
            
            self.log_test("Create Employee Org1 (JWT extraction)", success, details)
            return success
        except Exception as e:
            self.log_test("Create Employee Org1 (JWT extraction)", False, str(e))
            return False
    
    def test_create_employee_org2(self):
        """Test creating employee for org2"""
        try:
            headers = {"Authorization": f"Bearer {self.org2_token}"}
            employee_data = {
                "first_name": "Bob",
                "last_name": "Helper",
                "ssn": "444556666",
                "date_of_birth": "1988-07-22",
                "sex": "Male",
                "email": "bob.helper@org2.com",
                "phone": "2165553333",
                "address_street": "321 Pine Ave",
                "address_city": "Cleveland",
                "address_state": "OH",
                "address_zip": "44115",
                "employee_id": "EMP002",
                "hire_date": "2023-02-01",
                "job_title": "Personal Care Assistant",
                "employment_status": "Part-time",
                "emergency_contact_name": "Carol Helper",
                "emergency_contact_phone": "2165554444",
                "emergency_contact_relation": "Sister"
            }
            
            response = requests.post(f"{self.api_url}/employees", json=employee_data, headers=headers, timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                self.org2_employee_id = data.get('id')
                org_id_correct = data.get('organization_id') == self.org2_id
                success = org_id_correct
                details = f"Employee ID: {self.org2_employee_id}, Org ID: {data.get('organization_id')}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:300]}"
            
            self.log_test("Create Employee Org2", success, details)
            return success
        except Exception as e:
            self.log_test("Create Employee Org2", False, str(e))
            return False
    
    def test_get_employees_org1_isolation(self):
        """Test that org1 can only see their own employees"""
        try:
            headers = {"Authorization": f"Bearer {self.org1_token}"}
            response = requests.get(f"{self.api_url}/employees", headers=headers, timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                employee_ids = [e.get('id') for e in data]
                has_org1_employee = self.org1_employee_id in employee_ids
                has_org2_employee = self.org2_employee_id in employee_ids
                
                success = has_org1_employee and not has_org2_employee
                details = f"Count: {len(data)}, Has Org1: {has_org1_employee}, Has Org2: {has_org2_employee}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Get Employees Org1 (Data Isolation)", success, details)
            return success
        except Exception as e:
            self.log_test("Get Employees Org1 (Data Isolation)", False, str(e))
            return False
    
    def test_get_employees_org2_isolation(self):
        """Test that org2 can only see their own employees"""
        try:
            headers = {"Authorization": f"Bearer {self.org2_token}"}
            response = requests.get(f"{self.api_url}/employees", headers=headers, timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                employee_ids = [e.get('id') for e in data]
                has_org1_employee = self.org1_employee_id in employee_ids
                has_org2_employee = self.org2_employee_id in employee_ids
                
                success = not has_org1_employee and has_org2_employee
                details = f"Count: {len(data)}, Has Org1: {has_org1_employee}, Has Org2: {has_org2_employee}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Get Employees Org2 (Data Isolation)", success, details)
            return success
        except Exception as e:
            self.log_test("Get Employees Org2 (Data Isolation)", False, str(e))
            return False
    
    # ========================================
    # Insurance Contract Tests (CRITICAL FIX)
    # ========================================
    
    def test_create_insurance_contract_org1(self):
        """Test creating insurance contract for org1"""
        try:
            headers = {"Authorization": f"Bearer {self.org1_token}"}
            contract_data = {
                "payer_name": "Ohio Medicaid - Org1",
                "insurance_type": "Medicaid",
                "contract_number": "ORG1-CONTRACT-001",
                "start_date": "2024-01-01",
                "contact_person": "John Contract",
                "contact_phone": "6145551234",
                "contact_email": "john@org1.com",
                "is_active": True,
                "billable_services": [
                    {
                        "service_code": "T1019",
                        "service_name": "Personal Care",
                        "is_active": True
                    }
                ]
            }
            
            response = requests.post(f"{self.api_url}/insurance-contracts", json=contract_data, headers=headers, timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                self.org1_contract_id = data.get('id')
                org_id_correct = data.get('organization_id') == self.org1_id
                success = org_id_correct
                details = f"Contract ID: {self.org1_contract_id}, Org ID: {data.get('organization_id')}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:300]}"
            
            self.log_test("Create Insurance Contract Org1", success, details)
            return success
        except Exception as e:
            self.log_test("Create Insurance Contract Org1", False, str(e))
            return False
    
    def test_create_insurance_contract_org2(self):
        """Test creating insurance contract for org2"""
        try:
            headers = {"Authorization": f"Bearer {self.org2_token}"}
            contract_data = {
                "payer_name": "Ohio Medicaid - Org2",
                "insurance_type": "Medicaid",
                "contract_number": "ORG2-CONTRACT-001",
                "start_date": "2024-01-01",
                "contact_person": "Jane Contract",
                "contact_phone": "2165555678",
                "contact_email": "jane@org2.com",
                "is_active": True,
                "billable_services": [
                    {
                        "service_code": "T1020",
                        "service_name": "Home Health Aide",
                        "is_active": True
                    }
                ]
            }
            
            response = requests.post(f"{self.api_url}/insurance-contracts", json=contract_data, headers=headers, timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                self.org2_contract_id = data.get('id')
                org_id_correct = data.get('organization_id') == self.org2_id
                success = org_id_correct
                details = f"Contract ID: {self.org2_contract_id}, Org ID: {data.get('organization_id')}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:300]}"
            
            self.log_test("Create Insurance Contract Org2", success, details)
            return success
        except Exception as e:
            self.log_test("Create Insurance Contract Org2", False, str(e))
            return False
    
    def test_get_insurance_contracts_org1_isolation(self):
        """CRITICAL: Test that org1 can only see their own insurance contracts (NO DATA LEAKAGE)"""
        try:
            headers = {"Authorization": f"Bearer {self.org1_token}"}
            response = requests.get(f"{self.api_url}/insurance-contracts", headers=headers, timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                contract_ids = [c.get('id') for c in data]
                has_org1_contract = self.org1_contract_id in contract_ids
                has_org2_contract = self.org2_contract_id in contract_ids
                
                # CRITICAL: Should NOT see org2's contract
                success = has_org1_contract and not has_org2_contract
                details = f"Count: {len(data)}, Has Org1: {has_org1_contract}, Has Org2 (SHOULD BE FALSE): {has_org2_contract}"
                
                if has_org2_contract:
                    details += " ⚠️ DATA LEAKAGE DETECTED!"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Get Insurance Contracts Org1 (NO DATA LEAKAGE)", success, details)
            return success
        except Exception as e:
            self.log_test("Get Insurance Contracts Org1 (NO DATA LEAKAGE)", False, str(e))
            return False
    
    def test_get_insurance_contracts_org2_isolation(self):
        """CRITICAL: Test that org2 can only see their own insurance contracts (NO DATA LEAKAGE)"""
        try:
            headers = {"Authorization": f"Bearer {self.org2_token}"}
            response = requests.get(f"{self.api_url}/insurance-contracts", headers=headers, timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                contract_ids = [c.get('id') for c in data]
                has_org1_contract = self.org1_contract_id in contract_ids
                has_org2_contract = self.org2_contract_id in contract_ids
                
                # CRITICAL: Should NOT see org1's contract
                success = not has_org1_contract and has_org2_contract
                details = f"Count: {len(data)}, Has Org1 (SHOULD BE FALSE): {has_org1_contract}, Has Org2: {has_org2_contract}"
                
                if has_org1_contract:
                    details += " ⚠️ DATA LEAKAGE DETECTED!"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Get Insurance Contracts Org2 (NO DATA LEAKAGE)", success, details)
            return success
        except Exception as e:
            self.log_test("Get Insurance Contracts Org2 (NO DATA LEAKAGE)", False, str(e))
            return False
    
    # ========================================
    # Service Code Tests
    # ========================================
    
    def test_create_service_code_org1(self):
        """Test creating service code for org1 (should NOT require organization_id in body)"""
        try:
            headers = {"Authorization": f"Bearer {self.org1_token}"}
            service_data = {
                "service_name": "Personal Care - Org1",
                "service_code_internal": "PC001",
                "payer": "ODM",
                "payer_program": "SP",
                "procedure_code": "T1019",
                "service_description": "Personal care services",
                "service_category": "Personal Care",
                "effective_start_date": "2024-01-01",
                "is_active": True
            }
            
            response = requests.post(f"{self.api_url}/service-codes", json=service_data, headers=headers, timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                self.org1_service_id = data.get('id')
                org_id_correct = data.get('organization_id') == self.org1_id
                success = org_id_correct
                details = f"Service ID: {self.org1_service_id}, Org ID: {data.get('organization_id')}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:300]}"
            
            self.log_test("Create Service Code Org1 (JWT extraction)", success, details)
            return success
        except Exception as e:
            self.log_test("Create Service Code Org1 (JWT extraction)", False, str(e))
            return False
    
    def test_create_service_code_org2(self):
        """Test creating service code for org2"""
        try:
            headers = {"Authorization": f"Bearer {self.org2_token}"}
            service_data = {
                "service_name": "Home Health Aide - Org2",
                "service_code_internal": "HHA001",
                "payer": "ODM",
                "payer_program": "SP",
                "procedure_code": "T1020",
                "service_description": "Home health aide services",
                "service_category": "Home Health",
                "effective_start_date": "2024-01-01",
                "is_active": True
            }
            
            response = requests.post(f"{self.api_url}/service-codes", json=service_data, headers=headers, timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                self.org2_service_id = data.get('id')
                org_id_correct = data.get('organization_id') == self.org2_id
                success = org_id_correct
                details = f"Service ID: {self.org2_service_id}, Org ID: {data.get('organization_id')}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:300]}"
            
            self.log_test("Create Service Code Org2", success, details)
            return success
        except Exception as e:
            self.log_test("Create Service Code Org2", False, str(e))
            return False
    
    def test_get_service_codes_org1_isolation(self):
        """Test that org1 can only see their own service codes"""
        try:
            headers = {"Authorization": f"Bearer {self.org1_token}"}
            response = requests.get(f"{self.api_url}/service-codes", headers=headers, timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                service_ids = [s.get('id') for s in data]
                has_org1_service = self.org1_service_id in service_ids
                has_org2_service = self.org2_service_id in service_ids
                
                success = has_org1_service and not has_org2_service
                details = f"Count: {len(data)}, Has Org1: {has_org1_service}, Has Org2: {has_org2_service}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Get Service Codes Org1 (Data Isolation)", success, details)
            return success
        except Exception as e:
            self.log_test("Get Service Codes Org1 (Data Isolation)", False, str(e))
            return False
    
    def test_get_service_codes_org2_isolation(self):
        """Test that org2 can only see their own service codes"""
        try:
            headers = {"Authorization": f"Bearer {self.org2_token}"}
            response = requests.get(f"{self.api_url}/service-codes", headers=headers, timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                service_ids = [s.get('id') for s in data]
                has_org1_service = self.org1_service_id in service_ids
                has_org2_service = self.org2_service_id in service_ids
                
                success = not has_org1_service and has_org2_service
                details = f"Count: {len(data)}, Has Org1: {has_org1_service}, Has Org2: {has_org2_service}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Get Service Codes Org2 (Data Isolation)", success, details)
            return success
        except Exception as e:
            self.log_test("Get Service Codes Org2 (Data Isolation)", False, str(e))
            return False
    
    # ========================================
    # Claims Tests
    # ========================================
    
    def test_create_claim_org1(self):
        """Test creating claim for org1"""
        try:
            headers = {"Authorization": f"Bearer {self.org1_token}"}
            claim_data = {
                "claim_number": "CLM-ORG1-001",
                "patient_id": self.org1_patient_id,
                "patient_name": "John Doe",
                "patient_medicaid_number": "111111111111",
                "payer_id": self.org1_contract_id,
                "payer_name": "Ohio Medicaid - Org1",
                "service_period_start": "2024-01-01",
                "service_period_end": "2024-01-31",
                "line_items": [
                    {
                        "date_of_service": "2024-01-15",
                        "employee_name": "Alice Worker",
                        "service_code": "T1019",
                        "service_name": "Personal Care",
                        "units": 32,
                        "rate_per_unit": 15.0,
                        "amount": 480.0
                    }
                ],
                "total_units": 32,
                "total_amount": 480.0,
                "status": "draft"
            }
            
            response = requests.post(f"{self.api_url}/claims", json=claim_data, headers=headers, timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                self.org1_claim_id = data.get('id')
                org_id_correct = data.get('organization_id') == self.org1_id
                success = org_id_correct
                details = f"Claim ID: {self.org1_claim_id}, Org ID: {data.get('organization_id')}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:300]}"
            
            self.log_test("Create Claim Org1", success, details)
            return success
        except Exception as e:
            self.log_test("Create Claim Org1", False, str(e))
            return False
    
    def test_create_claim_org2(self):
        """Test creating claim for org2"""
        try:
            headers = {"Authorization": f"Bearer {self.org2_token}"}
            claim_data = {
                "claim_number": "CLM-ORG2-001",
                "patient_id": self.org2_patient_id,
                "patient_name": "Jane Smith",
                "patient_medicaid_number": "222222222222",
                "payer_id": self.org2_contract_id,
                "payer_name": "Ohio Medicaid - Org2",
                "service_period_start": "2024-01-01",
                "service_period_end": "2024-01-31",
                "line_items": [
                    {
                        "date_of_service": "2024-01-20",
                        "employee_name": "Bob Helper",
                        "service_code": "T1020",
                        "service_name": "Home Health Aide",
                        "units": 24,
                        "rate_per_unit": 18.0,
                        "amount": 432.0
                    }
                ],
                "total_units": 24,
                "total_amount": 432.0,
                "status": "draft"
            }
            
            response = requests.post(f"{self.api_url}/claims", json=claim_data, headers=headers, timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                self.org2_claim_id = data.get('id')
                org_id_correct = data.get('organization_id') == self.org2_id
                success = org_id_correct
                details = f"Claim ID: {self.org2_claim_id}, Org ID: {data.get('organization_id')}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:300]}"
            
            self.log_test("Create Claim Org2", success, details)
            return success
        except Exception as e:
            self.log_test("Create Claim Org2", False, str(e))
            return False
    
    def test_get_claims_org1_isolation(self):
        """Test that org1 can only see their own claims"""
        try:
            headers = {"Authorization": f"Bearer {self.org1_token}"}
            response = requests.get(f"{self.api_url}/claims", headers=headers, timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                claim_ids = [c.get('id') for c in data]
                has_org1_claim = self.org1_claim_id in claim_ids
                has_org2_claim = self.org2_claim_id in claim_ids
                
                success = has_org1_claim and not has_org2_claim
                details = f"Count: {len(data)}, Has Org1: {has_org1_claim}, Has Org2: {has_org2_claim}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Get Claims Org1 (Data Isolation)", success, details)
            return success
        except Exception as e:
            self.log_test("Get Claims Org1 (Data Isolation)", False, str(e))
            return False
    
    def test_get_claims_org2_isolation(self):
        """Test that org2 can only see their own claims"""
        try:
            headers = {"Authorization": f"Bearer {self.org2_token}"}
            response = requests.get(f"{self.api_url}/claims", headers=headers, timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                claim_ids = [c.get('id') for c in data]
                has_org1_claim = self.org1_claim_id in claim_ids
                has_org2_claim = self.org2_claim_id in claim_ids
                
                success = not has_org1_claim and has_org2_claim
                details = f"Count: {len(data)}, Has Org1: {has_org1_claim}, Has Org2: {has_org2_claim}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Get Claims Org2 (Data Isolation)", success, details)
            return success
        except Exception as e:
            self.log_test("Get Claims Org2 (Data Isolation)", False, str(e))
            return False
    
    # ========================================
    # Main Test Runner
    # ========================================
    
    def run_all_tests(self):
        """Run comprehensive multi-tenant backend tests"""
        print("=" * 80)
        print("🚀 COMPREHENSIVE MULTI-TENANT SAAS BACKEND TESTING")
        print("=" * 80)
        print("\nTesting all fixes from review request:")
        print("1. ✓ Data leakage in insurance contracts")
        print("2. ✓ PatientProfile organization_id field")
        print("3. ✓ /auth/me endpoint")
        print("4. ✓ Patient/Employee/Service Code creation (organization_id from JWT)")
        print("5. ✓ Multi-tenancy isolation across all endpoints")
        print("\n" + "=" * 80)
        
        # Phase 1: Authentication
        print("\n📝 PHASE 1: AUTHENTICATION")
        print("-" * 80)
        if not self.test_signup_org1():
            print("❌ Cannot proceed without org1 signup")
            return self.get_results()
        if not self.test_signup_org2():
            print("❌ Cannot proceed without org2 signup")
            return self.get_results()
        
        self.test_auth_me_org1()
        self.test_auth_me_org2()
        
        # Phase 2: Patient Multi-Tenancy
        print("\n👥 PHASE 2: PATIENT MULTI-TENANCY")
        print("-" * 80)
        self.test_create_patient_org1()
        self.test_create_patient_org2()
        self.test_get_patients_org1_isolation()
        self.test_get_patients_org2_isolation()
        
        # Phase 3: Employee Multi-Tenancy
        print("\n👷 PHASE 3: EMPLOYEE MULTI-TENANCY")
        print("-" * 80)
        self.test_create_employee_org1()
        self.test_create_employee_org2()
        self.test_get_employees_org1_isolation()
        self.test_get_employees_org2_isolation()
        
        # Phase 4: Insurance Contract Multi-Tenancy (CRITICAL)
        print("\n🏥 PHASE 4: INSURANCE CONTRACT MULTI-TENANCY (CRITICAL FIX)")
        print("-" * 80)
        self.test_create_insurance_contract_org1()
        self.test_create_insurance_contract_org2()
        self.test_get_insurance_contracts_org1_isolation()
        self.test_get_insurance_contracts_org2_isolation()
        
        # Phase 5: Service Code Multi-Tenancy
        print("\n📋 PHASE 5: SERVICE CODE MULTI-TENANCY")
        print("-" * 80)
        self.test_create_service_code_org1()
        self.test_create_service_code_org2()
        self.test_get_service_codes_org1_isolation()
        self.test_get_service_codes_org2_isolation()
        
        # Phase 6: Claims Multi-Tenancy
        print("\n💰 PHASE 6: CLAIMS MULTI-TENANCY")
        print("-" * 80)
        self.test_create_claim_org1()
        self.test_create_claim_org2()
        self.test_get_claims_org1_isolation()
        self.test_get_claims_org2_isolation()
        
        return self.get_results()


if __name__ == "__main__":
    tester = MultiTenantTester()
    exit_code = tester.run_all_tests()
    sys.exit(exit_code)
