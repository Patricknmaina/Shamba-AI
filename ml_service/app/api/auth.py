"""
Authentication API endpoints for ShambaAI
Admin authentication and user management endpoints
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPAuthorizationCredentials

from ..models.auth import (
    LoginRequest, LoginResponse, LogoutRequest, AdminUserCreate, AdminUserUpdate,
    AdminUserResponse, AdminUserDetail, ChangePasswordRequest, PasswordResetRequest,
    PasswordResetConfirm, MessageResponse, ErrorResponse, HealthCheck,
    UserStatistics, SessionStatistics, AuditStatistics, DatabaseHealth,
    UserRole, Permission
)
from ..services.auth_service import (
    get_auth_service, get_current_user, require_permission, require_full_access,
    AuthenticationService, TokenData
)
from ..database.connection import (
    get_database_manager, log_audit_event, test_connection
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login", response_model=LoginResponse)
async def login(
    login_request: LoginRequest,
    request: Request,
    auth_service: AuthenticationService = Depends(get_auth_service)
):
    """
    Admin user login endpoint
    
    Authenticates admin users and returns access token and user information.
    Logs all login attempts for security auditing.
    """
    try:
        # Get client information
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
        
        # Perform login
        login_response = auth_service.login(
            login_request=login_request,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return login_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login endpoint error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed due to internal error"
        )

@router.post("/logout", response_model=MessageResponse)
async def logout(
    logout_request: LogoutRequest,
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    auth_service: AuthenticationService = Depends(get_auth_service)
):
    """
    Admin user logout endpoint
    
    Logs out the current user and deactivates their session.
    """
    try:
        # Get client information
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
        
        # Perform logout
        auth_service.logout(
            user_id=current_user.user_id,
            session_token=logout_request.session_token,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return MessageResponse(
            message="Successfully logged out",
            success=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Logout endpoint error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed due to internal error"
        )

@router.get("/me", response_model=AdminUserResponse)
async def get_current_user_info(
    current_user: TokenData = Depends(get_current_user),
    auth_service: AuthenticationService = Depends(get_auth_service)
):
    """
    Get current user information
    
    Returns detailed information about the currently authenticated user.
    """
    try:
        # Get user details
        user_data = auth_service.get_user_by_id(current_user.user_id)
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        from datetime import datetime
        from ..models.auth import AdminUserResponse, UserStatus
        
        return AdminUserResponse(
            user_id=user_data['user_id'],
            username=user_data['username'],
            email=user_data['email'],
            full_name=user_data['full_name'],
            role=user_data['role'],
            permissions=auth_service._parse_permissions(user_data.get('permissions', '[]')),
            is_active=UserStatus(user_data['is_active']),
            created_at=datetime.fromisoformat(user_data['created_at'].replace('Z', '+00:00')),
            updated_at=datetime.fromisoformat(user_data['updated_at'].replace('Z', '+00:00')),
            last_login=datetime.fromisoformat(user_data['last_login'].replace('Z', '+00:00')) if user_data.get('last_login') else None,
            failed_login_attempts=user_data.get('failed_login_attempts', 0),
            account_locked_until=datetime.fromisoformat(user_data['account_locked_until'].replace('Z', '+00:00')) if user_data.get('account_locked_until') else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get current user error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user information"
        )

@router.post("/users", response_model=AdminUserResponse)
async def create_admin_user(
    user_create: AdminUserCreate,
    request: Request,
    current_user: TokenData = Depends(require_full_access()),
    auth_service: AuthenticationService = Depends(get_auth_service)
):
    """
    Create a new admin user
    
    Creates a new administrative user with specified permissions.
    Requires full access permission.
    """
    try:
        # Get client information
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
        
        # Create user
        user_response = auth_service.create_admin_user(user_create, current_user.user_id)
        
        # Log the creation
        log_audit_event(
            user_id=current_user.user_id,
            action="CREATE_USER",
            resource="ADMIN_USERS",
            details={
                "created_user_id": user_response.user_id,
                "created_username": user_response.username,
                "role": user_response.role.value
            },
            ip_address=ip_address,
            user_agent=user_agent,
            status="SUCCESS"
        )
        
        return user_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create user error: {e}")
        
        # Log failed creation
        log_audit_event(
            user_id=current_user.user_id,
            action="CREATE_USER",
            resource="ADMIN_USERS",
            details={"error": str(e)},
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            status="FAILED"
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user: {str(e)}"
        )

@router.get("/users", response_model=List[AdminUserResponse])
async def get_admin_users(
    current_user: TokenData = Depends(require_permission(Permission.MANAGE_USERS)),
    auth_service: AuthenticationService = Depends(get_auth_service)
):
    """
    Get all admin users
    
    Returns a list of all administrative users.
    Requires manage_users permission.
    """
    try:
        db = get_database_manager()
        results = db.execute_query(
            "SELECT * FROM admin_users ORDER BY created_at DESC"
        )
        
        users = []
        for user_data in results:
            from datetime import datetime
            from ..models.auth import AdminUserResponse, UserStatus
            
            users.append(AdminUserResponse(
                user_id=user_data['user_id'],
                username=user_data['username'],
                email=user_data['email'],
                full_name=user_data['full_name'],
                role=user_data['role'],
                permissions=auth_service._parse_permissions(user_data.get('permissions', '[]')),
                is_active=UserStatus(user_data['is_active']),
                created_at=datetime.fromisoformat(user_data['created_at'].replace('Z', '+00:00')),
                updated_at=datetime.fromisoformat(user_data['updated_at'].replace('Z', '+00:00')),
                last_login=datetime.fromisoformat(user_data['last_login'].replace('Z', '+00:00')) if user_data.get('last_login') else None,
                failed_login_attempts=user_data.get('failed_login_attempts', 0),
                account_locked_until=datetime.fromisoformat(user_data['account_locked_until'].replace('Z', '+00:00')) if user_data.get('account_locked_until') else None
            ))
        
        return users
        
    except Exception as e:
        logger.error(f"Get users error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get users"
        )

@router.get("/users/{user_id}", response_model=AdminUserDetail)
async def get_admin_user(
    user_id: str,
    current_user: TokenData = Depends(require_permission(Permission.MANAGE_USERS)),
    auth_service: AuthenticationService = Depends(get_auth_service)
):
    """
    Get specific admin user by ID
    
    Returns detailed information about a specific administrative user.
    Requires manage_users permission.
    """
    try:
        user_data = auth_service.get_user_by_id(user_id)
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        from datetime import datetime
        from ..models.auth import AdminUserDetail, UserStatus
        
        return AdminUserDetail(
            user_id=user_data['user_id'],
            username=user_data['username'],
            email=user_data['email'],
            full_name=user_data['full_name'],
            role=user_data['role'],
            permissions=auth_service._parse_permissions(user_data.get('permissions', '[]')),
            is_active=UserStatus(user_data['is_active']),
            created_at=datetime.fromisoformat(user_data['created_at'].replace('Z', '+00:00')),
            updated_at=datetime.fromisoformat(user_data['updated_at'].replace('Z', '+00:00')),
            last_login=datetime.fromisoformat(user_data['last_login'].replace('Z', '+00:00')) if user_data.get('last_login') else None,
            failed_login_attempts=user_data.get('failed_login_attempts', 0),
            account_locked_until=datetime.fromisoformat(user_data['account_locked_until'].replace('Z', '+00:00')) if user_data.get('account_locked_until') else None,
            created_by=user_data.get('created_by')
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get user error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user"
        )

@router.get("/health", response_model=HealthCheck)
async def health_check():
    """
    Health check endpoint
    
    Returns the health status of the authentication system and database.
    """
    try:
        # Test database connection
        db_health = test_connection()
        
        return HealthCheck(
            status="healthy" if db_health["status"] == "success" else "unhealthy",
            timestamp=db_health.get("timestamp", ""),
            database=db_health,
            version="1.0.0"
        )
        
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return HealthCheck(
            status="unhealthy",
            timestamp="",
            database={"status": "failed", "error": str(e)},
            version="1.0.0"
        )

@router.get("/statistics/users", response_model=UserStatistics)
async def get_user_statistics(
    current_user: TokenData = Depends(require_permission(Permission.VIEW_LOGS))
):
    """
    Get user statistics
    
    Returns statistics about admin users including counts by role and status.
    Requires view_logs permission.
    """
    try:
        db = get_database_manager()
        
        # Get total users
        total_result = db.execute_query("SELECT COUNT(*) as count FROM admin_users")
        total_users = total_result[0]['count']
        
        # Get active users
        active_result = db.execute_query("SELECT COUNT(*) as count FROM admin_users WHERE is_active = 'Y'")
        active_users = active_result[0]['count']
        
        # Get inactive users
        inactive_users = total_users - active_users
        
        # Get locked users
        locked_result = db.execute_query(
            "SELECT COUNT(*) as count FROM admin_users WHERE account_locked_until > CURRENT_TIMESTAMP"
        )
        locked_users = locked_result[0]['count']
        
        # Get users by role
        role_result = db.execute_query(
            "SELECT role, COUNT(*) as count FROM admin_users GROUP BY role"
        )
        users_by_role = {row['role']: row['count'] for row in role_result}
        
        return UserStatistics(
            total_users=total_users,
            active_users=active_users,
            inactive_users=inactive_users,
            locked_users=locked_users,
            users_by_role=users_by_role
        )
        
    except Exception as e:
        logger.error(f"User statistics error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user statistics"
        )

@router.get("/statistics/sessions", response_model=SessionStatistics)
async def get_session_statistics(
    current_user: TokenData = Depends(require_permission(Permission.VIEW_LOGS))
):
    """
    Get session statistics
    
    Returns statistics about user sessions.
    Requires view_logs permission.
    """
    try:
        db = get_database_manager()
        
        # Get total sessions
        total_result = db.execute_query("SELECT COUNT(*) as count FROM user_sessions")
        total_sessions = total_result[0]['count']
        
        # Get active sessions
        active_result = db.execute_query(
            "SELECT COUNT(*) as count FROM user_sessions WHERE is_active = 'Y' AND expires_at > CURRENT_TIMESTAMP"
        )
        active_sessions = active_result[0]['count']
        
        # Get expired sessions
        expired_sessions = total_sessions - active_sessions
        
        return SessionStatistics(
            total_sessions=total_sessions,
            active_sessions=active_sessions,
            expired_sessions=expired_sessions
        )
        
    except Exception as e:
        logger.error(f"Session statistics error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get session statistics"
        )

@router.post("/cleanup/sessions", response_model=MessageResponse)
async def cleanup_sessions(
    current_user: TokenData = Depends(require_full_access()),
    auth_service: AuthenticationService = Depends(get_auth_service)
):
    """
    Clean up expired sessions
    
    Manually triggers cleanup of expired user sessions.
    Requires full access permission.
    """
    try:
        auth_service.cleanup_expired_sessions()
        
        return MessageResponse(
            message="Expired sessions cleaned up successfully",
            success=True
        )
        
    except Exception as e:
        logger.error(f"Session cleanup error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cleanup sessions"
        )

# Additional endpoints for password management
@router.post("/change-password", response_model=MessageResponse)
async def change_password(
    password_request: ChangePasswordRequest,
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    auth_service: AuthenticationService = Depends(get_auth_service)
):
    """
    Change user password
    
    Allows authenticated users to change their own password.
    """
    try:
        # Verify current password
        user_data = auth_service.get_user_by_id(current_user.user_id)
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Verify current password (implementation needed)
        # This would require getting the stored password hash and verifying it
        
        # Hash new password
        new_password_hash = auth_service.hash_password(password_request.new_password)
        
        # Update password in database
        db = get_database_manager()
        db.execute_query(
            "UPDATE admin_users SET password_hash = :hash, updated_at = CURRENT_TIMESTAMP WHERE user_id = :user_id",
            {'hash': new_password_hash, 'user_id': current_user.user_id}
        )
        
        # Log password change
        log_audit_event(
            user_id=current_user.user_id,
            action="PASSWORD_CHANGE",
            resource="ADMIN_USERS",
            details={"user_id": current_user.user_id},
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            status="SUCCESS"
        )
        
        return MessageResponse(
            message="Password changed successfully",
            success=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Change password error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to change password"
        )
