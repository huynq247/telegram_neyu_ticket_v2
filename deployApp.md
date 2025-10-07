# SSH vào server
cd /opt/telegram-neyu

# Pull code mới
git pull origin enhancement/smart-auth-dual-user-support

# Rebuild và restart bot
docker-compose down
docker-compose build --no-cache telegram-bot
docker-compose up -d

# Xem logs để verify
docker-compose logs -f telegram-bot