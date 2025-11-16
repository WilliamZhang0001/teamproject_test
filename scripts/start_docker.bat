@echo off
chcp 65001 >nul
set skipPause=0
if /I "%~1"=="--no-pause" set skipPause=1
echo Starting Docker containers...
docker-compose up -d

echo Waiting for services to be ready...
timeout /t 5 /nobreak >nul

set maxRetries=30
set retryCount=0
set serviceReady=0

:check_loop
set /a retryCount+=1
echo Checking if frontend service is ready... (%retryCount%/%maxRetries%)

REM Use PowerShell to check service (more reliable)
powershell -Command "$response = Invoke-WebRequest -Uri 'http://localhost:3000' -TimeoutSec 2 -UseBasicParsing -ErrorAction SilentlyContinue; if ($response.StatusCode -eq 200) { exit 0 } else { exit 1 }" >nul 2>&1

if %errorlevel% equ 0 (
    echo Frontend service is ready!
    echo Opening browser...
    start http://localhost:3000
    echo.
    echo Docker containers started, browser opened!
    echo API Documentation: http://localhost:8000/docs
    echo Backend API: http://localhost:8000
    echo.
    echo View logs: docker-compose logs -f
    echo Stop services: docker-compose down
    goto :end
)

if %retryCount% geq %maxRetries% (
    echo Service startup timeout, but containers may still be starting...
    echo Please manually access: http://localhost:3000
    echo View logs: docker-compose logs -f
    goto :end
)

echo Service not ready yet, waiting 3 seconds before retry...
timeout /t 3 /nobreak >nul
goto :check_loop

:end
if "%skipPause%"=="0" (
    pause
)
exit /b

