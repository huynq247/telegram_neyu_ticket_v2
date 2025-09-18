# Telegram Bot Backend for Odoo Integration

Ứng dụng backend Python kết nối bot Telegram với hệ thống quản lý ticket Odoo. Ứng dụng cho phép người dùng tạo ticket hỗ trợ thông qua Telegram Bot và nhận thông báo khi ticket được xử lý xong.

## 🚀 Tính năng chính

- 🤖 **Telegram Bot**: Nhận và xử lý ticket từ người dùng Telegram
- 🔗 **Tích hợp Odoo**: Kết nối trực tiếp với API Odoo để quản lý tickets
- 📋 **Quản lý Ticket**: Tạo, cập nhật và theo dõi trạng thái tickets
- 📤 **Thông báo tự động**: Gửi thông báo khi ticket hoàn thành
- 📝 **Logging đầy đủ**: Theo dõi và debug với hệ thống log chi tiết
- ⚡ **Async Processing**: Xử lý bất đồng bộ cho hiệu suất cao

## 📁 Cấu trúc dự án

```
TelegramNeyu/
├── src/
│   ├── odoo/
│   │   ├── __init__.py
│   │   └── connector.py        # Kết nối và tương tác với Odoo API
│   ├── telegram/
│   │   ├── __init__.py
│   │   └── bot_handler.py      # Xử lý Telegram Bot
│   ├── ticket/
│   │   ├── __init__.py
│   │   └── manager.py          # Quản lý luồng ticket
│   └── __init__.py
├── config/
│   └── settings.py             # Cấu hình ứng dụng
├── logs/                       # Log files
├── telegram_neyu_env/          # Virtual environment
├── requirements.txt            # Python dependencies
├── main.py                     # Entry point
├── .env.example               # Template environment variables
└── README.md                  # Documentation này
```

## 📦 Cài đặt

### 1. Yêu cầu hệ thống
- Python 3.8 trở lên
- Odoo server với API access
- Telegram Bot Token

### 2. Clone và cài đặt
```bash
# Clone repository
git clone <repository-url>
cd TelegramNeyu

# Tạo virtual environment
python -m venv telegram_neyu_env

# Kích hoạt virtual environment
# Windows:
telegram_neyu_env\Scripts\activate
# Linux/Mac:
source telegram_neyu_env/bin/activate

# Cài đặt dependencies
pip install -r requirements.txt
```

### 3. Cấu hình môi trường

Sao chép file template và cấu hình:
```bash
cp .env.example .env
```

Chỉnh sửa file `.env` với thông tin của bạn:

```env
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_WEBHOOK_URL=  # Để trống để dùng polling mode

# Odoo Configuration
ODOO_URL=http://your-odoo-server.com
ODOO_DB=your_database_name
ODOO_USERNAME=your_odoo_username
ODOO_PASSWORD=your_odoo_password

# Application Settings
DEBUG_MODE=false
LOG_LEVEL=INFO
TICKET_CHECK_INTERVAL=60
```

### 4. Tạo Telegram Bot

1. Liên hệ [@BotFather](https://t.me/botfather) trên Telegram
2. Tạo bot mới với lệnh `/newbot`
3. Lấy token và đặt vào `TELEGRAM_BOT_TOKEN`

### 5. Cấu hình Odoo

Đảm bảo Odoo server có:
- Module `helpdesk` được cài đặt
- User có quyền truy cập API
- Các trường tùy chỉnh cho Telegram (optional):
  - `telegram_chat_id`
  - `telegram_user_id`

## 🏃‍♂️ Chạy ứng dụng

```bash
# Kích hoạt virtual environment (nếu chưa)
telegram_neyu_env\Scripts\activate  # Windows
# source telegram_neyu_env/bin/activate  # Linux/Mac

# Chạy ứng dụng
python main.py
```

Ứng dụng sẽ hiển thị thông tin cấu hình và bắt đầu chạy:

```
==================================================
🚀 TelegramNeyu v1.0.0
==================================================
📊 Debug Mode: False
📝 Log Level: INFO
📂 Log File: logs/app.log
🔗 Odoo URL: http://your-odoo-server.com
🗄️  Odoo DB: your_database
👤 Odoo User: your_user
🤖 Telegram Bot: ✅ Configured
📊 Polling Mode: Enabled
⏱️  Check Interval: 60s
==================================================
✅ Ứng dụng đang chạy... (Ctrl+C để dừng)
```

## 🤖 Cách sử dụng Bot

### Lệnh bot
- `/start` - Bắt đầu sử dụng bot
- `/newticket` - Tạo ticket mới
- `/mytickets` - Xem danh sách tickets của bạn
- `/help` - Hướng dẫn sử dụng
- `/cancel` - Hủy thao tác hiện tại

### Quy trình tạo ticket
1. Người dùng gõ `/newticket`
2. Nhập mô tả vấn đề
3. Chọn độ ưu tiên (Cao/Trung bình/Thấp)
4. Xác nhận tạo ticket
5. Nhận mã ticket và thông báo xác nhận

### Thông báo hoàn thành
Khi ticket trong Odoo chuyển sang trạng thái "Done", người dùng sẽ tự động nhận thông báo qua Telegram.

## 🔧 Cấu hình nâng cao

### Webhook Mode (Production)
Để sử dụng webhook thay vì polling:

```env
TELEGRAM_WEBHOOK_URL=https://your-domain.com/webhook
TELEGRAM_WEBHOOK_PORT=8443
```

### Logging
Cấu hình logging trong `.env`:

```env
LOG_LEVEL=DEBUG  # DEBUG, INFO, WARNING, ERROR
LOG_FILE_PATH=logs/app.log
LOG_MAX_SIZE=10485760  # 10MB
LOG_BACKUP_COUNT=5
```

### Monitoring
Điều chỉnh tần suất kiểm tra tickets:

```env
TICKET_CHECK_INTERVAL=30  # Kiểm tra mỗi 30 giây
```

## 🐛 Troubleshooting

### Lỗi kết nối Odoo
```
ERROR: Lỗi kết nối Odoo: [Errno 111] Connection refused
```
- Kiểm tra ODOO_URL có đúng không
- Đảm bảo Odoo server đang chạy
- Kiểm tra firewall và network

### Lỗi xác thực Odoo
```
ERROR: Xác thức Odoo thất bại
```
- Kiểm tra ODOO_USERNAME và ODOO_PASSWORD
- Đảm bảo user có quyền truy cập API
- Kiểm tra ODOO_DB có tồn tại không

### Lỗi Telegram Bot
```
ERROR: Bot token không hợp lệ
```
- Kiểm tra TELEGRAM_BOT_TOKEN
- Đảm bảo bot đã được tạo qua @BotFather

### Kiểm tra logs
```bash
tail -f logs/app.log
```

## 🔒 Bảo mật

- Không commit file `.env` vào git
- Sử dụng HTTPS cho webhook
- Định kỳ thay đổi passwords
- Giới hạn quyền user Odoo
- Monitor logs thường xuyên

## 📈 Monitoring và Maintenance

### Logs
- Application logs: `logs/app.log`
- Log rotation: Tự động khi đạt 10MB
- Backup: Giữ lại 5 files log cũ

### Performance
- Async processing cho tất cả I/O operations
- Connection pooling cho Odoo
- Efficient polling với backoff

### Health Check
Ứng dụng tự động kiểm tra:
- Kết nối Odoo
- Telegram Bot status
- Ticket processing

## 🤝 Đóng góp

1. Fork repository
2. Tạo feature branch
3. Commit changes
4. Push và tạo Pull Request

## 📄 License

MIT License - xem file LICENSE để biết chi tiết.

## 📞 Hỗ trợ

Nếu gặp vấn đề, vui lòng:
1. Kiểm tra logs trong `logs/app.log`
2. Tham khảo phần Troubleshooting
3. Tạo issue trên GitHub với thông tin chi tiết