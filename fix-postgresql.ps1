# 修复 PostgreSQL 初始化问题
# 使用方法: .\fix-postgresql.ps1

$SERVER = "root@66.154.108.62"
$SERVER_PORT = "22"

Write-Host "Checking PostgreSQL status..." -ForegroundColor Green

ssh -p $SERVER_PORT $SERVER @"
echo "=== PostgreSQL Service Status ==="
systemctl status postgresql --no-pager -l 2>/dev/null || echo "Service not running or not installed"

echo ""
echo "=== Data Directory Status ==="
if [ -d "/var/lib/pgsql/data" ]; then
    echo "Data directory exists: /var/lib/pgsql/data"
    echo "Directory contents:"
    ls -la /var/lib/pgsql/data 2>/dev/null | head -20 || echo "Cannot list contents"
    
    # Check if PostgreSQL is running
    if systemctl is-active --quiet postgresql 2>/dev/null; then
        echo ""
        echo "PostgreSQL is RUNNING - initialization not needed!"
        echo "You can proceed with database setup."
    else
        echo ""
        echo "PostgreSQL is NOT running"
        echo "Attempting to start PostgreSQL..."
        systemctl start postgresql 2>/dev/null && echo "Started successfully" || echo "Start failed"
    fi
else
    echo "Data directory does not exist"
fi

echo ""
echo "=== Try to connect to PostgreSQL ==="
sudo -u postgres psql -c "SELECT version();" 2>/dev/null && echo "PostgreSQL is accessible" || echo "Cannot connect to PostgreSQL"
"@

Write-Host ""
Write-Host "Check completed" -ForegroundColor Green


