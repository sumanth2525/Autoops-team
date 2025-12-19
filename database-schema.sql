-- AutoOps Task Board Database Schema
-- Run this script in SQL Server Management Studio (SSMS) to create the database and tables

-- Create Database (if it doesn't exist)
IF NOT EXISTS (SELECT * FROM sys.databases WHERE name = 'AutoOpsDB')
BEGIN
    CREATE DATABASE AutoOpsDB;
END
GO

USE AutoOpsDB;
GO

-- Create Users Table
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
    
    -- Create Indexes for better performance
    CREATE INDEX IX_Users_Username ON [dbo].[Users]([Username]);
    CREATE INDEX IX_Users_Email ON [dbo].[Users]([Email]);
    
    PRINT 'Users table created successfully';
END
ELSE
BEGIN
    PRINT 'Users table already exists';
END
GO

-- Optional: Create Tasks Table (for future use when storing tasks in database)
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[Tasks]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[Tasks] (
        [Id] INT IDENTITY(1,1) PRIMARY KEY,
        [UserId] INT NOT NULL,
        [Title] NVARCHAR(200) NOT NULL,
        [Description] NVARCHAR(MAX),
        [Assignee] NVARCHAR(100),
        [Priority] NVARCHAR(20) DEFAULT 'medium',
        [Status] NVARCHAR(20) DEFAULT 'todo',
        [CreatedAt] DATETIME DEFAULT GETDATE(),
        [UpdatedAt] DATETIME DEFAULT GETDATE(),
        FOREIGN KEY ([UserId]) REFERENCES [dbo].[Users]([Id]) ON DELETE CASCADE
    );
    
    CREATE INDEX IX_Tasks_UserId ON [dbo].[Tasks]([UserId]);
    CREATE INDEX IX_Tasks_Status ON [dbo].[Tasks]([Status]);
    
    PRINT 'Tasks table created successfully';
END
ELSE
BEGIN
    PRINT 'Tasks table already exists';
END
GO

PRINT 'Database setup completed!';
GO

