Write-Host "Starting Nova Monitoring Stack..." -ForegroundColor Green
Write-Host ""
Write-Host "Prometheus will be available at: http://localhost:9090" -ForegroundColor Yellow
Write-Host "Grafana will be available at: http://localhost:3000 (admin/nova123)" -ForegroundColor Yellow
Write-Host ""

Set-Location $PSScriptRoot
docker-compose up -d

Write-Host ""
Write-Host "Stack started! Access:" -ForegroundColor Green
Write-Host "- Prometheus: http://localhost:9090" -ForegroundColor Cyan
Write-Host "- Grafana: http://localhost:3000 (login: admin/nova123)" -ForegroundColor Cyan
Write-Host ""
Read-Host "Press Enter to continue"