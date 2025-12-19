-- AutoOps Task Board Database Setup Script
-- Run this script in SQL Server Management Studio to create the database

-- Create database if it doesn't exist
IF NOT EXISTS (SELECT * FROM sys.databases WHERE name = 'AutoOpsDB')
BEGIN
    CREATE DATABASE AutoOpsDB;
    PRINT 'Database AutoOpsDB created successfully.';
END
ELSE
BEGIN
    PRINT 'Database AutoOpsDB already exists.';
END
GO

USE AutoOpsDB;
GO

-- Create Users table
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Users' AND xtype='U')
BEGIN
    CREATE TABLE Users (
        UserId INT PRIMARY KEY IDENTITY(1,1),
        Username NVARCHAR(50) UNIQUE NOT NULL,
        Email NVARCHAR(100) UNIQUE NOT NULL,
        PasswordHash NVARCHAR(255) NOT NULL,
        FullName NVARCHAR(100),
        CreatedAt DATETIME DEFAULT GETDATE()
    );
    PRINT 'Users table created successfully.';
END
ELSE
BEGIN
    PRINT 'Users table already exists.';
END
GO

-- Create Tasks table
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Tasks' AND xtype='U')
BEGIN
    CREATE TABLE Tasks (
        TaskId INT PRIMARY KEY IDENTITY(1,1),
        UserId INT NOT NULL,
        Title NVARCHAR(200) NOT NULL,
        Description NVARCHAR(MAX),
        Assignee NVARCHAR(100),
        Priority NVARCHAR(20) DEFAULT 'medium',
        Status NVARCHAR(20) DEFAULT 'todo',
        CreatedAt DATETIME DEFAULT GETDATE(),
        UpdatedAt DATETIME DEFAULT GETDATE(),
        FOREIGN KEY (UserId) REFERENCES Users(UserId) ON DELETE CASCADE
    );
    PRINT 'Tasks table created successfully.';
END
ELSE
BEGIN
    PRINT 'Tasks table already exists.';
END
GO

-- Create index on UserId for better performance
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name='IX_Tasks_UserId')
BEGIN
    CREATE INDEX IX_Tasks_UserId ON Tasks(UserId);
    PRINT 'Index on Tasks.UserId created successfully.';
END
GO

PRINT 'Database setup completed!';
GO

