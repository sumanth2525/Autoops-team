@echo off
echo ========================================
echo AutoOps Task Board - Push to GitHub
echo ========================================
echo.

echo Step 1: Setting up remote...
git remote remove origin 2>nul
git remote add origin https://github.com/sumanth2525/autoops-task-board.git

REM If remote already exists, update it
git remote set-url origin https://github.com/sumanth2525/autoops-task-board.git 2>nul

echo.
echo Step 2: Renaming branch to main...
git branch -M main

echo.
echo Step 3: Pushing to GitHub...
echo.
echo NOTE: When prompted for credentials:
echo   Username: sumanth2525
echo   Password: [Use your Personal Access Token, NOT your GitHub password]
echo.
echo If you don't have a token yet:
echo   1. Go to: https://github.com/settings/tokens
echo   2. Generate new token (classic) with 'repo' scope
echo   3. Copy the token and use it as password
echo.

git push -u origin main

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo SUCCESS! Code pushed to GitHub!
    echo ========================================
    echo.
    echo View your repo at:
    echo https://github.com/sumanth2525/autoops-task-board
    echo.
) else (
    echo.
    echo ========================================
    echo ERROR: Push failed
    echo ========================================
    echo.
    echo Common issues:
    echo   1. Repository doesn't exist - Create it at https://github.com/new
    echo   2. Wrong credentials - Use Personal Access Token, not password
    echo   3. Token expired - Generate a new token
    echo.
    echo Get help: See GITHUB-TOKEN-SETUP.md
    echo.
)

pause

