#!/usr/bin/env python3
"""
Simple test to verify the Sandata submission validation logic
"""
import sys
import os
sys.path.append('/app/backend')

from server import submit_to_sandata, Timesheet, ExtractedData, EmployeeEntry
from unittest.mock import AsyncMock, patch
import asyncio

async def test_validation():
    """Test the validation logic for complete/incomplete profiles"""
    
    # Create a mock timesheet with extracted data
    timesheet = Timesheet(
        filename="test.pdf",
        file_type="pdf",
        patient_id="test-patient-id"
    )
    
    # Add extracted data with employee
    timesheet.extracted_data = ExtractedData(
        client_name="John Doe",
        employee_entries=[
            EmployeeEntry(
                employee_name="Jane Smith",
                service_code="HHA",
                signature="Yes"
            )
        ]
    )
    
    # Test 1: Incomplete patient profile
    print("Test 1: Incomplete patient profile")
    with patch('server.db') as mock_db:
        # Mock patient lookup - incomplete profile
        mock_db.patients.find_one = AsyncMock(return_value={
            "id": "test-patient-id",
            "first_name": "John",
            "last_name": "Doe",
            "is_complete": False
        })
        
        result = await submit_to_sandata(timesheet)
        print(f"Result: {result}")
        assert result["status"] == "blocked"
        assert "Patient profile incomplete" in result["message"]
        print("✓ Test 1 passed\n")
    
    # Test 2: Incomplete employee profile
    print("Test 2: Incomplete employee profile")
    with patch('server.db') as mock_db:
        # Mock patient lookup - complete profile
        mock_db.patients.find_one = AsyncMock(return_value={
            "id": "test-patient-id",
            "first_name": "John",
            "last_name": "Doe",
            "is_complete": True
        })
        
        # Mock employee lookup - incomplete profile
        mock_db.employees.find_one = AsyncMock(return_value={
            "id": "test-employee-id",
            "first_name": "Jane",
            "last_name": "Smith",
            "is_complete": False
        })
        
        result = await submit_to_sandata(timesheet)
        print(f"Result: {result}")
        assert result["status"] == "blocked"
        assert "Employee profile(s) incomplete" in result["message"]
        print("✓ Test 2 passed\n")
    
    # Test 3: All profiles complete - should proceed
    print("Test 3: All profiles complete")
    with patch('server.db') as mock_db:
        # Mock patient lookup - complete profile
        mock_db.patients.find_one = AsyncMock(return_value={
            "id": "test-patient-id",
            "first_name": "John",
            "last_name": "Doe",
            "is_complete": True
        })
        
        # Mock employee lookup - complete profile
        mock_db.employees.find_one = AsyncMock(return_value={
            "id": "test-employee-id",
            "first_name": "Jane",
            "last_name": "Smith",
            "is_complete": True
        })
        
        result = await submit_to_sandata(timesheet)
        print(f"Result: {result}")
        assert result["status"] == "success"
        assert "MOCKED" in result["message"]
        print("✓ Test 3 passed\n")
    
    print("All tests passed! ✓")

if __name__ == "__main__":
    asyncio.run(test_validation())