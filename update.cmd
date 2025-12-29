@echo off
setlocal

echo Updating foothold-sitac...

:: Pull latest changes from main branch
echo Fetching latest version from GitHub...
git pull origin main

:: Update dependencies
echo Installing/updating dependencies...
call poetry install --only main

echo Update complete!
echo this console should be closed automatically in 5 seconds
timeout /t 5
