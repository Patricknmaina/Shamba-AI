"""
User Interaction Logging Service for ShambaAI
Handles comprehensive logging of user interactions, page views, API requests, and errors
"""

import os
import json
import logging
import uuid
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from fastapi import Request, HTTPException
from pydantic import BaseModel

from ..database.connection import get_database_manager, log_audit_event
from ..models.auth import TokenData

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Interaction types
class InteractionType:
    """User interaction types"""
    ASK_QUESTION = "ASK_QUESTION"
    GET_INSIGHTS = "GET_INSIGHTS"
    VIEW_ABOUT = "VIEW_ABOUT"
    VIEW_ADMIN = "VIEW_ADMIN"
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    NAVIGATE = "NAVIGATE"
    SEARCH = "SEARCH"
    DOWNLOAD = "DOWNLOAD"
    UPLOAD = "UPLOAD"
    EXPORT = "EXPORT"
    SHARE = "SHARE"

# Page names
class PageName:
    """Page names for tracking"""
    HOME = "home"
    ABOUT = "about"
    ASK = "ask"
    INSIGHTS = "insights"
    ADMIN = "admin"
    LOGIN = "login"
    ERROR = "error"

# Feature categories
class FeatureCategory:
    """Feature categories for analytics"""
    AI = "AI"
    ANALYTICS = "Analytics"
    CONTENT = "Content"
    AUTHENTICATION = "Authentication"
    NAVIGATION = "Navigation"
    DATA_MANAGEMENT = "Data Management"
    REPORTING = "Reporting"

class UserLoggingService:
    """Service for logging user interactions and analytics"""
    
    def __init__(self):
        self.db = get_database_manager()
        self.enabled = self._is_logging_enabled()
    
    def _is_logging_enabled(self) -> bool:
        """Check if detailed logging is enabled"""
        try:
            config = self.db.execute_query(
                "SELECT config_value FROM system_config WHERE config_key = 'DETAILED_LOGGING'"
            )
            return config[0]['config_value'].lower() == 'true' if config else True
        except Exception:
            return True
    
    def _generate_id(self) -> str:
        """Generate a unique ID for logging"""
        return str(uuid.uuid4())
    
    def _get_client_info(self, request: Request) -> Dict[str, Any]:
        """Extract client information from request"""
        return {
            'ip_address': request.client.host if request.client else None,
            'user_agent': request.headers.get('user-agent'),
            'referrer': request.headers.get('referer'),
            'accept_language': request.headers.get('accept-language'),
            'accept_encoding': request.headers.get('accept-encoding')
        }
    
    def _get_session_id(self, request: Request) -> Optional[str]:
        """Get session ID from request headers or cookies"""
        # Try to get from Authorization header (JWT token)
        auth_header = request.headers.get('authorization')
        if auth_header and auth_header.startswith('Bearer '):
            # For now, we'll use a simple approach
            # In production, you'd decode the JWT to get session info
            return f"session_{hash(auth_header) % 1000000}"
        
        # Try to get from cookies
        session_cookie = request.cookies.get('session_id')
        if session_cookie:
            return session_cookie
        
        # Generate a temporary session ID
        return f"temp_{self._generate_id()[:8]}"
    
    def log_user_interaction(
        self,
        request: Request,
        interaction_type: str,
        page_name: str,
        action_name: str,
        user_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        input_data: Optional[Dict[str, Any]] = None,
        output_data: Optional[Dict[str, Any]] = None,
        response_time_ms: Optional[int] = None,
        success_status: bool = True,
        error_message: Optional[str] = None
    ) -> Optional[str]:
        """Log a user interaction"""
        if not self.enabled:
            return None
        
        try:
            interaction_id = self._generate_id()
            session_id = self._get_session_id(request)
            client_info = self._get_client_info(request)
            
            # Prepare data
            log_data = {
                'p_interaction_id': interaction_id,
                'p_user_id': user_id,
                'p_session_id': session_id,
                'p_interaction_type': interaction_type,
                'p_page_name': page_name,
                'p_action_name': action_name,
                'p_resource_type': resource_type,
                'p_resource_id': resource_id,
                'p_input_data': json.dumps(input_data) if input_data else None,
                'p_output_data': json.dumps(output_data) if output_data else None,
                'p_response_time_ms': response_time_ms,
                'p_success_status': 'Y' if success_status else 'N',
                'p_error_message': error_message,
                'p_ip_address': client_info['ip_address'],
                'p_user_agent': client_info['user_agent'],
                'p_referrer_url': client_info['referrer']
            }
            
            # Log using stored procedure
            self.db.execute_procedure('log_user_interaction', log_data)
            
            logger.info(f"Logged user interaction: {interaction_type} - {action_name}")
            return interaction_id
            
        except Exception as e:
            logger.error(f"Failed to log user interaction: {e}")
            return None
    
    def log_page_view(
        self,
        request: Request,
        page_name: str,
        user_id: Optional[str] = None,
        page_url: Optional[str] = None,
        page_title: Optional[str] = None,
        view_duration_seconds: Optional[int] = None,
        scroll_depth_pct: Optional[float] = None,
        elements_clicked: Optional[List[str]] = None,
        forms_interacted: Optional[List[str]] = None
    ) -> Optional[str]:
        """Log a page view"""
        if not self.enabled:
            return None
        
        try:
            view_id = self._generate_id()
            session_id = self._get_session_id(request)
            
            # Prepare data
            log_data = {
                'p_view_id': view_id,
                'p_session_id': session_id,
                'p_user_id': user_id,
                'p_page_name': page_name,
                'p_page_url': page_url or str(request.url),
                'p_page_title': page_title,
                'p_view_duration_seconds': view_duration_seconds,
                'p_scroll_depth_pct': scroll_depth_pct,
                'p_elements_clicked': json.dumps(elements_clicked) if elements_clicked else None,
                'p_forms_interacted': json.dumps(forms_interacted) if forms_interacted else None
            }
            
            # Log using stored procedure
            self.db.execute_procedure('log_page_view', log_data)
            
            logger.info(f"Logged page view: {page_name}")
            return view_id
            
        except Exception as e:
            logger.error(f"Failed to log page view: {e}")
            return None
    
    def log_api_request(
        self,
        request: Request,
        endpoint: str,
        method: str,
        user_id: Optional[str] = None,
        request_body: Optional[Dict[str, Any]] = None,
        response_status: int = 200,
        response_body: Optional[Dict[str, Any]] = None,
        response_time_ms: Optional[int] = None,
        request_size_bytes: Optional[int] = None,
        response_size_bytes: Optional[int] = None
    ) -> Optional[str]:
        """Log an API request"""
        if not self.enabled:
            return None
        
        try:
            request_id = self._generate_id()
            session_id = self._get_session_id(request)
            client_info = self._get_client_info(request)
            
            # Prepare headers (excluding sensitive information)
            request_headers = dict(request.headers)
            if 'authorization' in request_headers:
                request_headers['authorization'] = 'Bearer [REDACTED]'
            if 'cookie' in request_headers:
                request_headers['cookie'] = '[REDACTED]'
            
            # Prepare response headers (if available)
            response_headers = {}
            
            # Prepare data
            log_data = {
                'p_request_id': request_id,
                'p_session_id': session_id,
                'p_user_id': user_id,
                'p_endpoint': endpoint,
                'p_method': method,
                'p_request_headers': json.dumps(request_headers),
                'p_request_body': json.dumps(request_body) if request_body else None,
                'p_response_status': response_status,
                'p_response_headers': json.dumps(response_headers),
                'p_response_body': json.dumps(response_body) if response_body else None,
                'p_response_time_ms': response_time_ms,
                'p_request_size_bytes': request_size_bytes,
                'p_response_size_bytes': response_size_bytes,
                'p_ip_address': client_info['ip_address'],
                'p_user_agent': client_info['user_agent']
            }
            
            # Log using stored procedure
            self.db.execute_procedure('log_api_request', log_data)
            
            logger.info(f"Logged API request: {method} {endpoint} - {response_status}")
            return request_id
            
        except Exception as e:
            logger.error(f"Failed to log API request: {e}")
            return None
    
    def log_error(
        self,
        request: Request,
        error_type: str,
        error_category: str,
        error_message: str,
        user_id: Optional[str] = None,
        error_stack: Optional[str] = None,
        error_source: str = "backend",
        user_action: Optional[str] = None,
        browser_info: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """Log an error"""
        try:
            error_id = self._generate_id()
            session_id = self._get_session_id(request)
            client_info = self._get_client_info(request)
            
            # Prepare browser info
            if not browser_info:
                browser_info = {
                    'user_agent': client_info['user_agent'],
                    'accept_language': client_info['accept_language'],
                    'accept_encoding': client_info['accept_encoding']
                }
            
            # Prepare data
            log_data = {
                'p_error_id': error_id,
                'p_session_id': session_id,
                'p_user_id': user_id,
                'p_error_type': error_type,
                'p_error_category': error_category,
                'p_error_message': error_message,
                'p_error_stack': error_stack,
                'p_error_source': error_source,
                'p_page_url': str(request.url),
                'p_user_action': user_action,
                'p_browser_info': json.dumps(browser_info)
            }
            
            # Log using stored procedure
            self.db.execute_procedure('log_error', log_data)
            
            logger.error(f"Logged error: {error_type} - {error_message}")
            return error_id
            
        except Exception as e:
            logger.error(f"Failed to log error: {e}")
            return None
    
    def log_feature_usage(
        self,
        session_id: str,
        feature_name: str,
        feature_category: str,
        user_id: Optional[str] = None,
        success: bool = True,
        time_spent_seconds: Optional[int] = None,
        error_count: int = 0
    ) -> Optional[str]:
        """Log feature usage statistics"""
        if not self.enabled:
            return None
        
        try:
            # Check if feature usage record exists
            existing = self.db.execute_query(
                "SELECT usage_id, usage_count, success_rate, error_count FROM feature_usage WHERE session_id = :session_id AND feature_name = :feature_name",
                {'session_id': session_id, 'feature_name': feature_name}
            )
            
            if existing:
                # Update existing record
                usage_id = existing[0]['usage_id']
                current_count = existing[0]['usage_count']
                current_success_rate = existing[0]['success_rate']
                current_error_count = existing[0]['error_count']
                
                new_count = current_count + 1
                new_error_count = current_error_count + (0 if success else 1)
                new_success_rate = ((current_success_rate * current_count) + (100 if success else 0)) / new_count
                
                self.db.execute_query(
                    """
                    UPDATE feature_usage 
                    SET usage_count = :count, success_rate = :success_rate, error_count = :error_count,
                        last_used = CURRENT_TIMESTAMP,
                        total_time_spent_seconds = total_time_spent_seconds + :time_spent
                    WHERE usage_id = :usage_id
                    """,
                    {
                        'count': new_count,
                        'success_rate': new_success_rate,
                        'error_count': new_error_count,
                        'time_spent': time_spent_seconds or 0,
                        'usage_id': usage_id
                    }
                )
            else:
                # Create new record
                usage_id = self._generate_id()
                success_rate = 100.0 if success else 0.0
                
                self.db.execute_query(
                    """
                    INSERT INTO feature_usage (usage_id, session_id, user_id, feature_name, feature_category,
                                             usage_count, success_rate, error_count, total_time_spent_seconds,
                                             first_used, last_used, created_at, updated_at)
                    VALUES (:usage_id, :session_id, :user_id, :feature_name, :feature_category,
                           :count, :success_rate, :error_count, :time_spent,
                           CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    """,
                    {
                        'usage_id': usage_id,
                        'session_id': session_id,
                        'user_id': user_id,
                        'feature_name': feature_name,
                        'feature_category': feature_category,
                        'count': 1,
                        'success_rate': success_rate,
                        'error_count': 0 if success else 1,
                        'time_spent': time_spent_seconds or 0
                    }
                )
            
            logger.info(f"Logged feature usage: {feature_name}")
            return usage_id
            
        except Exception as e:
            logger.error(f"Failed to log feature usage: {e}")
            return None
    
    def get_user_analytics(
        self,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get user analytics data"""
        try:
            since_date = datetime.now() - timedelta(days=days)
            
            # Base query conditions
            where_conditions = ["timestamp >= :since_date"]
            params = {'since_date': since_date}
            
            if user_id:
                where_conditions.append("user_id = :user_id")
                params['user_id'] = user_id
            
            if session_id:
                where_conditions.append("session_id = :session_id")
                params['session_id'] = session_id
            
            where_clause = " AND ".join(where_conditions)
            
            # Get interaction summary
            interactions = self.db.execute_query(
                f"""
                SELECT 
                    interaction_type,
                    COUNT(*) as count,
                    AVG(response_time_ms) as avg_response_time,
                    COUNT(CASE WHEN success_status = 'Y' THEN 1 END) as success_count
                FROM user_interactions 
                WHERE {where_clause}
                GROUP BY interaction_type
                ORDER BY count DESC
                """,
                params
            )
            
            # Get page views
            page_views = self.db.execute_query(
                f"""
                SELECT 
                    page_name,
                    COUNT(*) as views,
                    AVG(view_duration_seconds) as avg_duration,
                    AVG(scroll_depth_pct) as avg_scroll_depth
                FROM page_views 
                WHERE {where_clause}
                GROUP BY page_name
                ORDER BY views DESC
                """,
                params
            )
            
            # Get feature usage
            feature_usage = self.db.execute_query(
                f"""
                SELECT 
                    feature_name,
                    feature_category,
                    SUM(usage_count) as total_usage,
                    AVG(success_rate) as avg_success_rate,
                    SUM(error_count) as total_errors
                FROM feature_usage 
                WHERE {where_clause}
                GROUP BY feature_name, feature_category
                ORDER BY total_usage DESC
                """,
                params
            )
            
            return {
                'interactions': interactions,
                'page_views': page_views,
                'feature_usage': feature_usage,
                'period_days': days,
                'since_date': since_date.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get user analytics: {e}")
            return {}
    
    def get_system_analytics(self, days: int = 7) -> Dict[str, Any]:
        """Get system-wide analytics"""
        try:
            # Use the views we created
            daily_summary = self.db.execute_query(
                "SELECT * FROM daily_interaction_summary WHERE interaction_date >= CURRENT_DATE - :days ORDER BY interaction_date DESC",
                {'days': days}
            )
            
            feature_stats = self.db.execute_query(
                "SELECT * FROM feature_usage_stats ORDER BY total_usage DESC"
            )
            
            page_analytics = self.db.execute_query(
                "SELECT * FROM page_analytics ORDER BY total_views DESC"
            )
            
            api_performance = self.db.execute_query(
                "SELECT * FROM api_performance ORDER BY total_requests DESC"
            )
            
            error_summary = self.db.execute_query(
                "SELECT * FROM error_summary ORDER BY error_count DESC"
            )
            
            return {
                'daily_summary': daily_summary,
                'feature_stats': feature_stats,
                'page_analytics': page_analytics,
                'api_performance': api_performance,
                'error_summary': error_summary,
                'period_days': days
            }
            
        except Exception as e:
            logger.error(f"Failed to get system analytics: {e}")
            return {}
    
    def cleanup_old_logs(self) -> bool:
        """Clean up old log entries"""
        try:
            self.db.execute_procedure('cleanup_old_logs')
            logger.info("Successfully cleaned up old logs")
            return True
        except Exception as e:
            logger.error(f"Failed to cleanup old logs: {e}")
            return False

# Global logging service instance
logging_service = UserLoggingService()

# Convenience functions for easy access
def log_interaction(
    request: Request,
    interaction_type: str,
    page_name: str,
    action_name: str,
    user_id: Optional[str] = None,
    **kwargs
) -> Optional[str]:
    """Log a user interaction"""
    return logging_service.log_user_interaction(
        request, interaction_type, page_name, action_name, user_id, **kwargs
    )

def log_page_view(
    request: Request,
    page_name: str,
    user_id: Optional[str] = None,
    **kwargs
) -> Optional[str]:
    """Log a page view"""
    return logging_service.log_page_view(
        request, page_name, user_id, **kwargs
    )

def log_api_request(
    request: Request,
    endpoint: str,
    method: str,
    user_id: Optional[str] = None,
    **kwargs
) -> Optional[str]:
    """Log an API request"""
    return logging_service.log_api_request(
        request, endpoint, method, user_id, **kwargs
    )

def log_error(
    request: Request,
    error_type: str,
    error_category: str,
    error_message: str,
    user_id: Optional[str] = None,
    **kwargs
) -> Optional[str]:
    """Log an error"""
    return logging_service.log_error(
        request, error_type, error_category, error_message, user_id, **kwargs
    )

def get_user_analytics(user_id: Optional[str] = None, **kwargs) -> Dict[str, Any]:
    """Get user analytics"""
    return logging_service.get_user_analytics(user_id, **kwargs)

def get_system_analytics(**kwargs) -> Dict[str, Any]:
    """Get system analytics"""
    return logging_service.get_system_analytics(**kwargs)
