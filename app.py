"""
AutoOps Task Board - Flask Backend Server
"""
import sys
# Fix Windows console encoding
if sys.platform == 'win32':
    import codecs
    if sys.stdout.encoding != 'utf-8':
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import bcrypt
import jwt
import os
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from functools import wraps
from dotenv import load_dotenv

# Try to import PostgreSQL library
try:
    import psycopg2
    from psycopg2 import pool
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False
    print('⚠️  PostgreSQL library not found. Please install psycopg2-binary:')
    print('   pip install psycopg2-binary')

# Load environment variables
load_dotenv()

app = Flask(__name__, static_folder='.')
CORS(app)

# Configuration
PORT = int(os.getenv('PORT', 3001))
JWT_SECRET = os.getenv('JWT_SECRET')
if not JWT_SECRET:
    raise ValueError('JWT_SECRET environment variable is required. Please set it in your .env file.')

# Email Configuration
# Method: 'api' for Brevo REST API (default), 'smtp_brevo' for Brevo SMTP, or 'smtp_gmail' for Gmail SMTP
EMAIL_METHOD = os.getenv('EMAIL_METHOD', 'api').lower()

# Brevo REST API Configuration (default)
BREVO_API_KEY = os.getenv('BREVO_API_KEY')
BREVO_API_URL = 'https://api.brevo.com/v3/smtp/email'
BREVO_SENDER_EMAIL = os.getenv('BREVO_SENDER_EMAIL', 'noreply@autoops.com')
BREVO_SENDER_NAME = os.getenv('BREVO_SENDER_NAME', 'AutoOps Team')

# Brevo SMTP Configuration
BREVO_SMTP_SERVER = os.getenv('BREVO_SMTP_SERVER', 'smtp-relay.brevo.com')
BREVO_SMTP_PORT = int(os.getenv('BREVO_SMTP_PORT', 587))
BREVO_SMTP_LOGIN = os.getenv('BREVO_SMTP_LOGIN')
BREVO_SMTP_PASSWORD = os.getenv('BREVO_SMTP_PASSWORD')

# Gmail SMTP Configuration
GMAIL_SMTP_SERVER = os.getenv('GMAIL_SMTP_SERVER', 'smtp.gmail.com')
GMAIL_SMTP_PORT = int(os.getenv('GMAIL_SMTP_PORT', 587))
GMAIL_SMTP_USERNAME = os.getenv('GMAIL_SMTP_USERNAME')
GMAIL_SMTP_PASSWORD = os.getenv('GMAIL_SMTP_PASSWORD')
GMAIL_SENDER_EMAIL = os.getenv('GMAIL_SENDER_EMAIL')
GMAIL_SENDER_NAME = os.getenv('GMAIL_SENDER_NAME', 'AutoOps Team')

# PostgreSQL Configuration (Cloud Database)
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'postgres')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
# Alternative: Use DATABASE_URL if provided (common in cloud platforms)
DATABASE_URL = os.getenv('DATABASE_URL', '')

# Database connection pool
db_pool = None

def get_db_connection():
    """Get PostgreSQL database connection"""
    global db_pool
    
    if not POSTGRES_AVAILABLE:
        print('[ERROR] PostgreSQL library not installed. Please install psycopg2-binary.')
        return None
    
    try:
        # Initialize connection pool if not exists
        if db_pool is None:
            if DATABASE_URL:
                # Use DATABASE_URL (common in cloud platforms like Railway, Heroku, etc.)
                db_pool = psycopg2.pool.SimpleConnectionPool(1, 20, DATABASE_URL)
            else:
                # Use individual connection parameters
                db_pool = psycopg2.pool.SimpleConnectionPool(
                    1, 20,
                    host=DB_HOST,
                    port=DB_PORT,
                    database=DB_NAME,
                    user=DB_USER,
                    password=DB_PASSWORD
                )
        
        # Get connection from pool
        conn = db_pool.getconn()
        return conn
    except Exception as e:
        print(f'[WARNING] Database connection error: {str(e)}')
        return None

def return_db_connection(conn):
    """Return connection to pool"""
    global db_pool
    if db_pool and conn:
        db_pool.putconn(conn)

def init_database():
    """Initialize database and create tables if they don't exist"""
    conn = get_db_connection()
    if not conn:
        print('[WARNING] Database connection unavailable. Tables will not be created.')
        return
    
    try:
        cursor = conn.cursor()
        
        # Create Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS "Users" (
                "Id" SERIAL PRIMARY KEY,
                "Username" VARCHAR(50) NOT NULL UNIQUE,
                "Email" VARCHAR(100) NOT NULL UNIQUE,
                "Password" VARCHAR(255) NOT NULL,
                "FullName" VARCHAR(100),
                "CreatedAt" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                "LastLogin" TIMESTAMP
            )
        """)
        
        # Create indexes for Users
        cursor.execute('CREATE INDEX IF NOT EXISTS "IX_Users_Username" ON "Users"("Username")')
        cursor.execute('CREATE INDEX IF NOT EXISTS "IX_Users_Email" ON "Users"("Email")')
        
        # Create Tasks table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS "Tasks" (
                "Id" SERIAL PRIMARY KEY,
                "UserId" INTEGER NOT NULL,
                "TaskId" VARCHAR(50),
                "Type" VARCHAR(20) DEFAULT 'task',
                "Title" VARCHAR(200) NOT NULL,
                "Description" TEXT,
                "Assignee" VARCHAR(100),
                "Priority" VARCHAR(20) DEFAULT 'medium',
                "Status" VARCHAR(20) DEFAULT 'todo',
                "CreatedAt" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                "UpdatedAt" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY ("UserId") REFERENCES "Users"("Id") ON DELETE CASCADE
            )
        """)
        
        # Create indexes for Tasks
        cursor.execute('CREATE INDEX IF NOT EXISTS "IX_Tasks_UserId" ON "Tasks"("UserId")')
        cursor.execute('CREATE INDEX IF NOT EXISTS "IX_Tasks_Status" ON "Tasks"("Status")')
        
        # Create function to update UpdatedAt timestamp
        cursor.execute("""
            CREATE OR REPLACE FUNCTION update_updated_at_column()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW."UpdatedAt" = CURRENT_TIMESTAMP;
                RETURN NEW;
            END;
            $$ language 'plpgsql'
        """)
        
        # Create trigger to auto-update UpdatedAt
        cursor.execute("""
            DROP TRIGGER IF EXISTS update_tasks_updated_at ON "Tasks";
            CREATE TRIGGER update_tasks_updated_at
                BEFORE UPDATE ON "Tasks"
                FOR EACH ROW
                EXECUTE FUNCTION update_updated_at_column()
        """)
        
        # Add Type column if it doesn't exist (for existing tables)
        cursor.execute("""
            DO $$ 
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name='Tasks' AND column_name='Type') THEN
                    ALTER TABLE "Tasks" ADD COLUMN "Type" VARCHAR(20) DEFAULT 'task';
                END IF;
            END $$;
        """)
        
        # Add TaskId column if it doesn't exist
        cursor.execute("""
            DO $$ 
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name='Tasks' AND column_name='TaskId') THEN
                    ALTER TABLE "Tasks" ADD COLUMN "TaskId" VARCHAR(50);
                END IF;
            END $$;
        """)
        
        conn.commit()
        print('[OK] Database tables created/verified')
    except Exception as e:
        print(f'[WARNING] Error creating tables: {str(e)}')
        conn.rollback()
    finally:
        return_db_connection(conn)

# Initialize database on startup
try:
    init_database()
except Exception as e:
    print(f'[WARNING] Database initialization warning: {str(e)}')
    print('[WARNING] Server will start but database features may be unavailable')

# Authentication decorator
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get('Authorization')
        
        if auth_header:
            try:
                token = auth_header.split(' ')[1]
            except IndexError:
                return jsonify({'message': 'Invalid token format'}), 401
        
        if not token:
            return jsonify({'message': 'Token is missing'}), 401
        
        try:
            data = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
            request.user = data
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired'}), 403
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Invalid token'}), 403
        
        return f(*args, **kwargs)
    return decorated

# Routes

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'ok', 'message': 'Server is running'})

def get_email_html(name):
    """Get HTML content for welcome email"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
    </head>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; background-color: #f4f5f7; margin: 0; padding: 0;">
        <div style="max-width: 600px; margin: 40px auto; background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); overflow: hidden;">
            <div style="background: linear-gradient(135deg, #0052cc 0%, #0065ff 100%); padding: 30px; text-align: center;">
                <h1 style="color: #ffffff; margin: 0; font-size: 28px;">Welcome to AutoOps!</h1>
            </div>
            <div style="padding: 30px;">
                <h2 style="color: #0052cc; margin-top: 0;">Hello {name}!</h2>
                <p style="font-size: 16px; color: #172b4d;">Thank you for joining our team. You can now:</p>
                <ul style="font-size: 16px; color: #42526e; line-height: 2;">
                    <li>Create and manage tasks</li>
                    <li>Track your work progress</li>
                    <li>Collaborate with your team</li>
                    <li>Stay organized with our Kanban board</li>
                </ul>
                <div style="margin: 30px 0; padding: 20px; background-color: #f4f5f7; border-radius: 6px; border-left: 4px solid #0052cc;">
                    <p style="margin: 0; color: #172b4d; font-weight: 600;">Get started by logging in and creating your first task!</p>
                </div>
                <p style="color: #6b778c; font-size: 14px; margin-top: 30px;">
                    This is an automated message. Please do not reply.
                </p>
            </div>
            <div style="background-color: #f4f5f7; padding: 20px; text-align: center; border-top: 1px solid #dfe1e6;">
                <p style="margin: 0; color: #6b778c; font-size: 12px;">
                    © 2024 AutoOps Team. All rights reserved.
                </p>
            </div>
        </div>
    </body>
    </html>
    """

def send_welcome_email_via_api(email, name):
    """Send welcome email using Brevo REST API"""
    if not BREVO_API_KEY:
        print('⚠️  Brevo API key not configured. Set BREVO_API_KEY in .env file')
        return False
    
    try:
        email_data = {
            "sender": {
                "name": BREVO_SENDER_NAME,
                "email": BREVO_SENDER_EMAIL
            },
            "to": [
                {
                    "email": email,
                    "name": name
                }
            ],
            "subject": "Welcome to AutoOps Task Board!",
            "htmlContent": get_email_html(name)
        }
        
        headers = {
            "accept": "application/json",
            "api-key": BREVO_API_KEY,
            "content-type": "application/json"
        }
        
        response = requests.post(BREVO_API_URL, json=email_data, headers=headers)
        
        if response.status_code == 201:
            print(f'✅ Welcome email sent to {email} via API')
            return True
        else:
            print(f'⚠️  Email API response: {response.status_code} - {response.text}')
            return False
            
    except Exception as e:
        print(f'❌ Error sending email via API: {str(e)}')
        return False

def send_welcome_email_via_smtp_brevo(email, name):
    """Send welcome email using Brevo SMTP"""
    if not BREVO_SMTP_LOGIN or not BREVO_SMTP_PASSWORD:
        print('⚠️  Brevo SMTP credentials not configured. Set BREVO_SMTP_LOGIN and BREVO_SMTP_PASSWORD in .env file')
        return False
    
    try:
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = 'Welcome to AutoOps Task Board!'
        msg['From'] = f'{BREVO_SENDER_NAME} <{BREVO_SENDER_EMAIL}>'
        msg['To'] = email
        
        # Create HTML part
        html_part = MIMEText(get_email_html(name), 'html')
        msg.attach(html_part)
        
        # Send email via SMTP
        with smtplib.SMTP(BREVO_SMTP_SERVER, BREVO_SMTP_PORT) as server:
            server.starttls()
            server.login(BREVO_SMTP_LOGIN, BREVO_SMTP_PASSWORD)
            server.send_message(msg)
        
        print(f'✅ Welcome email sent to {email} via Brevo SMTP')
        return True
        
    except Exception as e:
        print(f'❌ Error sending email via Brevo SMTP: {str(e)}')
        return False

def send_welcome_email_via_smtp_gmail(email, name):
    """Send welcome email using Gmail SMTP"""
    if not GMAIL_SMTP_USERNAME or not GMAIL_SMTP_PASSWORD:
        print('⚠️  Gmail SMTP credentials not configured. Set GMAIL_SMTP_USERNAME and GMAIL_SMTP_PASSWORD in .env file')
        return False
    
    try:
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = 'Welcome to AutoOps Task Board!'
        msg['From'] = f'{GMAIL_SENDER_NAME} <{GMAIL_SENDER_EMAIL}>'
        msg['To'] = email
        
        # Create HTML part
        html_part = MIMEText(get_email_html(name), 'html')
        msg.attach(html_part)
        
        # Send email via Gmail SMTP
        with smtplib.SMTP(GMAIL_SMTP_SERVER, GMAIL_SMTP_PORT) as server:
            server.starttls()
            server.login(GMAIL_SMTP_USERNAME, GMAIL_SMTP_PASSWORD)
            server.send_message(msg)
        
        print(f'✅ Welcome email sent to {email} via Gmail SMTP')
        return True
        
    except Exception as e:
        print(f'❌ Error sending email via Gmail SMTP: {str(e)}')
        print('💡 Note: Gmail requires App Password, not regular password. Enable 2FA and generate App Password.')
        return False

def send_welcome_email(email, name):
    """Send welcome email to new user (uses API or SMTP based on configuration)"""
    success = False
    
    if EMAIL_METHOD == 'smtp_gmail':
        success = send_welcome_email_via_smtp_gmail(email, name)
        # Fallback to Brevo API if Gmail fails
        if not success and BREVO_API_KEY:
            print('⚠️  Gmail SMTP failed, trying Brevo API fallback...')
            success = send_welcome_email_via_api(email, name)
    elif EMAIL_METHOD == 'smtp_brevo' or EMAIL_METHOD == 'smtp':
        success = send_welcome_email_via_smtp_brevo(email, name)
        # Fallback to API if SMTP fails
        if not success and BREVO_API_KEY:
            print('⚠️  Brevo SMTP failed, trying API fallback...')
            success = send_welcome_email_via_api(email, name)
    else:  # Default: API
        success = send_welcome_email_via_api(email, name)
        # Fallback to Gmail SMTP if API fails
        if not success and GMAIL_SMTP_USERNAME and GMAIL_SMTP_PASSWORD:
            print('⚠️  Brevo API failed, trying Gmail SMTP fallback...')
            success = send_welcome_email_via_smtp_gmail(email, name)

@app.route('/api/users', methods=['GET'])
@token_required
def get_users():
    """Get all users for team display"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'message': 'Database connection unavailable'}), 503
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT "Id", "Username", "Email", "FullName", "CreatedAt"
            FROM "Users"
            ORDER BY "CreatedAt" DESC
        """)
        
        users = []
        for row in cursor.fetchall():
            full_name = row[3] or row[1]  # Use FullName or Username as fallback
            initials = ''.join([n[0].upper() for n in full_name.split()[:2]]) if full_name else '?'
            
            users.append({
                'id': row[0],
                'username': row[1],
                'email': row[2],
                'fullName': full_name,
                'initials': initials,
                'createdAt': row[4].isoformat() if row[4] else None
            })
        
        return jsonify(users), 200
        
    except Exception as e:
        print(f'Error fetching users: {str(e)}')
        return jsonify({'message': 'Server error fetching users'}), 500
    finally:
        return_db_connection(conn)

@app.route('/api/auth/register', methods=['POST'])
def register():
    """Register a new user"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'message': 'Database connection unavailable. Please check SQL Server configuration.'}), 503
    
    try:
        data = request.get_json()
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        full_name = data.get('fullName')
        
        # Validation
        if not username or not email or not password:
            return jsonify({'message': 'Username, email, and password are required'}), 400
        
        if len(password) < 6:
            return jsonify({'message': 'Password must be at least 6 characters'}), 400
        
        cursor = conn.cursor()
        
        # Check if user already exists
        cursor.execute("""
            SELECT * FROM "Users" 
            WHERE "Username" = %s OR "Email" = %s
        """, (username, email))
        
        if cursor.fetchone():
            return jsonify({'message': 'Username or email already exists'}), 400
        
        # Hash password
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Insert new user
        cursor.execute("""
            INSERT INTO "Users" ("Username", "Email", "Password", "FullName")
            VALUES (%s, %s, %s, %s)
            RETURNING "Id", "Username", "Email", "FullName"
        """, (username, email, hashed_password, full_name))
        
        result = cursor.fetchone()
        conn.commit()
        
        if result:
            user_data = {
                'id': result[0],
                'username': result[1],
                'email': result[2],
                'fullName': result[3]
            }
            
            # Send welcome email
            try:
                send_welcome_email(user_data['email'], user_data['fullName'] or user_data['username'])
            except Exception as e:
                print(f'Email sending error (non-critical): {str(e)}')
                # Don't fail registration if email fails
            
            return jsonify({
                'message': 'User registered successfully',
                'user': user_data
            }), 201
        else:
            return jsonify({'message': 'Registration failed'}), 500
            
    except Exception as e:
        print(f'Registration error: {str(e)}')
        conn.rollback()
        return jsonify({'message': 'Server error during registration'}), 500
    finally:
        return_db_connection(conn)

@app.route('/api/auth/login', methods=['POST'])
def login():
    """Login user"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'message': 'Database connection unavailable. Please check SQL Server configuration.'}), 503
    
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'message': 'Username and password are required'}), 400
        
        cursor = conn.cursor()
        
        # Find user
        cursor.execute("""
            SELECT * FROM "Users" 
            WHERE "Username" = %s
        """, (username,))
        
        user = cursor.fetchone()
        
        if not user:
            return jsonify({'message': 'Invalid username or password'}), 401
        
        # Verify password
        if not bcrypt.checkpw(password.encode('utf-8'), user[3].encode('utf-8')):
            return jsonify({'message': 'Invalid username or password'}), 401
        
        # Update last login
        cursor.execute("""
            UPDATE "Users" 
            SET "LastLogin" = CURRENT_TIMESTAMP 
            WHERE "Id" = %s
        """, (user[0],))
        conn.commit()
        
        # Generate JWT token
        token = jwt.encode(
            {
                'userId': user[0],
                'username': user[1],
                'exp': datetime.utcnow() + timedelta(days=7)
            },
            JWT_SECRET,
            algorithm='HS256'
        )
        
        return jsonify({
            'message': 'Login successful',
            'token': token,
            'userId': user[0],
            'username': user[1],
            'fullName': user[4]
        }), 200
        
    except Exception as e:
        print(f'Login error: {str(e)}')
        conn.rollback()
        return jsonify({'message': 'Server error during login'}), 500
    finally:
        return_db_connection(conn)

@app.route('/api/auth/me', methods=['GET'])
@token_required
def get_current_user():
    """Get current user info"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'message': 'Database connection unavailable. Please check SQL Server configuration.'}), 503
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT "Id", "Username", "Email", "FullName", "CreatedAt", "LastLogin" 
            FROM "Users" 
            WHERE "Id" = %s
        """, (request.user['userId'],))
        
        user = cursor.fetchone()
        
        if not user:
            return jsonify({'message': 'User not found'}), 404
        
        return jsonify({
            'user': {
                'Id': user[0],
                'Username': user[1],
                'Email': user[2],
                'FullName': user[3],
                'CreatedAt': user[4].isoformat() if user[4] else None,
                'LastLogin': user[5].isoformat() if user[5] else None
            }
        }), 200
        
    except Exception as e:
        print(f'Get user error: {str(e)}')
        return jsonify({'message': 'Server error'}), 500
    finally:
        return_db_connection(conn)

# Task Management Routes

@app.route('/api/tasks', methods=['GET'])
@token_required
def get_tasks():
    """Get all tasks for the current user"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'message': 'Database connection unavailable'}), 503
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT "Id", "TaskId", "Type", "Title", "Description", "Assignee", "Priority", "Status", "CreatedAt", "UpdatedAt"
            FROM "Tasks"
            WHERE "UserId" = %s
            ORDER BY "CreatedAt" DESC
        """, (request.user['userId'],))
        
        tasks = []
        for row in cursor.fetchall():
            task_id = row[1] or f'AUTO-{str(row[0]).zfill(3)}'
            tasks.append({
                'id': str(row[0]),
                'taskId': task_id,
                'type': row[2] or 'task',
                'title': row[3],
                'description': row[4] or '',
                'assignee': row[5] or '',
                'priority': row[6] or 'medium',
                'status': row[7] or 'todo',
                'createdAt': row[8].isoformat() if row[8] else None,
                'updatedAt': row[9].isoformat() if row[9] else None
            })
        
        return jsonify(tasks), 200
        
    except Exception as e:
        print(f'Get tasks error: {str(e)}')
        return jsonify({'message': 'Server error'}), 500
    finally:
        return_db_connection(conn)

@app.route('/api/tasks', methods=['POST'])
@token_required
def create_task():
    """Create a new task"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'message': 'Database connection unavailable'}), 503
    
    try:
        data = request.get_json()
        cursor = conn.cursor()
        
        task_id = data.get('taskId') or f'AUTO-{int(datetime.now().timestamp() * 1000) % 10000}'
        
        cursor.execute("""
            INSERT INTO "Tasks" ("UserId", "TaskId", "Type", "Title", "Description", "Assignee", "Priority", "Status")
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING "Id", "TaskId", "Type", "Title", "Description", 
                   "Assignee", "Priority", "Status", 
                   "CreatedAt", "UpdatedAt"
        """, (
            request.user['userId'],
            task_id,
            data.get('type', 'task'),
            data.get('title'),
            data.get('description', ''),
            data.get('assignee', ''),
            data.get('priority', 'medium'),
            data.get('status', 'todo')
        ))
        
        row = cursor.fetchone()
        conn.commit()
        
        task = {
            'id': str(row[0]),
            'taskId': row[1] or task_id,
            'type': row[2] or 'task',
            'title': row[3],
            'description': row[4] or '',
            'assignee': row[5] or '',
            'priority': row[6] or 'medium',
            'status': row[7] or 'todo',
            'createdAt': row[8].isoformat() if row[8] else None,
            'updatedAt': row[9].isoformat() if row[9] else None
        }
        
        return jsonify(task), 201
        
    except Exception as e:
        print(f'Create task error: {str(e)}')
        conn.rollback()
        return jsonify({'message': 'Server error creating task'}), 500
    finally:
        return_db_connection(conn)

@app.route('/api/tasks/<int:task_id>', methods=['PUT'])
@token_required
def update_task(task_id):
    """Update an existing task"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'message': 'Database connection unavailable'}), 503
    
    try:
        data = request.get_json()
        cursor = conn.cursor()
        
        # Check if task belongs to user
        cursor.execute("""
            SELECT "UserId" FROM "Tasks" WHERE "Id" = %s
        """, (task_id,))
        
        task = cursor.fetchone()
        if not task or task[0] != request.user['userId']:
            return jsonify({'message': 'Task not found'}), 404
        
        cursor.execute("""
            UPDATE "Tasks"
            SET "Type" = %s, "Title" = %s, "Description" = %s, "Assignee" = %s, 
                "Priority" = %s, "Status" = %s
            WHERE "Id" = %s AND "UserId" = %s
            RETURNING "Id", "TaskId", "Type", "Title", "Description",
                   "Assignee", "Priority", "Status",
                   "CreatedAt", "UpdatedAt"
        """, (
            data.get('type', 'task'),
            data.get('title'),
            data.get('description', ''),
            data.get('assignee', ''),
            data.get('priority', 'medium'),
            data.get('status', 'todo'),
            task_id,
            request.user['userId']
        ))
        
        row = cursor.fetchone()
        conn.commit()
        
        if not row:
            return jsonify({'message': 'Task not found'}), 404
        
        task = {
            'id': str(row[0]),
            'taskId': row[1] or f'AUTO-{str(row[0]).zfill(3)}',
            'type': row[2] or 'task',
            'title': row[3],
            'description': row[4] or '',
            'assignee': row[5] or '',
            'priority': row[6] or 'medium',
            'status': row[7] or 'todo',
            'createdAt': row[8].isoformat() if row[8] else None,
            'updatedAt': row[9].isoformat() if row[9] else None
        }
        
        return jsonify(task), 200
        
    except Exception as e:
        print(f'Update task error: {str(e)}')
        conn.rollback()
        return jsonify({'message': 'Server error updating task'}), 500
    finally:
        return_db_connection(conn)

@app.route('/api/tasks/<int:task_id>', methods=['DELETE'])
@token_required
def delete_task(task_id):
    """Delete a task"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'message': 'Database connection unavailable'}), 503
    
    try:
        cursor = conn.cursor()
        
        # Check if task belongs to user
        cursor.execute("""
            SELECT "UserId" FROM "Tasks" WHERE "Id" = %s
        """, (task_id,))
        
        task = cursor.fetchone()
        if not task or task[0] != request.user['userId']:
            return jsonify({'message': 'Task not found'}), 404
        
        cursor.execute("""
            DELETE FROM "Tasks" WHERE "Id" = %s AND "UserId" = %s
        """, (task_id, request.user['userId']))
        
        conn.commit()
        
        return jsonify({'message': 'Task deleted successfully'}), 200
        
    except Exception as e:
        print(f'Delete task error: {str(e)}')
        conn.rollback()
        return jsonify({'message': 'Server error deleting task'}), 500
    finally:
        return_db_connection(conn)

# Serve static files
@app.route('/')
def index():
    """Serve login page"""
    return send_from_directory('.', 'login.html')

@app.route('/login.html')
def login_page():
    """Serve login page"""
    return send_from_directory('.', 'login.html')

@app.route('/index.html')
def board_page():
    """Serve task board page"""
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    """Serve static files"""
    return send_from_directory('.', path)

if __name__ == '__main__':
    # Get port from environment (Railway sets this automatically)
    port = int(os.getenv('PORT', PORT))
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    print(f'Starting Flask server on port {port}...')
    if DATABASE_URL:
        print(f'Database: Using DATABASE_URL (cloud database)')
    else:
        print(f'Database: {DB_NAME} on {DB_HOST}:{DB_PORT}')
    print(f'Debug mode: {debug_mode}')
    
    app.run(host='0.0.0.0', port=port, debug=debug_mode)

