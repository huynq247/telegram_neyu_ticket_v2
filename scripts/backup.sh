#!/bin/bash

# backup.sh
# Database backup script

set -e

BACKUP_DIR="./backup"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="telegram_neyu_backup_${DATE}.sql"

echo "💾 Creating database backup..."

# Create backup directory if it doesn't exist
mkdir -p $BACKUP_DIR

# Create database backup
docker compose exec postgres pg_dump -U postgres telegram_neyu > "${BACKUP_DIR}/${BACKUP_FILE}"

echo "✅ Backup created: ${BACKUP_DIR}/${BACKUP_FILE}"

# Keep only last 7 backups
echo "🧹 Cleaning old backups..."
cd $BACKUP_DIR
ls -t telegram_neyu_backup_*.sql | tail -n +8 | xargs rm -f
cd ..

echo "📊 Available backups:"
ls -la ${BACKUP_DIR}/telegram_neyu_backup_*.sql