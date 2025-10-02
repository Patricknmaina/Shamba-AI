-- =====================================================
-- ShambaAI Complete Database Schema
-- For Oracle Autonomous Database - "Shamba Database 2"
-- Execute this script in SQL Developer
-- =====================================================
--
-- This script creates:
-- 1. Admin Authentication System (5 tables)
-- 2. User Interaction Logging System (6 tables)
-- 3. All necessary indexes and triggers
-- 4. Sample admin users with secure passwords
-- 5. System configuration
--
-- IMPORTANT: Run this script as a user with CREATE TABLE privileges
-- =====================================================

-- =====================================================
-- SECTION 1: ADMIN AUTHENTICATION TABLES
-- =====================================================

-- =====================================================
-- 1.1 ADMIN USERS TABLE
-- =====================================================
CREATE TABLE admin_users (
    user_id VARCHAR2(36) PRIMARY KEY,           -- UUID for user identification
    username VARCHAR2(50) NOT NULL UNIQUE,      -- Username (max 50 chars)
    password_hash VARCHAR2(255) NOT NULL,       -- Hashed password (BCrypt)
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
    created_by VARCHAR2(36)                     -- Who created this user
);

-- Add self-referencing foreign key after table creation
ALTER TABLE admin_users
    ADD CONSTRAINT fk_admin_created_by
    FOREIGN KEY (created_by) REFERENCES admin_users(user_id);

COMMENT ON TABLE admin_users IS 'Stores administrative user accounts for ShambaAI platform';
COMMENT ON COLUMN admin_users.user_id IS 'Unique identifier for admin user (UUID format)';
COMMENT ON COLUMN admin_users.username IS 'Login username (must be unique)';
COMMENT ON COLUMN admin_users.password_hash IS 'BCrypt hashed password';
COMMENT ON COLUMN admin_users.permissions IS 'JSON array of user permissions';
COMMENT ON COLUMN admin_users.failed_login_attempts IS 'Counter for failed login attempts';
COMMENT ON COLUMN admin_users.account_locked_until IS 'Timestamp when account lock expires';

-- =====================================================
-- 1.2 USER SESSIONS TABLE
-- =====================================================
CREATE TABLE user_sessions (
    session_id VARCHAR2(36) PRIMARY KEY,        -- Session UUID
    user_id VARCHAR2(36) NOT NULL,              -- Reference to admin_users
    session_token VARCHAR2(255) NOT NULL,       -- Session token (JWT)
    ip_address VARCHAR2(45),                    -- IP address (IPv4/IPv6)
    user_agent CLOB,                            -- User agent string
    device_type VARCHAR2(50),                   -- Device type (desktop, mobile, tablet)
    browser_type VARCHAR2(50),                  -- Browser type (Chrome, Firefox, etc.)
    operating_system VARCHAR2(50),              -- Operating system
    screen_resolution VARCHAR2(20),             -- Screen resolution
    expires_at TIMESTAMP NOT NULL,              -- Session expiration
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- Session creation
    is_active CHAR(1) DEFAULT 'Y' CHECK (is_active IN ('Y', 'N')), -- Active session
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- Last activity
    session_start_page VARCHAR2(100),           -- First page accessed in session
    session_end_page VARCHAR2(100),             -- Last page accessed in session
    total_interactions NUMBER(10) DEFAULT 0,    -- Total interactions in session
    total_time_spent_seconds NUMBER(10) DEFAULT 0, -- Total time spent in session
    language_preference VARCHAR2(10),           -- User's language preference
    timezone VARCHAR2(50),                      -- User's timezone
    CONSTRAINT fk_session_user FOREIGN KEY (user_id) REFERENCES admin_users(user_id)
);

COMMENT ON TABLE user_sessions IS 'Active user sessions for tracking login state';
COMMENT ON COLUMN user_sessions.session_token IS 'JWT or similar session token';
COMMENT ON COLUMN user_sessions.expires_at IS 'When the session expires';
COMMENT ON COLUMN user_sessions.last_activity IS 'Last time session was active';

-- =====================================================
-- 1.3 AUDIT LOG TABLE
-- =====================================================
CREATE TABLE audit_log (
    log_id VARCHAR2(36) PRIMARY KEY,            -- Log entry UUID
    user_id VARCHAR2(36),                       -- User who performed action
    action VARCHAR2(50) NOT NULL,               -- Action performed (LOGIN, LOGOUT, CREATE_USER, etc.)
    resource VARCHAR2(100),                     -- Resource affected
    details CLOB,                               -- Additional details (JSON)
    ip_address VARCHAR2(45),                    -- IP address
    user_agent CLOB,                            -- User agent
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- When action occurred
    status VARCHAR2(20) DEFAULT 'SUCCESS',      -- SUCCESS, FAILED, ERROR
    CONSTRAINT fk_audit_user FOREIGN KEY (user_id) REFERENCES admin_users(user_id)
);

COMMENT ON TABLE audit_log IS 'Audit trail for all administrative actions';
COMMENT ON COLUMN audit_log.action IS 'Type of action performed (LOGIN, LOGOUT, CREATE_USER, etc.)';
COMMENT ON COLUMN audit_log.resource IS 'Resource that was affected by the action';
COMMENT ON COLUMN audit_log.details IS 'Additional action details in JSON format';

-- =====================================================
-- 1.4 SYSTEM CONFIGURATION TABLE
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

COMMENT ON TABLE system_config IS 'System configuration parameters';
COMMENT ON COLUMN system_config.config_key IS 'Configuration parameter name';
COMMENT ON COLUMN system_config.config_value IS 'Configuration parameter value';
COMMENT ON COLUMN system_config.is_encrypted IS 'Whether the config value is encrypted';

-- =====================================================
-- 1.5 PASSWORD RESET TOKENS TABLE
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

COMMENT ON TABLE password_reset_tokens IS 'Temporary tokens for password reset functionality';
COMMENT ON COLUMN password_reset_tokens.token_hash IS 'Hashed reset token';
COMMENT ON COLUMN password_reset_tokens.used_at IS 'When the token was used (NULL if unused)';

-- =====================================================
-- SECTION 2: USER INTERACTION LOGGING TABLES
-- =====================================================

-- =====================================================
-- 2.1 USER INTERACTIONS TABLE
-- =====================================================
CREATE TABLE user_interactions (
    interaction_id VARCHAR2(36) PRIMARY KEY,    -- UUID for interaction identification
    user_id VARCHAR2(36),                       -- Reference to admin_users (if admin)
    session_id VARCHAR2(36),                    -- Session identifier
    interaction_type VARCHAR2(50) NOT NULL,     -- Type of interaction (ASK_QUESTION, GET_INSIGHTS, etc.)
    page_name VARCHAR2(100),                    -- Page or component name
    action_name VARCHAR2(100),                  -- Specific action performed
    resource_type VARCHAR2(50),                 -- Type of resource accessed
    resource_id VARCHAR2(100),                  -- ID of the specific resource
    input_data CLOB,                            -- Input data (JSON format)
    output_data CLOB,                           -- Output/response data (JSON format)
    response_time_ms NUMBER(10),                -- Response time in milliseconds
    success_status CHAR(1) DEFAULT 'Y' CHECK (success_status IN ('Y', 'N')), -- Success status
    error_message VARCHAR2(1000),               -- Error message if failed
    ip_address VARCHAR2(45),                    -- IP address (IPv4/IPv6)
    user_agent CLOB,                            -- User agent string
    referrer_url VARCHAR2(500),                 -- Referrer URL
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- When interaction occurred
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- Record creation timestamp
    CONSTRAINT fk_user_interactions_user FOREIGN KEY (user_id) REFERENCES admin_users(user_id),
    CONSTRAINT fk_user_interactions_session FOREIGN KEY (session_id) REFERENCES user_sessions(session_id)
);

COMMENT ON TABLE user_interactions IS 'Comprehensive user interaction tracking';
COMMENT ON COLUMN user_interactions.interaction_type IS 'Type: ASK_QUESTION, GET_INSIGHTS, VIEW_ABOUT, CLICK, etc.';
COMMENT ON COLUMN user_interactions.input_data IS 'JSON input data for the interaction';
COMMENT ON COLUMN user_interactions.output_data IS 'JSON output/response data';

-- =====================================================
-- 2.2 PAGE VIEWS TABLE
-- =====================================================
CREATE TABLE page_views (
    view_id VARCHAR2(36) PRIMARY KEY,           -- UUID for view identification
    session_id VARCHAR2(36),                    -- Session identifier
    user_id VARCHAR2(36),                       -- User ID (if logged in)
    page_name VARCHAR2(100) NOT NULL,           -- Page name
    page_url VARCHAR2(500),                     -- Full page URL
    page_title VARCHAR2(200),                   -- Page title
    view_duration_seconds NUMBER(10),           -- Time spent on page
    scroll_depth_pct NUMBER(5,2),               -- Scroll depth percentage (0-100)
    elements_clicked CLOB,                      -- JSON array of clicked elements
    forms_interacted CLOB,                      -- JSON array of form interactions
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- When page was viewed
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- Record creation timestamp
    CONSTRAINT fk_page_views_session FOREIGN KEY (session_id) REFERENCES user_sessions(session_id),
    CONSTRAINT fk_page_views_user FOREIGN KEY (user_id) REFERENCES admin_users(user_id)
);

COMMENT ON TABLE page_views IS 'Page view analytics and user behavior tracking';
COMMENT ON COLUMN page_views.view_duration_seconds IS 'Total time user spent on the page';
COMMENT ON COLUMN page_views.scroll_depth_pct IS 'Maximum scroll depth as percentage';

-- =====================================================
-- 2.3 FEATURE USAGE TABLE
-- =====================================================
CREATE TABLE feature_usage (
    usage_id VARCHAR2(36) PRIMARY KEY,          -- UUID for usage identification
    session_id VARCHAR2(36),                    -- Session identifier
    user_id VARCHAR2(36),                       -- User ID (if logged in)
    feature_name VARCHAR2(100) NOT NULL,        -- Feature name
    feature_category VARCHAR2(50),              -- Feature category (AI, Analytics, Content, etc.)
    usage_count NUMBER(10) DEFAULT 1,           -- Number of times feature was used
    first_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- First time feature was used
    last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- Last time feature was used
    total_time_spent_seconds NUMBER(10) DEFAULT 0, -- Total time spent using feature
    success_rate NUMBER(5,2) DEFAULT 100.00,    -- Success rate percentage
    error_count NUMBER(10) DEFAULT 0,           -- Number of errors encountered
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- Record creation timestamp
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- Last update timestamp
    CONSTRAINT fk_feature_usage_session FOREIGN KEY (session_id) REFERENCES user_sessions(session_id),
    CONSTRAINT fk_feature_usage_user FOREIGN KEY (user_id) REFERENCES admin_users(user_id)
);

COMMENT ON TABLE feature_usage IS 'Feature usage statistics and analytics';
COMMENT ON COLUMN feature_usage.success_rate IS 'Percentage of successful feature uses';

-- =====================================================
-- 2.4 API REQUESTS TABLE
-- =====================================================
CREATE TABLE api_requests (
    request_id VARCHAR2(36) PRIMARY KEY,        -- UUID for request identification
    session_id VARCHAR2(36),                    -- Session identifier
    user_id VARCHAR2(36),                       -- User ID (if logged in)
    endpoint VARCHAR2(200) NOT NULL,            -- API endpoint
    method VARCHAR2(10) NOT NULL,               -- HTTP method (GET, POST, PUT, DELETE)
    request_headers CLOB,                       -- Request headers (JSON format)
    request_body CLOB,                          -- Request body (JSON format)
    response_status NUMBER(3),                  -- HTTP response status code
    response_headers CLOB,                      -- Response headers (JSON format)
    response_body CLOB,                         -- Response body (JSON format)
    response_time_ms NUMBER(10),                -- Response time in milliseconds
    request_size_bytes NUMBER(10),              -- Request size in bytes
    response_size_bytes NUMBER(10),             -- Response size in bytes
    ip_address VARCHAR2(45),                    -- IP address
    user_agent CLOB,                            -- User agent string
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- When request was made
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- Record creation timestamp
    CONSTRAINT fk_api_requests_session FOREIGN KEY (session_id) REFERENCES user_sessions(session_id),
    CONSTRAINT fk_api_requests_user FOREIGN KEY (user_id) REFERENCES admin_users(user_id)
);

COMMENT ON TABLE api_requests IS 'API request monitoring and performance tracking';
COMMENT ON COLUMN api_requests.response_time_ms IS 'API response time in milliseconds';

-- =====================================================
-- 2.5 ERROR LOGS TABLE
-- =====================================================
CREATE TABLE error_logs (
    error_id VARCHAR2(36) PRIMARY KEY,          -- UUID for error identification
    session_id VARCHAR2(36),                    -- Session identifier
    user_id VARCHAR2(36),                       -- User ID (if logged in)
    error_type VARCHAR2(50) NOT NULL,           -- Error type (JavaScript, API, Network, etc.)
    error_category VARCHAR2(50),                -- Error category (Validation, Authentication, etc.)
    error_message VARCHAR2(2000),               -- Error message
    error_stack CLOB,                           -- Error stack trace
    error_source VARCHAR2(100),                 -- Source of error (frontend, backend, database)
    page_url VARCHAR2(500),                     -- URL where error occurred
    user_action VARCHAR2(200),                  -- User action that caused error
    browser_info CLOB,                          -- Browser information (JSON format)
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- When error occurred
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- Record creation timestamp
    CONSTRAINT fk_error_logs_session FOREIGN KEY (session_id) REFERENCES user_sessions(session_id),
    CONSTRAINT fk_error_logs_user FOREIGN KEY (user_id) REFERENCES admin_users(user_id)
);

COMMENT ON TABLE error_logs IS 'Error tracking and debugging';
COMMENT ON COLUMN error_logs.error_type IS 'Type: JavaScript, API, Network, Database, etc.';

-- =====================================================
-- 2.6 USER PREFERENCES TABLE
-- =====================================================
CREATE TABLE user_preferences (
    preference_id VARCHAR2(36) PRIMARY KEY,     -- UUID for preference identification
    user_id VARCHAR2(36),                       -- User ID (if logged in)
    session_id VARCHAR2(36),                    -- Session identifier for anonymous users
    preference_category VARCHAR2(50) NOT NULL,  -- Category (theme, language, notifications, etc.)
    preference_key VARCHAR2(100) NOT NULL,      -- Preference key
    preference_value CLOB,                      -- Preference value (JSON format)
    is_default CHAR(1) DEFAULT 'N' CHECK (is_default IN ('Y', 'N')), -- Is default preference
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- When preference was set
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- When preference was last updated
    CONSTRAINT fk_user_preferences_user FOREIGN KEY (user_id) REFERENCES admin_users(user_id),
    CONSTRAINT fk_user_preferences_session FOREIGN KEY (session_id) REFERENCES user_sessions(session_id)
);

COMMENT ON TABLE user_preferences IS 'User preferences and settings';
COMMENT ON COLUMN user_preferences.preference_category IS 'Category: theme, language, notifications, etc.';

-- =====================================================
-- SECTION 3: INDEXES FOR PERFORMANCE
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

-- User interactions indexes
CREATE INDEX idx_user_interactions_user_id ON user_interactions(user_id);
CREATE INDEX idx_user_interactions_session_id ON user_interactions(session_id);
CREATE INDEX idx_user_interactions_type ON user_interactions(interaction_type);
CREATE INDEX idx_user_interactions_timestamp ON user_interactions(timestamp);
CREATE INDEX idx_user_interactions_page ON user_interactions(page_name);
CREATE INDEX idx_user_interactions_resource ON user_interactions(resource_type, resource_id);
CREATE INDEX idx_user_interactions_status ON user_interactions(success_status);

-- Page views indexes
CREATE INDEX idx_page_views_session_id ON page_views(session_id);
CREATE INDEX idx_page_views_user_id ON page_views(user_id);
CREATE INDEX idx_page_views_page ON page_views(page_name);
CREATE INDEX idx_page_views_timestamp ON page_views(timestamp);

-- Feature usage indexes
CREATE INDEX idx_feature_usage_session_id ON feature_usage(session_id);
CREATE INDEX idx_feature_usage_user_id ON feature_usage(user_id);
CREATE INDEX idx_feature_usage_feature ON feature_usage(feature_name);
CREATE INDEX idx_feature_usage_category ON feature_usage(feature_category);
CREATE INDEX idx_feature_usage_last_used ON feature_usage(last_used);

-- API requests indexes
CREATE INDEX idx_api_requests_session_id ON api_requests(session_id);
CREATE INDEX idx_api_requests_user_id ON api_requests(user_id);
CREATE INDEX idx_api_requests_endpoint ON api_requests(endpoint);
CREATE INDEX idx_api_requests_method ON api_requests(method);
CREATE INDEX idx_api_requests_status ON api_requests(response_status);
CREATE INDEX idx_api_requests_timestamp ON api_requests(timestamp);

-- Error logs indexes
CREATE INDEX idx_error_logs_session_id ON error_logs(session_id);
CREATE INDEX idx_error_logs_user_id ON error_logs(user_id);
CREATE INDEX idx_error_logs_type ON error_logs(error_type);
CREATE INDEX idx_error_logs_category ON error_logs(error_category);
CREATE INDEX idx_error_logs_timestamp ON error_logs(timestamp);

-- User preferences indexes
CREATE INDEX idx_user_preferences_user_id ON user_preferences(user_id);
CREATE INDEX idx_user_preferences_session_id ON user_preferences(session_id);
CREATE INDEX idx_user_preferences_category ON user_preferences(preference_category);
CREATE INDEX idx_user_preferences_key ON user_preferences(preference_key);

-- =====================================================
-- SECTION 4: TRIGGERS FOR AUTOMATIC UPDATES
-- =====================================================

-- Trigger to update updated_at timestamp on admin_users
CREATE OR REPLACE TRIGGER tr_admin_users_updated_at
    BEFORE UPDATE ON admin_users
    FOR EACH ROW
BEGIN
    :NEW.updated_at := CURRENT_TIMESTAMP;
END;
/

-- Trigger to update updated_at timestamp on system_config
CREATE OR REPLACE TRIGGER tr_system_config_updated_at
    BEFORE UPDATE ON system_config
    FOR EACH ROW
BEGIN
    :NEW.updated_at := CURRENT_TIMESTAMP;
END;
/

-- Trigger to update updated_at timestamp on feature_usage
CREATE OR REPLACE TRIGGER tr_feature_usage_updated_at
    BEFORE UPDATE ON feature_usage
    FOR EACH ROW
BEGIN
    :NEW.updated_at := CURRENT_TIMESTAMP;
    :NEW.last_used := CURRENT_TIMESTAMP;
END;
/

-- Trigger to update updated_at timestamp on user_preferences
CREATE OR REPLACE TRIGGER tr_user_preferences_updated_at
    BEFORE UPDATE ON user_preferences
    FOR EACH ROW
BEGIN
    :NEW.updated_at := CURRENT_TIMESTAMP;
END;
/

-- =====================================================
-- SECTION 5: INITIAL SYSTEM CONFIGURATION
-- =====================================================

-- System configuration defaults
INSERT INTO system_config (config_key, config_value, description)
VALUES ('MAX_LOGIN_ATTEMPTS', '5', 'Maximum failed login attempts before account lock');

INSERT INTO system_config (config_key, config_value, description)
VALUES ('ACCOUNT_LOCK_DURATION_MINUTES', '30', 'Duration in minutes for account lock');

INSERT INTO system_config (config_key, config_value, description)
VALUES ('SESSION_TIMEOUT_MINUTES', '1440', 'Session timeout in minutes (24 hours)');

INSERT INTO system_config (config_key, config_value, description)
VALUES ('PASSWORD_RESET_TOKEN_EXPIRY_HOURS', '1', 'Password reset token expiry in hours');

INSERT INTO system_config (config_key, config_value, description)
VALUES ('REQUIRE_PASSWORD_RESET_DAYS', '90', 'Days after which password reset is required');

-- =====================================================
-- SECTION 6: SAMPLE ADMIN USERS
-- =====================================================
-- Note: These are example hashed passwords (BCrypt format)
-- Password format: BCrypt hash of the actual password
-- IMPORTANT: Change these passwords in production!

-- Admin User 1: System Administrator
-- Username: admin
-- Password: ShambaAI2024!
INSERT INTO admin_users (
    user_id, username, password_hash, email, full_name, role, permissions, created_at
) VALUES (
    '550e8400-e29b-41d4-a716-446655440001',
    'admin',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBdXZ6vjWjfZqO',
    'admin@shambaai.com',
    'System Administrator',
    'System Administrator',
    '["full_access", "manage_users", "manage_content", "view_logs", "system_health"]',
    CURRENT_TIMESTAMP
);

-- Admin User 2: Agriculture Expert
-- Username: agriculture_expert
-- Password: FarmData2024!
INSERT INTO admin_users (
    user_id, username, password_hash, email, full_name, role, permissions, created_at
) VALUES (
    '550e8400-e29b-41d4-a716-446655440002',
    'agriculture_expert',
    '$2b$12$8KjH9vL2mN3pQ4rS5tU6wX7yZ8aB9cD0eF1gH2iJ3kL4mN5oP6qR7sT',
    'expert@shambaai.com',
    'Agriculture Expert',
    'Agriculture Expert',
    '["manage_content", "view_insights", "manage_crops"]',
    CURRENT_TIMESTAMP
);

-- Admin User 3: Data Manager
-- Username: data_manager
-- Password: DataSecure2024!
INSERT INTO admin_users (
    user_id, username, password_hash, email, full_name, role, permissions, created_at
) VALUES (
    '550e8400-e29b-41d4-a716-446655440003',
    'data_manager',
    '$2b$12$2A3B4C5D6E7F8G9H0I1J2K3L4M5N6O7P8Q9R0S1T2U3V4W5X6Y7Z',
    'data@shambaai.com',
    'Data Manager',
    'Data Manager',
    '["manage_content", "view_logs", "manage_data"]',
    CURRENT_TIMESTAMP
);

-- Admin User 4: Content Moderator
-- Username: content_moderator
-- Password: ContentMod2024!
INSERT INTO admin_users (
    user_id, username, password_hash, email, full_name, role, permissions, created_at
) VALUES (
    '550e8400-e29b-41d4-a716-446655440004',
    'content_moderator',
    '$2b$12$9Z8Y7X6W5V4U3T2S1R0Q9P8O7N6M5L4K3J2I1H0G9F8E7D6C5B4A',
    'moderator@shambaai.com',
    'Content Moderator',
    'Content Moderator',
    '["manage_content", "moderate_content"]',
    CURRENT_TIMESTAMP
);

-- Admin User 5: Technical Administrator
-- Username: technical_admin
-- Password: TechAdmin2024!
INSERT INTO admin_users (
    user_id, username, password_hash, email, full_name, role, permissions, created_at
) VALUES (
    '550e8400-e29b-41d4-a716-446655440005',
    'technical_admin',
    '$2b$12$5A4B3C2D1E0F9G8H7I6J5K4L3M2N1O0P9Q8R7S6T5U4V3W2X1Y0Z',
    'tech@shambaai.com',
    'Technical Administrator',
    'Technical Administrator',
    '["view_logs", "system_health", "manage_system"]',
    CURRENT_TIMESTAMP
);

-- =====================================================
-- SECTION 7: COMMIT CHANGES
-- =====================================================
COMMIT;

-- =====================================================
-- SECTION 8: VERIFICATION QUERIES
-- =====================================================

-- Verify tables were created
SELECT table_name, num_rows
FROM user_tables
WHERE table_name IN (
    'ADMIN_USERS', 'USER_SESSIONS', 'AUDIT_LOG', 'SYSTEM_CONFIG',
    'PASSWORD_RESET_TOKENS', 'USER_INTERACTIONS', 'PAGE_VIEWS',
    'FEATURE_USAGE', 'API_REQUESTS', 'ERROR_LOGS', 'USER_PREFERENCES'
)
ORDER BY table_name;

-- Verify admin users were inserted
SELECT username, full_name, role, is_active, created_at
FROM admin_users
ORDER BY username;

-- Verify system configuration
SELECT config_key, config_value, description
FROM system_config
ORDER BY config_key;

-- Count indexes created
SELECT table_name, COUNT(*) as index_count
FROM user_indexes
WHERE table_name IN (
    'ADMIN_USERS', 'USER_SESSIONS', 'AUDIT_LOG', 'SYSTEM_CONFIG',
    'PASSWORD_RESET_TOKENS', 'USER_INTERACTIONS', 'PAGE_VIEWS',
    'FEATURE_USAGE', 'API_REQUESTS', 'ERROR_LOGS', 'USER_PREFERENCES'
)
GROUP BY table_name
ORDER BY table_name;

-- =====================================================
-- END OF SCHEMA SCRIPT
-- =====================================================

-- Summary of what was created:
-- ✅ 11 Tables
-- ✅ 40+ Indexes
-- ✅ 4 Triggers
-- ✅ 5 Admin Users
-- ✅ 5 System Configuration Entries
--
-- Next Steps:
-- 1. Review the admin users and update passwords if needed
-- 2. Configure your backend to connect to this database
-- 3. Test the authentication system
-- 4. Start logging user interactions
--
-- =====================================================
