# Debug CI/CD Issues

## Checklist để kiểm tra tại sao CI/CD không deploy tự động:

### 1. **Kiểm tra GitHub Actions Status**
- Vào: https://github.com/huynq247/telegram_neyu_ticket_v2/actions
- Xem workflow runs có fail không
- Kiểm tra logs của từng step

### 2. **Kiểm tra GitHub Secrets** 
- Vào: https://github.com/huynq247/telegram_neyu_ticket_v2/settings/secrets/actions
- Cần có các secrets:
  - `REDHAT_HOST`: IP/hostname của RedHat server
  - `REDHAT_USER`: SSH username
  - `REDHAT_SSH_KEY`: Private SSH key content
  - `GITHUB_TOKEN`: Tự động có sẵn

### 3. **Kiểm tra RedHat Server Setup**
SSH vào server và kiểm tra:

```bash
# Kiểm tra thư mục deployment
ls -la /opt/telegram-neyu/

# Kiểm tra git repository
cd /opt/telegram-neyu
git status
git remote -v

# Kiểm tra Docker
docker --version
docker compose version

# Kiểm tra port SSH
ss -tlnp | grep 22022
```

### 4. **Common Issues và Solutions**

#### Issue: SSH Connection Failed
```bash
# Trên RedHat server, kiểm tra SSH config
sudo nano /etc/ssh/sshd_config
# Ensure port 22022 is configured
sudo systemctl restart sshd
```

#### Issue: Docker Compose Command Not Found
```bash
# Install docker compose V2
sudo curl -SL https://github.com/docker/compose/releases/download/v2.21.0/docker-compose-linux-x86_64 -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

#### Issue: Permission Denied
```bash
# Add user to docker group
sudo usermod -aG docker $USER
# Logout and login again
```

#### Issue: Repository Not Found
```bash
# Setup repository on server
cd /opt
sudo git clone https://github.com/huynq247/telegram_neyu_ticket_v2.git telegram-neyu
sudo chown -R $USER:$USER /opt/telegram-neyu
```

### 5. **Manual Deploy Test**
Trên RedHat server:

```bash
cd /opt/telegram-neyu
git pull origin main
docker compose pull
docker compose down
docker compose up -d
docker compose logs --tail=20
```

### 6. **Workflow Debug**
Nếu workflow vẫn fail, thêm debug step trong `.github/workflows/deploy.yml`:

```yaml
- name: Debug SSH Connection
  uses: appleboy/ssh-action@v1.0.0
  with:
    host: ${{ secrets.REDHAT_HOST }}
    port: 22022  
    username: ${{ secrets.REDHAT_USER }}
    key: ${{ secrets.REDHAT_SSH_KEY }}
    script: |
      echo "=== System Info ==="
      uname -a
      whoami
      pwd
      
      echo "=== Docker Info ==="
      docker --version
      docker compose version
      
      echo "=== Directory Check ==="
      ls -la /opt/
      
      if [ -d "/opt/telegram-neyu" ]; then
        echo "=== Repository Status ==="
        cd /opt/telegram-neyu
        git status
        git branch
      else
        echo "❌ Repository not found at /opt/telegram-neyu"
      fi
```

### 7. **Environment Variables**
Kiểm tra file `.env` trên server có đầy đủ:

```bash
cd /opt/telegram-neyu
cat .env
```

Required variables:
- TELEGRAM_BOT_TOKEN
- ODOO_URL
- ODOO_DB
- ODOO_USERNAME
- ODOO_PASSWORD
- ODOO_XMLRPC_URL