@echo off
echo ========================================
echo Create GitHub Repo and Push
echo ========================================
echo.

echo STEP 1: Create Repository on GitHub
echo.
echo Please do this FIRST:
echo   1. Open: https://github.com/new
echo   2. Repository name: autoops-task-board
echo   3. Choose Public or Private
echo   4. DO NOT check any boxes (README, .gitignore, license)
echo   5. Click "Create repository"
echo.
echo Press any key after you've created the repository...
pause >nul

echo.
echo ========================================
echo STEP 2: Setting up remote...
echo ========================================
echo.

REM Remove existing remote if any
git remote remove origin 2>nul

REM Add new remote
git remote add origin https://github.com/sumanth2525/autoops-task-board.git

echo Remote added: https://github.com/sumanth2525/autoops-task-board.git
echo.

echo ========================================
echo STEP 3: Renaming branch to main...
echo ========================================
echo.
git branch -M main
echo Branch renamed to main
echo.

echo ========================================
echo STEP 4: Pushing to GitHub...
echo ========================================
echo.
echo IMPORTANT: When prompted for credentials:
echo   Username: sumanth2525
echo   Password: [Use Personal Access Token, NOT your GitHub password]
echo.
echo If you don't have a token:
echo   1. Go to: https://github.com/settings/tokens
echo   2. Generate new token (classic) with 'repo' scope
echo   3. Copy and use it as password
echo.
echo Press any key to continue with push...
pause >nul

git push -u origin main

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo ✅ SUCCESS! Code pushed to GitHub!
    echo ========================================
    echo.
    echo View your repository at:
    echo https://github.com/sumanth2525/autoops-task-board
    echo.
    echo Next steps:
    echo   1. Deploy to Railway: See RAILWAY-DEPLOY.md
    echo   2. Share with your team
    echo.
) else (
    echo.
    echo ========================================
    echo ❌ ERROR: Push failed
    echo ========================================
    echo.
    echo Common issues:
    echo   1. Repository doesn't exist - Make sure you created it first
    echo   2. Wrong credentials - Use Personal Access Token
    echo   3. Token expired - Generate a new token
    echo   4. Network issue - Check your internet connection
    echo.
    echo Get help: See GITHUB-TOKEN-SETUP.md
    echo.
)

pause

