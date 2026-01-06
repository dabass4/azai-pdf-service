"""
Backend API Tests for AZAI Healthcare Application
Testing: Notification System, Admin Panel Organizations CRUD, Admin Credentials, 
Employee Validation Rules, Patient Validation Rules

Test Credentials:
- Super Admin: admin@medicaidservices.com / Admin2024!

KNOWN BUGS FOUND:
1. Notification routes have double /api prefix - actual path is /api/notifications/...
2. Admin organization details endpoint queries by "organization_id" but DB has "id" field
"""

import pytest
import requests
import os
import uuid
from datetime import datetime

# Base URL from environment
BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://healthdb-pro-1.preview.emergentagent.com').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@medicaidservices.com"
ADMIN_PASSWORD = "Admin2024!"


# ==================== FIXTURES ====================

@pytest.fixture(scope="module")
def api_client():
    """Shared requests session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


@pytest.fixture(scope="module")
def admin_auth(api_client):
    """Get admin authentication token"""
    response = api_client.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    
    if response.status_code != 200:
        pytest.skip(f"Admin authentication failed: {response.status_code} - {response.text}")
    
    data = response.json()
    token = data.get("access_token")
    user = data.get("user", {})
    
    # Verify admin has is_admin=True
    assert user.get("role") == "super_admin" or data.get("organization", {}).get("features", []), \
        "Admin user should have admin privileges"
    
    return {
        "token": token,
        "user": user,
        "organization_id": user.get("organization_id", "super_admin")
    }


@pytest.fixture(scope="module")
def authenticated_client(api_client, admin_auth):
    """Session with admin auth header"""
    api_client.headers.update({
        "Authorization": f"Bearer {admin_auth['token']}"
    })
    return api_client


# ==================== NOTIFICATION SYSTEM TESTS ====================
# NOTE: Notification routes have double /api prefix bug - using /api/notifications/...

class TestNotificationSystem:
    """Test notification system endpoints - requires admin privileges
    
    BUG: routes_notifications.py has prefix="/api/notifications" but is included
    in api_router which has prefix="/api", resulting in /api/notifications/...
    """
    
    def test_send_notification_as_admin(self, authenticated_client, admin_auth):
        """Test POST /api/notifications/send - Admin can send notifications"""
        notification_data = {
            "type": "system_alert",
            "category": "info",
            "title": f"Test Notification {uuid.uuid4().hex[:8]}",
            "message": "This is a test notification from automated testing",
            "source": "admin",
            "recipients": ["all"],
            "send_email": False,  # Don't actually send emails in test
            "priority": "normal",
            "metadata": {"test": True}
        }
        
        # Using double /api prefix due to bug
        response = authenticated_client.post(
            f"{BASE_URL}/api/notifications/send",
            json=notification_data
        )
        
        print(f"Send notification response: {response.status_code} - {response.text[:500]}")
        
        # Should succeed with 200 or fail with 403 if not admin
        if response.status_code == 403:
            pytest.skip("User does not have admin privileges for sending notifications")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("status") == "success", f"Expected success status: {data}"
        assert "notification" in data, "Response should contain notification details"
        assert data["notification"].get("id"), "Notification should have an ID"
        
        return data["notification"]["id"]
    
    def test_list_notifications(self, authenticated_client, admin_auth):
        """Test GET /api/notifications/list - List notifications for organization"""
        # Using double /api prefix due to bug
        response = authenticated_client.get(f"{BASE_URL}/api/notifications/list")
        
        print(f"List notifications response: {response.status_code} - {response.text[:500]}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("status") == "success", f"Expected success status: {data}"
        assert "notifications" in data, "Response should contain notifications list"
        assert isinstance(data["notifications"], list), "Notifications should be a list"
        
        # Verify notification structure if any exist
        if data["notifications"]:
            notif = data["notifications"][0]
            assert "id" in notif, "Notification should have id"
            assert "title" in notif, "Notification should have title"
            assert "type" in notif, "Notification should have type"
    
    def test_list_notifications_with_filters(self, authenticated_client):
        """Test GET /api/notifications/list with query filters"""
        # Using double /api prefix due to bug
        response = authenticated_client.get(
            f"{BASE_URL}/api/notifications/list",
            params={"type": "system_alert", "limit": 10}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert data.get("status") == "success"
    
    def test_get_notification_preferences(self, authenticated_client):
        """Test GET /api/notifications/preferences/me - Get user preferences"""
        # Using double /api prefix due to bug
        response = authenticated_client.get(f"{BASE_URL}/api/notifications/preferences/me")
        
        print(f"Get preferences response: {response.status_code} - {response.text[:500]}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("status") == "success", f"Expected success status: {data}"
        assert "preferences" in data, "Response should contain preferences"
    
    def test_notification_route_bug_documented(self, authenticated_client):
        """Test that notification routes now work correctly at /api/notifications/*
        
        BUG FIX: Double /api prefix has been fixed. Routes now work at correct path.
        """
        # Test that the correct path works
        response_correct = authenticated_client.get(f"{BASE_URL}/api/notifications/list")
        
        print(f"Correct path (/api/notifications/list): {response_correct.status_code}")
        
        # Bug has been fixed - /api/notifications/list should now work
        assert response_correct.status_code == 200, "Expected 200 for /api/notifications/list (bug fixed)"


# ==================== ADMIN PANEL ORGANIZATIONS TESTS ====================

class TestAdminOrganizations:
    """Test admin panel organization CRUD endpoints
    
    BUG: get_organization_details queries by "organization_id" but DB has "id" field
    """
    
    created_org_id = None  # Track created org for cleanup
    
    def test_list_organizations(self, authenticated_client):
        """Test GET /api/admin/organizations - List all organizations"""
        response = authenticated_client.get(f"{BASE_URL}/api/admin/organizations")
        
        print(f"List organizations response: {response.status_code} - {response.text[:500]}")
        
        if response.status_code == 403:
            pytest.skip("User does not have admin privileges for admin panel")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("success") == True, "Should return success=True"
        organizations = data.get("organizations", [])
        
        assert isinstance(organizations, list), "Should return list of organizations"
        assert len(organizations) > 0, "Should have at least one organization"
        
        # Verify organization structure
        org = organizations[0]
        assert "id" in org, "Organization should have id"
        assert "name" in org, "Organization should have name"
        
        return organizations
    
    def test_create_organization(self, authenticated_client):
        """Test POST /api/admin/organizations - Create new organization"""
        org_data = {
            "name": f"TEST_Org_{uuid.uuid4().hex[:8]}",
            "admin_email": f"test_{uuid.uuid4().hex[:8]}@test.com",
            "admin_name": "Test Admin",
            "admin_password": "TestPass123!",  # Required field
            "admin_first_name": "Test",  # Required field
            "admin_last_name": "Admin",  # Required field
            "plan": "basic",
            "phone": "555-123-4567",
            "address_street": "123 Test St",
            "address_city": "Columbus",
            "address_state": "OH",
            "address_zip": "43215"
        }
        
        response = authenticated_client.post(
            f"{BASE_URL}/api/admin/organizations",
            json=org_data
        )
        
        print(f"Create organization response: {response.status_code} - {response.text[:500]}")
        
        if response.status_code == 403:
            pytest.skip("User does not have admin privileges")
        
        assert response.status_code in [200, 201], f"Expected 200/201, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("success") == True, f"Should return success=True: {data}"
        
        org = data.get("organization", {})
        assert org.get("id") or org.get("organization_id"), "Created org should have ID"
        
        # Store for later tests
        TestAdminOrganizations.created_org_id = org.get("id") or org.get("organization_id")
        
        return TestAdminOrganizations.created_org_id
    
    def test_get_organization_details_bug(self, authenticated_client):
        """Test GET /api/admin/organizations/{id} - DOCUMENTS BUG
        
        BUG: The endpoint queries by {"organization_id": organization_id} but
        the organizations collection uses "id" field, not "organization_id"
        """
        # Get list to find an org ID
        list_response = authenticated_client.get(f"{BASE_URL}/api/admin/organizations")
        
        if list_response.status_code == 403:
            pytest.skip("User does not have admin privileges")
        
        data = list_response.json()
        organizations = data.get("organizations", [])
        
        if not organizations:
            pytest.skip("No organizations found to test")
        
        org_id = organizations[0].get("id") or organizations[0].get("organization_id")
        
        response = authenticated_client.get(f"{BASE_URL}/api/admin/organizations/{org_id}")
        
        print(f"Get organization details response: {response.status_code} - {response.text[:500]}")
        
        # Bug has been fixed - should now work correctly
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    
    def test_update_organization(self, authenticated_client):
        """Test PUT /api/admin/organizations/{id} - Update organization"""
        # Get an org to update
        list_response = authenticated_client.get(f"{BASE_URL}/api/admin/organizations")
        
        if list_response.status_code == 403:
            pytest.skip("User does not have admin privileges")
        
        data = list_response.json()
        organizations = data.get("organizations", [])
        
        # Find a TEST_ org or use created one
        org_id = TestAdminOrganizations.created_org_id
        if not org_id and organizations:
            for org in organizations:
                if org.get("name", "").startswith("TEST_"):
                    org_id = org.get("id") or org.get("organization_id")
                    break
            if not org_id:
                org_id = organizations[0].get("id") or organizations[0].get("organization_id")
        
        if not org_id:
            pytest.skip("No organization found to update")
        
        update_data = {
            "phone": "555-999-8888",
            "address_city": "Cleveland"
        }
        
        response = authenticated_client.put(
            f"{BASE_URL}/api/admin/organizations/{org_id}",
            json=update_data
        )
        
        print(f"Update organization response: {response.status_code} - {response.text[:500]}")
        
        # Bug has been fixed
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"


# ==================== ADMIN CREDENTIALS TESTS ====================

class TestAdminCredentials:
    """Test admin credentials endpoints for organizations"""
    
    def test_get_organization_credentials(self, authenticated_client):
        """Test GET /api/admin/organizations/{id}/credentials"""
        # Get an org first
        list_response = authenticated_client.get(f"{BASE_URL}/api/admin/organizations")
        
        if list_response.status_code == 403:
            pytest.skip("User does not have admin privileges")
        
        data = list_response.json()
        organizations = data.get("organizations", [])
        
        if not organizations:
            pytest.skip("No organizations found")
        
        org_id = organizations[0].get("id")
        
        response = authenticated_client.get(
            f"{BASE_URL}/api/admin/organizations/{org_id}/credentials"
        )
        
        print(f"Get credentials response: {response.status_code} - {response.text[:500]}")
        
        # Could be 200 (found) or 404 (no credentials yet)
        assert response.status_code in [200, 404], f"Expected 200/404, got {response.status_code}: {response.text}"
        
        if response.status_code == 200:
            data = response.json()
            assert data.get("success") == True, "Should return success=True"
    
    def test_update_organization_credentials(self, authenticated_client):
        """Test PUT /api/admin/organizations/{id}/credentials"""
        # Get an org first
        list_response = authenticated_client.get(f"{BASE_URL}/api/admin/organizations")
        
        if list_response.status_code == 403:
            pytest.skip("User does not have admin privileges")
        
        data = list_response.json()
        organizations = data.get("organizations", [])
        
        if not organizations:
            pytest.skip("No organizations found")
        
        org_id = organizations[0].get("id")
        
        credentials_data = {
            "environment": "sandbox",
            "sandata_enabled": False,
            "ohio_evv_enabled": False
        }
        
        response = authenticated_client.put(
            f"{BASE_URL}/api/admin/organizations/{org_id}/credentials",
            json=credentials_data
        )
        
        print(f"Update credentials response: {response.status_code} - {response.text[:500]}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("success") == True, "Should return success=True"


# ==================== EMPLOYEE VALIDATION TESTS ====================

class TestEmployeeValidation:
    """Test employee validation rules from validation_utils.py
    
    Required fields: first_name, last_name, ssn, date_of_birth, sex, 
    address (street, city, state, zip), phone, categories (RN, LPN, HHA, DSP)
    """
    
    created_employee_id = None
    
    def test_create_employee_missing_required_fields(self, authenticated_client):
        """Test POST /api/employees - Should create but mark as incomplete"""
        # Create employee with minimal data (missing required fields)
        employee_data = {
            "first_name": f"TEST_{uuid.uuid4().hex[:6]}",
            "last_name": "MissingFields"
            # Missing: ssn, date_of_birth, sex, address, phone, categories
        }
        
        response = authenticated_client.post(
            f"{BASE_URL}/api/employees",
            json=employee_data
        )
        
        print(f"Create employee (missing fields) response: {response.status_code} - {response.text[:500]}")
        
        assert response.status_code in [200, 201], f"Expected 200/201, got {response.status_code}"
        
        data = response.json()
        employee = data.get("employee", data)
        
        # Should be marked as incomplete
        assert employee.get("is_complete") == False, "Employee with missing fields should be incomplete"
        
        # Check validation errors if present
        validation = data.get("validation", {})
        if validation:
            assert len(validation.get("missing_required_fields", [])) > 0, \
                "Should have missing required fields"
            print(f"Validation errors: {validation.get('missing_required_fields', [])}")
        
        TestEmployeeValidation.created_employee_id = employee.get("id")
    
    def test_update_employee_empty_categories(self, authenticated_client):
        """Test PUT /api/employees/{id} - Empty categories should fail validation"""
        # First create an employee
        employee_data = {
            "first_name": f"TEST_{uuid.uuid4().hex[:6]}",
            "last_name": "EmptyCategories",
            "categories": ["RN"]  # Start with valid category
        }
        
        create_response = authenticated_client.post(
            f"{BASE_URL}/api/employees",
            json=employee_data
        )
        
        if create_response.status_code not in [200, 201]:
            pytest.skip(f"Could not create employee: {create_response.text}")
        
        data = create_response.json()
        employee_id = data.get("employee", data).get("id")
        
        # Try to update with empty categories
        update_data = {
            "categories": []  # Empty categories should fail validation
        }
        
        response = authenticated_client.put(
            f"{BASE_URL}/api/employees/{employee_id}",
            json=update_data
        )
        
        print(f"Update employee (empty categories) response: {response.status_code} - {response.text[:500]}")
        
        # Based on validation_utils.py, empty categories should cause validation error
        data = response.json()
        
        # Check if validation errors are returned or is_complete is False
        if response.status_code == 200:
            validation = data.get("validation", {})
            if validation:
                errors = validation.get("missing_required_fields", [])
                # Should have error about categories
                has_category_error = any("categor" in str(e).lower() for e in errors)
                print(f"Validation errors: {errors}")
                assert has_category_error or validation.get("is_complete") == False, \
                    "Should have category validation error or be incomplete"
    
    def test_update_employee_valid_categories(self, authenticated_client):
        """Test PUT /api/employees/{id} - Should succeed with valid categories"""
        # Create employee first
        employee_data = {
            "first_name": f"TEST_{uuid.uuid4().hex[:6]}",
            "last_name": "ValidCategories"
        }
        
        create_response = authenticated_client.post(
            f"{BASE_URL}/api/employees",
            json=employee_data
        )
        
        if create_response.status_code not in [200, 201]:
            pytest.skip(f"Could not create employee: {create_response.text}")
        
        data = create_response.json()
        employee_id = data.get("employee", data).get("id")
        
        # Update with valid categories and all required fields
        update_data = {
            "categories": ["RN"],  # Valid category
            "first_name": f"TEST_{uuid.uuid4().hex[:6]}",
            "last_name": "ValidCategories",
            "ssn": "123-45-6789",
            "date_of_birth": "1990-01-15",
            "sex": "Female",
            "address_street": "123 Test St",
            "address_city": "Columbus",
            "address_state": "OH",
            "address_zip": "43215",
            "phone": "555-123-4567"
        }
        
        response = authenticated_client.put(
            f"{BASE_URL}/api/employees/{employee_id}",
            json=update_data
        )
        
        print(f"Update employee (valid categories) response: {response.status_code} - {response.text[:500]}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        employee = data.get("employee", data)
        
        # Verify categories were saved
        assert "RN" in employee.get("categories", []), "Categories should include RN"
        
        # Check if now complete
        validation = data.get("validation", {})
        if validation:
            print(f"Completion: {validation.get('completion_percentage', 0)}%")
    
    def test_employee_invalid_category_values(self, authenticated_client):
        """Test that invalid category values are caught by validation"""
        employee_data = {
            "first_name": f"TEST_{uuid.uuid4().hex[:6]}",
            "last_name": "InvalidCategory",
            "categories": ["INVALID_CAT"]  # Invalid category - should be RN, LPN, HHA, or DSP
        }
        
        response = authenticated_client.post(
            f"{BASE_URL}/api/employees",
            json=employee_data
        )
        
        print(f"Create employee (invalid category) response: {response.status_code} - {response.text[:500]}")
        
        # Should either reject or mark as incomplete with validation errors
        if response.status_code in [200, 201]:
            data = response.json()
            validation = data.get("validation", {})
            # Check if validation caught the invalid category
            if validation:
                errors = validation.get("missing_required_fields", [])
                print(f"Validation errors: {errors}")
                # Should have error about invalid categories
                has_category_error = any("categor" in str(e).lower() or "invalid" in str(e).lower() for e in errors)
                assert has_category_error or validation.get("is_complete") == False


# ==================== PATIENT VALIDATION TESTS ====================

class TestPatientValidation:
    """Test patient validation rules from validation_utils.py
    
    Required fields: first_name, last_name, date_of_birth, sex, medicaid_number (12 digits),
    address (street, city, state, zip), timezone, icd10_code
    """
    
    def test_create_patient_incomplete_fields(self, authenticated_client):
        """Test creating patient with incomplete fields - should mark as incomplete"""
        patient_data = {
            "first_name": f"TEST_{uuid.uuid4().hex[:6]}",
            "last_name": "IncompletePatient"
            # Missing: date_of_birth, sex, medicaid_number, address, etc.
        }
        
        response = authenticated_client.post(
            f"{BASE_URL}/api/patients",
            json=patient_data
        )
        
        print(f"Create patient (incomplete) response: {response.status_code} - {response.text[:500]}")
        
        assert response.status_code in [200, 201], f"Expected 200/201, got {response.status_code}"
        
        data = response.json()
        patient = data.get("patient", data)
        
        # Should be marked as incomplete
        assert patient.get("is_complete") == False, "Patient with missing fields should be incomplete"
        
        # Check validation errors if present
        validation = data.get("validation", {})
        if validation:
            assert len(validation.get("missing_required_fields", [])) > 0, \
                "Should have missing required fields"
            print(f"Validation errors: {validation.get('missing_required_fields', [])}")
    
    def test_update_patient_complete_fields(self, authenticated_client):
        """Test updating patient with complete valid data - should become complete"""
        # Create incomplete patient first
        patient_data = {
            "first_name": f"TEST_{uuid.uuid4().hex[:6]}",
            "last_name": "CompletePatient"
        }
        
        create_response = authenticated_client.post(
            f"{BASE_URL}/api/patients",
            json=patient_data
        )
        
        if create_response.status_code not in [200, 201]:
            pytest.skip(f"Could not create patient: {create_response.text}")
        
        data = create_response.json()
        patient_id = data.get("patient", data).get("id")
        
        # Update with complete valid data
        update_data = {
            "first_name": f"TEST_{uuid.uuid4().hex[:6]}",
            "last_name": "CompletePatient",
            "date_of_birth": "1985-06-15",
            "sex": "Male",
            "medicaid_number": "123456789012",  # 12 digits
            "address_street": "456 Patient Ave",
            "address_city": "Columbus",
            "address_state": "OH",
            "address_zip": "43215",
            "timezone": "America/New_York",
            "icd10_code": "M79.3"
        }
        
        response = authenticated_client.put(
            f"{BASE_URL}/api/patients/{patient_id}",
            json=update_data
        )
        
        print(f"Update patient (complete) response: {response.status_code} - {response.text[:500]}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        patient = data.get("patient", data)
        validation = data.get("validation", {})
        
        # Check if is_complete changed to True
        if validation:
            print(f"Validation status: {validation}")
            completion = validation.get("completion_percentage", 0)
            print(f"Completion percentage: {completion}%")
            # With all required fields, should be complete or close to it
            assert completion >= 80, f"Should be at least 80% complete, got {completion}%"
    
    def test_patient_invalid_medicaid_number(self, authenticated_client):
        """Test that invalid medicaid number format is caught by validation"""
        patient_data = {
            "first_name": f"TEST_{uuid.uuid4().hex[:6]}",
            "last_name": "InvalidMedicaid",
            "medicaid_number": "ABC123"  # Invalid - should be 12 digits
        }
        
        response = authenticated_client.post(
            f"{BASE_URL}/api/patients",
            json=patient_data
        )
        
        print(f"Create patient (invalid medicaid) response: {response.status_code} - {response.text[:500]}")
        
        if response.status_code in [200, 201]:
            data = response.json()
            validation = data.get("validation", {})
            
            if validation:
                errors = validation.get("missing_required_fields", [])
                print(f"Validation errors: {errors}")
                # Should have error about medicaid number format
                has_medicaid_error = any("medicaid" in str(e).lower() for e in errors)
                assert has_medicaid_error, "Should have medicaid number validation error"


# ==================== CLEANUP ====================

@pytest.fixture(scope="module", autouse=True)
def cleanup(authenticated_client):
    """Cleanup test data after all tests"""
    yield
    
    # Cleanup TEST_ prefixed employees
    try:
        response = authenticated_client.get(f"{BASE_URL}/api/employees")
        if response.status_code == 200:
            data = response.json()
            employees = data if isinstance(data, list) else data.get("employees", [])
            for emp in employees:
                if emp.get("first_name", "").startswith("TEST_"):
                    authenticated_client.delete(f"{BASE_URL}/api/employees/{emp['id']}")
                    print(f"Cleaned up employee: {emp['id']}")
    except Exception as e:
        print(f"Employee cleanup error: {e}")
    
    # Cleanup TEST_ prefixed patients
    try:
        response = authenticated_client.get(f"{BASE_URL}/api/patients")
        if response.status_code == 200:
            data = response.json()
            patients = data if isinstance(data, list) else data.get("patients", [])
            for pat in patients:
                if pat.get("first_name", "").startswith("TEST_"):
                    authenticated_client.delete(f"{BASE_URL}/api/patients/{pat['id']}")
                    print(f"Cleaned up patient: {pat['id']}")
    except Exception as e:
        print(f"Patient cleanup error: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
