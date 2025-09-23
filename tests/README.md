# Testing Guide

This guide explains how to run and write tests for the Telegram Support Bot project.

## Test Structure

The project uses a comprehensive testing strategy with multiple layers:

```
tests/
├── conftest.py                 # Pytest configuration and shared fixtures
├── unit/                       # Unit tests (fast, isolated)
│   ├── domain/                 # Domain entity tests
│   │   ├── test_ticket.py
│   │   ├── test_comment.py
│   │   └── test_user.py
│   ├── application/            # Use case tests
│   │   ├── test_view_comments_use_case.py
│   │   ├── test_add_comment_use_case.py
│   │   └── test_view_tickets_use_case.py
│   └── presentation/           # Telegram handler tests
└── integration/                # Integration tests (slower, with external systems)
    └── infrastructure/         # Repository integration tests
        ├── test_postgresql_ticket_repository.py
        └── test_postgresql_comment_repository.py
```

## Running Tests

### Quick Start

1. **Install test dependencies:**
   ```bash
   python run_tests.py install
   ```

2. **Check test environment:**
   ```bash
   python run_tests.py check
   ```

3. **Run all tests:**
   ```bash
   python run_tests.py all
   ```

### Test Commands

- **Unit tests only (fast):**
  ```bash
  python run_tests.py unit
  ```

- **Integration tests only:**
  ```bash
  python run_tests.py integration
  ```

- **Fast tests only (exclude slow tests):**
  ```bash
  python run_tests.py fast
  ```

- **Tests with HTML coverage report:**
  ```bash
  python run_tests.py html
  ```

- **Specific test file:**
  ```bash
  python run_tests.py --test tests/unit/domain/test_ticket.py
  ```

- **Specific test function:**
  ```bash
  python run_tests.py --test tests/unit/domain/test_ticket.py::TestTicket::test_create_valid_ticket
  ```

### Direct pytest Commands

You can also use pytest directly:

```bash
# All tests with coverage
pytest tests/ --cov=src --cov-report=term-missing

# Unit tests only
pytest tests/unit/ -v

# Integration tests only
pytest tests/integration/ -v

# Specific test with verbose output
pytest tests/unit/domain/test_ticket.py::TestTicket::test_create_valid_ticket -v -s
```

## Test Categories

### Unit Tests

**Purpose:** Test individual components in isolation
**Characteristics:**
- Fast execution (< 1ms per test)
- No external dependencies
- Use mocks for dependencies
- Focus on business logic

**Examples:**
- Domain entity validation
- Use case logic
- Business rule enforcement

### Integration Tests

**Purpose:** Test component interactions with external systems
**Characteristics:**
- Slower execution
- Use real or test databases
- Test actual database operations
- Focus on data flow

**Examples:**
- Repository database operations  
- API endpoint testing
- Full workflow testing

## Test Coverage

The project aims for:
- **80%+ overall test coverage**
- **90%+ domain layer coverage** (business logic)
- **70%+ application layer coverage** (use cases)
- **60%+ infrastructure layer coverage** (repositories)

### Viewing Coverage

1. **Terminal coverage report:**
   ```bash
   python run_tests.py all
   ```

2. **HTML coverage report:**
   ```bash
   python run_tests.py html
   # Open htmlcov/index.html in browser
   ```

## Writing Tests

### Domain Entity Tests

Test business logic and validation:

```python
def test_ticket_validation(self):
    """Test ticket field validation"""
    with pytest.raises(ValueError, match="Title cannot be empty"):
        Ticket(
            number="TKT-001",
            title="",  # Invalid empty title
            description="Test",
            status=TicketStatus.OPEN,
            priority=TicketPriority.MEDIUM,
            creator_email="user@example.com"
        )
```

### Use Case Tests

Test business orchestration with mocked dependencies:

```python
@pytest.mark.asyncio
async def test_view_comments_success(self, use_case, mock_repositories):
    """Test successful comment viewing"""
    ticket_repo, comment_repo, user_repo = mock_repositories
    
    # Setup mocks
    ticket_repo.get_by_number.return_value = sample_ticket
    comment_repo.get_by_ticket_number.return_value = sample_comments
    
    # Execute
    response = await use_case.execute(request)
    
    # Verify
    assert len(response.comments) == 2
    ticket_repo.get_by_number.assert_called_once_with("TKT-001")
```

### Integration Tests

Test database operations:

```python
@pytest.mark.asyncio
async def test_create_ticket_database(self, repository, mock_connection):
    """Test ticket creation in database"""
    # Setup database mock
    mock_connection.fetchrow.return_value = sample_db_row
    
    # Execute
    created_ticket = await repository.create(sample_ticket)
    
    # Verify database interaction
    mock_connection.fetchrow.assert_called_once()
    assert "INSERT INTO tickets" in call_args[0][0]
```

## Test Best Practices

### 1. Test Naming
- Use descriptive test names: `test_create_ticket_with_invalid_email_should_raise_error`
- Follow pattern: `test_[what]_[condition]_[expected_result]`

### 2. Test Structure (AAA Pattern)
```python
def test_example(self):
    # Arrange - Set up test data
    ticket = create_sample_ticket()
    
    # Act - Execute the operation
    result = ticket.validate()
    
    # Assert - Verify the result
    assert result is True
```

### 3. Use Fixtures
```python
@pytest.fixture
def sample_ticket(self):
    """Reusable test data"""
    return Ticket(...)

def test_with_fixture(self, sample_ticket):
    # Use fixture
    assert sample_ticket.number == "TKT-001"
```

### 4. Mock External Dependencies
```python
@patch('src.infrastructure.database.connection.asyncpg.connect')
async def test_with_mocked_database(self, mock_connect):
    # Test with mocked database connection
    pass
```

### 5. Test Error Cases
```python
def test_invalid_input_raises_error(self):
    with pytest.raises(ValueError, match="Expected error message"):
        invalid_operation()
```

## Continuous Integration

Tests are designed to run in CI/CD environments:

### GitHub Actions Example
```yaml
- name: Run Tests
  run: |
    pip install -r requirements.txt
    pip install -r requirements-test.txt
    python run_tests.py all
```

### Test Performance
- Unit tests should complete in < 30 seconds
- Integration tests should complete in < 2 minutes  
- Full test suite should complete in < 5 minutes

## Troubleshooting

### Common Issues

1. **Import errors:**
   ```bash
   # Add project root to Python path
   export PYTHONPATH="${PYTHONPATH}:$(pwd)"
   ```

2. **Async test issues:**
   ```python
   # Use pytest-asyncio
   @pytest.mark.asyncio
   async def test_async_function():
       pass
   ```

3. **Database connection issues:**
   ```python
   # Use database fixtures for integration tests
   @pytest.fixture
   async def test_database():
       # Setup test database
       pass
   ```

### Debug Tests

```bash
# Run with verbose output and no capture
pytest tests/unit/domain/test_ticket.py -v -s

# Run with pdb debugger
pytest tests/unit/domain/test_ticket.py --pdb

# Run only failed tests
pytest --lf
```

## Test Data Management

### Fixtures for Test Data
- Use factories for creating test objects
- Keep test data minimal and focused
- Use realistic but not production data

### Database Testing
- Use separate test database
- Clean up after each test
- Use transactions that rollback

This comprehensive testing approach ensures code quality, reliability, and maintainability of the Telegram Support Bot.