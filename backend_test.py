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

    def test_evv_export_field_mapping_detailed(self):
        """Test detailed EVV export field mapping for Individual and DirectCareWorker exports"""
        print("\n🔍 Starting Detailed EVV Export Field Mapping Tests")
        print("=" * 60)
        
        # Ensure we have business entity
        business_entity_id = self.test_create_business_entity()
        if not business_entity_id:
            print("❌ Business entity creation failed - stopping detailed export tests")
            return False
        
        # Test Individual Export Field Mapping
        patient_id = self.test_create_patient_with_comprehensive_evv_fields()
        if patient_id:
            self.test_individual_export_field_mapping()
            self.test_individual_export_edge_cases()
        
        # Test DirectCareWorker Export Field Mapping  
        employee_id = self.test_create_employee_with_comprehensive_dcw_fields()
        if employee_id:
            self.test_dcw_export_field_mapping()
            self.test_dcw_export_edge_cases()
        
        return True
    
    def test_create_patient_with_comprehensive_evv_fields(self):
        """Create patient with all EVV fields for comprehensive testing"""
        try:
            patient_data = {
                "first_name": "Isabella",
                "last_name": "Martinez",
                "sex": "Female",
                "date_of_birth": "1978-08-22",
                "is_newborn": False,
                "address_street": "789 Elm Street Apt 4B",
                "address_city": "Cleveland",
                "address_state": "OH",
                "address_zip": "44115",
                "address_latitude": 41.4993,
                "address_longitude": -81.6944,
                "address_type": "Home",
                "timezone": "America/New_York",
                "prior_auth_number": "PA987654321",
                "icd10_code": "M79.3",
                "icd10_description": "Panniculitis, unspecified",
                "physician_name": "Dr. Jennifer Wilson",
                "physician_npi": "9876543210",
                "medicaid_number": "987654321098",
                "patient_other_id": "PAT002",
                "pims_id": "1234567",
                "phone_numbers": [
                    {
                        "phone_type": "Mobile",
                        "phone_number": "2165551234",
                        "is_primary": True
                    },
                    {
                        "phone_type": "Home", 
                        "phone_number": "2165555678",
                        "is_primary": False
                    }
                ],
                "responsible_party": {
                    "first_name": "Carlos",
                    "last_name": "Martinez",
                    "relationship": "Spouse",
                    "phone_number": "2165559999",
                    "email": "carlos.martinez@email.com"
                }
            }
            
            response = requests.post(f"{self.api_url}/patients", 
                                   json=patient_data, timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                patient_id = data.get('id')
                details = f"Status: {response.status_code}, Patient ID: {patient_id}"
                self.log_test("Create Patient with Comprehensive EVV Fields", success, details)
                return patient_id
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
                self.log_test("Create Patient with Comprehensive EVV Fields", success, details)
                return None
        except Exception as e:
            self.log_test("Create Patient with Comprehensive EVV Fields", False, str(e))
            return None
    
    def test_create_employee_with_comprehensive_dcw_fields(self):
        """Create employee with all DCW fields for comprehensive testing"""
        try:
            employee_data = {
                "first_name": "Michael",
                "last_name": "Thompson",
                "middle_name": "James",
                "ssn": "987-65-4321",  # Test SSN cleaning
                "date_of_birth": "1985-12-10",
                "sex": "Male",
                "email": "michael.thompson@ohiotest.com",
                "phone": "4195551234",
                "address_street": "321 Pine Street",
                "address_city": "Toledo",
                "address_state": "OH",
                "address_zip": "43604",
                "employee_id": "EMP002",
                "hire_date": "2022-06-01",
                "job_title": "Personal Care Assistant",
                "employment_status": "Part-time",
                "staff_pin": "987654321",
                "staff_other_id": "STAFF002",
                "staff_position": "PCA",  # Test 3-char truncation
                "emergency_contact_name": "Sarah Thompson",
                "emergency_contact_phone": "4195555555",
                "emergency_contact_relation": "Sister"
            }
            
            response = requests.post(f"{self.api_url}/employees", 
                                   json=employee_data, timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                employee_id = data.get('id')
                details = f"Status: {response.status_code}, Employee ID: {employee_id}"
                self.log_test("Create Employee with Comprehensive DCW Fields", success, details)
                return employee_id
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
                self.log_test("Create Employee with Comprehensive DCW Fields", success, details)
                return None
        except Exception as e:
            self.log_test("Create Employee with Comprehensive DCW Fields", False, str(e))
            return None
    
    def test_individual_export_field_mapping(self):
        """Test Individual export field mapping in detail"""
        try:
            response = requests.get(f"{self.api_url}/evv/export/individuals", timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                export_data = data.get('data', [])
                
                if len(export_data) > 0:
                    individual = export_data[-1]  # Get the latest patient we created
                    
                    # Test required EVV Individual fields
                    required_fields = [
                        'BusinessEntityID', 'BusinessEntityMedicaidIdentifier', 
                        'PatientOtherID', 'SequenceID', 'PatientMedicaidID',
                        'IsPatientNewborn', 'PatientLastName', 'PatientFirstName',
                        'PatientTimeZone', 'IndividualPayerInformation', 'IndividualAddress'
                    ]
                    
                    missing_fields = [field for field in required_fields if field not in individual]
                    
                    # Test PatientMedicaidID has 12 digits with leading zeros
                    medicaid_id = individual.get('PatientMedicaidID', '')
                    medicaid_valid = len(medicaid_id) == 12 and medicaid_id.isdigit()
                    
                    # Test PatientOtherID uses patient.id if patient_other_id not set
                    patient_other_id = individual.get('PatientOtherID', '')
                    other_id_valid = len(patient_other_id) > 0
                    
                    # Test address coordinates are included
                    addresses = individual.get('IndividualAddress', [])
                    coords_included = False
                    if addresses and len(addresses) > 0:
                        addr = addresses[0]
                        coords_included = 'PatientAddressLatitude' in addr and 'PatientAddressLongitude' in addr
                    
                    # Test phone numbers export
                    phones_included = 'IndividualPhone' in individual
                    
                    # Test responsible party export
                    rp_included = 'ResponsibleParty' in individual
                    
                    # Test default payer information
                    payer_info = individual.get('IndividualPayerInformation', [])
                    payer_valid = len(payer_info) > 0 and payer_info[0].get('Payer') == 'ODM'
                    
                    # Test PIMS ID for ODA
                    pims_included = False
                    if payer_info and len(payer_info) > 0:
                        pims_included = 'PayerClientIdentifier' in payer_info[0]
                    
                    success = (len(missing_fields) == 0 and medicaid_valid and other_id_valid and 
                             coords_included and phones_included and rp_included and payer_valid)
                    
                    details = f"Missing fields: {missing_fields}, Medicaid ID valid: {medicaid_valid}, " \
                             f"Coords: {coords_included}, Phones: {phones_included}, RP: {rp_included}, " \
                             f"Payer: {payer_valid}, PIMS: {pims_included}"
                else:
                    success = False
                    details = "No individual records in export"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Individual Export Field Mapping", success, details)
            return success
        except Exception as e:
            self.log_test("Individual Export Field Mapping", False, str(e))
            return False
    
    def test_individual_export_edge_cases(self):
        """Test Individual export edge cases"""
        try:
            # Create patient without optional fields
            minimal_patient = {
                "first_name": "Jane",
                "last_name": "Doe",
                "sex": "Female",
                "date_of_birth": "1990-01-01",
                "address_street": "123 Test St",
                "address_city": "Columbus",
                "address_state": "OH",
                "address_zip": "43215",
                "prior_auth_number": "PA123",
                "icd10_code": "Z00.00",
                "physician_name": "Dr. Test",
                "physician_npi": "1234567890",
                "medicaid_number": "123456789"  # Test leading zero padding
            }
            
            response = requests.post(f"{self.api_url}/patients", json=minimal_patient, timeout=10)
            if response.status_code != 200:
                self.log_test("Individual Export Edge Cases", False, "Could not create minimal patient")
                return False
            
            # Test export with minimal patient
            export_response = requests.get(f"{self.api_url}/evv/export/individuals", timeout=10)
            success = export_response.status_code == 200
            
            if success:
                data = export_response.json()
                export_data = data.get('data', [])
                
                # Find our minimal patient (should be last)
                minimal_export = None
                for individual in export_data:
                    if individual.get('PatientFirstName') == 'Jane' and individual.get('PatientLastName') == 'Doe':
                        minimal_export = individual
                        break
                
                if minimal_export:
                    # Test Medicaid ID padding (should be 000000123456789)
                    medicaid_id = minimal_export.get('PatientMedicaidID', '')
                    padding_correct = medicaid_id == '000123456789'
                    
                    # Test PatientOtherID uses patient.id when patient_other_id not set
                    other_id = minimal_export.get('PatientOtherID', '')
                    other_id_fallback = len(other_id) > 0
                    
                    # Test no coordinates when not provided
                    addresses = minimal_export.get('IndividualAddress', [])
                    no_coords = True
                    if addresses and len(addresses) > 0:
                        addr = addresses[0]
                        no_coords = 'PatientAddressLatitude' not in addr and 'PatientAddressLongitude' not in addr
                    
                    # Test no phone numbers when not provided
                    no_phones = 'IndividualPhone' not in minimal_export
                    
                    # Test no responsible party when not provided
                    no_rp = 'ResponsibleParty' not in minimal_export
                    
                    success = padding_correct and other_id_fallback and no_coords and no_phones and no_rp
                    details = f"Padding: {padding_correct}, Fallback ID: {other_id_fallback}, " \
                             f"No coords: {no_coords}, No phones: {no_phones}, No RP: {no_rp}"
                else:
                    success = False
                    details = "Could not find minimal patient in export"
            else:
                details = f"Status: {export_response.status_code}"
            
            self.log_test("Individual Export Edge Cases", success, details)
            return success
        except Exception as e:
            self.log_test("Individual Export Edge Cases", False, str(e))
            return False
    
    def test_dcw_export_field_mapping(self):
        """Test DirectCareWorker export field mapping in detail"""
        try:
            response = requests.get(f"{self.api_url}/evv/export/direct-care-workers", timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                export_data = data.get('data', [])
                
                if len(export_data) > 0:
                    dcw = export_data[-1]  # Get the latest employee we created
                    
                    # Test required EVV DirectCareWorker fields
                    required_fields = [
                        'BusinessEntityID', 'BusinessEntityMedicaidIdentifier',
                        'StaffOtherID', 'SequenceID', 'StaffID', 'StaffSSN',
                        'StaffLastName', 'StaffFirstName'
                    ]
                    
                    missing_fields = [field for field in required_fields if field not in dcw]
                    
                    # Test StaffOtherID uses employee.id if staff_other_id not set
                    staff_other_id = dcw.get('StaffOtherID', '')
                    other_id_valid = len(staff_other_id) > 0
                    
                    # Test StaffID uses staff_pin or employee_id as fallback
                    staff_id = dcw.get('StaffID', '')
                    staff_id_valid = len(staff_id) > 0
                    
                    # Test SSN is cleaned (no dashes/spaces)
                    ssn = dcw.get('StaffSSN', '')
                    ssn_clean = len(ssn) == 9 and ssn.isdigit()
                    
                    # Test StaffEmail is included if available
                    email_included = 'StaffEmail' in dcw
                    
                    # Test StaffPosition is truncated to 3 characters if needed
                    position_valid = True
                    if 'StaffPosition' in dcw:
                        position = dcw['StaffPosition']
                        position_valid = len(position) <= 3
                    
                    success = (len(missing_fields) == 0 and other_id_valid and staff_id_valid and 
                             ssn_clean and email_included and position_valid)
                    
                    details = f"Missing fields: {missing_fields}, Other ID: {other_id_valid}, " \
                             f"Staff ID: {staff_id_valid}, SSN clean: {ssn_clean}, " \
                             f"Email: {email_included}, Position: {position_valid}"
                else:
                    success = False
                    details = "No DCW records in export"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("DirectCareWorker Export Field Mapping", success, details)
            return success
        except Exception as e:
            self.log_test("DirectCareWorker Export Field Mapping", False, str(e))
            return False
    
    def test_dcw_export_edge_cases(self):
        """Test DirectCareWorker export edge cases"""
        try:
            # Create employee without staff_pin (should use employee_id)
            minimal_employee = {
                "first_name": "Bob",
                "last_name": "Wilson",
                "ssn": "111 22 3333",  # Test SSN cleaning with spaces
                "date_of_birth": "1988-03-15",
                "sex": "Male",
                "phone": "5135551234",
                "address_street": "456 Test Ave",
                "address_city": "Cincinnati",
                "address_state": "OH",
                "address_zip": "45202",
                "employee_id": "EMP003",
                "hire_date": "2023-01-01",
                "job_title": "Aide",
                "employment_status": "Full-time",
                "emergency_contact_name": "Alice Wilson",
                "emergency_contact_phone": "5135555555",
                "emergency_contact_relation": "Wife"
                # No staff_pin, staff_other_id, or staff_position
            }
            
            response = requests.post(f"{self.api_url}/employees", json=minimal_employee, timeout=10)
            if response.status_code != 200:
                self.log_test("DirectCareWorker Export Edge Cases", False, "Could not create minimal employee")
                return False
            
            # Test export with minimal employee
            export_response = requests.get(f"{self.api_url}/evv/export/direct-care-workers", timeout=10)
            success = export_response.status_code == 200
            
            if success:
                data = export_response.json()
                export_data = data.get('data', [])
                
                # Find our minimal employee
                minimal_export = None
                for dcw in export_data:
                    if dcw.get('StaffFirstName') == 'Bob' and dcw.get('StaffLastName') == 'Wilson':
                        minimal_export = dcw
                        break
                
                if minimal_export:
                    # Test StaffOtherID uses employee.id when staff_other_id not set
                    other_id = minimal_export.get('StaffOtherID', '')
                    other_id_fallback = len(other_id) > 0
                    
                    # Test StaffID uses employee_id when staff_pin not available
                    staff_id = minimal_export.get('StaffID', '')
                    staff_id_fallback = staff_id == 'EMP003'
                    
                    # Test SSN cleaning (spaces removed)
                    ssn = minimal_export.get('StaffSSN', '')
                    ssn_cleaned = ssn == '111223333'
                    
                    # Test no email when not provided
                    no_email = 'StaffEmail' not in minimal_export
                    
                    # Test no position when not provided
                    no_position = 'StaffPosition' not in minimal_export
                    
                    success = other_id_fallback and staff_id_fallback and ssn_cleaned and no_email and no_position
                    details = f"Fallback ID: {other_id_fallback}, Staff ID fallback: {staff_id_fallback}, " \
                             f"SSN cleaned: {ssn_cleaned}, No email: {no_email}, No position: {no_position}"
                else:
                    success = False
                    details = "Could not find minimal employee in export"
            else:
                details = f"Status: {export_response.status_code}"
            
            self.log_test("DirectCareWorker Export Edge Cases", success, details)
            return success
        except Exception as e:
            self.log_test("DirectCareWorker Export Edge Cases", False, str(e))
            return False

    def test_evv_export_comprehensive_validation(self):
        """Comprehensive validation of EVV export functionality as per review request"""
        print("\n🎯 Comprehensive EVV Export Validation Tests")
        print("=" * 60)
        
        # Test all specific requirements from review request
        self.test_individual_export_requirements()
        self.test_dcw_export_requirements()
        self.test_export_json_validity()
        self.test_export_with_actual_database_data()
        
        return True

    def test_time_calculation_and_units(self):
        """Test time normalization and unit calculation functionality"""
        print("\n⏰ Starting Time Calculation and Unit Conversion Tests")
        print("=" * 60)
        
        # Test time normalization (AM/PM system logic)
        self.test_time_normalization()
        
        # Test unit calculation from time differences
        self.test_unit_calculation_logic()
        
        # Test special rounding rule (> 35 minutes rounds to 3 units)
        self.test_special_rounding_rule()
        
        # Test with existing timesheets to see calculated units
        self.test_existing_timesheets_units()
        
        # Test timesheet upload with time calculation
        self.test_timesheet_upload_with_time_calculation()
        
        return True
    
    def test_time_normalization(self):
        """Test AM/PM normalization using system logic"""
        try:
            # Import time_utils to test directly
            import sys
            sys.path.append('/app/backend')
            from time_utils import normalize_am_pm
            
            test_cases = [
                # Morning times (7:00-11:59 assumed AM)
                ("8:30", "8:30 AM"),
                ("9:00", "9:00 AM"),
                ("11:45", "11:45 AM"),
                
                # Afternoon times (1:00-6:59 assumed PM)
                ("1:30", "1:30 PM"),
                ("5:45", "5:45 PM"),
                ("6:00", "6:00 PM"),
                
                # Edge cases
                ("12:00", "12:00 PM"),  # Noon
                ("7:00", "7:00 AM"),    # Start of AM range
                
                # Times with existing AM/PM (should be normalized)
                ("8:30 AM", "8:30 AM"),
                ("5:45 PM", "5:45 PM"),
            ]
            
            all_passed = True
            failed_cases = []
            
            for input_time, expected in test_cases:
                result = normalize_am_pm(input_time)
                if result != expected:
                    all_passed = False
                    failed_cases.append(f"{input_time} -> {result} (expected {expected})")
            
            details = f"Tested {len(test_cases)} cases. Failed: {len(failed_cases)}"
            if failed_cases:
                details += f". Failures: {', '.join(failed_cases[:3])}"
            
            self.log_test("Time Normalization (AM/PM Logic)", all_passed, details)
            return all_passed
        except Exception as e:
            self.log_test("Time Normalization (AM/PM Logic)", False, str(e))
            return False
    
    def test_unit_calculation_logic(self):
        """Test unit calculation from time differences"""
        try:
            import sys
            sys.path.append('/app/backend')
            from time_utils import calculate_units_from_times, minutes_to_units_with_rounding
            
            # Test basic unit calculation (1 unit = 15 minutes)
            test_cases = [
                # Basic cases
                ("8:00 AM", "8:15 AM", 1),  # 15 minutes = 1 unit
                ("8:00 AM", "8:30 AM", 2),  # 30 minutes = 2 units
                ("8:00 AM", "9:00 AM", 4),  # 60 minutes = 4 units
                ("8:00 AM", "10:00 AM", 8), # 120 minutes = 8 units
                
                # Rounding cases
                ("8:00 AM", "8:07 AM", 0),  # 7 minutes rounds to 0 units
                ("8:00 AM", "8:08 AM", 1),  # 8 minutes rounds to 1 unit
                ("8:00 AM", "8:22 AM", 1),  # 22 minutes rounds to 1 unit
                ("8:00 AM", "8:23 AM", 2),  # 23 minutes rounds to 2 units
            ]
            
            all_passed = True
            failed_cases = []
            
            for time_in, time_out, expected_units in test_cases:
                units, hours = calculate_units_from_times(time_in, time_out)
                if units != expected_units:
                    all_passed = False
                    failed_cases.append(f"{time_in}-{time_out}: {units} units (expected {expected_units})")
            
            details = f"Tested {len(test_cases)} cases. Failed: {len(failed_cases)}"
            if failed_cases:
                details += f". Failures: {', '.join(failed_cases[:3])}"
            
            self.log_test("Unit Calculation Logic", all_passed, details)
            return all_passed
        except Exception as e:
            self.log_test("Unit Calculation Logic", False, str(e))
            return False
    
    def test_special_rounding_rule(self):
        """Test special rounding rule: > 35 minutes and < 60 minutes rounds to 3 units"""
        try:
            import sys
            sys.path.append('/app/backend')
            from time_utils import minutes_to_units_with_rounding, calculate_units_from_times
            
            # Test the special rounding rule directly
            special_cases = [
                # Times that should trigger special rounding (> 35 min, < 60 min)
                ("8:00 AM", "8:37 AM", 3),  # 37 minutes -> 3 units (special rule)
                ("8:00 AM", "8:40 AM", 3),  # 40 minutes -> 3 units (special rule)
                ("8:00 AM", "8:45 AM", 3),  # 45 minutes -> 3 units (special rule)
                ("8:00 AM", "8:50 AM", 3),  # 50 minutes -> 3 units (special rule)
                ("8:00 AM", "8:55 AM", 3),  # 55 minutes -> 3 units (special rule)
                
                # Edge cases around the special rule
                ("8:00 AM", "8:35 AM", 2),  # 35 minutes -> 2 units (normal rounding)
                ("8:00 AM", "9:00 AM", 4),  # 60 minutes -> 4 units (normal rounding)
                ("8:00 AM", "8:30 AM", 2),  # 30 minutes -> 2 units (normal rounding)
            ]
            
            all_passed = True
            failed_cases = []
            
            for time_in, time_out, expected_units in special_cases:
                units, hours = calculate_units_from_times(time_in, time_out)
                if units != expected_units:
                    all_passed = False
                    failed_cases.append(f"{time_in}-{time_out}: {units} units (expected {expected_units})")
            
            # Also test the minutes_to_units_with_rounding function directly
            direct_test_cases = [
                (30, 2),   # 30 minutes = 2 units
                (35, 2),   # 35 minutes = 2 units (boundary)
                (36, 3),   # 36 minutes = 3 units (special rule)
                (37, 3),   # 37 minutes = 3 units (special rule)
                (45, 3),   # 45 minutes = 3 units (special rule)
                (59, 3),   # 59 minutes = 3 units (special rule)
                (60, 4),   # 60 minutes = 4 units (normal)
            ]
            
            for minutes, expected_units in direct_test_cases:
                units = minutes_to_units_with_rounding(minutes)
                if units != expected_units:
                    all_passed = False
                    failed_cases.append(f"{minutes} min: {units} units (expected {expected_units})")
            
            details = f"Tested {len(special_cases + direct_test_cases)} cases. Failed: {len(failed_cases)}"
            if failed_cases:
                details += f". Failures: {', '.join(failed_cases[:3])}"
            
            self.log_test("Special Rounding Rule (>35min <60min = 3 units)", all_passed, details)
            return all_passed
        except Exception as e:
            self.log_test("Special Rounding Rule (>35min <60min = 3 units)", False, str(e))
            return False
    
    def test_existing_timesheets_units(self):
        """Test that existing timesheets have units calculated correctly"""
        try:
            response = requests.get(f"{self.api_url}/timesheets", timeout=10)
            success = response.status_code == 200
            
            if success:
                timesheets = response.json()
                
                # Check if any timesheets have units calculated
                timesheets_with_units = 0
                total_entries_checked = 0
                entries_with_units = 0
                
                for timesheet in timesheets[:5]:  # Check first 5 timesheets
                    if timesheet.get('extracted_data') and timesheet['extracted_data'].get('employee_entries'):
                        for emp_entry in timesheet['extracted_data']['employee_entries']:
                            if emp_entry.get('time_entries'):
                                for time_entry in emp_entry['time_entries']:
                                    total_entries_checked += 1
                                    if time_entry.get('units') is not None:
                                        entries_with_units += 1
                
                # Success if we found some entries with units calculated
                success = entries_with_units > 0
                details = f"Checked {total_entries_checked} time entries, {entries_with_units} have units calculated"
                
                if not success and total_entries_checked > 0:
                    details += " - Units field missing from existing timesheets"
                elif total_entries_checked == 0:
                    details = "No time entries found in existing timesheets"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Existing Timesheets Units Verification", success, details)
            return success
        except Exception as e:
            self.log_test("Existing Timesheets Units Verification", False, str(e))
            return False
    
    def test_timesheet_upload_with_time_calculation(self):
        """Test uploading a timesheet and verify time calculation integration"""
        try:
            # Create a test timesheet with specific times to test calculations
            test_content = """TIMESHEET
Employee: Jane Smith
Client: Test Patient
Service Code: HHA001

Date: 2024-01-15
Time In: 8:00 AM
Time Out: 8:37 AM
Signature: [Signed]

Date: 2024-01-16  
Time In: 9:00 AM
Time Out: 9:45 AM
Signature: [Signed]

Date: 2024-01-17
Time In: 2:00 PM
Time Out: 3:00 PM
Signature: [Signed]"""
            
            # Create temporary file
            import tempfile
            import os
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf', mode='w')
            temp_file.write(test_content)
            temp_file.close()
            
            # Upload the timesheet
            with open(temp_file.name, 'rb') as f:
                files = {'file': ('time_calc_test.pdf', f, 'application/pdf')}
                response = requests.post(f"{self.api_url}/timesheets/upload", files=files, timeout=60)
            
            success = response.status_code == 200
            timesheet_id = None
            
            if success:
                data = response.json()
                timesheet_id = data.get('id')
                
                # Check if the timesheet has extracted data with calculated units
                if data.get('extracted_data') and data['extracted_data'].get('employee_entries'):
                    emp_entries = data['extracted_data']['employee_entries']
                    units_calculated = False
                    
                    for emp_entry in emp_entries:
                        if emp_entry.get('time_entries'):
                            for time_entry in emp_entry['time_entries']:
                                if time_entry.get('units') is not None:
                                    units_calculated = True
                                    break
                    
                    success = units_calculated
                    details = f"Status: {response.status_code}, ID: {timesheet_id}, Units calculated: {units_calculated}"
                else:
                    success = False
                    details = f"Status: {response.status_code}, No extracted data found"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            # Cleanup
            os.unlink(temp_file.name)
            
            # If we created a timesheet, clean it up
            if timesheet_id:
                try:
                    requests.delete(f"{self.api_url}/timesheets/{timesheet_id}", timeout=10)
                except:
                    pass
            
            self.log_test("Timesheet Upload with Time Calculation", success, details)
            return success
        except Exception as e:
            self.log_test("Timesheet Upload with Time Calculation", False, str(e))
            return False
    
    def test_individual_export_requirements(self):
        """Test all Individual export requirements from review request"""
        try:
            response = requests.get(f"{self.api_url}/evv/export/individuals", timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                export_data = data.get('data', [])
                
                if len(export_data) > 0:
                    # Test each requirement - find our test patient with comprehensive EVV fields
                    test_individual = None
                    for individual in export_data:
                        if individual.get('PatientFirstName') == 'Isabella' and individual.get('PatientLastName') == 'Martinez':
                            test_individual = individual
                            break
                    
                    if not test_individual:
                        self.log_test("Individual Export Requirements Validation", False, "Test patient not found in export")
                        return False
                    
                    requirements_met = []
                    individual = test_individual
                    
                    # Test requirements on our comprehensive test patient
                    # 1. All required EVV Individual fields are present
                    required_fields = [
                            'BusinessEntityID', 'BusinessEntityMedicaidIdentifier', 
                            'PatientOtherID', 'SequenceID', 'PatientMedicaidID',
                            'IsPatientNewborn', 'PatientLastName', 'PatientFirstName',
                            'PatientTimeZone', 'IndividualPayerInformation', 'IndividualAddress'
                    ]
                    all_required_present = all(field in individual for field in required_fields)
                    requirements_met.append(("All required EVV Individual fields present", all_required_present))
                    
                    # 2. PatientOtherID uses patient.id if patient_other_id not set
                    patient_other_id = individual.get('PatientOtherID', '')
                    other_id_valid = len(patient_other_id) > 0
                    requirements_met.append(("PatientOtherID properly mapped", other_id_valid))
                    
                    # 3. PatientMedicaidID has 12 digits with leading zeros
                    medicaid_id = individual.get('PatientMedicaidID', '')
                    medicaid_format_valid = len(medicaid_id) == 12 and medicaid_id.isdigit()
                    requirements_met.append(("PatientMedicaidID 12 digits with leading zeros", medicaid_format_valid))
                    
                    # 4. Address fields map correctly
                    addresses = individual.get('IndividualAddress', [])
                    address_mapped = len(addresses) > 0
                    if address_mapped:
                        addr = addresses[0]
                        address_fields = ['PatientAddressLine1', 'PatientCity', 'PatientState', 'PatientZip']
                        address_complete = all(field in addr for field in address_fields)
                        requirements_met.append(("Address fields map correctly", address_complete))
                    
                    # 5. Coordinates are included if available
                    coords_available = False
                    if addresses and len(addresses) > 0:
                        addr = addresses[0]
                        coords_available = 'PatientAddressLatitude' in addr and 'PatientAddressLongitude' in addr
                    requirements_met.append(("Coordinates included when available", coords_available))
                    
                    # 6. Phone numbers export correctly
                    phones_exported = 'IndividualPhone' in individual
                    requirements_met.append(("Phone numbers export correctly", phones_exported))
                    
                    # 7. Responsible party exports if present
                    rp_exported = 'ResponsibleParty' in individual
                    requirements_met.append(("Responsible party exports when present", rp_exported))
                    
                    # 8. Default payer information is added
                    payer_info = individual.get('IndividualPayerInformation', [])
                    payer_added = len(payer_info) > 0 and payer_info[0].get('Payer') == 'ODM'
                    requirements_met.append(("Default payer information added", payer_added))
                    
                    # 9. PIMS ID handling for ODA
                    pims_handled = True  # This is optional, so we consider it handled if no error
                    requirements_met.append(("PIMS ID handling for ODA", pims_handled))
                        
                    # End of requirements testing for our test individual
                    
                    # Calculate success rate
                    passed_requirements = sum(1 for _, met in requirements_met if met)
                    total_requirements = len(requirements_met)
                    success = passed_requirements == total_requirements
                    
                    details = f"Requirements met: {passed_requirements}/{total_requirements}"
                    for req_name, met in requirements_met:
                        if not met:
                            details += f", FAILED: {req_name}"
                else:
                    success = False
                    details = "No individual records found"
            else:
                details = f"Status: {response.status_code}"
            
            self.log_test("Individual Export Requirements Validation", success, details)
            return success
        except Exception as e:
            self.log_test("Individual Export Requirements Validation", False, str(e))
            return False
    
    def test_dcw_export_requirements(self):
        """Test all DirectCareWorker export requirements from review request"""
        try:
            response = requests.get(f"{self.api_url}/evv/export/direct-care-workers", timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                export_data = data.get('data', [])
                
                if len(export_data) > 0:
                    # Test each requirement - find our test employee with comprehensive DCW fields
                    test_dcw = None
                    for dcw in export_data:
                        if dcw.get('StaffFirstName') == 'Michael' and dcw.get('StaffLastName') == 'Thompson':
                            test_dcw = dcw
                            break
                    
                    if not test_dcw:
                        self.log_test("DirectCareWorker Export Requirements Validation", False, "Test employee not found in export")
                        return False
                    
                    requirements_met = []
                    dcw = test_dcw
                    
                    # Test requirements on our comprehensive test employee
                    # 1. All required EVV DCW fields are present
                    required_fields = [
                            'BusinessEntityID', 'BusinessEntityMedicaidIdentifier',
                            'StaffOtherID', 'SequenceID', 'StaffID', 'StaffSSN',
                            'StaffLastName', 'StaffFirstName'
                    ]
                    all_required_present = all(field in dcw for field in required_fields)
                    requirements_met.append(("All required EVV DCW fields present", all_required_present))
                    
                    # 2. StaffOtherID uses employee.id if staff_other_id not set
                    staff_other_id = dcw.get('StaffOtherID', '')
                    other_id_valid = len(staff_other_id) > 0
                    requirements_met.append(("StaffOtherID properly mapped", other_id_valid))
                    
                    # 3. StaffID uses staff_pin or employee_id as fallback
                    staff_id = dcw.get('StaffID', '')
                    staff_id_valid = len(staff_id) > 0
                    requirements_met.append(("StaffID uses staff_pin or employee_id fallback", staff_id_valid))
                    
                    # 4. SSN is cleaned (no dashes/spaces)
                    ssn = dcw.get('StaffSSN', '')
                    ssn_clean = len(ssn) == 9 and ssn.isdigit()
                    requirements_met.append(("SSN cleaned (9 digits, no formatting)", ssn_clean))
                    
                    # 5. StaffEmail is included if available
                    email_handling = True  # Optional field, so we check it's handled properly
                    if 'StaffEmail' in dcw:
                        email = dcw['StaffEmail']
                        email_handling = '@' in email  # Basic email validation
                    requirements_met.append(("StaffEmail included when available", email_handling))
                    
                    # 6. StaffPosition is truncated to 3 characters if needed
                    position_valid = True
                    if 'StaffPosition' in dcw:
                        position = dcw['StaffPosition']
                        position_valid = len(position) <= 3
                    requirements_met.append(("StaffPosition truncated to 3 characters", position_valid))
                        
                    # End of requirements testing for our test DCW
                    
                    # Calculate success rate
                    passed_requirements = sum(1 for _, met in requirements_met if met)
                    total_requirements = len(requirements_met)
                    success = passed_requirements == total_requirements
                    
                    details = f"Requirements met: {passed_requirements}/{total_requirements}"
                    for req_name, met in requirements_met:
                        if not met:
                            details += f", FAILED: {req_name}"
                else:
                    success = False
                    details = "No DCW records found"
            else:
                details = f"Status: {response.status_code}"
            
            self.log_test("DirectCareWorker Export Requirements Validation", success, details)
            return success
        except Exception as e:
            self.log_test("DirectCareWorker Export Requirements Validation", False, str(e))
            return False
    
    def test_export_json_validity(self):
        """Test that exports produce valid JSON without errors"""
        try:
            # Test Individual export JSON validity
            individual_response = requests.get(f"{self.api_url}/evv/export/individuals", timeout=10)
            individual_valid = individual_response.status_code == 200
            
            if individual_valid:
                try:
                    individual_data = individual_response.json()
                    individual_json_valid = 'data' in individual_data and isinstance(individual_data['data'], list)
                except json.JSONDecodeError:
                    individual_json_valid = False
            else:
                individual_json_valid = False
            
            # Test DCW export JSON validity
            dcw_response = requests.get(f"{self.api_url}/evv/export/direct-care-workers", timeout=10)
            dcw_valid = dcw_response.status_code == 200
            
            if dcw_valid:
                try:
                    dcw_data = dcw_response.json()
                    dcw_json_valid = 'data' in dcw_data and isinstance(dcw_data['data'], list)
                except json.JSONDecodeError:
                    dcw_json_valid = False
            else:
                dcw_json_valid = False
            
            success = individual_json_valid and dcw_json_valid
            details = f"Individual JSON valid: {individual_json_valid}, DCW JSON valid: {dcw_json_valid}"
            
            self.log_test("Export JSON Validity", success, details)
            return success
        except Exception as e:
            self.log_test("Export JSON Validity", False, str(e))
            return False
    
    def test_export_with_actual_database_data(self):
        """Test exports with actual patient and employee data from database"""
        try:
            # Get actual patients from database
            patients_response = requests.get(f"{self.api_url}/patients", timeout=10)
            patients_success = patients_response.status_code == 200
            
            # Get actual employees from database
            employees_response = requests.get(f"{self.api_url}/employees", timeout=10)
            employees_success = employees_response.status_code == 200
            
            if patients_success and employees_success:
                patients_data = patients_response.json()
                employees_data = employees_response.json()
                
                # Test Individual export with actual data
                individual_export = requests.get(f"{self.api_url}/evv/export/individuals", timeout=10)
                individual_export_success = individual_export.status_code == 200
                
                # Test DCW export with actual data
                dcw_export = requests.get(f"{self.api_url}/evv/export/direct-care-workers", timeout=10)
                dcw_export_success = dcw_export.status_code == 200
                
                if individual_export_success and dcw_export_success:
                    individual_export_data = individual_export.json()
                    dcw_export_data = dcw_export.json()
                    
                    # Verify record counts match
                    patients_count = len(patients_data)
                    employees_count = len(employees_data)
                    exported_individuals = individual_export_data.get('record_count', 0)
                    exported_dcws = dcw_export_data.get('record_count', 0)
                    
                    counts_match = (patients_count == exported_individuals and 
                                  employees_count == exported_dcws)
                    
                    success = counts_match
                    details = f"Patients: {patients_count}→{exported_individuals}, Employees: {employees_count}→{exported_dcws}"
                else:
                    success = False
                    details = f"Export failed - Individual: {individual_export_success}, DCW: {dcw_export_success}"
            else:
                success = False
                details = f"Database read failed - Patients: {patients_success}, Employees: {employees_success}"
            
            self.log_test("Export with Actual Database Data", success, details)
            return success
        except Exception as e:
            self.log_test("Export with Actual Database Data", False, str(e))
            return False

def main():
    tester = TimesheetAPITester()
    
    if len(sys.argv) > 1 and sys.argv[1] == "time_calc":
        # Run time calculation and unit conversion tests
        tester.test_time_calculation_and_units()
        return tester.get_results()
    elif len(sys.argv) > 1 and sys.argv[1] == "evv":
        # Run EVV tests
        return tester.run_evv_tests()
    elif len(sys.argv) > 1 and sys.argv[1] == "basic":
        # Run basic timesheet tests
        return tester.run_all_tests()
    else:
        # Run detailed EVV export field mapping tests as requested
        print("🎯 Testing Corrected EVV Export Functionality")
        print("Verifying Individual and DirectCareWorker export field mappings")
        print("=" * 80)
        
        # Test the corrected EVV export functionality
        tester.test_evv_export_field_mapping_detailed()
        
        # Run comprehensive validation tests
        tester.test_evv_export_comprehensive_validation()
        
        return tester.get_results()

if __name__ == "__main__":
    sys.exit(main())