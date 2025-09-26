@echo off
echo Starting Nova Monitoring Stack...
echo.
echo Prometheus will be available at: http://localhost:9090
echo Grafana will be available at: http://localhost:3000 (admin/nova123)
echo.
cd /d "%~dp0"
docker-compose up -d
echo.
echo Stack started! Access:
echo - Prometheus: http://localhost:9090
echo - Grafana: http://localhost:3000 (login: admin/nova123)
echo.
pause