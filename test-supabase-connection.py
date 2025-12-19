"""
Test Supabase PostgreSQL Connection
"""
import sys
# Fix Windows console encoding
if sys.platform == 'win32':
    import codecs
    if sys.stdout.encoding != 'utf-8':
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

import psycopg2
from dotenv import load_dotenv
import os

# Load environment variables from .env
load_dotenv()

# Fetch variables
USER = os.getenv("DB_USER") or os.getenv("user")
PASSWORD = os.getenv("DB_PASSWORD") or os.getenv("password")
HOST = os.getenv("DB_HOST") or os.getenv("host")
PORT = os.getenv("DB_PORT") or os.getenv("port")
DBNAME = os.getenv("DB_NAME") or os.getenv("dbname")

# Also try DATABASE_URL
DATABASE_URL = os.getenv("DATABASE_URL")

print("=" * 60)
print("Testing Supabase PostgreSQL Connection")
print("=" * 60)
print(f"Host: {HOST}")
print(f"Port: {PORT}")
print(f"Database: {DBNAME}")
print(f"User: {USER}")
print(f"Password: {'*' * len(PASSWORD) if PASSWORD else 'Not set'}")
print(f"Using DATABASE_URL: {'Yes' if DATABASE_URL else 'No'}")
print("=" * 60)

# Connect to the database
try:
    if DATABASE_URL:
        # Use connection string
        print("\n[CONNECT] Connecting using DATABASE_URL...")
        connection = psycopg2.connect(DATABASE_URL)
    else:
        # Use individual parameters
        print("\n[CONNECT] Connecting using individual parameters...")
        connection = psycopg2.connect(
            user=USER,
            password=PASSWORD,
            host=HOST,
            port=PORT,
            dbname=DBNAME,
            sslmode='require'
        )
    
    print("[OK] Connection successful!")
    
    # Create a cursor to execute SQL queries
    cursor = connection.cursor()
    
    # Test query - get current time
    cursor.execute("SELECT NOW();")
    result = cursor.fetchone()
    print(f"[TIME] Current Database Time: {result[0]}")
    
    # Test query - check if tables exist
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_type = 'BASE TABLE'
        ORDER BY table_name;
    """)
    tables = cursor.fetchall()
    print(f"\n[TABLES] Tables found: {len(tables)}")
    for table in tables:
        print(f"   - {table[0]}")
    
    # Check Users table structure if it exists
    if any('Users' in str(table) for table in tables):
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'Users'
            ORDER BY ordinal_position;
        """)
        columns = cursor.fetchall()
        print(f"\n[USERS] Users table columns:")
        for col in columns:
            print(f"   - {col[0]} ({col[1]})")
    
    # Check Tasks table structure if it exists
    if any('Tasks' in str(table) for table in tables):
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'Tasks'
            ORDER BY ordinal_position;
        """)
        columns = cursor.fetchall()
        print(f"\n[TASKS] Tasks table columns:")
        for col in columns:
            print(f"   - {col[0]} ({col[1]})")

    # Close the cursor and connection
    cursor.close()
    connection.close()
    print("\n[OK] Connection closed successfully!")
    print("\n[SUCCESS] All tests passed! Your Supabase connection is working!")

except psycopg2.OperationalError as e:
    print(f"\n[ERROR] Connection failed: {e}")
    print("\n[TIPS] Troubleshooting:")
    print("   1. Check your .env file has correct credentials")
    print("   2. Verify your Supabase database is running")
    print("   3. Check if your network supports IPv6 (Supabase uses IPv6)")
    print("   4. Try using Session Pooler in Supabase if on IPv4-only network")
except Exception as e:
    print(f"\n[ERROR] Error: {e}")
    print("\n💡 Check your .env file configuration")
