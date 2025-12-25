# 依赖安装脚本（Windows PowerShell）

Write-Host "=========================================="
Write-Host "安装 pgvector 向量数据库依赖"
Write-Host "=========================================="

# 检查Python
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Python 未安装" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Python 已安装: $(python --version)" -ForegroundColor Green

# 升级pip
Write-Host ""
Write-Host "升级 pip..."
python -m pip install --upgrade pip

# 安装依赖
Write-Host ""
Write-Host "安装依赖包..."
python -m pip install -r requirements.txt

# 验证安装
Write-Host ""
Write-Host "验证安装..."
python -c "
import sys
missing = []

try:
    import redis
    print('✅ redis')
except ImportError:
    print('⚠️  redis (可选)')
    missing.append('redis')

try:
    import sqlalchemy
    print('✅ sqlalchemy')
except ImportError:
    print('❌ sqlalchemy')
    missing.append('sqlalchemy')

try:
    import pgvector
    print('✅ pgvector')
except ImportError:
    print('❌ pgvector')
    missing.append('pgvector')

try:
    import google.genai
    print('✅ google-genai')
except ImportError:
    print('❌ google-genai')
    missing.append('google-genai')

if missing:
    print(f'\n⚠️  缺少依赖: {missing}')
    sys.exit(1)
else:
    print('\n✅ 所有依赖已安装')
"

Write-Host ""
Write-Host "=========================================="
Write-Host "安装完成！"
Write-Host "=========================================="

