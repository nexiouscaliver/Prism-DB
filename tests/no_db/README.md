# No Database Tests

This directory contains tests that can be run without a database connection. These tests are designed to validate the basic functionality of various components in isolation, using mocks to simulate any database-dependent components.

## Purpose

The main purpose of these tests is to:

1. Provide a quick way to verify basic functionality without setting up a database
2. Enable CI/CD pipelines to run tests without database configuration
3. Test edge cases and error handling more easily with mocked responses
4. Increase test coverage for core functionality

## Test Structure

### Mock Strategy

Tests in this directory use the following mocking strategies:

- **Complete Dependency Mocking**: For tests like `test_basic_agent_mocks.py`, we mock all external dependencies (including libraries like `agno`, `spacy`, etc.) to ensure the tests can run in any environment.
- **Partial Mocking**: Some tests may use partial mocking, where only database connections are mocked but real library dependencies are used.
- **Sample Data**: Tests use the sample data defined in `sample_data.py` to provide consistent test inputs and expected outputs.

### Running the Tests

To run all the tests in this directory:

```bash
python -m tests.no_db.run_tests
```

To run a specific test:

```bash
python -m tests.no_db.test_basic_agent_mocks
```

## Adding New Tests

When adding new tests to this directory:

1. Ensure the test doesn't require a database connection
2. Use appropriate mocking for any database-dependent components
3. Consider adding new sample data to `sample_data.py` if needed
4. Ensure the test can be run in isolation
5. Update this README if you introduce a new testing approach

## Best Practices

- Keep test files focused on testing specific components or functions
- Use descriptive test names that clearly indicate what's being tested
- Make use of setUp/tearDown for common test setup and cleanup
- Mock external dependencies at the lowest possible level
- Add comments explaining complex mocking setups 