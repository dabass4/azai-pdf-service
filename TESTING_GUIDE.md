# Testing Guide - Timesheet SaaS

## Quick Start

### Run All Tests
```bash
./scripts/run_all_tests.sh
```

### Run Critical Tests Only (Before Deployment)
```bash
cd /app/backend
pytest tests/test_critical_regression.py -v -m critical
```

### Run Specific Test Categories
```bash
# Time parsing tests
pytest tests/ -v -m time

# Date parsing tests  
pytest tests/ -v -m date

# Multi-tenancy tests
pytest tests/ -v -m multitenancy

# Authentication tests
pytest tests/ -v -m auth
```

---

## Test Categories

### 1. Critical Regression Tests
**File**: `/app/backend/tests/test_critical_regression.py`

**Purpose**: Prevent breaking changes to core functionality

**Tests**:
- ✅ Time parsing (13 formats)
- ✅ Date parsing (7 formats)
- ✅ Special rounding rule (>35 min = 3 units)
- ✅ Unit calculations
- ✅ Hours calculations
- ✅ Module API stability

**Run**: `pytest tests/test_critical_regression.py -v -m critical`

**Status**: 8/8 PASSING ✅

---

### 2. Time & Date Parsing Tests
**Files**: 
- `/app/backend/test_time_utils.py`
- `/app/backend/test_date_utils.py`

**Purpose**: Comprehensive testing of all time/date formats

**Tests**:
- 31 time parsing test cases
- 21 date parsing test cases
- Week range parsing
- Format normalization

**Run**: 
```bash
cd /app/backend
python3 test_time_utils.py
python3 test_date_utils.py
```

**Status**: 52/52 PASSING ✅

---

## Writing New Tests

### Test Structure

```python
import pytest

@pytest.mark.critical  # Mark as critical test
@pytest.mark.time      # Category marker
def test_my_feature():
    """Clear description of what's being tested"""
    # Arrange
    input_data = "test input"
    
    # Act
    result = function_to_test(input_data)
    
    # Assert
    assert result == expected_output, "Clear failure message"
```

### Best Practices

1. **Test One Thing**: Each test should verify one specific behavior
2. **Clear Names**: `test_time_parsing_handles_military_format()` not `test1()`
3. **Good Assertions**: Include helpful error messages
4. **Independence**: Tests should not depend on each other
5. **Fast**: Keep tests fast (<1 second per test)

### Adding Regression Tests

When fixing a bug, ALWAYS add a regression test:

```python
def test_bug_123_time_parsing_321_format():
    """
    Regression test for Bug #123
    Ensure "321" format parses correctly as 3:21 PM
    """
    result = normalize_am_pm("321")
    assert result == "3:21 PM", "Bug #123 regression detected!"
```

---

## Test Fixtures

Located in `/app/backend/tests/conftest.py`

Available fixtures:
- `test_db`: Test database connection
- `test_user_data`: Sample user data
- `test_patient_data`: Sample patient data
- `test_employee_data`: Sample employee data
- `test_timesheet_data`: Sample timesheet data

Usage:
```python
def test_with_database(test_db):
    # test_db is automatically provided
    result = await test_db.patients.find().to_list(10)
    assert len(result) >= 0
```

---

## CI/CD Integration

### GitHub Actions Example

Create `.github/workflows/test.yml`:

```yaml
name: Test Suite

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        cd backend
        pip install -r requirements.txt
        pip install pytest pytest-asyncio
    
    - name: Run critical tests
      run: |
        cd backend
        pytest tests/test_critical_regression.py -v -m critical
    
    - name: Run all tests
      run: |
        ./scripts/run_all_tests.sh
```

---

## Test-Driven Development (TDD)

### Process

1. **Write Test First** (RED)
```python
def test_new_feature():
    result = new_function("input")
    assert result == "expected"
```

2. **Run Test - It Should Fail**
```bash
pytest tests/test_new_feature.py
# FAIL: new_function not implemented
```

3. **Implement Feature** (GREEN)
```python
def new_function(input):
    return "expected"
```

4. **Run Test - It Should Pass**
```bash
pytest tests/test_new_feature.py
# PASS: All tests passed
```

5. **Refactor** (REFACTOR)
- Improve code quality
- Run tests again to ensure nothing broke

---

## Debugging Failed Tests

### Show Detailed Output
```bash
pytest tests/test_file.py -vv
```

### Show Print Statements
```bash
pytest tests/test_file.py -s
```

### Run Specific Test
```bash
pytest tests/test_file.py::test_specific_function -v
```

### Drop to Debugger on Failure
```bash
pytest tests/test_file.py --pdb
```

### See Test Coverage
```bash
pytest tests/ --cov=/app/backend --cov-report=html
# Opens coverage report in browser
```

---

## Common Issues

### Issue: Import Errors
**Solution**: Ensure `/app/backend` is in Python path
```python
import sys
sys.path.insert(0, '/app/backend')
```

### Issue: Database Connection Fails
**Solution**: Check MongoDB is running
```bash
sudo supervisorctl status mongodb
```

### Issue: Tests Pass Locally But Fail in CI
**Solution**: Check environment variables are set
```bash
export MONGO_URL="mongodb://localhost:27017"
export DB_NAME="timesheet_scanner_test"
```

---

## Test Maintenance

### When to Update Tests

1. **Feature Changes**: Update tests when requirements change
2. **Bug Fixes**: Add regression tests for fixed bugs
3. **Refactoring**: Tests should still pass after refactoring
4. **API Changes**: Update tests if API contracts change

### Test Review Checklist

- [ ] All tests have clear names and descriptions
- [ ] Tests are independent (can run in any order)
- [ ] Tests are fast (<1 second each)
- [ ] Critical paths have regression tests
- [ ] Test coverage is >80% for critical modules
- [ ] Flaky tests are fixed or removed
- [ ] Tests document expected behavior

---

## Performance Testing

### Measure Test Execution Time
```bash
pytest tests/ --durations=10
# Shows 10 slowest tests
```

### Parallel Test Execution
```bash
pip install pytest-xdist
pytest tests/ -n 4  # Run on 4 CPU cores
```

---

## Resources

- **Pytest Documentation**: https://docs.pytest.org/
- **Test Fixtures**: https://docs.pytest.org/en/stable/fixture.html
- **Markers**: https://docs.pytest.org/en/stable/mark.html
- **Coverage**: https://coverage.readthedocs.io/

---

**Last Updated**: 2025-11-07  
**Next Review**: 2025-12-07
