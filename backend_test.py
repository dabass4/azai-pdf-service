import requests
import sys
import json
import os
from datetime import datetime, timezone
from pathlib import Path
import tempfile
import uuid

class TimesheetAPITester:
    def __init__(self, base_url="https://timescan-app.preview.emergentagent.com"):
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

    def run_evv_tests(self):
        """Run comprehensive EVV API tests"""
        print("\n🏥 Starting Ohio Medicaid EVV Backend Tests")
        print(f"Testing against: {self.api_url}")
        print("=" * 60)
        
        # Test basic connectivity first
        if not self.test_root_endpoint():
            print("❌ Root endpoint failed - stopping EVV tests")
            return self.get_results()
        
        # Step 1: Create business entity (required for other operations)
        business_entity_id = self.test_create_business_entity()
        if not business_entity_id:
            print("❌ Business entity creation failed - stopping EVV tests")
            return self.get_results()
        
        # Step 2: Test business entity endpoints
        self.test_get_business_entities()
        self.test_get_active_business_entity()
        
        # Step 3: Create sample patient with EVV fields
        patient_id = self.test_create_patient_with_evv_fields()
        
        # Step 4: Create sample employee with DCW fields  
        employee_id = self.test_create_employee_with_dcw_fields()
        
        # Step 5: Create sample EVV visit
        visit_id = self.test_create_evv_visit(patient_id, employee_id)
        
        # Step 6: Test EVV visit management
        if visit_id:
            self.test_get_evv_visits()
            self.test_get_specific_evv_visit(visit_id)
            self.test_update_evv_visit(visit_id)
        
        # Step 7: Test export functionality
        self.test_export_individuals()
        self.test_export_direct_care_workers()
        self.test_export_visits()
        
        # Step 8: Test submission to mock aggregator
        individual_txn_id = self.test_submit_individuals()
        dcw_txn_id = self.test_submit_direct_care_workers()
        visit_txn_id = self.test_submit_visits()
        
        # Step 9: Query submission status
        if individual_txn_id:
            self.test_query_evv_status(individual_txn_id)
        if dcw_txn_id:
            self.test_query_evv_status(dcw_txn_id)
        if visit_txn_id:
            self.test_query_evv_status(visit_txn_id)
        
        # Step 10: Test transmission history
        self.test_get_evv_transmissions()
        
        # Step 11: Test reference data endpoints
        self.test_get_evv_payers()
        self.test_get_evv_programs()
        self.test_get_evv_procedure_codes()
        self.test_get_evv_exception_codes()
        
        # Step 12: Cleanup - delete test visit
        if visit_id:
            self.test_delete_evv_visit(visit_id)
        
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

    # ========================================
    # EVV Test Methods
    # ========================================
    
    def test_create_business_entity(self):
        """Test creating business entity configuration"""
        try:
            entity_data = {
                "business_entity_id": "OHIOTEST01",
                "business_entity_medicaid_id": "1234567",
                "agency_name": "Ohio Test Healthcare Agency",
                "contact_name": "Sarah Johnson",
                "contact_email": "sarah.johnson@ohiotest.com",
                "contact_phone": "6145551234",
                "is_active": True
            }
            
            response = requests.post(f"{self.api_url}/evv/business-entity", 
                                   json=entity_data, timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                entity_id = data.get('id')
                details = f"Status: {response.status_code}, Entity ID: {entity_id}"
                self.log_test("Create Business Entity", success, details)
                return entity_id
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
                self.log_test("Create Business Entity", success, details)
                return None
        except Exception as e:
            self.log_test("Create Business Entity", False, str(e))
            return None
    
    def test_get_business_entities(self):
        """Test getting all business entities"""
        try:
            response = requests.get(f"{self.api_url}/evv/business-entity", timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                success = isinstance(data, list)
                details = f"Status: {response.status_code}, Count: {len(data) if isinstance(data, list) else 'N/A'}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Get Business Entities", success, details)
            return success
        except Exception as e:
            self.log_test("Get Business Entities", False, str(e))
            return False
    
    def test_get_active_business_entity(self):
        """Test getting active business entity"""
        try:
            response = requests.get(f"{self.api_url}/evv/business-entity/active", timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                has_required_fields = all(key in data for key in ['business_entity_id', 'business_entity_medicaid_id', 'is_active'])
                success = success and has_required_fields and data.get('is_active') == True
                details = f"Status: {response.status_code}, Entity: {data.get('business_entity_id')}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Get Active Business Entity", success, details)
            return success
        except Exception as e:
            self.log_test("Get Active Business Entity", False, str(e))
            return False
    
    def test_create_patient_with_evv_fields(self):
        """Test creating patient with EVV fields"""
        try:
            patient_data = {
                "first_name": "Maria",
                "last_name": "Rodriguez",
                "sex": "Female",
                "date_of_birth": "1985-03-15",
                "address_street": "123 Main Street",
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
            
            response = requests.post(f"{self.api_url}/patients", 
                                   json=patient_data, timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                patient_id = data.get('id')
                has_evv_fields = all(key in data for key in ['address_latitude', 'address_longitude', 'timezone'])
                success = success and has_evv_fields
                details = f"Status: {response.status_code}, Patient ID: {patient_id}"
                self.log_test("Create Patient with EVV Fields", success, details)
                return patient_id
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
                self.log_test("Create Patient with EVV Fields", success, details)
                return None
        except Exception as e:
            self.log_test("Create Patient with EVV Fields", False, str(e))
            return None
    
    def test_create_employee_with_dcw_fields(self):
        """Test creating employee with DCW fields"""
        try:
            employee_data = {
                "first_name": "John",
                "last_name": "Smith",
                "ssn": "123456789",
                "date_of_birth": "1990-05-20",
                "sex": "Male",
                "email": "john.smith@ohiotest.com",
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
            
            response = requests.post(f"{self.api_url}/employees", 
                                   json=employee_data, timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                employee_id = data.get('id')
                has_dcw_fields = all(key in data for key in ['staff_pin', 'staff_other_id', 'staff_position'])
                success = success and has_dcw_fields
                details = f"Status: {response.status_code}, Employee ID: {employee_id}"
                self.log_test("Create Employee with DCW Fields", success, details)
                return employee_id
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
                self.log_test("Create Employee with DCW Fields", success, details)
                return None
        except Exception as e:
            self.log_test("Create Employee with DCW Fields", False, str(e))
            return None
    
    def test_create_evv_visit(self, patient_id, employee_id):
        """Test creating EVV visit record"""
        if not patient_id or not employee_id:
            self.log_test("Create EVV Visit", False, "Missing patient or employee ID")
            return None
        
        try:
            visit_data = {
                "visit_other_id": "VISIT001",
                "staff_other_id": "STAFF001",
                "patient_other_id": "PAT001",
                "patient_medicaid_id": "123456789012",
                "payer": "ODM",
                "payer_program": "Medicaid Fee-For-Service",
                "procedure_code": "T1019",
                "timezone": "America/New_York",
                "adj_in_datetime": "2024-01-15T09:00:00Z",
                "adj_out_datetime": "2024-01-15T17:00:00Z",
                "start_latitude": 39.9612,
                "start_longitude": -82.9988,
                "end_latitude": 39.9612,
                "end_longitude": -82.9988,
                "hours_to_bill": 8.0,
                "units_to_bill": 32,
                "member_verified_times": True,
                "member_verified_service": True,
                "calls": [
                    {
                        "call_external_id": "CALL001",
                        "call_datetime": "2024-01-15T09:00:00Z",
                        "call_assignment": "Call In",
                        "call_type": "Mobile",
                        "call_latitude": 39.9612,
                        "call_longitude": -82.9988,
                        "timezone": "America/New_York"
                    },
                    {
                        "call_external_id": "CALL002",
                        "call_datetime": "2024-01-15T17:00:00Z",
                        "call_assignment": "Call Out",
                        "call_type": "Mobile",
                        "call_latitude": 39.9612,
                        "call_longitude": -82.9988,
                        "timezone": "America/New_York"
                    }
                ]
            }
            
            response = requests.post(f"{self.api_url}/evv/visits", 
                                   json=visit_data, timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                visit_id = data.get('id')
                has_required_fields = all(key in data for key in ['visit_other_id', 'payer', 'procedure_code'])
                success = success and has_required_fields
                details = f"Status: {response.status_code}, Visit ID: {visit_id}"
                self.log_test("Create EVV Visit", success, details)
                return visit_id
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
                self.log_test("Create EVV Visit", success, details)
                return None
        except Exception as e:
            self.log_test("Create EVV Visit", False, str(e))
            return None
    
    def test_get_evv_visits(self):
        """Test getting all EVV visits"""
        try:
            response = requests.get(f"{self.api_url}/evv/visits", timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                success = isinstance(data, list)
                details = f"Status: {response.status_code}, Count: {len(data) if isinstance(data, list) else 'N/A'}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Get EVV Visits", success, details)
            return success
        except Exception as e:
            self.log_test("Get EVV Visits", False, str(e))
            return False
    
    def test_get_specific_evv_visit(self, visit_id):
        """Test getting specific EVV visit"""
        if not visit_id:
            self.log_test("Get Specific EVV Visit", False, "No visit ID provided")
            return False
        
        try:
            response = requests.get(f"{self.api_url}/evv/visits/{visit_id}", timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                has_required_fields = all(key in data for key in ['id', 'visit_other_id', 'payer'])
                success = success and has_required_fields
                details = f"Status: {response.status_code}, Visit: {data.get('visit_other_id')}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Get Specific EVV Visit", success, details)
            return success
        except Exception as e:
            self.log_test("Get Specific EVV Visit", False, str(e))
            return False
    
    def test_update_evv_visit(self, visit_id):
        """Test updating EVV visit"""
        if not visit_id:
            self.log_test("Update EVV Visit", False, "No visit ID provided")
            return False
        
        try:
            # First get the existing visit
            get_response = requests.get(f"{self.api_url}/evv/visits/{visit_id}", timeout=10)
            if get_response.status_code != 200:
                self.log_test("Update EVV Visit", False, "Could not fetch existing visit")
                return False
            
            visit_data = get_response.json()
            visit_data['visit_memo'] = "Updated visit memo for testing"
            visit_data['hours_to_bill'] = 7.5
            
            response = requests.put(f"{self.api_url}/evv/visits/{visit_id}", 
                                  json=visit_data, timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                success = data.get('visit_memo') == "Updated visit memo for testing"
                details = f"Status: {response.status_code}, Updated memo: {data.get('visit_memo')}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Update EVV Visit", success, details)
            return success
        except Exception as e:
            self.log_test("Update EVV Visit", False, str(e))
            return False
    
    def test_export_individuals(self):
        """Test exporting individuals"""
        try:
            response = requests.get(f"{self.api_url}/evv/export/individuals", timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                has_required_fields = all(key in data for key in ['status', 'record_type', 'record_count', 'data'])
                success = success and has_required_fields and data.get('record_type') == 'Individual'
                details = f"Status: {response.status_code}, Records: {data.get('record_count')}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Export Individuals", success, details)
            return success
        except Exception as e:
            self.log_test("Export Individuals", False, str(e))
            return False
    
    def test_export_direct_care_workers(self):
        """Test exporting direct care workers"""
        try:
            response = requests.get(f"{self.api_url}/evv/export/direct-care-workers", timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                has_required_fields = all(key in data for key in ['status', 'record_type', 'record_count', 'data'])
                success = success and has_required_fields and data.get('record_type') == 'DirectCareWorker'
                details = f"Status: {response.status_code}, Records: {data.get('record_count')}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Export Direct Care Workers", success, details)
            return success
        except Exception as e:
            self.log_test("Export Direct Care Workers", False, str(e))
            return False
    
    def test_export_visits(self):
        """Test exporting visits"""
        try:
            response = requests.get(f"{self.api_url}/evv/export/visits", timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                has_required_fields = all(key in data for key in ['status', 'record_type', 'record_count', 'data'])
                success = success and has_required_fields and data.get('record_type') == 'Visit'
                details = f"Status: {response.status_code}, Records: {data.get('record_count')}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Export Visits", success, details)
            return success
        except Exception as e:
            self.log_test("Export Visits", False, str(e))
            return False
    
    def test_submit_individuals(self):
        """Test submitting individuals to aggregator"""
        try:
            response = requests.post(f"{self.api_url}/evv/submit/individuals", timeout=30)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                has_required_fields = all(key in data for key in ['status', 'transaction_id'])
                success = success and has_required_fields and data.get('status') == 'success'
                transaction_id = data.get('transaction_id')
                details = f"Status: {response.status_code}, TxnID: {transaction_id}"
                self.log_test("Submit Individuals", success, details)
                return transaction_id
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
                self.log_test("Submit Individuals", success, details)
                return None
        except Exception as e:
            self.log_test("Submit Individuals", False, str(e))
            return None
    
    def test_submit_direct_care_workers(self):
        """Test submitting direct care workers to aggregator"""
        try:
            response = requests.post(f"{self.api_url}/evv/submit/direct-care-workers", timeout=30)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                has_required_fields = all(key in data for key in ['status', 'transaction_id'])
                success = success and has_required_fields and data.get('status') == 'success'
                transaction_id = data.get('transaction_id')
                details = f"Status: {response.status_code}, TxnID: {transaction_id}"
                self.log_test("Submit Direct Care Workers", success, details)
                return transaction_id
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
                self.log_test("Submit Direct Care Workers", success, details)
                return None
        except Exception as e:
            self.log_test("Submit Direct Care Workers", False, str(e))
            return None
    
    def test_submit_visits(self):
        """Test submitting visits to aggregator"""
        try:
            response = requests.post(f"{self.api_url}/evv/submit/visits", timeout=30)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                has_required_fields = all(key in data for key in ['status'])
                success = success and has_required_fields and data.get('status') == 'success'
                transaction_id = data.get('transaction_id')
                details = f"Status: {response.status_code}, TxnID: {transaction_id}"
                self.log_test("Submit Visits", success, details)
                return transaction_id
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
                self.log_test("Submit Visits", success, details)
                return None
        except Exception as e:
            self.log_test("Submit Visits", False, str(e))
            return None
    
    def test_query_evv_status(self, transaction_id):
        """Test querying EVV submission status"""
        if not transaction_id:
            self.log_test("Query EVV Status", False, "No transaction ID provided")
            return False
        
        try:
            response = requests.get(f"{self.api_url}/evv/status/{transaction_id}", timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                has_required_fields = all(key in data for key in ['status', 'transaction_id'])
                success = success and has_required_fields
                details = f"Status: {response.status_code}, TxnStatus: {data.get('overall_status', 'N/A')}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Query EVV Status", success, details)
            return success
        except Exception as e:
            self.log_test("Query EVV Status", False, str(e))
            return False
    
    def test_get_evv_transmissions(self):
        """Test getting EVV transmission history"""
        try:
            response = requests.get(f"{self.api_url}/evv/transmissions", timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                success = isinstance(data, list)
                details = f"Status: {response.status_code}, Count: {len(data) if isinstance(data, list) else 'N/A'}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Get EVV Transmissions", success, details)
            return success
        except Exception as e:
            self.log_test("Get EVV Transmissions", False, str(e))
            return False
    
    def test_get_evv_payers(self):
        """Test getting EVV payers reference data"""
        try:
            response = requests.get(f"{self.api_url}/evv/reference/payers", timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                has_payers = 'payers' in data and isinstance(data['payers'], list)
                success = success and has_payers
                details = f"Status: {response.status_code}, Payers: {len(data.get('payers', []))}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Get EVV Payers", success, details)
            return success
        except Exception as e:
            self.log_test("Get EVV Payers", False, str(e))
            return False
    
    def test_get_evv_programs(self):
        """Test getting EVV programs reference data"""
        try:
            response = requests.get(f"{self.api_url}/evv/reference/programs", timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                has_programs = 'programs' in data and isinstance(data['programs'], dict)
                success = success and has_programs
                details = f"Status: {response.status_code}, Programs: {len(data.get('programs', {}))}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Get EVV Programs", success, details)
            return success
        except Exception as e:
            self.log_test("Get EVV Programs", False, str(e))
            return False
    
    def test_get_evv_procedure_codes(self):
        """Test getting EVV procedure codes reference data"""
        try:
            response = requests.get(f"{self.api_url}/evv/reference/procedure-codes", timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                has_codes = 'procedure_codes' in data and isinstance(data['procedure_codes'], dict)
                success = success and has_codes
                details = f"Status: {response.status_code}, Codes: {len(data.get('procedure_codes', {}))}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Get EVV Procedure Codes", success, details)
            return success
        except Exception as e:
            self.log_test("Get EVV Procedure Codes", False, str(e))
            return False
    
    def test_get_evv_exception_codes(self):
        """Test getting EVV exception codes reference data"""
        try:
            response = requests.get(f"{self.api_url}/evv/reference/exception-codes", timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                has_codes = 'exception_codes' in data and isinstance(data['exception_codes'], dict)
                success = success and has_codes
                details = f"Status: {response.status_code}, Codes: {len(data.get('exception_codes', {}))}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Get EVV Exception Codes", success, details)
            return success
        except Exception as e:
            self.log_test("Get EVV Exception Codes", False, str(e))
            return False
    
    def test_delete_evv_visit(self, visit_id):
        """Test deleting EVV visit"""
        if not visit_id:
            self.log_test("Delete EVV Visit", False, "No visit ID provided")
            return False
        
        try:
            response = requests.delete(f"{self.api_url}/evv/visits/{visit_id}", timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                success = "message" in data
                details = f"Status: {response.status_code}, Message: {data.get('message', 'N/A')}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Delete EVV Visit", success, details)
            return success
        except Exception as e:
            self.log_test("Delete EVV Visit", False, str(e))
            return False

def main():
    tester = TimesheetAPITester()
    
    # Run both basic timesheet tests and EVV tests
    print("Running basic timesheet backend tests...")
    basic_result = tester.run_all_tests()
    
    # Reset test counters for EVV tests
    tester.tests_run = 0
    tester.tests_passed = 0
    tester.test_results = []
    
    print("\nRunning comprehensive Ohio Medicaid EVV backend tests...")
    evv_result = tester.run_evv_tests()
    
    return evv_result

if __name__ == "__main__":
    sys.exit(main())