# Supabase Setup Guide - Next Steps

Since you've already created the **Tasks** and **Users** tables in Supabase, follow these steps to connect your application:

## Step 1: Get Your Supabase Connection String

1. In your Supabase dashboard, click the **"Connect"** button (top right)
2. You'll see connection options:
   - **Connection string** (URI format) - Use this one!
   - **Connection pooling** (for serverless)
   - **Direct connection**

3. Copy the **Connection string (URI)** - it looks like:
   ```
   postgresql://postgres:[YOUR-PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres
   ```

4. **Important:** Replace `[YOUR-PASSWORD]` with your actual database password
   - If you don't know it, go to **Settings** → **Database** → **Database Password**
   - Or reset it if needed

## Step 2: Create .env File

Create a `.env` file in your project root:

```powershell
notepad .env
```

Add these lines (replace with your Supabase connection string):

```env
# Supabase Database Connection
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@db.xxxxx.supabase.co:5432/postgres?sslmode=require
DB_SSL=true

# Application Settings
JWT_SECRET=your-secret-key-here-change-this-to-random-string
PORT=3001

# Optional: Email Configuration (if you want email features)
BREVO_API_KEY=your-brevo-api-key
BREVO_SENDER_EMAIL=noreply@autoops.com
```

**Example DATABASE_URL:**
```
DATABASE_URL=postgresql://postgres:MyPassword123@db.abcdefghijklmnop.supabase.co:5432/postgres?sslmode=require
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

## Step 4: Verify Tables Structure (Optional)

Since you already created tables, verify they match the expected structure:

1. Go to **Table Editor** in Supabase
2. Check that your tables have these columns:

**Users Table:**
- `Id` (SERIAL/INTEGER, Primary Key)
- `Username` (VARCHAR, Unique)
- `Email` (VARCHAR, Unique)
- `Password` (VARCHAR)
- `FullName` (VARCHAR, nullable)
- `CreatedAt` (TIMESTAMP)
- `LastLogin` (TIMESTAMP, nullable)

**Tasks Table:**
- `Id` (SERIAL/INTEGER, Primary Key)
- `UserId` (INTEGER, Foreign Key to Users.Id)
- `TaskId` (VARCHAR, nullable)
- `Type` (VARCHAR, default 'task')
- `Title` (VARCHAR)
- `Description` (TEXT, nullable)
- `Assignee` (VARCHAR, nullable)
- `Priority` (VARCHAR, default 'medium')
- `Status` (VARCHAR, default 'todo')
- `CreatedAt` (TIMESTAMP)
- `UpdatedAt` (TIMESTAMP)

**If columns are missing**, you can add them via SQL Editor:
```sql
-- Add missing columns if needed
ALTER TABLE "Tasks" ADD COLUMN IF NOT EXISTS "TaskId" VARCHAR(50);
ALTER TABLE "Tasks" ADD COLUMN IF NOT EXISTS "Type" VARCHAR(20) DEFAULT 'task';
```

## Step 5: Create Indexes and Trigger (Recommended)

Run this in Supabase **SQL Editor** to optimize performance:

```sql
-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS "IX_Users_Username" ON "Users"("Username");
CREATE INDEX IF NOT EXISTS "IX_Users_Email" ON "Users"("Email");
CREATE INDEX IF NOT EXISTS "IX_Tasks_UserId" ON "Tasks"("UserId");
CREATE INDEX IF NOT EXISTS "IX_Tasks_Status" ON "Tasks"("Status");

-- Create function to auto-update UpdatedAt
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW."UpdatedAt" = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger for Tasks table
DROP TRIGGER IF EXISTS update_tasks_updated_at ON "Tasks";
CREATE TRIGGER update_tasks_updated_at
    BEFORE UPDATE ON "Tasks"
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
```

## Step 6: Run Your Application

### Python/Flask:
```powershell
python app.py
```

### Node.js/Express:
```powershell
npm start
```

## Step 7: Test the Connection

1. Open browser: `http://localhost:3001`
2. Check console output - you should see:
   ```
   ✅ Connected to PostgreSQL successfully
   ✅ Database tables created/verified
   ```
3. Try to **register a new user** to test the connection
4. Check Supabase **Table Editor** - you should see the new user appear

## Step 8: (Optional) Set Up Row Level Security (RLS)

Your tables show "UNRESTRICTED" which means RLS is disabled. For production:

1. Go to **Authentication** → **Policies** in Supabase
2. Enable RLS on your tables
3. Create policies to control access

**For now, you can skip this** - your application handles authentication via JWT tokens.

## Troubleshooting

### Connection Error: "SSL connection required"
- Make sure your DATABASE_URL includes `?sslmode=require` at the end
- Or set `DB_SSL=true` in `.env`

### Connection Error: "password authentication failed"
- Double-check your database password in Supabase Settings
- Make sure there are no extra spaces in DATABASE_URL
- URL-encode special characters in password if needed

### Tables not found error
- Verify table names are exactly: `"Users"` and `"Tasks"` (with quotes, case-sensitive)
- Check you're using the correct schema (usually `public`)

### Test Connection Manually

**Python:**
```powershell
python -c "import psycopg2; import os; from dotenv import load_dotenv; load_dotenv(); conn = psycopg2.connect(os.getenv('DATABASE_URL')); print('✅ Connected!'); conn.close()"
```

**Node.js:**
```powershell
node -e "require('dotenv').config(); const {Pool}=require('pg'); const p=new Pool({connectionString:process.env.DATABASE_URL}); p.query('SELECT NOW()').then(r=>{console.log('✅ Connected!',r.rows[0]); p.end()})"
```

## Quick Commands Summary

```powershell
# 1. Create .env file
notepad .env

# 2. Install dependencies (Python)
pip install -r requirements.txt

# OR (Node.js)
npm install

# 3. Run application
python app.py
# OR
npm start

# 4. Test in browser
# Open: http://localhost:3001
```

## Next Steps After Connection Works

1. ✅ Test user registration
2. ✅ Test user login
3. ✅ Test creating tasks
4. ✅ Verify data appears in Supabase Table Editor
5. 🚀 Deploy your application to production

---

**Need Help?** Check the console output for specific error messages and refer to the troubleshooting section above.
