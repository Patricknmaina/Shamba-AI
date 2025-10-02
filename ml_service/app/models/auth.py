"""
Authentication Models for ShambaAI
Pydantic models for admin authentication
"""

from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import uuid

class UserRole(str, Enum):
    """Admin user roles"""
    SYSTEM_ADMINISTRATOR = "System Administrator"
    AGRICULTURE_EXPERT = "Agriculture Expert"
    DATA_MANAGER = "Data Manager"
    CONTENT_MODERATOR = "Content Moderator"
    TECHNICAL_ADMINISTRATOR = "Technical Administrator"

class Permission(str, Enum):
    """Admin permissions"""
    FULL_ACCESS = "full_access"
    MANAGE_USERS = "manage_users"
    MANAGE_CONTENT = "manage_content"
    VIEW_INSIGHTS = "view_insights"
    VIEW_LOGS = "view_logs"
    SYSTEM_HEALTH = "system_health"
    MANAGE_CROPS = "manage_crops"
    MANAGE_DATA = "manage_data"
    MODERATE_CONTENT = "moderate_content"
    MANAGE_SYSTEM = "manage_system"

class UserStatus(str, Enum):
    """User account status"""
    ACTIVE = "Y"
    INACTIVE = "N"

class SessionStatus(str, Enum):
    """Session status"""
    ACTIVE = "Y"
    INACTIVE = "N"

class AuditAction(str, Enum):
    """Audit log actions"""
    LOGIN_SUCCESS = "LOGIN_SUCCESS"
    LOGIN_FAILED = "LOGIN_FAILED"
    LOGOUT = "LOGOUT"
    CREATE_USER = "CREATE_USER"
    UPDATE_USER = "UPDATE_USER"
    DELETE_USER = "DELETE_USER"
    PASSWORD_CHANGE = "PASSWORD_CHANGE"
    PERMISSION_CHANGE = "PERMISSION_CHANGE"
    SYSTEM_CONFIG_CHANGE = "SYSTEM_CONFIG_CHANGE"

class AuditStatus(str, Enum):
    """Audit log status"""
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    ERROR = "ERROR"

# Base Models
class AdminUserBase(BaseModel):
    """Base admin user model"""
    username: str = Field(..., min_length=3, max_length=50, description="Username")
    email: EmailStr = Field(..., description="Email address")
    full_name: str = Field(..., min_length=2, max_length=100, description="Full name")
    role: UserRole = Field(..., description="User role")

class AdminUserCreate(AdminUserBase):
    """Model for creating admin user"""
    password: str = Field(..., min_length=8, max_length=128, description="Password")
    permissions: List[Permission] = Field(default_factory=list, description="User permissions")
    
    @validator('password')
    def validate_password(cls, v):
        """Validate password strength"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in v):
            raise ValueError('Password must contain at least one special character')
        return v

class AdminUserUpdate(BaseModel):
    """Model for updating admin user"""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    role: Optional[UserRole] = None
    permissions: Optional[List[Permission]] = None
    is_active: Optional[UserStatus] = None

class AdminUserResponse(AdminUserBase):
    """Model for admin user response"""
    user_id: str = Field(..., description="User ID")
    permissions: List[Permission] = Field(..., description="User permissions")
    is_active: UserStatus = Field(..., description="Account status")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    last_login: Optional[datetime] = Field(None, description="Last login timestamp")
    failed_login_attempts: int = Field(0, description="Failed login attempts")
    account_locked_until: Optional[datetime] = Field(None, description="Account lock expiration")
    
    class Config:
        from_attributes = True

class AdminUserDetail(AdminUserResponse):
    """Detailed admin user model"""
    created_by: Optional[str] = Field(None, description="Created by user ID")

# Authentication Models
class LoginRequest(BaseModel):
    """Login request model"""
    username: str = Field(..., min_length=3, max_length=50, description="Username")
    password: str = Field(..., min_length=1, description="Password")

class LoginResponse(BaseModel):
    """Login response model"""
    access_token: str = Field(..., description="Access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration in seconds")
    user: AdminUserResponse = Field(..., description="User information")

class LogoutRequest(BaseModel):
    """Logout request model"""
    session_token: Optional[str] = Field(None, description="Session token")

# Session Models
class SessionCreate(BaseModel):
    """Model for creating session"""
    user_id: str = Field(..., description="User ID")
    ip_address: Optional[str] = Field(None, description="IP address")
    user_agent: Optional[str] = Field(None, description="User agent")
    expires_at: datetime = Field(..., description="Session expiration")

class SessionResponse(BaseModel):
    """Model for session response"""
    session_id: str = Field(..., description="Session ID")
    user_id: str = Field(..., description="User ID")
    session_token: str = Field(..., description="Session token")
    ip_address: Optional[str] = Field(None, description="IP address")
    user_agent: Optional[str] = Field(None, description="User agent")
    expires_at: datetime = Field(..., description="Session expiration")
    created_at: datetime = Field(..., description="Session creation")
    is_active: SessionStatus = Field(..., description="Session status")
    last_activity: datetime = Field(..., description="Last activity")

    class Config:
        from_attributes = True

# Audit Models
class AuditLogCreate(BaseModel):
    """Model for creating audit log"""
    user_id: Optional[str] = Field(None, description="User ID")
    action: AuditAction = Field(..., description="Action performed")
    resource: str = Field(..., max_length=100, description="Resource affected")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional details")
    ip_address: Optional[str] = Field(None, description="IP address")
    user_agent: Optional[str] = Field(None, description="User agent")
    status: AuditStatus = Field(default=AuditStatus.SUCCESS, description="Action status")

class AuditLogResponse(BaseModel):
    """Model for audit log response"""
    log_id: str = Field(..., description="Log ID")
    user_id: Optional[str] = Field(None, description="User ID")
    username: Optional[str] = Field(None, description="Username")
    action: AuditAction = Field(..., description="Action performed")
    resource: str = Field(..., description="Resource affected")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional details")
    ip_address: Optional[str] = Field(None, description="IP address")
    user_agent: Optional[str] = Field(None, description="User agent")
    timestamp: datetime = Field(..., description="Timestamp")
    status: AuditStatus = Field(..., description="Action status")

    class Config:
        from_attributes = True

# System Configuration Models
class SystemConfigCreate(BaseModel):
    """Model for creating system configuration"""
    config_key: str = Field(..., max_length=100, description="Configuration key")
    config_value: str = Field(..., description="Configuration value")
    description: Optional[str] = Field(None, max_length=500, description="Description")
    is_encrypted: bool = Field(default=False, description="Is value encrypted")

class SystemConfigUpdate(BaseModel):
    """Model for updating system configuration"""
    config_value: str = Field(..., description="Configuration value")
    description: Optional[str] = Field(None, max_length=500, description="Description")
    is_encrypted: Optional[bool] = Field(None, description="Is value encrypted")

class SystemConfigResponse(BaseModel):
    """Model for system configuration response"""
    config_key: str = Field(..., description="Configuration key")
    config_value: str = Field(..., description="Configuration value")
    description: Optional[str] = Field(None, description="Description")
    is_encrypted: bool = Field(..., description="Is value encrypted")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    updated_by: Optional[str] = Field(None, description="Updated by user ID")

    class Config:
        from_attributes = True

# Password Reset Models
class PasswordResetRequest(BaseModel):
    """Model for password reset request"""
    username: str = Field(..., description="Username")
    email: EmailStr = Field(..., description="Email address")

class PasswordResetToken(BaseModel):
    """Model for password reset token"""
    token: str = Field(..., description="Reset token")
    expires_at: datetime = Field(..., description="Token expiration")

class PasswordResetConfirm(BaseModel):
    """Model for password reset confirmation"""
    token: str = Field(..., description="Reset token")
    new_password: str = Field(..., min_length=8, max_length=128, description="New password")
    
    @validator('new_password')
    def validate_password(cls, v):
        """Validate password strength"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in v):
            raise ValueError('Password must contain at least one special character')
        return v

# Change Password Models
class ChangePasswordRequest(BaseModel):
    """Model for changing password"""
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, max_length=128, description="New password")
    
    @validator('new_password')
    def validate_password(cls, v):
        """Validate password strength"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in v):
            raise ValueError('Password must contain at least one special character')
        return v

# Token Models
class TokenData(BaseModel):
    """Token data model"""
    user_id: Optional[str] = None
    username: Optional[str] = None
    permissions: Optional[List[Permission]] = None

class Token(BaseModel):
    """Token model"""
    access_token: str
    token_type: str

# Response Models
class MessageResponse(BaseModel):
    """Generic message response"""
    message: str = Field(..., description="Response message")
    success: bool = Field(default=True, description="Success status")
    data: Optional[Dict[str, Any]] = Field(None, description="Additional data")

class ErrorResponse(BaseModel):
    """Error response model"""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Error details")
    status_code: int = Field(..., description="HTTP status code")

# Health Check Models
class HealthCheck(BaseModel):
    """Health check model"""
    status: str = Field(..., description="Health status")
    timestamp: datetime = Field(..., description="Check timestamp")
    database: Optional[Dict[str, Any]] = Field(None, description="Database status")
    version: str = Field(..., description="Application version")

# Statistics Models
class UserStatistics(BaseModel):
    """User statistics model"""
    total_users: int = Field(..., description="Total number of users")
    active_users: int = Field(..., description="Number of active users")
    inactive_users: int = Field(..., description="Number of inactive users")
    locked_users: int = Field(..., description="Number of locked users")
    users_by_role: Dict[str, int] = Field(..., description="Users by role")

class SessionStatistics(BaseModel):
    """Session statistics model"""
    total_sessions: int = Field(..., description="Total number of sessions")
    active_sessions: int = Field(..., description="Number of active sessions")
    expired_sessions: int = Field(..., description="Number of expired sessions")

class AuditStatistics(BaseModel):
    """Audit statistics model"""
    total_logs: int = Field(..., description="Total number of audit logs")
    logs_today: int = Field(..., description="Audit logs today")
    failed_logins: int = Field(..., description="Failed login attempts")
    actions_by_type: Dict[str, int] = Field(..., description="Actions by type")

# Database Health Models
class DatabaseHealth(BaseModel):
    """Database health model"""
    status: str = Field(..., description="Database status")
    admin_users_count: int = Field(..., description="Number of admin users")
    database_version: str = Field(..., description="Database version")
    pool_size: Optional[str] = Field(None, description="Connection pool size")
    last_check: datetime = Field(..., description="Last health check")
