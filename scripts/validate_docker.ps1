# GravityAI Docker Validation Script
# Requires Docker running locally

Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "GravityAI Docker Image Validation Suite" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan

# 1. Build backend image
Write-Host "`n[1/5] Building Docker Backend image..." -ForegroundColor Yellow
$buildStart = Get-Date
docker build -t gravityai-backend:test -f docker/Dockerfile.backend .
$buildEnd = Get-Date
$buildDuration = ($buildEnd - $buildStart).TotalSeconds
Write-Host "Backend image built successfully in $([Math]::Round($buildDuration, 2)) seconds." -ForegroundColor Green

# 2. Report image size
Write-Host "`n[2/5] Querying Image Size..." -ForegroundColor Yellow
$imgSize = docker images gravityai-backend:test --format "{{.Size}}"
Write-Host "gravityai-backend:test Image Size: $imgSize" -ForegroundColor Green

# 3. Start container and monitor startup timing
Write-Host "`n[3/5] Starting container in background..." -ForegroundColor Yellow
$containerId = docker run -d -p 8000:8000 --env APP_ENV=development gravityai-backend:test
Start-Sleep -Seconds 5

$logs = docker logs $containerId
Write-Host "Container logs captured:" -ForegroundColor Gray
Write-Host $logs -ForegroundColor DarkGray

# 4. Verify Health-check endpoint
Write-Host "`n[4/5] Testing Health Check endpoint..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/system/health" -Method Get
    Write-Host "Response received:" -ForegroundColor Green
    $response | Format-List | Out-String | Write-Host -ForegroundColor Gray
    Write-Host "Docker Health Check Passed!" -ForegroundColor Green
} catch {
    Write-Error "Health check endpoint failed: $_"
}

# 5. Clean up container
Write-Host "`n[5/5] Terminating validation container..." -ForegroundColor Yellow
docker kill $containerId | Out-Null
docker rm $containerId | Out-Null
Write-Host "Cleanup complete." -ForegroundColor Green
Write-Host "`nDocker Validation Complete!" -ForegroundColor Cyan
