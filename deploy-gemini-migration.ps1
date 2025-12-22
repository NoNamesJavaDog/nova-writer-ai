# 部署 Gemini API 迁移
# 使用方法: .\deploy-gemini-migration.ps1

$SERVER = "root@66.154.108.62"
$SERVER_PORT = "22"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  部署 Gemini API 迁移" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 1. 上传后端文件
Write-Host "[1/4] 上传后端文件..." -ForegroundColor Yellow
scp -P $SERVER_PORT backend/gemini_service.py "${SERVER}:/opt/novawrite-ai/backend/"
scp -P $SERVER_PORT backend/main.py "${SERVER}:/opt/novawrite-ai/backend/"
scp -P $SERVER_PORT backend/schemas.py "${SERVER}:/opt/novawrite-ai/backend/"
scp -P $SERVER_PORT backend/config.py "${SERVER}:/opt/novawrite-ai/backend/"
scp -P $SERVER_PORT backend/requirements.txt "${SERVER}:/opt/novawrite-ai/backend/"

Write-Host "✅ 后端文件上传完成" -ForegroundColor Green

# 2. 安装依赖
Write-Host ""
Write-Host "[2/4] 安装后端依赖..." -ForegroundColor Yellow
ssh -p $SERVER_PORT $SERVER "cd /opt/novawrite-ai/backend && source ../venv/bin/activate && pip install google-genai>=0.2.0"

Write-Host "✅ 依赖安装完成" -ForegroundColor Green

# 3. 检查并配置 GEMINI_API_KEY
Write-Host ""
Write-Host "[3/4] 检查 GEMINI_API_KEY 配置..." -ForegroundColor Yellow
$hasKey = ssh -p $SERVER_PORT $SERVER "grep -q '^GEMINI_API_KEY=' /opt/novawrite-ai/backend/.env 2>/dev/null && echo 'yes' || echo 'no'"

if ($hasKey -match "no") {
    Write-Host "⚠️  未找到 GEMINI_API_KEY，请在服务器上配置:" -ForegroundColor Yellow
    Write-Host "  ssh $SERVER -p $SERVER_PORT" -ForegroundColor Gray
    Write-Host "  echo 'GEMINI_API_KEY=your_key_here' >> /opt/novawrite-ai/backend/.env" -ForegroundColor Gray
} else {
    Write-Host "✅ GEMINI_API_KEY 已配置" -ForegroundColor Green
}

# 4. 重启后端服务
Write-Host ""
Write-Host "[4/4] 重启后端服务..." -ForegroundColor Yellow
ssh -p $SERVER_PORT $SERVER "systemctl restart novawrite-backend; sleep 3; systemctl status novawrite-backend --no-pager | head -10"

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  后端部署完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "下一步: 重新部署前端" -ForegroundColor Yellow
Write-Host "  运行: .\deploy.ps1" -ForegroundColor Gray
Write-Host ""
