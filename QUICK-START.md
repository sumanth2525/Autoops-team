# Quick Start Guide - AutoOps Task Board

## Fastest Way to Run (Windows)

### Option 1: Use the Quick Start Script (Easiest)
```batch
quick-start.bat
```

This script will:
- Check Python installation
- Install dependencies automatically
- Create .env file if missing
- Start the server

### Option 2: Manual Commands

#### 1. Install Dependencies
```batch
pip install -r requirements.txt
pip install pyodbc
```

#### 2. Create .env File (if not exists)
Create a `.env` file in the project root with:
```env
JWT_SECRET=your-secret-key-change-this-in-production
PORT=3001
DB_SERVER=SUMANTH\SQLEXPRESS
DB_NAME=AutoOpsDB
DB_USER=
DB_PASSWORD=
EMAIL_METHOD=api
BREVO_API_KEY=
BREVO_SENDER_EMAIL=noreply@autoops.com
BREVO_SENDER_NAME=AutoOps Team
```

#### 3. Run the Application
```batch
python run.py
```

Or:
```batch
python app.py
```

## Access the Application

- **Login Page**: http://localhost:3001
- **Task Board**: http://localhost:3001/index.html
- **API Health Check**: http://localhost:3001/api/health

## Quick Commands Reference

### Start Server
```batch
python run.py
```

### Install/Update Dependencies
```batch
pip install -r requirements.txt
pip install pyodbc
```

### Check if Server is Running
```batch
curl http://localhost:3001/api/health
```

### Stop Server
Press `Ctrl+C` in the terminal

## Troubleshooting

### Port Already in Use
If port 3001 is busy, change `PORT` in `.env` file or use:
```batch
set PORT=3002 && python run.py
```

### Database Connection Issues
- Make sure SQL Server is running
- Check `DB_SERVER` in `.env` matches your SQL Server instance
- For Windows Authentication, leave `DB_USER` and `DB_PASSWORD` empty

### Missing Dependencies
```batch
pip install --upgrade -r requirements.txt
```

## Development Mode

For development with auto-reload:
```batch
set FLASK_DEBUG=True && python run.py
```
