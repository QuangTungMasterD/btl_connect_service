@echo off
setlocal enabledelayedexpansion

set SCRIPT_DIR=%~dp0
set PROJECT_ROOT=%SCRIPT_DIR%..

set COLLECTION=%SCRIPT_DIR%collection\notification_collection.json
set ENV_FILE=%SCRIPT_DIR%environment\notification_environment.json
set PUBLISH_SCRIPT=%SCRIPT_DIR%scripts\publish_events.py
set REPORTS_DIR=%PROJECT_ROOT%\reports
set REPORT_JSON=%REPORTS_DIR%\newman-report.json
set REPORT_HTML=%REPORTS_DIR%\newman-report.html

if not exist "%REPORTS_DIR%" mkdir "%REPORTS_DIR%"

echo 🚀 B7 Notification Service Test Suite (Windows)
echo ==============================================
echo 📁 Project root: %PROJECT_ROOT%
echo 📄 JSON report: %REPORT_JSON%
echo 📄 HTML report: %REPORT_HTML%

curl -s http://localhost:8000/health > nul
if errorlevel 1 (
    echo ❌ B7 service is not running at http://localhost:8000
    echo    Please start it with: docker-compose up -d
    exit /b 1
)

echo 📤 Sending test events to RabbitMQ...
for /f "delims=" %%a in ('python "%PUBLISH_SCRIPT%" --host localhost --port 5672') do set EVENT_ID=%%a
if "%EVENT_ID%"=="" (
    echo ❌ Failed to get event ID. Please check RabbitMQ and script.
    exit /b 1
)
echo    Event ID for created: %EVENT_ID%

echo ⏳ Waiting for events to be processed...
timeout /t 5 /nobreak > nul

:: Cập nhật testEventId vào environment file bằng Python (chính xác và an toàn)
python -c "import json; data=json.load(open('%ENV_FILE%','r')); [v.update({'value':'%EVENT_ID%'}) for v in data.get('values',[]) if v.get('key')=='testEventId']; json.dump(data, open('%ENV_FILE%','w'), indent=2)"

echo.
echo 🧪 Running Newman tests...
echo ===========================

cd /d "%SCRIPT_DIR%"
if not exist "node_modules\newman-reporter-htmlextra" (
    echo 📦 Installing newman-reporter-htmlextra locally...
    call npm install newman-reporter-htmlextra
)

npx newman run "%COLLECTION%" ^
    --environment "%ENV_FILE%" ^
    --reporters cli,json,htmlextra ^
    --reporter-json-export "%REPORT_JSON%" ^
    --reporter-htmlextra-export "%REPORT_HTML%"

echo.
echo ✅ Tests completed.
echo 📊 JSON report: %REPORT_JSON%
echo 📄 HTML report: %REPORT_HTML%