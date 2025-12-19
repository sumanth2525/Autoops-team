-- AutoOps Task Board Database Schema (PostgreSQL)
-- Run this script in your cloud database to create the tables

-- Create Users Table
CREATE TABLE IF NOT EXISTS "Users" (
    "Id" SERIAL PRIMARY KEY,
    "Username" VARCHAR(50) NOT NULL UNIQUE,
    "Email" VARCHAR(100) NOT NULL UNIQUE,
    "Password" VARCHAR(255) NOT NULL,
    "FullName" VARCHAR(100),
    "CreatedAt" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    "LastLogin" TIMESTAMP
);

-- Create Indexes for better performance
CREATE INDEX IF NOT EXISTS "IX_Users_Username" ON "Users"("Username");
CREATE INDEX IF NOT EXISTS "IX_Users_Email" ON "Users"("Email");

-- Create Tasks Table
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
);

-- Create Indexes for Tasks
CREATE INDEX IF NOT EXISTS "IX_Tasks_UserId" ON "Tasks"("UserId");
CREATE INDEX IF NOT EXISTS "IX_Tasks_Status" ON "Tasks"("Status");

-- Create function to update UpdatedAt timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW."UpdatedAt" = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger to auto-update UpdatedAt
DROP TRIGGER IF EXISTS update_tasks_updated_at ON "Tasks";
CREATE TRIGGER update_tasks_updated_at
    BEFORE UPDATE ON "Tasks"
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
