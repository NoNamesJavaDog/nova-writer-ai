# 检查服务器系统信息
# 使用方法: .\check-server.ps1

$SERVER = "root@66.154.108.62"
$SERVER_PORT = "22"

Write-Host "Checking server system information..." -ForegroundColor Green

ssh -p $SERVER_PORT $SERVER @"
echo "=== System Information ===" 
cat /etc/os-release 2>/dev/null || cat /etc/redhat-release 2>/dev/null || uname -a
echo ""
echo "=== Package Managers ==="
which apt-get 2>/dev/null && echo "apt-get: OK" || echo "apt-get: NOT FOUND"
which yum 2>/dev/null && echo "yum: OK" || echo "yum: NOT FOUND"
which dnf 2>/dev/null && echo "dnf: OK" || echo "dnf: NOT FOUND"
echo ""
echo "=== Python ==="
python3 --version 2>/dev/null || python --version 2>/dev/null || echo "Python: NOT INSTALLED"
echo ""
echo "=== PostgreSQL ==="
which psql 2>/dev/null && echo "PostgreSQL: OK" || echo "PostgreSQL: NOT FOUND"
echo ""
echo "=== Nginx ==="
which nginx 2>/dev/null && echo "Nginx: OK" || echo "Nginx: NOT FOUND"
"@

Write-Host ""
Write-Host "Check completed" -ForegroundColor Green
