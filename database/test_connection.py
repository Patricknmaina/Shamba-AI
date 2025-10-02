#!/usr/bin/env python3
"""
ShambaAI Database Connection Test Script
Tests connection to Oracle Autonomous Database and verifies schema
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import cx_Oracle
except ImportError:
    print("❌ ERROR: cx_Oracle not installed")
    print("   Install with: pip install cx_Oracle")
    sys.exit(1)

try:
    from dotenv import load_dotenv
except ImportError:
    print("❌ ERROR: python-dotenv not installed")
    print("   Install with: pip install python-dotenv")
    sys.exit(1)


class DatabaseTester:
    """Test Oracle Database connection and schema"""

    def __init__(self):
        """Initialize tester with environment variables"""
        # Load environment variables
        env_path = Path(__file__).parent.parent / "ml_service" / ".env"
        if env_path.exists():
            load_dotenv(env_path)
            print(f"✅ Loaded environment from: {env_path}")
        else:
            print(f"⚠️  Warning: .env file not found at {env_path}")

        # Get database credentials
        self.user = os.getenv('ORACLE_USER')
        self.password = os.getenv('ORACLE_PASSWORD')
        self.dsn = os.getenv('ORACLE_DSN')
        self.wallet_location = os.getenv('ORACLE_WALLET_LOCATION')
        self.wallet_password = os.getenv('ORACLE_WALLET_PASSWORD')

        self.connection = None
        self.results = []

    def add_result(self, test_name, passed, message=""):
        """Add test result"""
        self.results.append({
            'test': test_name,
            'passed': passed,
            'message': message
        })

    def check_credentials(self):
        """Check if all required credentials are set"""
        print("\n" + "="*60)
        print("1. CHECKING ENVIRONMENT VARIABLES")
        print("="*60)

        required_vars = ['ORACLE_USER', 'ORACLE_PASSWORD', 'ORACLE_DSN']
        all_set = True

        for var in required_vars:
            value = os.getenv(var)
            if value:
                # Mask password
                display_value = '*' * len(value) if var == 'ORACLE_PASSWORD' else value
                print(f"✅ {var}: {display_value}")
            else:
                print(f"❌ {var}: Not set")
                all_set = False

        # Optional wallet variables
        if self.wallet_location:
            print(f"✅ ORACLE_WALLET_LOCATION: {self.wallet_location}")
        else:
            print("⚠️  ORACLE_WALLET_LOCATION: Not set (may not be needed)")

        self.add_result("Environment Variables", all_set,
                       "All required variables set" if all_set else "Missing required variables")
        return all_set

    def test_connection(self):
        """Test database connection"""
        print("\n" + "="*60)
        print("2. TESTING DATABASE CONNECTION")
        print("="*60)

        try:
            # Configure wallet if provided
            if self.wallet_location and self.wallet_password:
                print(f"📁 Using wallet: {self.wallet_location}")
                cx_Oracle.init_oracle_client(
                    config_dir=self.wallet_location
                )

            # Attempt connection
            print(f"🔌 Connecting to: {self.dsn}")
            self.connection = cx_Oracle.connect(
                user=self.user,
                password=self.password,
                dsn=self.dsn,
                encoding="UTF-8"
            )

            print("✅ Connection successful!")

            # Get database info
            cursor = self.connection.cursor()
            cursor.execute("SELECT * FROM V$VERSION WHERE ROWNUM = 1")
            version = cursor.fetchone()
            print(f"📊 Database version: {version[0]}")

            cursor.execute("SELECT SYS_CONTEXT('USERENV', 'DB_NAME') FROM DUAL")
            db_name = cursor.fetchone()[0]
            print(f"📊 Database name: {db_name}")

            cursor.execute("SELECT SYS_CONTEXT('USERENV', 'CURRENT_USER') FROM DUAL")
            current_user = cursor.fetchone()[0]
            print(f"👤 Connected as: {current_user}")

            cursor.close()

            self.add_result("Database Connection", True, f"Connected as {current_user}")
            return True

        except cx_Oracle.DatabaseError as e:
            error_obj, = e.args
            print(f"❌ Connection failed: {error_obj.message}")
            self.add_result("Database Connection", False, str(error_obj.message))
            return False
        except Exception as e:
            print(f"❌ Connection failed: {str(e)}")
            self.add_result("Database Connection", False, str(e))
            return False

    def test_tables_exist(self):
        """Check if all required tables exist"""
        print("\n" + "="*60)
        print("3. CHECKING TABLES")
        print("="*60)

        required_tables = [
            'ADMIN_USERS', 'USER_SESSIONS', 'AUDIT_LOG', 'SYSTEM_CONFIG',
            'PASSWORD_RESET_TOKENS', 'USER_INTERACTIONS', 'PAGE_VIEWS',
            'FEATURE_USAGE', 'API_REQUESTS', 'ERROR_LOGS', 'USER_PREFERENCES'
        ]

        cursor = self.connection.cursor()

        try:
            # Check each table
            existing_tables = []
            missing_tables = []

            for table in required_tables:
                cursor.execute(
                    "SELECT COUNT(*) FROM user_tables WHERE table_name = :table_name",
                    {'table_name': table}
                )
                count = cursor.fetchone()[0]

                if count > 0:
                    print(f"✅ {table}")
                    existing_tables.append(table)
                else:
                    print(f"❌ {table} - NOT FOUND")
                    missing_tables.append(table)

            print(f"\n📊 Tables found: {len(existing_tables)}/{len(required_tables)}")

            all_exist = len(missing_tables) == 0
            message = "All tables exist" if all_exist else f"Missing: {', '.join(missing_tables)}"
            self.add_result("Tables Exist", all_exist, message)

            cursor.close()
            return all_exist

        except Exception as e:
            print(f"❌ Error checking tables: {str(e)}")
            cursor.close()
            self.add_result("Tables Exist", False, str(e))
            return False

    def test_admin_users(self):
        """Check if admin users exist"""
        print("\n" + "="*60)
        print("4. CHECKING ADMIN USERS")
        print("="*60)

        cursor = self.connection.cursor()

        try:
            cursor.execute("SELECT COUNT(*) FROM admin_users")
            count = cursor.fetchone()[0]

            print(f"📊 Total admin users: {count}")

            if count > 0:
                # Get user details
                cursor.execute(
                    """
                    SELECT username, email, role, is_active
                    FROM admin_users
                    ORDER BY username
                    """
                )

                print("\nAdmin Users:")
                print("-" * 80)
                print(f"{'Username':<20} {'Email':<30} {'Role':<20} {'Active':<10}")
                print("-" * 80)

                for row in cursor:
                    username, email, role, is_active = row
                    status = "✅ Yes" if is_active == 'Y' else "❌ No"
                    print(f"{username:<20} {email:<30} {role:<20} {status:<10}")

                print("-" * 80)

                self.add_result("Admin Users", True, f"{count} admin users found")
                cursor.close()
                return True
            else:
                print("⚠️  No admin users found")
                self.add_result("Admin Users", False, "No admin users found")
                cursor.close()
                return False

        except Exception as e:
            print(f"❌ Error checking admin users: {str(e)}")
            cursor.close()
            self.add_result("Admin Users", False, str(e))
            return False

    def test_indexes(self):
        """Check if indexes are created"""
        print("\n" + "="*60)
        print("5. CHECKING INDEXES")
        print("="*60)

        cursor = self.connection.cursor()

        try:
            cursor.execute(
                """
                SELECT COUNT(*)
                FROM user_indexes
                WHERE table_name IN (
                    'ADMIN_USERS', 'USER_SESSIONS', 'AUDIT_LOG', 'SYSTEM_CONFIG',
                    'PASSWORD_RESET_TOKENS', 'USER_INTERACTIONS', 'PAGE_VIEWS',
                    'FEATURE_USAGE', 'API_REQUESTS', 'ERROR_LOGS', 'USER_PREFERENCES'
                )
                AND index_name NOT LIKE 'SYS_%'
                """
            )
            count = cursor.fetchone()[0]

            print(f"📊 Total indexes: {count}")

            if count >= 40:
                print("✅ Sufficient indexes created")
                self.add_result("Indexes", True, f"{count} indexes created")
                result = True
            else:
                print(f"⚠️  Warning: Only {count} indexes found (expected 40+)")
                self.add_result("Indexes", False, f"Only {count} indexes (expected 40+)")
                result = False

            cursor.close()
            return result

        except Exception as e:
            print(f"❌ Error checking indexes: {str(e)}")
            cursor.close()
            self.add_result("Indexes", False, str(e))
            return False

    def test_insert_and_query(self):
        """Test insert and query operations"""
        print("\n" + "="*60)
        print("6. TESTING INSERT & QUERY")
        print("="*60)

        cursor = self.connection.cursor()

        try:
            # Test insert into system_config
            test_key = 'TEST_CONNECTION_' + datetime.now().strftime('%Y%m%d%H%M%S')

            print(f"📝 Inserting test config: {test_key}")
            cursor.execute(
                """
                INSERT INTO system_config (config_key, config_value, description)
                VALUES (:key, :value, :desc)
                """,
                {
                    'key': test_key,
                    'value': 'test_value',
                    'desc': 'Test connection config'
                }
            )
            self.connection.commit()
            print("✅ Insert successful")

            # Test query
            print(f"🔍 Querying test config: {test_key}")
            cursor.execute(
                "SELECT config_value FROM system_config WHERE config_key = :key",
                {'key': test_key}
            )
            result = cursor.fetchone()

            if result and result[0] == 'test_value':
                print("✅ Query successful")
            else:
                print("❌ Query failed")
                cursor.close()
                return False

            # Clean up
            print(f"🗑️  Deleting test config")
            cursor.execute(
                "DELETE FROM system_config WHERE config_key = :key",
                {'key': test_key}
            )
            self.connection.commit()
            print("✅ Cleanup successful")

            self.add_result("Insert & Query", True, "Insert, query, and delete successful")
            cursor.close()
            return True

        except Exception as e:
            print(f"❌ Error in insert/query test: {str(e)}")
            self.connection.rollback()
            cursor.close()
            self.add_result("Insert & Query", False, str(e))
            return False

    def test_system_config(self):
        """Check system configuration"""
        print("\n" + "="*60)
        print("7. CHECKING SYSTEM CONFIGURATION")
        print("="*60)

        cursor = self.connection.cursor()

        try:
            cursor.execute("SELECT COUNT(*) FROM system_config")
            count = cursor.fetchone()[0]

            print(f"📊 Configuration entries: {count}")

            if count > 0:
                cursor.execute(
                    """
                    SELECT config_key, config_value, description
                    FROM system_config
                    ORDER BY config_key
                    """
                )

                print("\nSystem Configuration:")
                print("-" * 80)
                for row in cursor:
                    config_key, config_value, description = row
                    print(f"🔧 {config_key}: {config_value}")
                    print(f"   {description}")

                self.add_result("System Config", True, f"{count} config entries found")
                result = True
            else:
                print("⚠️  No system configuration found")
                self.add_result("System Config", False, "No config entries")
                result = False

            cursor.close()
            return result

        except Exception as e:
            print(f"❌ Error checking system config: {str(e)}")
            cursor.close()
            self.add_result("System Config", False, str(e))
            return False

    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)

        passed_count = sum(1 for r in self.results if r['passed'])
        total_count = len(self.results)

        print(f"\n{'Test':<30} {'Status':<10} {'Message':<30}")
        print("-" * 80)

        for result in self.results:
            status = "✅ PASS" if result['passed'] else "❌ FAIL"
            message = result['message'][:30] if result['message'] else ""
            print(f"{result['test']:<30} {status:<10} {message:<30}")

        print("-" * 80)
        print(f"\nTotal: {passed_count}/{total_count} tests passed")

        if passed_count == total_count:
            print("\n✅✅✅ ALL TESTS PASSED! Database is ready to use. ✅✅✅")
        else:
            print(f"\n⚠️  WARNING: {total_count - passed_count} test(s) failed.")

        print("="*60 + "\n")

    def run_all_tests(self):
        """Run all tests"""
        print("\n" + "="*60)
        print("SHAMBAAI DATABASE CONNECTION TEST")
        print("="*60)
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # Run tests
        if not self.check_credentials():
            print("\n❌ Cannot proceed without proper credentials")
            return False

        if not self.test_connection():
            print("\n❌ Cannot proceed without database connection")
            return False

        # Run remaining tests
        self.test_tables_exist()
        self.test_admin_users()
        self.test_indexes()
        self.test_system_config()
        self.test_insert_and_query()

        # Print summary
        self.print_summary()

        # Close connection
        if self.connection:
            self.connection.close()
            print("🔌 Database connection closed")

        return True


def main():
    """Main function"""
    tester = DatabaseTester()
    tester.run_all_tests()


if __name__ == "__main__":
    main()
