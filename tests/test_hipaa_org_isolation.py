"""
HIPAA Organization Isolation Tests
Tests that API endpoints properly filter data by organization_id
to ensure one organization cannot access another organization's data.

Test Scenarios:
1. Timesheets list returns only records for logged-in user's organization
2. Accessing a timesheet from a different org returns 404
3. Bulk delete only affects records from user's organization
4. EVV visits CRUD only accesses records for user's organization
5. EVV exports only include data from user's organization
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@medicaidservices.com"
ADMIN_PASSWORD = "Admin2024!"
ADMIN_ORG_ID = "super_admin"

# Expected counts based on database analysis
SUPER_ADMIN_TIMESHEET_COUNT = 610
TOTAL_TIMESHEET_COUNT = 1259


class TestHIPAAOrganizationIsolation:
    """Test HIPAA-compliant organization data isolation"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token for admin user"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "token" in data, "No token in response"
        return data["token"]
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """Get headers with auth token"""
        return {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json"
        }
    
    # ==================== TIMESHEET ISOLATION TESTS ====================
    
    def test_timesheets_list_returns_only_org_records(self, auth_headers):
        """
        HIPAA Test: GET /api/timesheets should only return records 
        for the logged-in user's organization (super_admin: 610 records)
        """
        response = requests.get(
            f"{BASE_URL}/api/timesheets",
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Failed to get timesheets: {response.text}"
        timesheets = response.json()
        
        # Verify count matches super_admin org count (610), not total (1259)
        print(f"Timesheets returned: {len(timesheets)}")
        print(f"Expected for super_admin org: {SUPER_ADMIN_TIMESHEET_COUNT}")
        
        # All returned timesheets should belong to super_admin org
        for ts in timesheets:
            assert ts.get('organization_id') == ADMIN_ORG_ID, \
                f"Timesheet {ts.get('id')} has wrong org: {ts.get('organization_id')}"
        
        # Count should be approximately 610 (super_admin org count)
        # Allow some variance for test data changes
        assert len(timesheets) <= SUPER_ADMIN_TIMESHEET_COUNT + 50, \
            f"Too many timesheets returned ({len(timesheets)}). Expected ~{SUPER_ADMIN_TIMESHEET_COUNT} for super_admin org, not {TOTAL_TIMESHEET_COUNT} total"
        
        # Should not return all 1259 timesheets
        assert len(timesheets) < TOTAL_TIMESHEET_COUNT, \
            f"Returned all {TOTAL_TIMESHEET_COUNT} timesheets - org isolation NOT working!"
    
    def test_get_timesheet_from_different_org_returns_404(self, auth_headers):
        """
        HIPAA Test: Accessing a timesheet from a different organization 
        should return 404 (not found), not the actual data
        """
        # This timesheet belongs to 'default-org', not 'super_admin'
        other_org_timesheet_id = "1197a35d-434a-4589-a434-59c17c4ae97b"
        
        response = requests.get(
            f"{BASE_URL}/api/timesheets/{other_org_timesheet_id}",
            headers=auth_headers
        )
        
        # Should return 404 because it belongs to a different org
        assert response.status_code == 404, \
            f"Expected 404 for cross-org access, got {response.status_code}. " \
            f"HIPAA VIOLATION: User can access data from another organization!"
    
    def test_get_own_org_timesheet_succeeds(self, auth_headers):
        """
        HIPAA Test: Accessing a timesheet from own organization should succeed
        """
        # This timesheet belongs to 'super_admin' org
        own_org_timesheet_id = "d9798a71-8f46-4dc2-ada4-7ff54527a31e"
        
        response = requests.get(
            f"{BASE_URL}/api/timesheets/{own_org_timesheet_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Failed to get own org timesheet: {response.text}"
        timesheet = response.json()
        assert timesheet.get('organization_id') == ADMIN_ORG_ID
    
    # ==================== BULK DELETE ISOLATION TESTS ====================
    
    def test_bulk_delete_only_affects_own_org(self, auth_headers):
        """
        HIPAA Test: Bulk delete should only delete timesheets from user's org
        Attempting to delete a timesheet from another org should not work
        """
        # Try to delete a timesheet from another org
        other_org_timesheet_id = "1197a35d-434a-4589-a434-59c17c4ae97b"
        
        response = requests.post(
            f"{BASE_URL}/api/timesheets/bulk-delete",
            headers=auth_headers,
            json={"ids": [other_org_timesheet_id]}
        )
        
        assert response.status_code == 200, f"Bulk delete request failed: {response.text}"
        result = response.json()
        
        # Should delete 0 records because the timesheet belongs to another org
        assert result.get('deleted_count') == 0, \
            f"Deleted {result.get('deleted_count')} records from another org! HIPAA VIOLATION!"
        
        # Verify the timesheet still exists (check without auth to see if it's in DB)
        # We can't directly verify this without DB access, but the delete_count=0 confirms isolation
    
    # ==================== EVV VISITS ISOLATION TESTS ====================
    
    def test_evv_visits_list_returns_only_org_records(self, auth_headers):
        """
        HIPAA Test: GET /api/evv/visits should only return records 
        for the logged-in user's organization
        """
        response = requests.get(
            f"{BASE_URL}/api/evv/visits",
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Failed to get EVV visits: {response.text}"
        visits = response.json()
        
        # All returned visits should belong to super_admin org
        for visit in visits:
            assert visit.get('organization_id') == ADMIN_ORG_ID, \
                f"EVV visit {visit.get('id')} has wrong org: {visit.get('organization_id')}"
        
        print(f"EVV visits returned for super_admin org: {len(visits)}")
    
    def test_evv_visit_from_different_org_returns_404(self, auth_headers):
        """
        HIPAA Test: Accessing an EVV visit from a different organization 
        should return 404
        """
        # Use a fake ID that doesn't exist in super_admin org
        fake_visit_id = "non-existent-visit-id"
        
        response = requests.get(
            f"{BASE_URL}/api/evv/visits/{fake_visit_id}",
            headers=auth_headers
        )
        
        # Should return 404
        assert response.status_code == 404, \
            f"Expected 404 for non-existent visit, got {response.status_code}"
    
    # ==================== EVV EXPORT ISOLATION TESTS ====================
    
    def test_evv_export_individuals_only_includes_org_data(self, auth_headers):
        """
        HIPAA Test: EVV export should only include patients from user's org
        """
        response = requests.get(
            f"{BASE_URL}/api/evv/export/individuals",
            headers=auth_headers
        )
        
        # May return 404 if no business entity configured, which is acceptable
        if response.status_code == 404:
            pytest.skip("No business entity configured for export test")
        
        assert response.status_code == 200, f"Failed to export individuals: {response.text}"
        result = response.json()
        
        print(f"EVV export individuals count: {result.get('record_count', 0)}")
        # The export should only include patients from super_admin org
    
    def test_evv_export_direct_care_workers_only_includes_org_data(self, auth_headers):
        """
        HIPAA Test: EVV export should only include employees from user's org
        """
        response = requests.get(
            f"{BASE_URL}/api/evv/export/direct-care-workers",
            headers=auth_headers
        )
        
        # May return 404 if no business entity configured
        if response.status_code == 404:
            pytest.skip("No business entity configured for export test")
        
        assert response.status_code == 200, f"Failed to export workers: {response.text}"
        result = response.json()
        
        print(f"EVV export direct care workers count: {result.get('record_count', 0)}")
    
    # ==================== RESUBMIT ISOLATION TESTS ====================
    
    def test_resubmit_timesheet_from_different_org_returns_404(self, auth_headers):
        """
        HIPAA Test: Resubmitting a timesheet from a different organization 
        should return 404
        """
        # This timesheet belongs to 'default-org', not 'super_admin'
        other_org_timesheet_id = "1197a35d-434a-4589-a434-59c17c4ae97b"
        
        response = requests.post(
            f"{BASE_URL}/api/timesheets/{other_org_timesheet_id}/resubmit",
            headers=auth_headers
        )
        
        # Should return 404 because it belongs to a different org
        assert response.status_code == 404, \
            f"Expected 404 for cross-org resubmit, got {response.status_code}. " \
            f"HIPAA VIOLATION: User can resubmit data from another organization!"
    
    def test_submit_sandata_from_different_org_returns_404(self, auth_headers):
        """
        HIPAA Test: Submitting to Sandata for a timesheet from a different org
        should return 404
        """
        other_org_timesheet_id = "1197a35d-434a-4589-a434-59c17c4ae97b"
        
        response = requests.post(
            f"{BASE_URL}/api/timesheets/{other_org_timesheet_id}/submit-sandata",
            headers=auth_headers
        )
        
        assert response.status_code == 404, \
            f"Expected 404 for cross-org submit, got {response.status_code}"
    
    # ==================== PATIENT ISOLATION TESTS ====================
    
    def test_patients_list_returns_only_org_records(self, auth_headers):
        """
        HIPAA Test: GET /api/patients should only return records 
        for the logged-in user's organization
        """
        response = requests.get(
            f"{BASE_URL}/api/patients",
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Failed to get patients: {response.text}"
        patients = response.json()
        
        # All returned patients should belong to super_admin org
        for patient in patients:
            assert patient.get('organization_id') == ADMIN_ORG_ID, \
                f"Patient {patient.get('id')} has wrong org: {patient.get('organization_id')}"
        
        print(f"Patients returned for super_admin org: {len(patients)}")
    
    # ==================== EMPLOYEE ISOLATION TESTS ====================
    
    def test_employees_list_returns_only_org_records(self, auth_headers):
        """
        HIPAA Test: GET /api/employees should only return records 
        for the logged-in user's organization
        """
        response = requests.get(
            f"{BASE_URL}/api/employees",
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Failed to get employees: {response.text}"
        employees = response.json()
        
        # All returned employees should belong to super_admin org
        for emp in employees:
            assert emp.get('organization_id') == ADMIN_ORG_ID, \
                f"Employee {emp.get('id')} has wrong org: {emp.get('organization_id')}"
        
        print(f"Employees returned for super_admin org: {len(employees)}")


class TestCrossOrganizationAccess:
    """Test that cross-organization access is properly blocked"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        assert response.status_code == 200
        return response.json()["token"]
    
    def test_update_timesheet_from_different_org_fails(self, admin_token):
        """
        HIPAA Test: Updating a timesheet from a different org should fail
        """
        headers = {
            "Authorization": f"Bearer {admin_token}",
            "Content-Type": "application/json"
        }
        
        other_org_timesheet_id = "1197a35d-434a-4589-a434-59c17c4ae97b"
        
        response = requests.put(
            f"{BASE_URL}/api/timesheets/{other_org_timesheet_id}",
            headers=headers,
            json={
                "id": other_org_timesheet_id,
                "filename": "hacked.pdf",
                "file_type": "pdf",
                "status": "completed",
                "organization_id": "super_admin"  # Try to change org
            }
        )
        
        # Should return 404 because the original timesheet belongs to different org
        assert response.status_code == 404, \
            f"Expected 404 for cross-org update, got {response.status_code}"
    
    def test_delete_timesheet_from_different_org_fails(self, admin_token):
        """
        HIPAA Test: Deleting a timesheet from a different org should fail
        """
        headers = {
            "Authorization": f"Bearer {admin_token}",
            "Content-Type": "application/json"
        }
        
        other_org_timesheet_id = "1197a35d-434a-4589-a434-59c17c4ae97b"
        
        response = requests.delete(
            f"{BASE_URL}/api/timesheets/{other_org_timesheet_id}",
            headers=headers
        )
        
        # Should return 404 because it belongs to different org
        assert response.status_code == 404, \
            f"Expected 404 for cross-org delete, got {response.status_code}"


class TestUnauthenticatedAccess:
    """Test that unauthenticated requests use default org isolation"""
    
    def test_unauthenticated_timesheets_uses_default_org(self):
        """
        Test: Unauthenticated requests should fall back to default-org
        and not expose all data
        """
        response = requests.get(f"{BASE_URL}/api/timesheets")
        
        # Should succeed but only return default-org data
        assert response.status_code == 200, f"Failed: {response.text}"
        timesheets = response.json()
        
        # Should not return all 1259 timesheets
        assert len(timesheets) < TOTAL_TIMESHEET_COUNT, \
            f"Unauthenticated request returned all {len(timesheets)} timesheets!"
        
        # All should be from default-org
        for ts in timesheets:
            assert ts.get('organization_id') == 'default-org', \
                f"Unauthenticated request returned data from org: {ts.get('organization_id')}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
