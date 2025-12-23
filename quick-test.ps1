# Quick API Test
$baseUrl = "http://66.154.108.62"
Write-Host "Testing API endpoints..." -ForegroundColor Cyan

# Test 1: Health check
Write-Host "`n1. Testing health endpoint..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/api/health" -Method GET -ErrorAction Stop
    Write-Host "   Health check: OK" -ForegroundColor Green
} catch {
    Write-Host "   Health check: FAILED - $($_.Exception.Message)" -ForegroundColor Red
}

# Test 2: Frontend
Write-Host "`n2. Testing frontend..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "$baseUrl/" -Method GET -UseBasicParsing -ErrorAction Stop
    if ($response.StatusCode -eq 200) {
        Write-Host "   Frontend: OK (Status: $($response.StatusCode))" -ForegroundColor Green
    }
} catch {
    Write-Host "   Frontend: FAILED - $($_.Exception.Message)" -ForegroundColor Red
}

# Test 3: Backend service status
Write-Host "`n3. Testing backend service..." -ForegroundColor Yellow
try {
    ssh root@66.154.108.62 "systemctl is-active novawrite-backend" | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   Backend service: Running" -ForegroundColor Green
    } else {
        Write-Host "   Backend service: Not running" -ForegroundColor Red
    }
} catch {
    Write-Host "   Backend service: Unable to check" -ForegroundColor Yellow
}

Write-Host "`nTest completed!" -ForegroundColor Cyan

