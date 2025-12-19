"""
Test SQL Server Connection for AutoOps Task Board
"""
import os
import sys
from dotenv import load_dotenv

# Fix Windows console encoding
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Load environment variables
load_dotenv()

# Configuration
DB_SERVER = os.getenv('DB_SERVER', 'SUMANTH\\SQLEXPRESS')
DB_NAME = os.getenv('DB_NAME', 'AutoOpsDB')
DB_USER = os.getenv('DB_USER', '')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')

print('Testing SQL Server connection...')
print(f'   Server: {DB_SERVER}')
print(f'   Database: {DB_NAME}')
print(f'   Authentication: {"SQL Server" if DB_USER else "Windows"}')
print('')

# Try to import SQL library
try:
    import pyodbc
    SQL_LIBRARY = 'pyodbc'
    print('[OK] Using pyodbc library')
except ImportError:
    try:
        import pymssql
        SQL_LIBRARY = 'pymssql'
        print('[OK] Using pymssql library')
    except ImportError:
        print('[ERROR] No SQL Server library found!')
        print('   Please install: pip install pyodbc')
        print('   Or: pip install pymssql')
        sys.exit(1)

print('')

# Test connection
try:
    if SQL_LIBRARY == 'pyodbc':
        # Try pyodbc
        if DB_USER and DB_PASSWORD:
            conn_str = (
                f'DRIVER={{ODBC Driver 17 for SQL Server}};'
                f'SERVER={DB_SERVER};'
                f'DATABASE=master;'
                f'UID={DB_USER};'
                f'PWD={DB_PASSWORD};'
                f'TrustServerCertificate=yes;'
            )
        else:
            conn_str = (
                f'DRIVER={{ODBC Driver 17 for SQL Server}};'
                f'SERVER={DB_SERVER};'
                f'DATABASE=master;'
                f'Trusted_Connection=yes;'
                f'TrustServerCertificate=yes;'
            )
        
        print('   Attempting connection to master database...')
        conn = pyodbc.connect(conn_str, timeout=10)
        print('[SUCCESS] Connected to SQL Server!')
        
        # Check if target database exists
        cursor = conn.cursor()
        cursor.execute(f"SELECT name FROM sys.databases WHERE name = '{DB_NAME}'")
        result = cursor.fetchone()
        
        if result:
            print(f'[OK] Database "{DB_NAME}" exists')
            
            # Try to connect to the actual database
            conn.close()
            if DB_USER and DB_PASSWORD:
                conn_str = (
                    f'DRIVER={{ODBC Driver 17 for SQL Server}};'
                    f'SERVER={DB_SERVER};'
                    f'DATABASE={DB_NAME};'
                    f'UID={DB_USER};'
                    f'PWD={DB_PASSWORD};'
                    f'TrustServerCertificate=yes;'
                )
            else:
                conn_str = (
                    f'DRIVER={{ODBC Driver 17 for SQL Server}};'
                    f'SERVER={DB_SERVER};'
                    f'DATABASE={DB_NAME};'
                    f'Trusted_Connection=yes;'
                    f'TrustServerCertificate=yes;'
                )
            
            conn = pyodbc.connect(conn_str, timeout=10)
            print(f'[SUCCESS] Connected to database "{DB_NAME}"')
            conn.close()
            print('\n[SUCCESS] All checks passed! Database is ready.')
        else:
            print(f'[WARNING] Database "{DB_NAME}" does NOT exist')
            print('\nTo create the database, run this in SSMS:')
            print(f'   CREATE DATABASE {DB_NAME};')
            print('\n   Or run the database-schema.sql script.')
        
    elif SQL_LIBRARY == 'pymssql':
        # Try pymssql
        server_parts = DB_SERVER.replace('\\', '/').split('/')
        server = server_parts[0]
        
        if not DB_USER or not DB_PASSWORD:
            print('[WARNING] pymssql requires SQL Server Authentication')
            print('   Please set DB_USER and DB_PASSWORD in .env file')
            sys.exit(1)
        
        print('   Attempting connection to master database...')
        conn = pymssql.connect(
            server=server,
            user=DB_USER,
            password=DB_PASSWORD,
            database='master',
            timeout=10
        )
        print('[SUCCESS] Connected to SQL Server!')
        
        # Check if target database exists
        cursor = conn.cursor()
        cursor.execute(f"SELECT name FROM sys.databases WHERE name = '{DB_NAME}'")
        result = cursor.fetchone()
        
        if result:
            print(f'[OK] Database "{DB_NAME}" exists')
            
            # Try to connect to the actual database
            conn.close()
            conn = pymssql.connect(
                server=server,
                user=DB_USER,
                password=DB_PASSWORD,
                database=DB_NAME,
                timeout=10
            )
            print(f'[SUCCESS] Connected to database "{DB_NAME}"')
            conn.close()
            print('\n[SUCCESS] All checks passed! Database is ready.')
        else:
            print(f'[WARNING] Database "{DB_NAME}" does NOT exist')
            print('\nTo create the database, run this in SSMS:')
            print(f'   CREATE DATABASE {DB_NAME};')
            print('\n   Or run the database-schema.sql script.')
    
except Exception as e:
    print(f'\n[ERROR] Connection failed!')
    print(f'   Error: {str(e)}')
    print('\nTroubleshooting steps:')
    print('   1. Make sure SQL Server is running')
    print('   2. Check if SQL Server Browser service is running')
    print('   3. Verify the server name is correct in .env file')
    print('   4. Check Windows Firewall settings')
    print('   5. Try connecting with SQL Server Management Studio first')
    print('   6. For Windows Auth: Ensure your user has SQL Server access')
    print('   7. For SQL Auth: Verify username and password are correct')
    
    # Try alternative server names
    print('\nTry these alternative server names in .env:')
    print('   DB_SERVER=localhost\\SQLEXPRESS')
    print('   DB_SERVER=.\\SQLEXPRESS')
    print('   DB_SERVER=(local)\\SQLEXPRESS')
    
    sys.exit(1)

