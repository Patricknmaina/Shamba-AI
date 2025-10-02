"""
User Logs API endpoints for ShambaAI
Administrative endpoints for viewing and managing user interaction logs
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from fastapi.responses import JSONResponse

from ..models.auth import MessageResponse, ErrorResponse
from ..services.auth_service import get_current_user, require_permission, Permission
from ..services.logging_service import (
    get_logging_service, UserLoggingService, get_user_analytics, get_system_analytics
)
from ..database.connection import get_database_manager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/logs", tags=["User Logs"])

# Pydantic models for responses
from pydantic import BaseModel

class UserInteractionLog(BaseModel):
    """User interaction log model"""
    interaction_id: str
    user_id: Optional[str]
    session_id: str
    interaction_type: str
    page_name: str
    action_name: str
    resource_type: Optional[str]
    resource_id: Optional[str]
    response_time_ms: Optional[int]
    success_status: str
    error_message: Optional[str]
    ip_address: Optional[str]
    timestamp: datetime

class PageViewLog(BaseModel):
    """Page view log model"""
    view_id: str
    session_id: str
    user_id: Optional[str]
    page_name: str
    page_url: Optional[str]
    page_title: Optional[str]
    view_duration_seconds: Optional[int]
    scroll_depth_pct: Optional[float]
    timestamp: datetime

class FeatureUsageLog(BaseModel):
    """Feature usage log model"""
    usage_id: str
    session_id: str
    user_id: Optional[str]
    feature_name: str
    feature_category: str
    usage_count: int
    success_rate: float
    total_errors: int
    last_used: datetime

class APIRequestLog(BaseModel):
    """API request log model"""
    request_id: str
    session_id: str
    user_id: Optional[str]
    endpoint: str
    method: str
    response_status: int
    response_time_ms: Optional[int]
    request_size_bytes: Optional[int]
    response_size_bytes: Optional[int]
    timestamp: datetime

class ErrorLog(BaseModel):
    """Error log model"""
    error_id: str
    session_id: str
    user_id: Optional[str]
    error_type: str
    error_category: str
    error_message: str
    error_source: str
    page_url: Optional[str]
    timestamp: datetime

class AnalyticsSummary(BaseModel):
    """Analytics summary model"""
    total_interactions: int
    unique_sessions: int
    unique_users: int
    avg_response_time_ms: float
    success_rate: float
    error_count: int

@router.get("/interactions", response_model=List[UserInteractionLog])
async def get_user_interactions(
    request: Request,
    days: int = Query(7, ge=1, le=365, description="Number of days to retrieve"),
    user_id: Optional[str] = Query(None, description="Filter by specific user ID"),
    session_id: Optional[str] = Query(None, description="Filter by specific session ID"),
    interaction_type: Optional[str] = Query(None, description="Filter by interaction type"),
    page_name: Optional[str] = Query(None, description="Filter by page name"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    offset: int = Query(0, ge=0, description="Number of records to skip"),
    current_user = Depends(require_permission(Permission.VIEW_LOGS))
):
    """
    Get user interaction logs
    
    Retrieves user interaction logs with optional filtering.
    Requires view_logs permission.
    """
    try:
        db = get_database_manager()
        since_date = datetime.now() - timedelta(days=days)
        
        # Build query conditions
        where_conditions = ["timestamp >= :since_date"]
        params = {'since_date': since_date, 'limit': limit, 'offset': offset}
        
        if user_id:
            where_conditions.append("user_id = :user_id")
            params['user_id'] = user_id
        
        if session_id:
            where_conditions.append("session_id = :session_id")
            params['session_id'] = session_id
        
        if interaction_type:
            where_conditions.append("interaction_type = :interaction_type")
            params['interaction_type'] = interaction_type
        
        if page_name:
            where_conditions.append("page_name = :page_name")
            params['page_name'] = page_name
        
        where_clause = " AND ".join(where_conditions)
        
        # Execute query
        results = db.execute_query(
            f"""
            SELECT interaction_id, user_id, session_id, interaction_type, page_name, action_name,
                   resource_type, resource_id, response_time_ms, success_status, error_message,
                   ip_address, timestamp
            FROM user_interactions 
            WHERE {where_clause}
            ORDER BY timestamp DESC
            OFFSET :offset ROWS FETCH NEXT :limit ROWS ONLY
            """,
            params
        )
        
        # Convert to response models
        interactions = []
        for row in results:
            interactions.append(UserInteractionLog(
                interaction_id=row['interaction_id'],
                user_id=row['user_id'],
                session_id=row['session_id'],
                interaction_type=row['interaction_type'],
                page_name=row['page_name'],
                action_name=row['action_name'],
                resource_type=row['resource_type'],
                resource_id=row['resource_id'],
                response_time_ms=row['response_time_ms'],
                success_status=row['success_status'],
                error_message=row['error_message'],
                ip_address=row['ip_address'],
                timestamp=row['timestamp']
            ))
        
        return interactions
        
    except Exception as e:
        logger.error(f"Failed to get user interactions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user interactions"
        )

@router.get("/page-views", response_model=List[PageViewLog])
async def get_page_views(
    days: int = Query(7, ge=1, le=365, description="Number of days to retrieve"),
    user_id: Optional[str] = Query(None, description="Filter by specific user ID"),
    session_id: Optional[str] = Query(None, description="Filter by specific session ID"),
    page_name: Optional[str] = Query(None, description="Filter by page name"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    offset: int = Query(0, ge=0, description="Number of records to skip"),
    current_user = Depends(require_permission(Permission.VIEW_LOGS))
):
    """
    Get page view logs
    
    Retrieves page view analytics with optional filtering.
    Requires view_logs permission.
    """
    try:
        db = get_database_manager()
        since_date = datetime.now() - timedelta(days=days)
        
        # Build query conditions
        where_conditions = ["timestamp >= :since_date"]
        params = {'since_date': since_date, 'limit': limit, 'offset': offset}
        
        if user_id:
            where_conditions.append("user_id = :user_id")
            params['user_id'] = user_id
        
        if session_id:
            where_conditions.append("session_id = :session_id")
            params['session_id'] = session_id
        
        if page_name:
            where_conditions.append("page_name = :page_name")
            params['page_name'] = page_name
        
        where_clause = " AND ".join(where_conditions)
        
        # Execute query
        results = db.execute_query(
            f"""
            SELECT view_id, session_id, user_id, page_name, page_url, page_title,
                   view_duration_seconds, scroll_depth_pct, timestamp
            FROM page_views 
            WHERE {where_clause}
            ORDER BY timestamp DESC
            OFFSET :offset ROWS FETCH NEXT :limit ROWS ONLY
            """,
            params
        )
        
        # Convert to response models
        page_views = []
        for row in results:
            page_views.append(PageViewLog(
                view_id=row['view_id'],
                session_id=row['session_id'],
                user_id=row['user_id'],
                page_name=row['page_name'],
                page_url=row['page_url'],
                page_title=row['page_title'],
                view_duration_seconds=row['view_duration_seconds'],
                scroll_depth_pct=row['scroll_depth_pct'],
                timestamp=row['timestamp']
            ))
        
        return page_views
        
    except Exception as e:
        logger.error(f"Failed to get page views: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve page views"
        )

@router.get("/feature-usage", response_model=List[FeatureUsageLog])
async def get_feature_usage(
    days: int = Query(30, ge=1, le=365, description="Number of days to retrieve"),
    user_id: Optional[str] = Query(None, description="Filter by specific user ID"),
    feature_name: Optional[str] = Query(None, description="Filter by feature name"),
    feature_category: Optional[str] = Query(None, description="Filter by feature category"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    offset: int = Query(0, ge=0, description="Number of records to skip"),
    current_user = Depends(require_permission(Permission.VIEW_LOGS))
):
    """
    Get feature usage logs
    
    Retrieves feature usage statistics with optional filtering.
    Requires view_logs permission.
    """
    try:
        db = get_database_manager()
        since_date = datetime.now() - timedelta(days=days)
        
        # Build query conditions
        where_conditions = ["last_used >= :since_date"]
        params = {'since_date': since_date, 'limit': limit, 'offset': offset}
        
        if user_id:
            where_conditions.append("user_id = :user_id")
            params['user_id'] = user_id
        
        if feature_name:
            where_conditions.append("feature_name = :feature_name")
            params['feature_name'] = feature_name
        
        if feature_category:
            where_conditions.append("feature_category = :feature_category")
            params['feature_category'] = feature_category
        
        where_clause = " AND ".join(where_conditions)
        
        # Execute query
        results = db.execute_query(
            f"""
            SELECT usage_id, session_id, user_id, feature_name, feature_category,
                   usage_count, success_rate, error_count as total_errors, last_used
            FROM feature_usage 
            WHERE {where_clause}
            ORDER BY last_used DESC
            OFFSET :offset ROWS FETCH NEXT :limit ROWS ONLY
            """,
            params
        )
        
        # Convert to response models
        feature_usage = []
        for row in results:
            feature_usage.append(FeatureUsageLog(
                usage_id=row['usage_id'],
                session_id=row['session_id'],
                user_id=row['user_id'],
                feature_name=row['feature_name'],
                feature_category=row['feature_category'],
                usage_count=row['usage_count'],
                success_rate=float(row['success_rate']),
                total_errors=row['total_errors'],
                last_used=row['last_used']
            ))
        
        return feature_usage
        
    except Exception as e:
        logger.error(f"Failed to get feature usage: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve feature usage"
        )

@router.get("/api-requests", response_model=List[APIRequestLog])
async def get_api_requests(
    days: int = Query(7, ge=1, le=365, description="Number of days to retrieve"),
    user_id: Optional[str] = Query(None, description="Filter by specific user ID"),
    endpoint: Optional[str] = Query(None, description="Filter by endpoint"),
    method: Optional[str] = Query(None, description="Filter by HTTP method"),
    status_code: Optional[int] = Query(None, description="Filter by response status code"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    offset: int = Query(0, ge=0, description="Number of records to skip"),
    current_user = Depends(require_permission(Permission.VIEW_LOGS))
):
    """
    Get API request logs
    
    Retrieves API request logs with optional filtering.
    Requires view_logs permission.
    """
    try:
        db = get_database_manager()
        since_date = datetime.now() - timedelta(days=days)
        
        # Build query conditions
        where_conditions = ["timestamp >= :since_date"]
        params = {'since_date': since_date, 'limit': limit, 'offset': offset}
        
        if user_id:
            where_conditions.append("user_id = :user_id")
            params['user_id'] = user_id
        
        if endpoint:
            where_conditions.append("endpoint LIKE :endpoint")
            params['endpoint'] = f"%{endpoint}%"
        
        if method:
            where_conditions.append("method = :method")
            params['method'] = method
        
        if status_code:
            where_conditions.append("response_status = :status_code")
            params['status_code'] = status_code
        
        where_clause = " AND ".join(where_conditions)
        
        # Execute query
        results = db.execute_query(
            f"""
            SELECT request_id, session_id, user_id, endpoint, method, response_status,
                   response_time_ms, request_size_bytes, response_size_bytes, timestamp
            FROM api_requests 
            WHERE {where_clause}
            ORDER BY timestamp DESC
            OFFSET :offset ROWS FETCH NEXT :limit ROWS ONLY
            """,
            params
        )
        
        # Convert to response models
        api_requests = []
        for row in results:
            api_requests.append(APIRequestLog(
                request_id=row['request_id'],
                session_id=row['session_id'],
                user_id=row['user_id'],
                endpoint=row['endpoint'],
                method=row['method'],
                response_status=row['response_status'],
                response_time_ms=row['response_time_ms'],
                request_size_bytes=row['request_size_bytes'],
                response_size_bytes=row['response_size_bytes'],
                timestamp=row['timestamp']
            ))
        
        return api_requests
        
    except Exception as e:
        logger.error(f"Failed to get API requests: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve API requests"
        )

@router.get("/errors", response_model=List[ErrorLog])
async def get_error_logs(
    days: int = Query(7, ge=1, le=365, description="Number of days to retrieve"),
    user_id: Optional[str] = Query(None, description="Filter by specific user ID"),
    error_type: Optional[str] = Query(None, description="Filter by error type"),
    error_category: Optional[str] = Query(None, description="Filter by error category"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    offset: int = Query(0, ge=0, description="Number of records to skip"),
    current_user = Depends(require_permission(Permission.VIEW_LOGS))
):
    """
    Get error logs
    
    Retrieves error logs with optional filtering.
    Requires view_logs permission.
    """
    try:
        db = get_database_manager()
        since_date = datetime.now() - timedelta(days=days)
        
        # Build query conditions
        where_conditions = ["timestamp >= :since_date"]
        params = {'since_date': since_date, 'limit': limit, 'offset': offset}
        
        if user_id:
            where_conditions.append("user_id = :user_id")
            params['user_id'] = user_id
        
        if error_type:
            where_conditions.append("error_type = :error_type")
            params['error_type'] = error_type
        
        if error_category:
            where_conditions.append("error_category = :error_category")
            params['error_category'] = error_category
        
        where_clause = " AND ".join(where_conditions)
        
        # Execute query
        results = db.execute_query(
            f"""
            SELECT error_id, session_id, user_id, error_type, error_category, error_message,
                   error_source, page_url, timestamp
            FROM error_logs 
            WHERE {where_clause}
            ORDER BY timestamp DESC
            OFFSET :offset ROWS FETCH NEXT :limit ROWS ONLY
            """,
            params
        )
        
        # Convert to response models
        error_logs = []
        for row in results:
            error_logs.append(ErrorLog(
                error_id=row['error_id'],
                session_id=row['session_id'],
                user_id=row['user_id'],
                error_type=row['error_type'],
                error_category=row['error_category'],
                error_message=row['error_message'],
                error_source=row['error_source'],
                page_url=row['page_url'],
                timestamp=row['timestamp']
            ))
        
        return error_logs
        
    except Exception as e:
        logger.error(f"Failed to get error logs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve error logs"
        )

@router.get("/analytics/user/{user_id}", response_model=Dict[str, Any])
async def get_user_analytics_endpoint(
    user_id: str,
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    current_user = Depends(require_permission(Permission.VIEW_LOGS))
):
    """
    Get analytics for a specific user
    
    Retrieves comprehensive analytics for a specific user.
    Requires view_logs permission.
    """
    try:
        analytics = get_user_analytics(user_id=user_id, days=days)
        return analytics
        
    except Exception as e:
        logger.error(f"Failed to get user analytics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user analytics"
        )

@router.get("/analytics/system", response_model=Dict[str, Any])
async def get_system_analytics_endpoint(
    days: int = Query(7, ge=1, le=365, description="Number of days to analyze"),
    current_user = Depends(require_permission(Permission.VIEW_LOGS))
):
    """
    Get system-wide analytics
    
    Retrieves comprehensive system analytics.
    Requires view_logs permission.
    """
    try:
        analytics = get_system_analytics(days=days)
        return analytics
        
    except Exception as e:
        logger.error(f"Failed to get system analytics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve system analytics"
        )

@router.get("/analytics/summary", response_model=AnalyticsSummary)
async def get_analytics_summary(
    days: int = Query(7, ge=1, le=365, description="Number of days to summarize"),
    current_user = Depends(require_permission(Permission.VIEW_LOGS))
):
    """
    Get analytics summary
    
    Retrieves a summary of key analytics metrics.
    Requires view_logs permission.
    """
    try:
        db = get_database_manager()
        since_date = datetime.now() - timedelta(days=days)
        
        # Get summary data
        summary_data = db.execute_query(
            """
            SELECT 
                COUNT(*) as total_interactions,
                COUNT(DISTINCT session_id) as unique_sessions,
                COUNT(DISTINCT user_id) as unique_users,
                AVG(response_time_ms) as avg_response_time_ms,
                COUNT(CASE WHEN success_status = 'Y' THEN 1 END) as success_count,
                COUNT(CASE WHEN success_status = 'N' THEN 1 END) as error_count
            FROM user_interactions 
            WHERE timestamp >= :since_date
            """,
            {'since_date': since_date}
        )
        
        if not summary_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No analytics data found"
            )
        
        data = summary_data[0]
        total_interactions = data['total_interactions'] or 0
        success_count = data['success_count'] or 0
        
        summary = AnalyticsSummary(
            total_interactions=total_interactions,
            unique_sessions=data['unique_sessions'] or 0,
            unique_users=data['unique_users'] or 0,
            avg_response_time_ms=float(data['avg_response_time_ms'] or 0),
            success_rate=(success_count / total_interactions * 100) if total_interactions > 0 else 0,
            error_count=data['error_count'] or 0
        )
        
        return summary
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get analytics summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve analytics summary"
        )

@router.post("/cleanup", response_model=MessageResponse)
async def cleanup_logs(
    current_user = Depends(require_permission(Permission.SYSTEM_HEALTH))
):
    """
    Clean up old log entries
    
    Manually triggers cleanup of old log entries.
    Requires system_health permission.
    """
    try:
        logging_service = get_logging_service()
        success = logging_service.cleanup_old_logs()
        
        if success:
            return MessageResponse(
                message="Log cleanup completed successfully",
                success=True
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Log cleanup failed"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Log cleanup error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cleanup logs"
        )

@router.get("/export", response_class=JSONResponse)
async def export_logs(
    log_type: str = Query(..., description="Type of logs to export (interactions, page_views, api_requests, errors)"),
    days: int = Query(30, ge=1, le=365, description="Number of days to export"),
    format: str = Query("json", description="Export format (json, csv)"),
    current_user = Depends(require_permission(Permission.VIEW_LOGS))
):
    """
    Export logs
    
    Exports logs in specified format.
    Requires view_logs permission.
    """
    try:
        db = get_database_manager()
        since_date = datetime.now() - timedelta(days=days)
        
        # Determine table and columns based on log type
        table_configs = {
            'interactions': {
                'table': 'user_interactions',
                'columns': ['interaction_id', 'user_id', 'session_id', 'interaction_type', 'page_name', 'action_name', 'timestamp']
            },
            'page_views': {
                'table': 'page_views',
                'columns': ['view_id', 'session_id', 'user_id', 'page_name', 'page_url', 'timestamp']
            },
            'api_requests': {
                'table': 'api_requests',
                'columns': ['request_id', 'session_id', 'user_id', 'endpoint', 'method', 'response_status', 'timestamp']
            },
            'errors': {
                'table': 'error_logs',
                'columns': ['error_id', 'session_id', 'user_id', 'error_type', 'error_category', 'error_message', 'timestamp']
            }
        }
        
        if log_type not in table_configs:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid log type. Must be one of: {', '.join(table_configs.keys())}"
            )
        
        config = table_configs[log_type]
        columns_str = ', '.join(config['columns'])
        
        # Get data
        results = db.execute_query(
            f"""
            SELECT {columns_str}
            FROM {config['table']}
            WHERE timestamp >= :since_date
            ORDER BY timestamp DESC
            """,
            {'since_date': since_date}
        )
        
        if format.lower() == 'csv':
            # Generate CSV
            import csv
            import io
            
            output = io.StringIO()
            if results:
                writer = csv.DictWriter(output, fieldnames=config['columns'])
                writer.writeheader()
                writer.writerows(results)
            
            csv_content = output.getvalue()
            output.close()
            
            return JSONResponse(
                content={"csv_data": csv_content},
                headers={"Content-Type": "application/json"}
            )
        else:
            # Return JSON
            return JSONResponse(content=results)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to export logs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export logs"
        )
