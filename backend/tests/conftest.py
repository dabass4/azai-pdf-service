"""
Pytest configuration and fixtures for backend tests
"""
import pytest
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
import sys

# Add backend to path
sys.path.insert(0, '/app/backend')

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def test_db():
    """Provide a test database connection"""
    client = AsyncIOMotorClient(os.environ.get('MONGO_URL', 'mongodb://localhost:27017'))
    db = client['timesheet_scanner_test']
    
    yield db
    
    # Cleanup after tests
    await db.client.drop_database('timesheet_scanner_test')
    client.close()

@pytest.fixture
def test_user_data():
    """Provide test user data"""
    return {
        "email": "test@example.com",
        "password": "Test123!",
        "first_name": "Test",
        "last_name": "User",
        "organization_name": "Test Organization"
    }

@pytest.fixture
def test_patient_data():
    """Provide test patient data"""
    return {
        "first_name": "John",
        "last_name": "Doe",
        "sex": "Male",
        "date_of_birth": "1980-01-01",
        "medicaid_number": "123456789012",
        "is_complete": True
    }

@pytest.fixture
def test_employee_data():
    """Provide test employee data"""
    return {
        "first_name": "Jane",
        "last_name": "Smith",
        "sex": "Female",
        "date_of_birth": "1990-05-15",
        "ssn": "123-45-6789",
        "is_complete": True
    }

@pytest.fixture
def test_timesheet_data():
    """Provide test timesheet extracted data"""
    return {
        "client_name": "John Doe",
        "week_of": "Week of 10/6/2024",
        "employee_entries": [
            {
                "employee_name": "Jane Smith",
                "service_code": "HHA",
                "signature": "Yes",
                "time_entries": [
                    {
                        "date": "10/6",
                        "time_in": "8:00 AM",
                        "time_out": "4:00 PM",
                        "hours_worked": "8.0"
                    }
                ]
            }
        ]
    }
