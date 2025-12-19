const express = require('express');
const { Pool } = require('pg');
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
const cors = require('cors');
const path = require('path');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 3000;
const JWT_SECRET = process.env.JWT_SECRET;
if (!JWT_SECRET) {
    console.error('❌ ERROR: JWT_SECRET environment variable is required. Please set it in your .env file.');
    process.exit(1);
}

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.static(__dirname));

// PostgreSQL Configuration (Cloud Database)
// Use DATABASE_URL if provided (common in cloud platforms like Railway, Heroku, etc.)
// Otherwise use individual connection parameters
const dbConfig = process.env.DATABASE_URL ? {
    connectionString: process.env.DATABASE_URL,
    ssl: process.env.DB_SSL === 'true' ? { rejectUnauthorized: false } : false
} : {
    host: process.env.DB_HOST || 'localhost',
    port: process.env.DB_PORT || 5432,
    database: process.env.DB_NAME || 'postgres',
    user: process.env.DB_USER || 'postgres',
    password: process.env.DB_PASSWORD || '',
    ssl: process.env.DB_SSL === 'true' ? { rejectUnauthorized: false } : false
};

let pool;

// Initialize PostgreSQL Connection Pool
async function initDatabase() {
    try {
        pool = new Pool(dbConfig);
        
        // Test connection
        const client = await pool.connect();
        console.log('✅ Connected to PostgreSQL successfully');
        client.release();
        
        // Create tables if they don't exist
        await createTables();
    } catch (err) {
        console.error('⚠️  Database connection error:', err.message);
        console.error('⚠️  Server will start but database features will be unavailable');
        console.error('⚠️  Please check:');
        console.error('   1. PostgreSQL database is running');
        console.error('   2. Database connection string is correct');
        console.error('   3. DATABASE_URL or DB_HOST/DB_NAME/DB_USER/DB_PASSWORD are set correctly');
        // Don't exit - allow server to start without database for testing
        pool = null;
    }
}

// Create database tables
async function createTables() {
    try {
        const client = await pool.connect();
        
        // Users table
        await client.query(`
            CREATE TABLE IF NOT EXISTS "Users" (
                "Id" SERIAL PRIMARY KEY,
                "Username" VARCHAR(50) NOT NULL UNIQUE,
                "Email" VARCHAR(100) NOT NULL UNIQUE,
                "Password" VARCHAR(255) NOT NULL,
                "FullName" VARCHAR(100),
                "CreatedAt" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                "LastLogin" TIMESTAMP
            )
        `);
        
        // Create indexes
        await client.query('CREATE INDEX IF NOT EXISTS "IX_Users_Username" ON "Users"("Username")');
        await client.query('CREATE INDEX IF NOT EXISTS "IX_Users_Email" ON "Users"("Email")');
        
        // Tasks table
        await client.query(`
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
        `);
        
        // Create indexes for Tasks
        await client.query('CREATE INDEX IF NOT EXISTS "IX_Tasks_UserId" ON "Tasks"("UserId")');
        await client.query('CREATE INDEX IF NOT EXISTS "IX_Tasks_Status" ON "Tasks"("Status")');
        
        // Create function to update UpdatedAt timestamp
        await client.query(`
            CREATE OR REPLACE FUNCTION update_updated_at_column()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW."UpdatedAt" = CURRENT_TIMESTAMP;
                RETURN NEW;
            END;
            $$ language 'plpgsql'
        `);
        
        // Create trigger to auto-update UpdatedAt
        await client.query(`
            DROP TRIGGER IF EXISTS update_tasks_updated_at ON "Tasks";
            CREATE TRIGGER update_tasks_updated_at
                BEFORE UPDATE ON "Tasks"
                FOR EACH ROW
                EXECUTE FUNCTION update_updated_at_column()
        `);
        
        client.release();
        console.log('✅ Database tables created/verified');
    } catch (err) {
        console.error('❌ Error creating tables:', err);
        throw err;
    }
}

// Initialize database on startup
initDatabase();

// Authentication Middleware
function authenticateToken(req, res, next) {
    const authHeader = req.headers['authorization'];
    const token = authHeader && authHeader.split(' ')[1];

    if (!token) {
        return res.status(401).json({ message: 'Access token required' });
    }

    jwt.verify(token, JWT_SECRET, (err, user) => {
        if (err) {
            return res.status(403).json({ message: 'Invalid or expired token' });
        }
        req.user = user;
        next();
    });
}

// Routes

// Health check
app.get('/api/health', (req, res) => {
    res.json({ status: 'ok', message: 'Server is running' });
});

// Register new user
app.post('/api/auth/register', async (req, res) => {
    try {
        if (!pool) {
            return res.status(503).json({ message: 'Database connection unavailable. Please check SQL Server configuration.' });
        }

        const { username, email, password, fullName } = req.body;

        // Validation
        if (!username || !email || !password) {
            return res.status(400).json({ message: 'Username, email, and password are required' });
        }

        if (password.length < 6) {
            return res.status(400).json({ message: 'Password must be at least 6 characters' });
        }

        // Check if user already exists
        const checkResult = await pool.query(`
            SELECT * FROM "Users" 
            WHERE "Username" = $1 OR "Email" = $2
        `, [username, email]);

        if (checkResult.rows.length > 0) {
            return res.status(400).json({ message: 'Username or email already exists' });
        }

        // Hash password
        const hashedPassword = await bcrypt.hash(password, 10);

        // Insert new user
        const result = await pool.query(`
            INSERT INTO "Users" ("Username", "Email", "Password", "FullName")
            VALUES ($1, $2, $3, $4)
            RETURNING "Id", "Username", "Email", "FullName"
        `, [username, email, hashedPassword, fullName || null]);

        const newUser = result.rows[0];
        
        res.status(201).json({
            message: 'User registered successfully',
            user: {
                id: newUser.Id,
                username: newUser.Username,
                email: newUser.Email,
                fullName: newUser.FullName
            }
        });
    } catch (error) {
        console.error('Registration error:', error);
        res.status(500).json({ message: 'Server error during registration' });
    }
});

// Login
app.post('/api/auth/login', async (req, res) => {
    try {
        if (!pool) {
            return res.status(503).json({ message: 'Database connection unavailable. Please check SQL Server configuration.' });
        }

        const { username, password } = req.body;

        if (!username || !password) {
            return res.status(400).json({ message: 'Username and password are required' });
        }

        // Find user
        const result = await pool.query(`
            SELECT * FROM "Users" 
            WHERE "Username" = $1
        `, [username]);

        if (result.rows.length === 0) {
            return res.status(401).json({ message: 'Invalid username or password' });
        }

        const user = result.rows[0];

        // Verify password
        const isValidPassword = await bcrypt.compare(password, user.Password);
        if (!isValidPassword) {
            return res.status(401).json({ message: 'Invalid username or password' });
        }

        // Update last login
        await pool.query(`
            UPDATE "Users" 
            SET "LastLogin" = CURRENT_TIMESTAMP 
            WHERE "Id" = $1
        `, [user.Id]);

        // Generate JWT token
        const token = jwt.sign(
            { userId: user.Id, username: user.Username },
            JWT_SECRET,
            { expiresIn: '7d' }
        );

        res.json({
            message: 'Login successful',
            token,
            userId: user.Id,
            username: user.Username,
            fullName: user.FullName
        });
    } catch (error) {
        console.error('Login error:', error);
        res.status(500).json({ message: 'Server error during login' });
    }
});

// Get current user info
app.get('/api/auth/me', authenticateToken, async (req, res) => {
    try {
        if (!pool) {
            return res.status(503).json({ message: 'Database connection unavailable. Please check SQL Server configuration.' });
        }

        const result = await pool.query(`
            SELECT "Id", "Username", "Email", "FullName", "CreatedAt", "LastLogin" 
            FROM "Users" 
            WHERE "Id" = $1
        `, [req.user.userId]);

        if (result.rows.length === 0) {
            return res.status(404).json({ message: 'User not found' });
        }

        res.json({ user: result.rows[0] });
    } catch (error) {
        console.error('Get user error:', error);
        res.status(500).json({ message: 'Server error' });
    }
});

// Serve static files
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'login.html'));
});

app.get('/index.html', (req, res) => {
    res.sendFile(path.join(__dirname, 'index.html'));
});

app.get('/login.html', (req, res) => {
    res.sendFile(path.join(__dirname, 'login.html'));
});

// Start server
app.listen(PORT, () => {
    console.log(`🚀 Server running on http://localhost:${PORT}`);
    if (process.env.DATABASE_URL) {
        console.log(`📊 Database: Using DATABASE_URL (cloud database)`);
    } else {
        console.log(`📊 Database: ${dbConfig.database} on ${dbConfig.host}:${dbConfig.port}`);
    }
});

// Graceful shutdown
process.on('SIGINT', async () => {
    console.log('\n🛑 Shutting down server...');
    if (pool) {
        await pool.end();
        console.log('✅ Database connection closed');
    }
    process.exit(0);
});
