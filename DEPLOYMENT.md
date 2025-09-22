# Telegram Bot Deployment Guide

## 🚀 Quick Deploy to RedHat Server

### Prerequisites
- RedHat/CentOS server with sudo access
- SSH access to the server
- GitHub repository access

### 1. Server Setup (One-time)

SSH vào server và chạy:

```bash
# Download setup script
curl -sSL https://raw.githubusercontent.com/huynq247/telegram_neyu_ticket_v2/main/scripts/setup-redhat-server.sh -o setup.sh

# Make executable and run
chmod +x setup.sh
./setup.sh
```

### 2. Configure Environment

```bash
cd /opt/telegram-neyu
nano .env
```

Điền thông tin:
```bash
TELEGRAM_BOT_TOKEN=your_bot_token_here
DB_PASSWORD=your_secure_password
DB_HOST=postgres
DB_NAME=telegram_neyu
DB_USER=postgres
```

### 3. Deploy Application

```bash
# Manual deployment
./scripts/deploy.sh

# Or wait for automatic deployment via GitHub Actions
```

### 4. Monitor Application

```bash
# View logs
./scripts/logs.sh

# Health check
./scripts/health-check.sh

# Create backup
./scripts/backup.sh
```

## 🔄 CI/CD Pipeline

### GitHub Secrets Required

Add these secrets in GitHub repository settings:

```
REDHAT_HOST=your_server_ip
REDHAT_USER=your_username  
REDHAT_SSH_KEY=your_private_key
```

### Automatic Deployment

Push to `main` branch triggers:
1. ✅ Code testing
2. 🐳 Docker image build
3. 📦 Push to GitHub Container Registry
4. 🚀 Deploy to RedHat server

## 📊 Management Commands

### Container Management
```bash
# View status
docker compose ps

# View logs (real-time)
docker compose logs -f telegram-bot

# Restart service
docker compose restart telegram-bot

# Update and redeploy
git pull && docker compose up -d --build
```

### Database Management
```bash
# Connect to database
docker compose exec postgres psql -U postgres -d telegram_neyu

# Create backup
./scripts/backup.sh

# Restore backup
docker compose exec -T postgres psql -U postgres -d telegram_neyu < backup/backup_file.sql
```

### Troubleshooting
```bash
# Check container health
docker compose exec telegram-bot python -c "print('✅ Bot is running')"

# Check database connection
docker compose exec postgres pg_isready -U postgres

# View full logs
docker compose logs --tail=100 telegram-bot

# Reset everything
docker compose down -v && docker compose up -d
```

## 🛡️ Security Best Practices

1. **SSH Key Authentication**: Disable password login
2. **Firewall**: Only open necessary ports (22, 80, 443)
3. **SSL/TLS**: Use HTTPS for webhook URLs
4. **Environment Variables**: Never commit secrets to git
5. **Regular Updates**: Keep server and containers updated

## 📈 Monitoring

- **Health Checks**: Automated container health monitoring
- **Log Rotation**: Automatic log cleanup (max 10MB, 3 files)
- **Backup Strategy**: Daily database backups (7 days retention)
- **Resource Monitoring**: Docker stats and system resources

## 🆘 Emergency Procedures

### Bot Not Responding
```bash
docker compose restart telegram-bot
./scripts/logs.sh -e  # Check errors
```

### Database Issues
```bash
docker compose restart postgres
./scripts/health-check.sh
```

### Complete Reset
```bash
docker compose down -v
docker system prune -f
./scripts/deploy.sh
```

### Rollback Deployment
```bash
git checkout v2.0  # Previous version
./scripts/deploy.sh
```