# PowerShell script to start Docker and automatically open browser
Write-Host "Starting Docker containers..." -ForegroundColor Cyan
docker-compose up -d

Write-Host "Waiting for services to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

$maxRetries = 30
$retryCount = 0
$serviceReady = $false

while ($retryCount -lt $maxRetries -and -not $serviceReady) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:3000" -TimeoutSec 2 -UseBasicParsing -ErrorAction SilentlyContinue
        if ($response.StatusCode -eq 200) {
            $serviceReady = $true
            Write-Host "Frontend service is ready!" -ForegroundColor Green
            Write-Host "Opening browser..." -ForegroundColor Cyan
            Start-Process "http://localhost:3000"
            Write-Host ""
            Write-Host "Docker containers started, browser opened!" -ForegroundColor Green
            Write-Host "API Documentation: http://localhost:8000/docs" -ForegroundColor Yellow
            Write-Host "Backend API: http://localhost:8000" -ForegroundColor Yellow
            Write-Host ""
            Write-Host "View logs: docker-compose logs -f" -ForegroundColor Cyan
            Write-Host "Stop services: docker-compose down" -ForegroundColor Cyan
        }
    } catch {
        $retryCount++
        Write-Host "Service not ready yet, waiting 3 seconds before retry... ($retryCount/$maxRetries)" -ForegroundColor Yellow
        Start-Sleep -Seconds 3
    }
}

if (-not $serviceReady) {
    Write-Host "Service startup timeout, but containers may still be starting..." -ForegroundColor Red
    Write-Host "Please manually access: http://localhost:3000" -ForegroundColor Yellow
}

