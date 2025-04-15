# PrismDB Test Suite

This directory contains tests for the PrismDB application. The test suite uses pytest for test running and mocking.

## Directory Structure

- `tests/unit/`: Unit tests for individual components
- `tests/integration/`: Integration tests that test multiple components together
- `tests/conftest.py`: Shared test fixtures and configuration

## Running Tests

### Prerequisites

Make sure you have installed all the required dependencies:

```bash
pip install -r requirements.txt
```

### Running All Tests

To run all tests:

```bash
pytest
```

### Running Specific Test Categories

To run only unit tests:

```bash
pytest tests/unit/
```

To run only integration tests:

```bash
pytest tests/integration/
```

### Running a Specific Test File

```bash
pytest tests/unit/test_base_tool.py
```

### Running a Specific Test

```bash
pytest tests/unit/test_base_tool.py::TestBaseTool::test_base_tool_initialization
```

## Test Coverage

To run tests with coverage reporting:

```bash
pytest --cov=.
```

For a more detailed HTML coverage report:

```bash
pytest --cov=. --cov-report=html
```

Then open `htmlcov/index.html` in your browser to view the coverage report.

## Writing New Tests

### Guidelines for Adding New Tests

1. **Organize by Component**: Place tests in the appropriate directory structure based on what you're testing:
   - `unit/`: For testing individual functions, classes, or methods
   - `integration/`: For testing interactions between components

2. **Naming Conventions**:
   - Test files should be named `test_*.py`
   - Test classes should be named `Test*`
   - Test methods should be named `test_*`

3. **Test Structure**:
   - Each test should focus on a single functionality
   - Use meaningful test names that describe what's being tested
   - Follow the Arrange-Act-Assert (AAA) pattern

4. **Mocking**:
   - Use fixtures from `conftest.py` when possible
   - Use `unittest.mock` for mocking dependencies
   - Use `patch` or `MagicMock` for complex mocking scenarios

### Example of a New Test

```python
import pytest
from unittest.mock import patch, MagicMock
from your_module import YourClass

class TestYourClass:
    """Tests for YourClass."""
    
    def test_your_method(self):
        """Test that your_method works correctly."""
        # Arrange
        instance = YourClass()
        
        # Act
        result = instance.your_method()
        
        # Assert
        assert result == expected_value
    
    @patch('your_module.dependency')
    def test_with_mock(self, mock_dependency):
        """Test a method that has dependencies."""
        # Arrange
        mock_dependency.return_value = "mocked_value"
        instance = YourClass()
        
        # Act
        result = instance.method_with_dependency()
        
        # Assert
        assert result == "mocked_value"
        mock_dependency.assert_called_once()
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure that the project root is in your Python path. You might need to run:
   ```bash
   export PYTHONPATH=$PYTHONPATH:$(pwd)
   ```

2. **Database Connection Issues**: Integration tests use SQLite in-memory databases. If you see connection errors, ensure SQLite is working correctly.

3. **Async Test Failures**: Make sure you mark async tests with `@pytest.mark.asyncio` and have `pytest-asyncio` installed.

## Continuous Integration

Tests are automatically run in CI/CD pipelines when changes are pushed to the repository. Ensure all tests pass locally before pushing changes. 