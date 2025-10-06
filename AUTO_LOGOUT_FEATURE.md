# Auto-Logout Feature Implementation

## 📋 Tổng Quan
Đã implement tính năng tự động logout sau 10 phút không hoạt động.

## 🔧 Các Component

### 1. AutoLogoutService
**File:** `src/telegram_bot/services/auto_logout_service.py`

**Chức năng:**
- Track last activity time của mỗi user
- Warning user sau 8 phút không hoạt động (còn 2 phút nữa sẽ logout)
- Tự động logout sau 10 phút không hoạt động
- Background monitoring task chạy mỗi 30 giây

**Key Methods:**
- `track_activity(user_id)` - Track user activity
- `should_warn(user_id)` - Check if should send warning
- `should_logout(user_id)` - Check if should auto-logout
- `send_warning(user_id)` - Send inactivity warning
- `auto_logout_user(user_id)` - Perform auto-logout
- `monitor_loop()` - Background monitoring task

### 2. Integration với Bot Handler
**File:** `src/telegram_bot/bot_handler.py`

**Thay đổi:**

#### Import:
```python
from .services.auto_logout_service import AutoLogoutService
```

#### Khởi tạo:
```python
self.auto_logout_service = None  # Will be initialized after bot is ready
```

#### Trong initialize():
```python
# Initialize and start auto-logout service
self.auto_logout_service = AutoLogoutService(
    self.auth_service, 
    self,  # Pass bot handler for sending messages
    inactive_minutes=10  # 10 minutes timeout
)
self.auto_logout_service.start_monitoring()
```

#### Activity Tracking Middleware:
```python
async def track_user_activity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Middleware to track user activity for auto-logout"""
    if update.effective_user and hasattr(self, 'auto_logout_service') and self.auto_logout_service:
        user_id = update.effective_user.id
        
        # Only track if user is authenticated
        is_valid, _ = self.auth_service.validate_session(user_id)
        if is_valid:
            self.auto_logout_service.track_activity(user_id)

# Register as group -1 (runs before all handlers)
self.application.add_handler(MessageHandler(filters.ALL, track_user_activity), group=-1)
self.application.add_handler(CallbackQueryHandler(track_user_activity), group=-1)
```

#### Trong stop():
```python
# Stop auto-logout service
if self.auto_logout_service:
    self.auto_logout_service.stop_monitoring()
```

## ⚙️ Cấu Hình

### Timeout Settings:
- **Inactive timeout:** 10 phút
- **Warning threshold:** 8 phút (2 phút trước khi logout)
- **Check interval:** 30 giây

### Customization:
Để thay đổi timeout, sửa trong `bot_handler.py`:
```python
self.auto_logout_service = AutoLogoutService(
    self.auth_service, 
    self,
    inactive_minutes=15  # Change to 15 minutes
)
```

## 🔄 Workflow

1. **User Activity Detected**
   - Mọi message/callback từ authenticated user được track
   - `last_activity[user_id]` được update với timestamp hiện tại
   - Warning flag được reset nếu user quay lại active

2. **Monitoring Loop (mỗi 30s)**
   - Check tất cả tracked users
   - Calculate inactive time for each user
   
3. **Warning Phase (sau 8 phút)**
   - Nếu inactive >= 8 phút và chưa được warn:
     - Gửi warning message
     - Set `warned_users[user_id] = True`
   
4. **Auto-Logout (sau 10 phút)**
   - Nếu inactive >= 10 phút:
     - Call `auth_service.revoke_session(user_id)`
     - Gửi logout notification
     - Clean up tracking data

## 📊 Status Monitoring

Để check status của service:
```python
status = bot_handler.auto_logout_service.get_status()
# Returns:
# {
#     'is_running': True,
#     'inactive_timeout_minutes': 10,
#     'warning_threshold_seconds': 120,
#     'tracked_users': 5,
#     'warned_users': 1
# }
```

## 🔒 Security Features

1. **Chỉ track authenticated users**
   - Check `auth_service.validate_session()` trước khi track

2. **Automatic cleanup**
   - Users không authenticated sẽ bị remove khỏi tracking
   - Logout tự động clean up tracking data

3. **Thread-safe**
   - Sử dụng asyncio tasks
   - Proper cancellation handling

## 📝 Messages

### Warning Message (sau 8 phút):
```
⚠️ Inactivity Warning

You have been inactive for 8 minutes.
You will be automatically logged out in 2 minutes if no activity is detected.

Send any message or use any command to stay logged in.
```

### Logout Message (sau 10 phút):
```
🚪 Auto Logout

You have been automatically logged out due to 10 minutes of inactivity.

Use /login to log in again or /start to see available commands.
```

## 🧪 Testing

1. Login vào bot
2. Đợi 8 phút → Nhận warning
3. Không làm gì → Sau 2 phút nữa sẽ bị logout
4. Hoặc send message/command → Warning reset, timer restart

## 📌 Notes

- Service chạy background task riêng biệt
- Không ảnh hưởng đến performance bot
- Graceful shutdown khi bot stop
- Compatible với existing session management

## 🚀 Deployment

Không cần thay đổi gì - feature tự động activate khi bot start.

Logs sẽ hiển thị:
```
✅ Auto-logout service started (10 min timeout)
```

---
**Status:** ✅ Ready for testing
**Version:** 1.0.0
**Date:** 2025-10-06
