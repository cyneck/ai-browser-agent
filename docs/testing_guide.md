# Testing Guide for ARIA Snapshot Usage

This guide explains how to test the ARIA snapshot functionality comprehensively.

## Overview

The ARIA snapshot usage example (`examples/aria_snapshot_usage.py`) has been designed with comprehensive testing in mind. We've created multiple types of tests to ensure reliability and functionality.

## Test Structure

### 1. Unit Tests (`tests/unit/test_aria_snapshot_usage.py`)

**Purpose**: Test individual methods with mocked dependencies
**Advantages**: Fast, isolated, no external dependencies
**Use Cases**: Development, CI/CD pipelines, quick validation

**Key Test Categories**:
- Setup and cleanup functionality
- ARIA snapshot parsing and extraction
- Element finding algorithms
- Selector generation logic
- Form analysis capabilities
- Error handling

### 2. Integration Tests (`tests/integration/test_aria_snapshot_integration.py`)

**Purpose**: Test with real browser instances and HTML pages
**Advantages**: Real-world validation, end-to-end testing
**Use Cases**: Pre-deployment validation, compatibility testing

**Key Test Categories**:
- Real browser interaction
- HTML page analysis
- Performance testing
- Edge case handling
- Cross-browser compatibility

## Running Tests

### Quick Start

```bash
# Install test dependencies
pip install -r test_requirements.txt

# Run all unit tests
python -m pytest tests/unit/test_aria_snapshot_usage.py -v

# Run integration tests (requires Playwright)
python -m pytest tests/integration/test_aria_snapshot_integration.py -v

# Run with coverage
python -m pytest tests/ --cov=examples --cov-report=html
```

### Using the Test Runner

We've provided a convenient test runner script:

```bash
python scripts/test_aria_usage.py
```

This interactive script offers:
1. Unit Tests Only
2. Integration Tests Only  
3. All Tests (excluding slow)
4. All Tests (including slow)
5. Smoke Test (basic functionality)
6. Run with Coverage
7. Check test dependencies
8. Run example manually (demo)

### Advanced Testing Commands

```bash
# Run specific test class
python -m pytest tests/unit/test_aria_snapshot_usage.py::TestARIASnapshotExamples -v

# Run specific test method
python -m pytest tests/unit/test_aria_snapshot_usage.py::TestARIASnapshotExamples::test_find_interactive_elements -v

# Run tests with detailed output
python -m pytest tests/ -v -s --tb=long

# Run tests in parallel (if pytest-xdist is installed)
python -m pytest tests/ -n auto

# Run with timeout protection
python -m pytest tests/ --timeout=300

# Skip slow tests
python -m pytest tests/ -m "not slow"

# Run only integration tests
python -m pytest tests/ -m integration
```

## Test Categories and Markers

### Markers Used

- `@pytest.mark.slow`: Tests that take significant time (external sites, large operations)
- `@pytest.mark.integration`: Integration tests requiring real browser
- `@pytest.mark.unit`: Unit tests with mocked dependencies  
- `@pytest.mark.network`: Tests requiring network access

### Running by Category

```bash
# Skip slow tests (recommended for development)
python -m pytest -m "not slow"

# Run only unit tests
python -m pytest -m unit

# Run only integration tests
python -m pytest -m integration

# Run tests that don't require network
python -m pytest -m "not network"
```

## Understanding Test Output

### Successful Unit Test Example

```
tests/unit/test_aria_snapshot_usage.py::TestARIASnapshotExamples::test_find_interactive_elements PASSED
```

This indicates:
- The test file and class
- The specific test method
- PASSED status

### Successful Integration Test Example  

```
tests/integration/test_aria_snapshot_integration.py::TestARIASnapshotIntegration::test_basic_aria_snapshot_with_real_page PASSED
```

Integration tests may show:
- Browser console output
- ARIA snapshot JSON data
- Performance timing information

### Coverage Report

When using `--cov`, you'll see:
```
Name                                   Stmts   Miss  Cover
----------------------------------------------------------
examples/aria_snapshot_usage.py         150      5    97%
----------------------------------------------------------
TOTAL                                   150      5    97%
```

## Troubleshooting Common Issues

### 1. Playwright Not Installed

```
Error: Could not setup Playwright
```

**Solution**:
```bash
pip install playwright
playwright install
```

### 2. Missing Test Dependencies

```
ModuleNotFoundError: No module named 'pytest'
```

**Solution**:
```bash
pip install -r test_requirements.txt
```

### 3. Browser Launch Failures

```
Error: Browser launch failed
```

**Solutions**:
- Ensure Playwright browsers are installed: `playwright install`
- Try running in headless mode (already default in tests)
- Check system permissions for browser execution

### 4. Timeout Issues

```
Test timed out after 300 seconds
```

**Solutions**:
- Increase timeout: `pytest --timeout=600`
- Skip slow tests: `pytest -m "not slow"`
- Check network connectivity for external site tests

### 5. Network-Related Test Failures

```
Test failed: network issue
```

**Solutions**:
- Run without network tests: `pytest -m "not network"`
- Check internet connectivity
- Some tests may be skipped automatically

## Best Practices for Testing ARIA Snapshots

### 1. Mock External Dependencies

Unit tests should mock Playwright components:
```python
@pytest.fixture
def mock_playwright():
    mock_page = Mock()
    mock_page.accessibility.snapshot.return_value = sample_data
    return mock_page
```

### 2. Use Representative Test Data

Create realistic ARIA snapshots for testing:
```python
sample_aria_snapshot = {
    "role": "WebArea",
    "name": "Test Page",
    "children": [
        {"role": "button", "name": "Submit"},
        {"role": "textbox", "name": "Search"}
    ]
}
```

### 3. Test Edge Cases

Include tests for:
- Empty pages
- Pages with no interactive elements  
- Malformed HTML
- Network failures
- Browser crashes

### 4. Performance Considerations

Monitor test performance:
```python
def test_aria_snapshot_performance(self):
    start_time = time.time()
    snapshot = examples.basic_aria_snapshot(url)
    duration = time.time() - start_time
    assert duration < 10.0, f"Too slow: {duration}s"
```

### 5. Consistent Test Environment

Use fixtures for consistent setup:
```python
@pytest.fixture
def test_html_file(self, tmp_path):
    html_content = "<!DOCTYPE html>..."
    test_file = tmp_path / "test.html"
    test_file.write_text(html_content)
    return f"file://{test_file.resolve()}"
```

## Continuous Integration

For CI/CD pipelines, use:

```bash
# Install dependencies
pip install -r test_requirements.txt
playwright install --with-deps

# Run tests with appropriate markers
python -m pytest tests/ -m "not slow and not network" --tb=short

# Generate coverage report  
python -m pytest tests/ --cov=examples --cov-report=xml
```

## Development Workflow

### 1. TDD Approach

1. Write failing test for new feature
2. Implement minimal code to pass test
3. Refactor and improve
4. Repeat

### 2. Testing New Features

When adding new methods to `ARIASnapshotExamples`:

1. Add unit tests with mocks first
2. Add integration tests with real browsers
3. Update test runner if needed
4. Add performance tests for complex operations

### 3. Debugging Test Failures

Use these techniques:
- Add `-s` flag to see print statements
- Use `--tb=long` for detailed tracebacks
- Add `import pdb; pdb.set_trace()` for debugging
- Check test logs and browser console output

## Test Maintenance

### Regular Maintenance Tasks

1. **Update test data**: Keep ARIA snapshot samples current with web standards
2. **Review slow tests**: Optimize or move to appropriate category
3. **Check dependencies**: Update test requirements regularly  
4. **Validate browser compatibility**: Test with different Playwright browser versions

### Code Quality Checks

```bash
# Run linting (if configured)
black tests/ examples/
isort tests/ examples/

# Type checking (if using mypy)
mypy examples/ tests/

# Security checks (if using bandit)
bandit -r examples/
```

This comprehensive testing approach ensures the ARIA snapshot functionality is reliable, maintainable, and ready for production use.