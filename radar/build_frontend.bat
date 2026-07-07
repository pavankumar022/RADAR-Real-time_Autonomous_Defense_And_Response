@echo off
echo [RADAR] Building React frontend...
cd frontend
call npm run build
if errorlevel 1 (
    echo ERROR: Frontend build failed.
    cd ..
    exit /b 1
)
cd ..
if exist backend\dist rmdir /s /q backend\dist
xcopy /e /i /q frontend\dist backend\dist
echo [RADAR] Frontend built into backend\dist successfully.
