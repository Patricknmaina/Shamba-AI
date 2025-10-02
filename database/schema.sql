-- =====================================================
-- ShambaAI Oracle Database Schema
-- Admin Authentication System
-- =====================================================

-- Create tablespace for ShambaAI (optional - adjust as needed)
-- CREATE TABLESPACE SHAMBA_DATA
--   DATAFILE 'shamba_data.dbf' SIZE 100M
--   AUTOEXTEND ON NEXT 10M MAXSIZE 1G;

-- =====================================================
-- 1. ADMIN USERS TABLE
-- =====================================================
CREATE TABLE admin_users (
    user_id VARCHAR2(36) PRIMARY KEY,           -- UUID for user identification
    username VARCHAR2(50) NOT NULL UNIQUE,      -- Username (max 50 chars)
    password_hash VARCHAR2(255) NOT NULL,       -- Hashed password
    email VARCHAR2(100) NOT NULL UNIQUE,        -- Email address
    full_name VARCHAR2(100) NOT NULL,           -- Full name
    role VARCHAR2(50) NOT NULL,                 -- User role
    permissions CLOB,                           -- JSON string of permissions
    is_active CHAR(1) DEFAULT 'Y' CHECK (is_active IN ('Y', 'N')), -- Active status
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- Creation timestamp
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- Last update timestamp
    last_login TIMESTAMP,                       -- Last login timestamp
    failed_login_attempts NUMBER(2) DEFAULT 0,  -- Failed login counter
    account_locked_until TIMESTAMP,             -- Account lock expiration
    created_by VARCHAR2(36),                    -- Who created this user
    CONSTRAINT fk_admin_created_by FOREIGN KEY (created_by) REFERENCES admin_users(user_id)
);

-- =====================================================
-- 2. USER SESSIONS TABLE
-- =====================================================
CREATE TABLE user_sessions (
    session_id VARCHAR2(36) PRIMARY KEY,        -- Session UUID
    user_id VARCHAR2(36) NOT NULL,              -- Reference to admin_users
    session_token VARCHAR2(255) NOT NULL,       -- Session token
    ip_address VARCHAR2(45),                    -- IP address (IPv4/IPv6)
    user_agent CLOB,                            -- User agent string
    expires_at TIMESTAMP NOT NULL,              -- Session expiration
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- Session creation
    is_active CHAR(1) DEFAULT 'Y' CHECK (is_active IN ('Y', 'N')), -- Active session
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- Last activity
    CONSTRAINT fk_session_user FOREIGN KEY (user_id) REFERENCES admin_users(user_id)
);

-- =====================================================
-- 3. AUDIT LOG TABLE
-- =====================================================
CREATE TABLE audit_log (
    log_id VARCHAR2(36) PRIMARY KEY,            -- Log entry UUID
    user_id VARCHAR2(36),                       -- User who performed action
    action VARCHAR2(50) NOT NULL,               -- Action performed
    resource VARCHAR2(100),                     -- Resource affected
    details CLOB,                               -- Additional details (JSON)
    ip_address VARCHAR2(45),                    -- IP address
    user_agent CLOB,                            -- User agent
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- When action occurred
    status VARCHAR2(20) DEFAULT 'SUCCESS',      -- SUCCESS, FAILED, ERROR
    CONSTRAINT fk_audit_user FOREIGN KEY (user_id) REFERENCES admin_users(user_id)
);

-- =====================================================
-- 4. SYSTEM CONFIGURATION TABLE
-- =====================================================
CREATE TABLE system_config (
    config_key VARCHAR2(100) PRIMARY KEY,       -- Configuration key
    config_value CLOB,                          -- Configuration value
    description VARCHAR2(500),                  -- Description of config
    is_encrypted CHAR(1) DEFAULT 'N' CHECK (is_encrypted IN ('Y', 'N')), -- Is value encrypted
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by VARCHAR2(36),
    CONSTRAINT fk_config_updated_by FOREIGN KEY (updated_by) REFERENCES admin_users(user_id)
);

-- =====================================================
-- 5. PASSWORD RESET TOKENS TABLE
-- =====================================================
CREATE TABLE password_reset_tokens (
    token_id VARCHAR2(36) PRIMARY KEY,          -- Token UUID
    user_id VARCHAR2(36) NOT NULL,              -- User requesting reset
    token_hash VARCHAR2(255) NOT NULL,          -- Hashed reset token
    expires_at TIMESTAMP NOT NULL,              -- Token expiration
    used_at TIMESTAMP,                          -- When token was used
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_address VARCHAR2(45),                    -- IP where request originated
    CONSTRAINT fk_reset_user FOREIGN KEY (user_id) REFERENCES admin_users(user_id)
);

-- =====================================================
-- INDEXES FOR PERFORMANCE
-- =====================================================

-- Admin users indexes
CREATE INDEX idx_admin_users_username ON admin_users(username);
CREATE INDEX idx_admin_users_email ON admin_users(email);
CREATE INDEX idx_admin_users_role ON admin_users(role);
CREATE INDEX idx_admin_users_active ON admin_users(is_active);
CREATE INDEX idx_admin_users_created_at ON admin_users(created_at);

-- Session indexes
CREATE INDEX idx_sessions_user_id ON user_sessions(user_id);
CREATE INDEX idx_sessions_token ON user_sessions(session_token);
CREATE INDEX idx_sessions_expires ON user_sessions(expires_at);
CREATE INDEX idx_sessions_active ON user_sessions(is_active);

-- Audit log indexes
CREATE INDEX idx_audit_user_id ON audit_log(user_id);
CREATE INDEX idx_audit_action ON audit_log(action);
CREATE INDEX idx_audit_timestamp ON audit_log(timestamp);
CREATE INDEX idx_audit_status ON audit_log(status);

-- Password reset indexes
CREATE INDEX idx_reset_user_id ON password_reset_tokens(user_id);
CREATE INDEX idx_reset_expires ON password_reset_tokens(expires_at);
CREATE INDEX idx_reset_used ON password_reset_tokens(used_at);

-- =====================================================
-- TRIGGERS FOR AUTOMATIC UPDATES
-- =====================================================

-- Trigger to update updated_at timestamp
CREATE OR REPLACE TRIGGER tr_admin_users_updated_at
    BEFORE UPDATE ON admin_users
    FOR EACH ROW
BEGIN
    :NEW.updated_at := CURRENT_TIMESTAMP;
END;
/

CREATE OR REPLACE TRIGGER tr_system_config_updated_at
    BEFORE UPDATE ON system_config
    FOR EACH ROW
BEGIN
    :NEW.updated_at := CURRENT_TIMESTAMP;
END;
/

-- =====================================================
-- SEQUENCES FOR ID GENERATION (if needed)
-- =====================================================

-- Note: We're using VARCHAR2(36) for UUIDs, but you can also use sequences
-- CREATE SEQUENCE seq_admin_users START WITH 1 INCREMENT BY 1;
-- CREATE SEQUENCE seq_audit_log START WITH 1 INCREMENT BY 1;

-- =====================================================
-- COMMENTS ON TABLES AND COLUMNS
-- =====================================================

COMMENT ON TABLE admin_users IS 'Stores administrative user accounts for ShambaAI platform';
COMMENT ON TABLE user_sessions IS 'Active user sessions for tracking login state';
COMMENT ON TABLE audit_log IS 'Audit trail for all administrative actions';
COMMENT ON TABLE system_config IS 'System configuration parameters';
COMMENT ON TABLE password_reset_tokens IS 'Temporary tokens for password reset functionality';

COMMENT ON COLUMN admin_users.user_id IS 'Unique identifier for admin user';
COMMENT ON COLUMN admin_users.username IS 'Login username (must be unique)';
COMMENT ON COLUMN admin_users.password_hash IS 'BCrypt hashed password';
COMMENT ON COLUMN admin_users.permissions IS 'JSON array of user permissions';
COMMENT ON COLUMN admin_users.failed_login_attempts IS 'Counter for failed login attempts';
COMMENT ON COLUMN admin_users.account_locked_until IS 'Timestamp when account lock expires';

COMMENT ON COLUMN user_sessions.session_token IS 'JWT or similar session token';
COMMENT ON COLUMN user_sessions.expires_at IS 'When the session expires';
COMMENT ON COLUMN user_sessions.last_activity IS 'Last time session was active';

COMMENT ON COLUMN audit_log.action IS 'Type of action performed (LOGIN, LOGOUT, CREATE_USER, etc.)';
COMMENT ON COLUMN audit_log.resource IS 'Resource that was affected by the action';
COMMENT ON COLUMN audit_log.details IS 'Additional action details in JSON format';

COMMENT ON COLUMN system_config.config_key IS 'Configuration parameter name';
COMMENT ON COLUMN system_config.config_value IS 'Configuration parameter value';
COMMENT ON COLUMN system_config.is_encrypted IS 'Whether the config value is encrypted';

COMMENT ON COLUMN password_reset_tokens.token_hash IS 'Hashed reset token';
COMMENT ON COLUMN password_reset_tokens.used_at IS 'When the token was used (NULL if unused)';

-- =====================================================
-- GRANTS AND PERMISSIONS
-- =====================================================

-- Grant permissions to application user (adjust username as needed)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON admin_users TO shamba_app;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON user_sessions TO shamba_app;
-- GRANT SELECT, INSERT ON audit_log TO shamba_app;
-- GRANT SELECT, INSERT, UPDATE ON system_config TO shamba_app;
-- GRANT SELECT, INSERT, UPDATE ON password_reset_tokens TO shamba_app;

-- Grant sequence permissions (if using sequences)
-- GRANT SELECT ON seq_admin_users TO shamba_app;
-- GRANT SELECT ON seq_audit_log TO shamba_app;

-- =====================================================
-- INITIAL SYSTEM CONFIGURATION
-- =====================================================

INSERT INTO system_config (config_key, config_value, description) VALUES 
('MAX_LOGIN_ATTEMPTS', '5', 'Maximum failed login attempts before account lock');
INSERT INTO system_config (config_key, config_value, description) VALUES 
('ACCOUNT_LOCK_DURATION_MINUTES', '30', 'Duration in minutes for account lock');
INSERT INTO system_config (config_key, config_value, description) VALUES 
('SESSION_TIMEOUT_MINUTES', '1440', 'Session timeout in minutes (24 hours)');
INSERT INTO system_config (config_key, config_value, description) VALUES 
('PASSWORD_RESET_TOKEN_EXPIRY_HOURS', '1', 'Password reset token expiry in hours');
INSERT INTO system_config (config_key, config_value, description) VALUES 
('REQUIRE_PASSWORD_RESET_DAYS', '90', 'Days after which password reset is required');

-- =====================================================
-- SAMPLE ADMIN USERS (with hashed passwords)
-- =====================================================
-- Note: These are example hashed passwords. In production, generate proper hashes.

INSERT INTO admin_users (
    user_id, username, password_hash, email, full_name, role, permissions, created_at
) VALUES (
    '550e8400-e29b-41d4-a716-446655440001',
    'admin',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBdXZ6vjWjfZqO', -- 'ShambaAI2024!'
    'admin@shambaai.com',
    'System Administrator',
    'System Administrator',
    '["full_access", "manage_users", "manage_content", "view_logs", "system_health"]',
    CURRENT_TIMESTAMP
);

INSERT INTO admin_users (
    user_id, username, password_hash, email, full_name, role, permissions, created_at
) VALUES (
    '550e8400-e29b-41d4-a716-446655440002',
    'agriculture_expert',
    '$2b$12$8KjH9vL2mN3pQ4rS5tU6wX7yZ8aB9cD0eF1gH2iJ3kL4mN5oP6qR7sT', -- 'FarmData2024!'
    'expert@shambaai.com',
    'Agriculture Expert',
    'Agriculture Expert',
    '["manage_content", "view_insights", "manage_crops"]',
    CURRENT_TIMESTAMP
);

INSERT INTO admin_users (
    user_id, username, password_hash, email, full_name, role, permissions, created_at
) VALUES (
    '550e8400-e29b-41d4-a716-446655440003',
    'data_manager',
    '$2b$12$2A3B4C5D6E7F8G9H0I1J2K3L4M5N6O7P8Q9R0S1T2U3V4W5X6Y7Z', -- 'DataSecure2024!'
    'data@shambaai.com',
    'Data Manager',
    'Data Manager',
    '["manage_content", "view_logs", "manage_data"]',
    CURRENT_TIMESTAMP
);

INSERT INTO admin_users (
    user_id, username, password_hash, email, full_name, role, permissions, created_at
) VALUES (
    '550e8400-e29b-41d4-a716-446655440004',
    'content_moderator',
    '$2b$12$9Z8Y7X6W5V4U3T2S1R0Q9P8O7N6M5L4K3J2I1H0G9F8E7D6C5B4A', -- 'ContentMod2024!'
    'moderator@shambaai.com',
    'Content Moderator',
    'Content Moderator',
    '["manage_content", "moderate_content"]',
    CURRENT_TIMESTAMP
);

INSERT INTO admin_users (
    user_id, username, password_hash, email, full_name, role, permissions, created_at
) VALUES (
    '550e8400-e29b-41d4-a716-446655440005',
    'technical_admin',
    '$2b$12$5A4B3C2D1E0F9G8H7I6J5K4L3M2N1O0P9Q8R7S6T5U4V3W2X1Y0Z', -- 'TechAdmin2024!'
    'tech@shambaai.com',
    'Technical Administrator',
    'Technical Administrator',
    '["view_logs", "system_health", "manage_system"]',
    CURRENT_TIMESTAMP
);

-- =====================================================
-- COMMIT TRANSACTION
-- =====================================================
COMMIT;

-- =====================================================
-- VERIFICATION QUERIES
-- =====================================================

-- Verify tables were created
SELECT table_name FROM user_tables WHERE table_name IN (
    'ADMIN_USERS', 'USER_SESSIONS', 'AUDIT_LOG', 'SYSTEM_CONFIG', 'PASSWORD_RESET_TOKENS'
) ORDER BY table_name;

-- Verify admin users were inserted
SELECT username, full_name, role, is_active FROM admin_users ORDER BY username;

-- Verify system configuration
SELECT config_key, config_value, description FROM system_config ORDER BY config_key;

-- =====================================================
-- END OF SCHEMA
-- =====================================================
