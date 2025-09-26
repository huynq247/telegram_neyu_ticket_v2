# Smart Authentication System - Utilities

Bộ công cụ hỗ trợ cho hệ thống **Smart Authentication** với **file-based credentials** và **inactivity timeout**.

## 🚀 Quick Start

### 1. Quick Setup (Recommended)
```bash
python scripts/setup_smart_auth.py
```

### 2. Generate Sample Files
```bash
python scripts/generate_smart_auth_file.py
```

### 3. Manual Management
```bash
python -m src.telegram_bot.utils.smart_auth_utils <command>
```

## 📋 Available Commands

### Smart Auth Utils (`smart_auth_utils.py`)

| Command | Description | Example |
|---------|-------------|---------|
| `create-sample` | Tạo file mẫu | `python smart_auth_utils.py create-sample` |
| `add-user` | Thêm user mới (interactive) | `python smart_auth_utils.py add-user` |
| `list-users` | Liệt kê tất cả users | `python smart_auth_utils.py list-users` |
| `change-password` | Đổi mật khẩu user | `python smart_auth_utils.py change-password` |
| `validate` | Kiểm tra file hợp lệ | `python smart_auth_utils.py validate` |
| `encode` | Mã hóa password | `python smart_auth_utils.py encode mypassword` |
| `decode` | Giải mã password | `python smart_auth_utils.py decode <encoded>` |

### File Generators

#### Setup Wizard (`setup_smart_auth.py`)
```bash
python scripts/setup_smart_auth.py
```
- ✅ Hướng dẫn từng bước
- ✅ Kiểm tra hệ thống
- ✅ Tạo config phù hợp

#### Sample Generator (`generate_smart_auth_file.py`)
```bash
python scripts/generate_smart_auth_file.py
```
- 🏢 Production sample với accounts thực
- 🔧 Development sample với test accounts
- 📊 Chi tiết metadata và documentation

## 📁 File Structure

### user.auth.smart Format
```json
{
  "users": {
    "email@domain.com": {
      "name": "User Name",
      "password": "base64_encoded_password",
      "uid": "smart_1001",
      "partner_id": 1,
      "company_id": 1,
      "groups": ["Help Desk User"],
      "is_helpdesk_manager": false,
      "is_helpdesk_user": true,
      "session_type": "smart_auth",
      "created_at": "2025-01-09T...",
      "last_used": null
    }
  },
  "metadata": {
    "version": "1.0.0",
    "created_at": "2025-01-09T...",
    "description": "Smart Authentication Configuration",
    "security_level": "Tier 1 (Basic Protection)",
    "last_modified": "2025-01-09T..."
  }
}
```

### Session Types
| Type | Timeout | Description |
|------|---------|-------------|
| `admin_session` | 8 hours | Admin/Manager users |
| `smart_auth` | 24 hours | Regular authenticated users |
| `manual_login` | 48 hours | Portal users |

## 🔐 Security Features

### Tier 1 Security (Current)
- ✅ **Base64 encoding** cho passwords
- ✅ **File-based** credential storage
- ✅ **Session timeout** based on user type
- ✅ **Activity tracking** extends sessions
- ✅ **Warning system** before timeout

### Security Best Practices
1. **File Permissions**: `chmod 600 user.auth.smart`
2. **Secure Location**: Store outside web-accessible directories
3. **Regular Rotation**: Change passwords periodically
4. **Backup**: Keep secure backups of auth file
5. **Monitoring**: Monitor access logs

## 🛠️ Management Workflow

### 1. Initial Setup
```bash
# Quick setup
python scripts/setup_smart_auth.py

# Or generate sample
python scripts/generate_smart_auth_file.py
```

### 2. Add New User
```bash
python -m src.telegram_bot.utils.smart_auth_utils add-user
```

### 3. List Users
```bash
python -m src.telegram_bot.utils.smart_auth_utils list-users
```

### 4. Change Password
```bash
python -m src.telegram_bot.utils.smart_auth_utils change-password
```

### 5. Validate File
```bash
python -m src.telegram_bot.utils.smart_auth_utils validate
```

## 📊 Usage Examples

### Production Setup
```bash
# 1. Create production config
python scripts/setup_smart_auth.py
# Choose option 1 (Production)

# 2. Secure the file
chmod 600 user.auth.smart

# 3. Test with Telegram bot
# Use /me command to test smart auth
```

### Development Setup
```bash
# 1. Create dev config
python scripts/setup_smart_auth.py
# Choose option 2 (Development)

# 2. Test accounts available:
# admin@dev.local / admin123
# user@dev.local / user123
```

### Adding Custom User
```bash
python -m src.telegram_bot.utils.smart_auth_utils add-user

# Interactive prompts:
# Email: newuser@company.com
# Full Name: New User
# Password: [enter password]
# Is Helpdesk Manager? (y/n): n
# Is Helpdesk User? (y/n): y
```

## 🔧 Troubleshooting

### Common Issues

#### 1. Import Error
```bash
❌ Cannot import SmartAuthUtils
```
**Solution**: Run from project root directory

#### 2. File Not Found
```bash
❌ Auth file not found: user.auth.smart
```
**Solution**: Create file first with `create-sample` command

#### 3. Invalid JSON
```bash
❌ JSON parsing error
```
**Solution**: Validate file with `validate` command

#### 4. Permission Denied
```bash
❌ Permission denied
```
**Solution**: Check file permissions and ownership

### Validation Errors

#### Check File Structure
```bash
python -m src.telegram_bot.utils.smart_auth_utils validate
```

#### Common Validation Issues
- ❌ **Missing 'users' section**
- ❌ **Invalid email format**
- ❌ **Missing required fields**
- ❌ **Invalid password encoding**
- ⚠️  **Missing metadata section**
- ⚠️  **Non-boolean permission fields**

## 🚀 Integration

### Bot Integration
Smart auth được tích hợp tự động khi:
1. File `user.auth.smart` tồn tại
2. `SmartAuthFileManager` được khởi tạo thành công
3. `EnhancedSessionManager` được kích hoạt

### Activity Tracking
Tự động track các hoạt động:
- ✅ **Commands** (`/start`, `/menu`, `/help`)
- ✅ **Callbacks** (button clicks)  
- ✅ **Conversations** (ticket creation, etc.)

### Session Management
- ✅ **Automatic timeout** based on user type
- ✅ **Activity extension** keeps sessions alive
- ✅ **Warning system** before timeout
- ✅ **Manual extension** available

## 📚 API Reference

### SmartAuthUtils Class

#### Password Methods
- `encode_password(password: str) -> str`
- `decode_password(encoded: str) -> str`

#### Validation Methods
- `validate_email(email: str) -> bool`
- `validate_auth_file(file_path: str) -> bool`

#### File Management
- `create_sample_auth_file(file_path: str) -> bool`
- `add_user_interactive(file_path: str) -> bool`
- `list_users(file_path: str) -> bool`
- `change_password(file_path: str) -> bool`

### CLI Commands
All CLI commands support custom file path:
```bash
python smart_auth_utils.py <command> [custom_file.json]
```

## 🎯 Advanced Usage

### Custom Session Types
Modify metadata để add session types mới:
```json
"session_types": {
  "custom_session": "12 hours inactivity timeout"
}
```

### Batch User Creation
Create script với multiple users:
```python
from smart_auth_utils import SmartAuthUtils

users = [
    {"email": "user1@domain.com", "name": "User 1", "password": "pass1"},
    {"email": "user2@domain.com", "name": "User 2", "password": "pass2"}
]

# Implement batch creation logic
```

### Integration với External Systems
```python
# Example: Sync with LDAP/AD
def sync_with_ldap():
    # Implementation for syncing users
    pass
```

---

## 📞 Support

Nếu gặp vấn đề:
1. ✅ Check **file permissions** và **location**
2. ✅ Validate file với `validate` command
3. ✅ Test với **development accounts** trước
4. ✅ Check **bot logs** cho detailed errors

---

**🚀 Happy coding with Smart Authentication!**