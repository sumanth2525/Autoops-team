# Cloud Database Setup Guide

This guide will help you migrate from local SQL Server to a cloud PostgreSQL database.

## Step 1: Get Your Cloud Database Connection String

1. **In your cloud database dashboard** (Railway, Neon, Heroku, etc.):
   - Click the **"Connect"** button (usually shown in the database section)
   - Copy the **Connection String** or **DATABASE_URL**
   - It should look like:
     ```
     postgresql://user:password@host:port/database?sslmode=require
     ```

## Step 2: Set Up Environment Variables

Create or update your `.env` file with the cloud database connection:

### Option A: Using DATABASE_URL (Recommended)
```env
DATABASE_URL=postgresql://user:password@host:port/database?sslmode=require
DB_SSL=true
JWT_SECRET=your-secret-key-here
PORT=3001
```

### Option B: Using Individual Parameters
```env
DB_HOST=your-database-host
DB_PORT=5432
DB_NAME=your-database-name
DB_USER=your-username
DB_PASSWORD=your-password
DB_SSL=true
JWT_SECRET=your-secret-key-here
PORT=3001
```

## Step 3: Install Dependencies

### For Python/Flask:
```powershell
pip install -r requirements.txt
```

### For Node.js/Express:
```powershell
npm install
```

## Step 4: Set Up Database Schema

### Option A: Run SQL Script in Cloud Database Dashboard
1. Open your cloud database dashboard
2. Go to **SQL Editor** or **Query** section
3. Copy the contents of `database-schema-postgresql.sql`
4. Paste and execute the script

### Option B: Use psql Command Line (if you have psql installed)
```powershell
psql "your-database-url" -f database-schema-postgresql.sql
```

### Option C: Tables Will Auto-Create
The application will automatically create tables on first run if they don't exist.

## Step 5: Run the Application

### Python/Flask:
```powershell
python app.py
```

### Node.js/Express:
```powershell
npm start
```

## Step 6: Verify Connection

1. Open your browser: `http://localhost:3001`
2. Try to register a new user
3. Check the console for: `✅ Connected to PostgreSQL successfully`

## Troubleshooting

### Connection Issues

**Error: "Database connection unavailable"**
- Check your `.env` file has correct credentials
- Verify DATABASE_URL is correct (no extra spaces)
- Ensure SSL is enabled if required (set `DB_SSL=true`)

**Error: "SSL connection required"**
- Add `?sslmode=require` to your DATABASE_URL
- Or set `DB_SSL=true` in `.env`

**Error: "password authentication failed"**
- Double-check your database password
- Some cloud providers require you to reset the password

### Common Commands

**Check if .env file exists:**
```powershell
type .env
```

**View environment variables:**
```powershell
Get-Content .env
```

**Test database connection (Python):**
```powershell
python -c "import psycopg2; conn = psycopg2.connect('your-database-url'); print('Connected!')"
```

**Test database connection (Node.js):**
```powershell
node -e "const {Pool}=require('pg'); const p=new Pool({connectionString:process.env.DATABASE_URL}); p.query('SELECT NOW()').then(r=>{console.log('Connected!',r.rows[0]); p.end()})"
```

## Quick Setup Commands (All-in-One)

### Python Setup:
```powershell
# 1. Install dependencies
pip install -r requirements.txt

# 2. Create .env file (edit with your values)
notepad .env

# 3. Run application
python app.py
```

### Node.js Setup:
```powershell
# 1. Install dependencies
npm install

# 2. Create .env file (edit with your values)
notepad .env

# 3. Run application
npm start
```

## Environment Variables Reference

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | Full PostgreSQL connection string | `postgresql://user:pass@host:5432/db` |
| `DB_HOST` | Database host (if not using DATABASE_URL) | `your-db.railway.app` |
| `DB_PORT` | Database port | `5432` |
| `DB_NAME` | Database name | `postgres` |
| `DB_USER` | Database username | `postgres` |
| `DB_PASSWORD` | Database password | `your-password` |
| `DB_SSL` | Enable SSL connection | `true` |
| `JWT_SECRET` | Secret key for JWT tokens | `your-secret-key` |
| `PORT` | Server port | `3001` |

## Next Steps

1. ✅ Database connected
2. ✅ Tables created
3. ✅ Application running
4. 🚀 Deploy to production (Railway, Heroku, etc.)

---

**Note:** The application automatically creates tables on first connection if they don't exist, so you can skip Step 4 if you prefer.
