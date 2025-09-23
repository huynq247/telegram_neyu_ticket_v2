-- Telegram User Mapping Table
-- Stores telegram_id to email mappings for Smart Auto-Authentication
-- This table allows users to automatically login with /me command after initial authentication

CREATE TABLE IF NOT EXISTS telegram_user_mapping (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL,
    email VARCHAR(255) NOT NULL,
    telegram_username VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP DEFAULT (CURRENT_TIMESTAMP + INTERVAL '30 days'),
    is_active BOOLEAN DEFAULT TRUE
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_telegram_mapping_telegram_id 
ON telegram_user_mapping (telegram_id);

CREATE INDEX IF NOT EXISTS idx_telegram_mapping_email 
ON telegram_user_mapping (email);

CREATE INDEX IF NOT EXISTS idx_telegram_mapping_expires_at 
ON telegram_user_mapping (expires_at);

-- Create index for cleanup queries
CREATE INDEX IF NOT EXISTS idx_telegram_mapping_cleanup 
ON telegram_user_mapping (expires_at, is_active);

-- Add comment to table
COMMENT ON TABLE telegram_user_mapping IS 'Stores telegram user to email mappings for Smart Auto-Authentication with 30-day expiry';
COMMENT ON COLUMN telegram_user_mapping.telegram_id IS 'Telegram user ID (unique)';
COMMENT ON COLUMN telegram_user_mapping.email IS 'User email address for authentication';
COMMENT ON COLUMN telegram_user_mapping.expires_at IS 'Mapping expiry date (30 days from creation)';
COMMENT ON COLUMN telegram_user_mapping.is_active IS 'Whether mapping is active (for soft delete)';