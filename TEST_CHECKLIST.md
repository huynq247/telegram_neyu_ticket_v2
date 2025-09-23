# 📋 Test Checklist - Telegram Support Bot

Đây là checklist để kiểm tra và test tất cả các thành phần của dự án sau khi refactor sang Clean Architecture.

## 🏗️ **Kiểm Tra Cấu Trúc Dự Án**

### ✅ **1. Cấu Trúc Thư Mục**
- [ ] `src/domain/` - Chứa business logic thuần túy
  - [ ] `entities/` - Ticket, Comment, User entities
  - [ ] `repositories/` - Abstract repository interfaces
  - [ ] `services/` - Domain services
- [ ] `src/application/` - Use cases và business orchestration
  - [ ] `use_cases/` - ViewComments, AddComment, ViewTickets
  - [ ] `dto/` - Data Transfer Objects
- [ ] `src/infrastructure/` - External systems implementation
  - [ ] `repositories/` - PostgreSQL implementations
  - [ ] `database/` - Database connection
- [ ] `src/presentation/` - Telegram UI layer
  - [ ] `handlers/` - Telegram message handlers
  - [ ] `formatters/` - Message formatting
  - [ ] `keyboards/` - Telegram keyboards
- [ ] `src/container.py` - Dependency injection
- [ ] `src/config/` - Configuration management

### ✅ **2. Files Tồn Tại**
- [ ] `src/app.py` - Main application entry point
- [ ] `requirements.txt` - Dependencies chính
- [ ] `requirements-test.txt` - Test dependencies
- [ ] `pytest.ini` - Test configuration
- [ ] `run_tests.py` - Test runner script
- [ ] `tests/conftest.py` - Test fixtures
- [ ] `.env.example` - Environment variables template

## 🧪 **Kiểm Tra Test Framework**

### ✅ **3. Test Dependencies**
```bash
# Kiểm tra pytest có cài đặt không
python -c "import pytest; print(f'pytest {pytest.__version__}')"

# Kiểm tra pytest-asyncio
python -c "import pytest_asyncio; print('pytest-asyncio OK')"

# Kiểm tra coverage
python -c "import coverage; print('coverage OK')"
```

- [ ] pytest đã cài đặt
- [ ] pytest-asyncio đã cài đặt  
- [ ] pytest-cov đã cài đặt
- [ ] unittest.mock có sẵn

### ✅ **4. Test Structure**
- [ ] `tests/unit/domain/` - Domain entity tests
- [ ] `tests/unit/application/` - Use case tests
- [ ] `tests/integration/infrastructure/` - Repository tests
- [ ] Test files có naming convention đúng: `test_*.py`

## 🔧 **Kiểm Tra Dependencies**

### ✅ **5. Python Packages**
```bash
# Install main dependencies
pip install -r requirements.txt

# Install test dependencies  
pip install -r requirements-test.txt
```

**Main Dependencies:**
- [ ] `python-telegram-bot==20.6` - Telegram bot framework
- [ ] `asyncpg==0.28.0` - PostgreSQL async driver
- [ ] `pydantic==2.4.2` - Data validation
- [ ] `python-dotenv==1.0.0` - Environment variables

**Test Dependencies:**
- [ ] `pytest>=7.4.0`
- [ ] `pytest-asyncio>=0.21.0`
- [ ] `pytest-cov>=4.1.0`
- [ ] `pytest-mock>=3.11.1`

## 🏃‍♂️ **Quick Test Commands**

### ✅ **6. Test Environment Setup**
```bash
# 1. Kiểm tra test environment
python run_tests.py check

# 2. Cài đặt test dependencies
python run_tests.py install
```

### ✅ **7. Run Tests by Category**
```bash
# Unit tests only (nhanh)
python run_tests.py unit

# Integration tests only  
python run_tests.py integration

# All tests với coverage
python run_tests.py all

# Tests với HTML report
python run_tests.py html
```

### ✅ **8. Specific Tests**
```bash
# Test specific file
python run_tests.py --test tests/unit/domain/test_comment.py

# Test specific function
pytest tests/unit/domain/test_comment.py::TestComment::test_create_valid_comment -v

# Test với debug output
pytest tests/unit/domain/test_comment.py -v -s
```

## 🎯 **Manual Testing Components**

### ✅ **9. Domain Layer Testing**
Kiểm tra business logic không có external dependencies:

```python
# Test Comment entity
python -c "
from src.domain.entities.comment import Comment, CommentType
comment = Comment(
    ticket_number='TKT-001',
    content='Test comment',
    author_email='test@example.com'
)
print(f'Comment created: {comment.content}')
print(f'Comment type: {comment.comment_type}')
print(f'Is recent: {comment.is_recent}')
"
```

- [ ] Comment entity tạo được
- [ ] Validation hoạt động (empty content, invalid email)
- [ ] Business rules hoạt động (permissions, visibility)

### ✅ **10. Application Layer Testing**
Kiểm tra use cases với mock dependencies:

```python
# Test import use cases
python -c "
from src.application.use_cases.view_comments import ViewCommentsUseCase
from src.application.dto import ViewCommentsRequest
print('Use cases import successfully')
"
```

- [ ] Use cases import được
- [ ] DTOs hoạt động
- [ ] Business validation logic

### ✅ **11. Infrastructure Layer Testing**
Kiểm tra database connections:

```python
# Test database imports
python -c "
from src.infrastructure.database.connection import DatabaseConnection
from src.infrastructure.repositories.postgresql_comment_repository import PostgreSQLCommentRepository
print('Infrastructure imports successfully')
"
```

- [ ] Repository implementations import được
- [ ] Database connection class hoạt động
- [ ] Async methods defined correctly

### ✅ **12. Dependency Injection Testing**
Kiểm tra container setup:

```python
# Test DI container
python -c "
from src.container import Container
from src.config.container_config import ContainerConfig
container = Container()
config = ContainerConfig()
print('DI container works')
"
```

- [ ] Container tạo được
- [ ] Dependencies resolve được
- [ ] Configuration load được

## 🚀 **Integration Testing**

### ✅ **13. Database Setup (Optional)**
Nếu muốn test với database thật:

```bash
# Setup test database
createdb telegram_bot_test

# Set environment variables
export DATABASE_URL="postgresql://user:pass@localhost/telegram_bot_test"
export TEST_DATABASE_URL="postgresql://user:pass@localhost/telegram_bot_test"
```

- [ ] Test database tạo được
- [ ] Connection string hoạt động
- [ ] Tables có thể tạo được

### ✅ **14. End-to-End Flow Testing**
Test workflow hoàn chỉnh:

```python
# Test complete flow (với mocks)
python -c "
import asyncio
from src.container import Container
from src.application.dto import ViewCommentsRequest

async def test_flow():
    container = Container()
    # This would require proper setup
    print('Flow test would work with proper setup')

asyncio.run(test_flow())
"
```

## 📊 **Coverage & Quality Checks**

### ✅ **15. Code Coverage**
```bash
# Run tests với coverage details
python run_tests.py html

# Check coverage thresholds
pytest tests/ --cov=src --cov-fail-under=80
```

- [ ] Coverage >= 80% overall
- [ ] Domain layer coverage >= 90%
- [ ] Application layer coverage >= 70%
- [ ] HTML report tạo được

### ✅ **16. Code Quality**
```bash
# Check imports
find src/ -name "*.py" -exec python -m py_compile {} \;

# Check syntax
python -m compileall src/
```

- [ ] All Python files compile được
- [ ] No syntax errors
- [ ] Import paths đúng

## 🔍 **Common Issues & Solutions**

### ✅ **17. Troubleshooting**

**Issue: Import errors**
```bash
# Solution: Add project to Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
# Or
python -m pytest tests/ # Run as module
```

**Issue: Async test errors**
```bash
# Solution: Check pytest-asyncio
pip install pytest-asyncio
# Ensure @pytest.mark.asyncio on async tests
```

**Issue: No tests collected**
```bash
# Solution: Check test file naming
# Files must be: test_*.py or *_test.py
# Functions must be: test_*
```

**Issue: Mock import errors**
```bash
# Solution: Use proper mock imports
from unittest.mock import Mock, AsyncMock, patch
```

## ✅ **Final Checklist**

### **18. Ready for Development**
- [ ] All dependencies installed (`pip install -r requirements.txt`)
- [ ] Test dependencies installed (`pip install -r requirements-test.txt`)
- [ ] Test environment verified (`python run_tests.py check`)
- [ ] Sample tests run successfully (`python run_tests.py unit`)
- [ ] Code structure follows Clean Architecture
- [ ] All layers properly separated
- [ ] Dependency injection working
- [ ] Tests provide good coverage

### **19. Ready for Production**
- [ ] All tests pass (`python run_tests.py all`)
- [ ] Coverage meets requirements (>= 80%)
- [ ] Integration tests with real database work
- [ ] Error handling tested
- [ ] Performance acceptable
- [ ] Documentation complete

---

## 🎯 **Quick Start Commands**

```bash
# 1. Setup
pip install -r requirements.txt
pip install -r requirements-test.txt

# 2. Verify
python run_tests.py check

# 3. Test
python run_tests.py unit      # Fast unit tests
python run_tests.py all       # All tests with coverage
python run_tests.py html      # Generate HTML coverage report

# 4. Development
pytest tests/unit/domain/test_comment.py -v -s  # Debug specific test
```

**📌 Lưu ý:** Checklist này giúp đảm bảo project hoạt động đúng sau khi refactor. Hãy đi từng bước để xác định vấn đề nếu có.