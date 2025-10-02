"""
Oracle Database Connection Management for ShambaAI
Handles connections to Oracle Autonomous Database
"""

import os
import logging
from typing import Optional, Dict, Any
from contextlib import contextmanager
import cx_Oracle
from cx_Oracle import Connection, Cursor
import json
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseConfig:
    """Database configuration management"""
    
    def __init__(self):
        self.host = os.getenv('DB_HOST', 'localhost')
        self.port = os.getenv('DB_PORT', '1521')
        self.service_name = os.getenv('DB_SERVICE_NAME', 'XE')
        self.username = os.getenv('DB_USERNAME', 'shamba_app')
        self.password = os.getenv('DB_PASSWORD', 'ShambaAI_DB_2024!')
        self.wallet_location = os.getenv('WALLET_LOCATION', '/opt/oracle/wallet')
        self.connection_string = os.getenv('DB_CONNECTION_STRING')
        
        # Pool configuration
        self.pool_min_size = int(os.getenv('DB_POOL_MIN_SIZE', '5'))
        self.pool_max_size = int(os.getenv('DB_POOL_MAX_SIZE', '20'))
        self.pool_increment = int(os.getenv('DB_POOL_INCREMENT', '2'))
        
        # SSL Configuration
        self.ssl_enabled = os.getenv('SSL_ENABLED', 'true').lower() == 'true'
        self.ssl_verify = os.getenv('SSL_VERIFY', 'true').lower() == 'true'
    
    def get_connection_string(self) -> str:
        """Get the appropriate connection string based on configuration"""
        if self.connection_string:
            return self.connection_string
        
        if self.ssl_enabled:
            # For Oracle Autonomous Database with SSL
            return f"{self.host}:{self.port}/{self.service_name}?TNS_ADMIN={self.wallet_location}"
        else:
            # For local Oracle database
            return f"{self.host}:{self.port}/{self.service_name}"
    
    def get_dsn(self) -> str:
        """Get DSN for connection pool"""
        return cx_Oracle.makedsn(
            self.host,
            self.port,
            service_name=self.service_name
        )

class DatabaseManager:
    """Oracle Database connection manager"""
    
    def __init__(self, config: Optional[DatabaseConfig] = None):
        self.config = config or DatabaseConfig()
        self.pool = None
        self._initialize_pool()
    
    def _initialize_pool(self):
        """Initialize connection pool"""
        try:
            if self.ssl_enabled:
                # For Oracle Autonomous Database
                self.pool = cx_Oracle.SessionPool(
                    user=self.config.username,
                    password=self.config.password,
                    dsn=self.config.get_connection_string(),
                    min=self.config.pool_min_size,
                    max=self.config.pool_max_size,
                    increment=self.config.pool_increment,
                    encoding="UTF-8",
                    threaded=True
                )
            else:
                # For local Oracle database
                self.pool = cx_Oracle.SessionPool(
                    user=self.config.username,
                    password=self.config.password,
                    dsn=self.config.get_dsn(),
                    min=self.config.pool_min_size,
                    max=self.config.pool_max_size,
                    increment=self.config.pool_increment,
                    encoding="UTF-8",
                    threaded=True
                )
            
            logger.info("Database connection pool initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database pool: {e}")
            raise
    
    @contextmanager
    def get_connection(self):
        """Get a connection from the pool"""
        connection = None
        try:
            connection = self.pool.acquire()
            yield connection
        except Exception as e:
            logger.error(f"Database connection error: {e}")
            if connection:
                connection.rollback()
            raise
        finally:
            if connection:
                self.pool.release(connection)
    
    @contextmanager
    def get_cursor(self):
        """Get a cursor from the pool"""
        with self.get_connection() as connection:
            cursor = connection.cursor()
            try:
                yield cursor
            finally:
                cursor.close()
    
    def execute_query(self, query: str, params: Optional[Dict] = None) -> list:
        """Execute a SELECT query and return results"""
        try:
            with self.get_cursor() as cursor:
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                
                # Get column names
                columns = [desc[0] for desc in cursor.description]
                
                # Fetch all results
                results = cursor.fetchall()
                
                # Convert to list of dictionaries
                return [dict(zip(columns, row)) for row in results]
                
        except Exception as e:
            logger.error(f"Query execution error: {e}")
            raise
    
    def execute_procedure(self, procedure_name: str, params: Optional[Dict] = None) -> Any:
        """Execute a stored procedure"""
        try:
            with self.get_cursor() as cursor:
                if params:
                    result = cursor.callproc(procedure_name, list(params.values()))
                else:
                    result = cursor.callproc(procedure_name)
                
                return result
                
        except Exception as e:
            logger.error(f"Procedure execution error: {e}")
            raise
    
    def execute_function(self, function_name: str, params: Optional[Dict] = None) -> Any:
        """Execute a stored function"""
        try:
            with self.get_cursor() as cursor:
                if params:
                    result = cursor.callfunc(function_name, cx_Oracle.STRING, list(params.values()))
                else:
                    result = cursor.callfunc(function_name, cx_Oracle.STRING)
                
                return result
                
        except Exception as e:
            logger.error(f"Function execution error: {e}")
            raise
    
    def test_connection(self) -> Dict[str, Any]:
        """Test database connection and return status"""
        try:
            with self.get_cursor() as cursor:
                # Test basic connectivity
                cursor.execute("SELECT COUNT(*) FROM admin_users")
                admin_count = cursor.fetchone()[0]
                
                # Get database version
                cursor.execute("SELECT BANNER FROM v$version WHERE ROWNUM = 1")
                version = cursor.fetchone()[0]
                
                return {
                    "status": "success",
                    "admin_users_count": admin_count,
                    "database_version": version,
                    "timestamp": datetime.now().isoformat(),
                    "pool_size": self.pool.opened if hasattr(self.pool, 'opened') else 'unknown'
                }
                
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def close_pool(self):
        """Close the connection pool"""
        if self.pool:
            self.pool.close()
            logger.info("Database connection pool closed")

# Global database manager instance
db_manager: Optional[DatabaseManager] = None

def get_database_manager() -> DatabaseManager:
    """Get the global database manager instance"""
    global db_manager
    if db_manager is None:
        db_manager = DatabaseManager()
    return db_manager

def initialize_database():
    """Initialize the database connection"""
    global db_manager
    try:
        db_manager = DatabaseManager()
        logger.info("Database initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        return False

def close_database():
    """Close the database connection"""
    global db_manager
    if db_manager:
        db_manager.close_pool()
        db_manager = None
        logger.info("Database connection closed")

# Utility functions for common database operations
def hash_password(password: str) -> str:
    """Hash a password using database function"""
    try:
        db = get_database_manager()
        result = db.execute_function('hash_password', {'p_password': password})
        return result
    except Exception as e:
        logger.error(f"Password hashing error: {e}")
        # Fallback to Python hashing if database function fails
        import hashlib
        return hashlib.sha256(password.encode()).hexdigest()

def authenticate_user(username: str, password: str) -> Optional[str]:
    """Authenticate user using database function"""
    try:
        db = get_database_manager()
        user_id = db.execute_function('authenticate_user', {
            'p_username': username,
            'p_password': password
        })
        return user_id if user_id else None
    except Exception as e:
        logger.error(f"User authentication error: {e}")
        return None

def create_admin_user(user_data: Dict[str, Any]) -> bool:
    """Create a new admin user"""
    try:
        db = get_database_manager()
        db.execute_procedure('create_admin_user', user_data)
        return True
    except Exception as e:
        logger.error(f"User creation error: {e}")
        return False

def get_system_config(config_key: str) -> Optional[str]:
    """Get system configuration value"""
    try:
        db = get_database_manager()
        results = db.execute_query(
            "SELECT config_value FROM system_config WHERE config_key = :key",
            {'key': config_key}
        )
        return results[0]['config_value'] if results else None
    except Exception as e:
        logger.error(f"Config retrieval error: {e}")
        return None

def log_audit_event(user_id: Optional[str], action: str, resource: str, 
                   details: Optional[Dict] = None, ip_address: Optional[str] = None,
                   user_agent: Optional[str] = None, status: str = 'SUCCESS'):
    """Log an audit event"""
    try:
        db = get_database_manager()
        
        audit_data = {
            'log_id': str(datetime.now().timestamp()).replace('.', ''),
            'user_id': user_id,
            'action': action,
            'resource': resource,
            'details': json.dumps(details) if details else None,
            'ip_address': ip_address,
            'user_agent': user_agent,
            'status': status
        }
        
        db.execute_query(
            """
            INSERT INTO audit_log (log_id, user_id, action, resource, details, 
                                 ip_address, user_agent, timestamp, status)
            VALUES (:log_id, :user_id, :action, :resource, :details, 
                   :ip_address, :user_agent, CURRENT_TIMESTAMP, :status)
            """,
            audit_data
        )
        
    except Exception as e:
        logger.error(f"Audit logging error: {e}")

# Environment-specific configuration
def load_config_from_database():
    """Load configuration from database system_config table"""
    try:
        db = get_database_manager()
        results = db.execute_query("SELECT config_key, config_value FROM system_config")
        
        config = {}
        for row in results:
            config[row['config_key']] = row['config_value']
        
        return config
        
    except Exception as e:
        logger.error(f"Config loading error: {e}")
        return {}

# Cleanup procedures
def cleanup_expired_sessions():
    """Clean up expired sessions"""
    try:
        db = get_database_manager()
        db.execute_procedure('cleanup_expired_sessions')
        logger.info("Expired sessions cleaned up")
    except Exception as e:
        logger.error(f"Session cleanup error: {e}")

def cleanup_old_audit_logs():
    """Clean up old audit logs"""
    try:
        db = get_database_manager()
        db.execute_procedure('cleanup_old_audit_logs')
        logger.info("Old audit logs cleaned up")
    except Exception as e:
        logger.error(f"Audit cleanup error: {e}")
