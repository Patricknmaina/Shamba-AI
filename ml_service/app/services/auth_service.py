"""
Authentication Service for ShambaAI
Handles admin authentication, session management, and user operations
"""

import os
import json
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from ..database.connection import (
    get_database_manager, authenticate_user, create_admin_user,
    log_audit_event, cleanup_expired_sessions
)
from ..models.auth import (
    AdminUserCreate, AdminUserUpdate, AdminUserResponse, LoginRequest,
    LoginResponse, SessionResponse, AuditLogCreate, UserRole, Permission,
    TokenData, AdminUserDetail, ChangePasswordRequest, PasswordResetRequest,
    PasswordResetConfirm, SystemConfigResponse
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))  # 24 hours

# Security
security = HTTPBearer()

class AuthenticationService:
    """Authentication service for admin users"""
    
    def __init__(self):
        self.db = get_database_manager()
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        try:
            # Try database hashing first
            db_hash = self.db.execute_function('hash_password', {'p_password': plain_password})
            return db_hash == hashed_password
        except Exception:
            # Fallback to Python hashing
            return pwd_context.verify(plain_password, hashed_password)
    
    def hash_password(self, password: str) -> str:
        """Hash a password"""
        try:
            # Try database hashing first
            return self.db.execute_function('hash_password', {'p_password': password})
        except Exception:
            # Fallback to Python hashing
            return pwd_context.hash(password)
    
    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[TokenData]:
        """Verify JWT token and return token data"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id: str = payload.get("sub")
            if user_id is None:
                return None
            
            # Get user details from database
            user_data = self.get_user_by_id(user_id)
            if not user_data:
                return None
            
            token_data = TokenData(
                user_id=user_id,
                username=user_data.get('username'),
                permissions=self._parse_permissions(user_data.get('permissions', '[]'))
            )
            return token_data
            
        except JWTError:
            return None
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate user with username and password"""
        try:
            # Use database authentication function
            user_id = authenticate_user(username, password)
            if not user_id:
                return None
            
            # Get user details
            user_data = self.get_user_by_id(user_id)
            return user_data
            
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return None
    
    def login(self, login_request: LoginRequest, ip_address: Optional[str] = None,
              user_agent: Optional[str] = None) -> LoginResponse:
        """Perform user login"""
        # Authenticate user
        user_data = self.authenticate_user(login_request.username, login_request.password)
        if not user_data:
            # Log failed login attempt
            log_audit_event(
                user_id=None,
                action="LOGIN_FAILED",
                resource="AUTHENTICATION",
                details={"username": login_request.username, "reason": "invalid_credentials"},
                ip_address=ip_address,
                user_agent=user_agent,
                status="FAILED"
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Check if account is active
        if user_data.get('is_active') != 'Y':
            log_audit_event(
                user_id=user_data.get('user_id'),
                action="LOGIN_FAILED",
                resource="AUTHENTICATION",
                details={"username": login_request.username, "reason": "account_inactive"},
                ip_address=ip_address,
                user_agent=user_agent,
                status="FAILED"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is inactive"
            )
        
        # Check if account is locked
        if user_data.get('account_locked_until'):
            lock_until = datetime.fromisoformat(user_data['account_locked_until'].replace('Z', '+00:00'))
            if lock_until > datetime.now():
                log_audit_event(
                    user_id=user_data.get('user_id'),
                    action="LOGIN_FAILED",
                    resource="AUTHENTICATION",
                    details={"username": login_request.username, "reason": "account_locked"},
                    ip_address=ip_address,
                    user_agent=user_agent,
                    status="FAILED"
                )
                raise HTTPException(
                    status_code=status.HTTP_423_LOCKED,
                    detail="Account is temporarily locked due to failed login attempts"
                )
        
        # Create access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = self.create_access_token(
            data={"sub": user_data['user_id'], "username": user_data['username']},
            expires_delta=access_token_expires
        )
        
        # Create session
        session_data = self.create_session(
            user_id=user_data['user_id'],
            ip_address=ip_address,
            user_agent=user_agent,
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES
        )
        
        # Log successful login
        log_audit_event(
            user_id=user_data['user_id'],
            action="LOGIN_SUCCESS",
            resource="AUTHENTICATION",
            details={"username": login_request.username, "session_id": session_data['session_id']},
            ip_address=ip_address,
            user_agent=user_agent,
            status="SUCCESS"
        )
        
        # Convert user data to response model
        user_response = AdminUserResponse(
            user_id=user_data['user_id'],
            username=user_data['username'],
            email=user_data['email'],
            full_name=user_data['full_name'],
            role=user_data['role'],
            permissions=self._parse_permissions(user_data.get('permissions', '[]')),
            is_active=user_data['is_active'],
            created_at=datetime.fromisoformat(user_data['created_at'].replace('Z', '+00:00')),
            updated_at=datetime.fromisoformat(user_data['updated_at'].replace('Z', '+00:00')),
            last_login=datetime.fromisoformat(user_data['last_login'].replace('Z', '+00:00')) if user_data.get('last_login') else None,
            failed_login_attempts=user_data.get('failed_login_attempts', 0),
            account_locked_until=datetime.fromisoformat(user_data['account_locked_until'].replace('Z', '+00:00')) if user_data.get('account_locked_until') else None
        )
        
        return LoginResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=user_response
        )
    
    def logout(self, user_id: str, session_token: Optional[str] = None,
               ip_address: Optional[str] = None, user_agent: Optional[str] = None):
        """Perform user logout"""
        try:
            # Deactivate session
            if session_token:
                self.db.execute_query(
                    "UPDATE user_sessions SET is_active = 'N' WHERE session_token = :token AND user_id = :user_id",
                    {'token': session_token, 'user_id': user_id}
                )
            else:
                # Deactivate all active sessions for user
                self.db.execute_query(
                    "UPDATE user_sessions SET is_active = 'N' WHERE user_id = :user_id AND is_active = 'Y'",
                    {'user_id': user_id}
                )
            
            # Log logout
            log_audit_event(
                user_id=user_id,
                action="LOGOUT",
                resource="AUTHENTICATION",
                details={"session_token": session_token},
                ip_address=ip_address,
                user_agent=user_agent,
                status="SUCCESS"
            )
            
        except Exception as e:
            logger.error(f"Logout error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Logout failed"
            )
    
    def create_session(self, user_id: str, ip_address: Optional[str] = None,
                      user_agent: Optional[str] = None, expires_in: int = 1440) -> Dict[str, Any]:
        """Create a new user session"""
        try:
            import uuid
            session_id = str(uuid.uuid4())
            session_token = str(uuid.uuid4())
            expires_at = datetime.now() + timedelta(minutes=expires_in)
            
            session_data = {
                'session_id': session_id,
                'user_id': user_id,
                'session_token': session_token,
                'ip_address': ip_address,
                'user_agent': user_agent,
                'expires_at': expires_at,
                'created_at': datetime.now(),
                'is_active': 'Y',
                'last_activity': datetime.now()
            }
            
            self.db.execute_query(
                """
                INSERT INTO user_sessions (session_id, user_id, session_token, ip_address, 
                                         user_agent, expires_at, created_at, is_active, last_activity)
                VALUES (:session_id, :user_id, :session_token, :ip_address, 
                       :user_agent, :expires_at, :created_at, :is_active, :last_activity)
                """,
                session_data
            )
            
            return session_data
            
        except Exception as e:
            logger.error(f"Session creation error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Session creation failed"
            )
    
    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        try:
            results = self.db.execute_query(
                "SELECT * FROM admin_users WHERE user_id = :user_id",
                {'user_id': user_id}
            )
            return results[0] if results else None
        except Exception as e:
            logger.error(f"Get user error: {e}")
            return None
    
    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user by username"""
        try:
            results = self.db.execute_query(
                "SELECT * FROM admin_users WHERE username = :username",
                {'username': username}
            )
            return results[0] if results else None
        except Exception as e:
            logger.error(f"Get user error: {e}")
            return None
    
    def create_admin_user(self, user_create: AdminUserCreate, created_by: str) -> AdminUserResponse:
        """Create a new admin user"""
        try:
            import uuid
            user_id = str(uuid.uuid4())
            
            user_data = {
                'p_user_id': user_id,
                'p_username': user_create.username,
                'p_password': user_create.password,
                'p_email': user_create.email,
                'p_full_name': user_create.full_name,
                'p_role': user_create.role.value,
                'p_permissions': json.dumps([p.value for p in user_create.permissions]),
                'p_created_by': created_by
            }
            
            # Create user using database procedure
            self.db.execute_procedure('create_admin_user', user_data)
            
            # Get created user
            user = self.get_user_by_id(user_id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to retrieve created user"
                )
            
            return AdminUserResponse(
                user_id=user['user_id'],
                username=user['username'],
                email=user['email'],
                full_name=user['full_name'],
                role=user['role'],
                permissions=self._parse_permissions(user.get('permissions', '[]')),
                is_active=user['is_active'],
                created_at=datetime.fromisoformat(user['created_at'].replace('Z', '+00:00')),
                updated_at=datetime.fromisoformat(user['updated_at'].replace('Z', '+00:00')),
                last_login=None,
                failed_login_attempts=0,
                account_locked_until=None
            )
            
        except Exception as e:
            logger.error(f"Create user error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create user: {str(e)}"
            )
    
    def get_current_user(self, credentials: HTTPAuthorizationCredentials = Depends(security)) -> TokenData:
        """Get current authenticated user from token"""
        try:
            token = credentials.credentials
            token_data = self.verify_token(token)
            if token_data is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Could not validate credentials",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            return token_data
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Get current user error: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    def has_permission(self, user_permissions: List[Permission], required_permission: Permission) -> bool:
        """Check if user has required permission"""
        return required_permission in user_permissions or Permission.FULL_ACCESS in user_permissions
    
    def require_permission(self, required_permission: Permission):
        """Decorator to require specific permission"""
        def permission_checker(current_user: TokenData = Depends(self.get_current_user)):
            if not self.has_permission(current_user.permissions or [], required_permission):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions"
                )
            return current_user
        return permission_checker
    
    def cleanup_expired_sessions(self):
        """Clean up expired sessions"""
        try:
            cleanup_expired_sessions()
        except Exception as e:
            logger.error(f"Session cleanup error: {e}")
    
    def _parse_permissions(self, permissions_json: str) -> List[Permission]:
        """Parse permissions from JSON string"""
        try:
            if not permissions_json:
                return []
            permissions_list = json.loads(permissions_json)
            return [Permission(p) for p in permissions_list if p in [p.value for p in Permission]]
        except Exception:
            return []

# Global authentication service instance
auth_service = AuthenticationService()

# Dependency functions
def get_auth_service() -> AuthenticationService:
    """Get authentication service instance"""
    return auth_service

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> TokenData:
    """Get current authenticated user"""
    return auth_service.get_current_user(credentials)

def require_permission(permission: Permission):
    """Require specific permission"""
    return auth_service.require_permission(permission)

def require_full_access():
    """Require full access permission"""
    return require_permission(Permission.FULL_ACCESS)
