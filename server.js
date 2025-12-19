const express = require('express');
const sql = require('mssql');
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

// SQL Server Configuration
const dbConfig = {
    server: process.env.DB_SERVER || 'SUMANTH\\SQLEXPRESS',
    database: process.env.DB_NAME || 'AutoOpsDB',
    user: process.env.DB_USER || '',
    password: process.env.DB_PASSWORD || '',
    options: {
        encrypt: process.env.DB_ENCRYPT === 'true', // Use true for Azure SQL
        trustServerCertificate: true, // Use true for local SQL Server
        enableArithAbort: true
    }
};

// Use Windows Authentication if no user/password provided
if (!dbConfig.user && !dbConfig.password) {
    dbConfig.options.trustedConnection = true;
}

let pool;

// Initialize SQL Server Connection Pool
async function initDatabase() {
    try {
        pool = await sql.connect(dbConfig);
        console.log('✅ Connected to SQL Server successfully');
        
        // Create tables if they don't exist
        await createTables();
    } catch (err) {
        console.error('⚠️  Database connection error:', err.message);
        console.error('⚠️  Server will start but database features will be unavailable');
        console.error('⚠️  Please check:');
        console.error('   1. SQL Server is running');
        console.error('   2. Database "AutoOpsDB" exists');
        console.error('   3. Your Windows user has access to SQL Server');
        console.error('   4. Server name in .env matches your SQL Server instance');
        // Don't exit - allow server to start without database for testing
        pool = null;
    }
}

// Create database tables
async function createTables() {
    try {
        const request = pool.request();
        
        // Users table
        await request.query(`
            IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[Users]') AND type in (N'U'))
            BEGIN
                CREATE TABLE [dbo].[Users] (
                    [Id] INT IDENTITY(1,1) PRIMARY KEY,
                    [Username] NVARCHAR(50) NOT NULL UNIQUE,
                    [Email] NVARCHAR(100) NOT NULL UNIQUE,
                    [Password] NVARCHAR(255) NOT NULL,
                    [FullName] NVARCHAR(100),
                    [CreatedAt] DATETIME DEFAULT GETDATE(),
                    [LastLogin] DATETIME
                );
                CREATE INDEX IX_Users_Username ON [dbo].[Users]([Username]);
                CREATE INDEX IX_Users_Email ON [dbo].[Users]([Email]);
            END
        `);
        
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
        const checkRequest = pool.request();
        checkRequest.input('username', sql.NVarChar, username);
        checkRequest.input('email', sql.NVarChar, email);
        
        const existingUser = await checkRequest.query(`
            SELECT * FROM [dbo].[Users] 
            WHERE Username = @username OR Email = @email
        `);

        if (existingUser.recordset.length > 0) {
            return res.status(400).json({ message: 'Username or email already exists' });
        }

        // Hash password
        const hashedPassword = await bcrypt.hash(password, 10);

        // Insert new user
        const insertRequest = pool.request();
        insertRequest.input('username', sql.NVarChar, username);
        insertRequest.input('email', sql.NVarChar, email);
        insertRequest.input('password', sql.NVarChar, hashedPassword);
        insertRequest.input('fullName', sql.NVarChar, fullName || null);

        const result = await insertRequest.query(`
            INSERT INTO [dbo].[Users] (Username, Email, Password, FullName)
            OUTPUT INSERTED.Id, INSERTED.Username, INSERTED.Email, INSERTED.FullName
            VALUES (@username, @email, @password, @fullName)
        `);

        const newUser = result.recordset[0];
        
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
        const request = pool.request();
        request.input('username', sql.NVarChar, username);
        
        const result = await request.query(`
            SELECT * FROM [dbo].[Users] 
            WHERE Username = @username
        `);

        if (result.recordset.length === 0) {
            return res.status(401).json({ message: 'Invalid username or password' });
        }

        const user = result.recordset[0];

        // Verify password
        const isValidPassword = await bcrypt.compare(password, user.Password);
        if (!isValidPassword) {
            return res.status(401).json({ message: 'Invalid username or password' });
        }

        // Update last login
        const updateRequest = pool.request();
        updateRequest.input('userId', sql.Int, user.Id);
        await updateRequest.query(`
            UPDATE [dbo].[Users] 
            SET LastLogin = GETDATE() 
            WHERE Id = @userId
        `);

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

        const request = pool.request();
        request.input('userId', sql.Int, req.user.userId);
        
        const result = await request.query(`
            SELECT Id, Username, Email, FullName, CreatedAt, LastLogin 
            FROM [dbo].[Users] 
            WHERE Id = @userId
        `);

        if (result.recordset.length === 0) {
            return res.status(404).json({ message: 'User not found' });
        }

        res.json({ user: result.recordset[0] });
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
    console.log(`📊 Database: ${dbConfig.database} on ${dbConfig.server}`);
});

// Graceful shutdown
process.on('SIGINT', async () => {
    console.log('\n🛑 Shutting down server...');
    if (pool) {
        await pool.close();
        console.log('✅ Database connection closed');
    }
    process.exit(0);
});
