# pgvector 向量数据库集成 - 完整部署和测试脚本 (PowerShell)
# 在远程服务器上运行此脚本来部署和测试所有功能

$ErrorActionPreference = "Stop"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "pgvector 向量数据库集成 - 部署和测试" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# 步骤1: 检查前置要求
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "步骤1: 检查前置要求" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# 检查Python
if (Get-Command python -ErrorAction SilentlyContinue) {
    $pythonVersion = python --version
    Write-Host "✅ Python 已安装: $pythonVersion" -ForegroundColor Green
    $pythonCmd = "python"
} elseif (Get-Command python3 -ErrorAction SilentlyContinue) {
    $pythonVersion = python3 --version
    Write-Host "✅ Python3 已安装: $pythonVersion" -ForegroundColor Green
    $pythonCmd = "python3"
} else {
    Write-Host "❌ Python 未安装，请先安装 Python 3.8+" -ForegroundColor Red
    exit 1
}

# 检查pip
if (Get-Command pip -ErrorAction SilentlyContinue) {
    $pipCmd = "pip"
    Write-Host "✅ pip 已安装" -ForegroundColor Green
} elseif (Get-Command pip3 -ErrorAction SilentlyContinue) {
    $pipCmd = "pip3"
    Write-Host "✅ pip3 已安装" -ForegroundColor Green
} else {
    Write-Host "⚠️  pip 未找到，尝试使用 python -m pip" -ForegroundColor Yellow
    $pipCmd = "$pythonCmd -m pip"
}

# 检查PostgreSQL
if (Get-Command psql -ErrorAction SilentlyContinue) {
    Write-Host "✅ PostgreSQL 客户端已安装" -ForegroundColor Green
} else {
    Write-Host "⚠️  psql 未找到，请确保PostgreSQL已安装" -ForegroundColor Yellow
}

# 检查Redis（可选）
if (Get-Command redis-cli -ErrorAction SilentlyContinue) {
    Write-Host "✅ Redis 已安装（可选）" -ForegroundColor Green
} else {
    Write-Host "⚠️  Redis 未安装（可选，缓存功能将被禁用）" -ForegroundColor Yellow
}

Write-Host ""

# 步骤2: 检查环境变量
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "步骤2: 检查环境变量" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

if (Test-Path .env) {
    Write-Host "✅ .env 文件存在" -ForegroundColor Green
    
    # 加载.env文件（简单处理）
    Get-Content .env | ForEach-Object {
        if ($_ -match '^\s*([^#][^=]*)=(.*)$') {
            $key = $matches[1].Trim()
            $value = $matches[2].Trim()
            [Environment]::SetEnvironmentVariable($key, $value, "Process")
        }
    }
    
    if ($env:GEMINI_API_KEY) {
        Write-Host "✅ GEMINI_API_KEY 已设置" -ForegroundColor Green
    } else {
        Write-Host "⚠️  GEMINI_API_KEY 未设置" -ForegroundColor Yellow
    }
    
    if ($env:DATABASE_URL) {
        Write-Host "✅ DATABASE_URL 已设置" -ForegroundColor Green
    } else {
        Write-Host "⚠️  DATABASE_URL 未设置" -ForegroundColor Yellow
    }
} else {
    Write-Host "⚠️  .env 文件不存在" -ForegroundColor Yellow
    Write-Host "请创建 .env 文件并配置以下变量："
    Write-Host "  GEMINI_API_KEY=your_api_key"
    Write-Host "  DATABASE_URL=postgresql://user:password@host:port/database"
    Write-Host ""
    $continue = Read-Host "是否继续？(y/n)"
    if ($continue -ne "y" -and $continue -ne "Y") {
        exit 1
    }
}

Write-Host ""

# 步骤3: 安装依赖
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "步骤3: 安装Python依赖" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

Write-Host "升级pip..."
& $pythonCmd -m pip install --upgrade pip --quiet

Write-Host "安装依赖包..."
& $pipCmd install -r requirements.txt

Write-Host "✅ 依赖安装完成" -ForegroundColor Green
Write-Host ""

# 步骤4: 验证依赖安装
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "步骤4: 验证依赖安装" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

& $pythonCmd -c @"
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
    print(f'✅ sqlalchemy ({sqlalchemy.__version__})')
except ImportError:
    print('❌ sqlalchemy')
    missing.append('sqlalchemy')
    sys.exit(1)

try:
    import pgvector
    print('✅ pgvector')
except ImportError:
    print('❌ pgvector')
    missing.append('pgvector')
    sys.exit(1)

try:
    import google.genai
    print('✅ google-genai')
except ImportError:
    print('❌ google-genai')
    missing.append('google-genai')
    sys.exit(1)

if 'redis' in missing:
    print('\n⚠️  Redis未安装，缓存功能将被禁用')
else:
    print('\n✅ 所有依赖已安装')
"@

if ($LASTEXITCODE -ne 0) {
    Write-Host "依赖验证失败，请检查错误信息" -ForegroundColor Red
    exit 1
}

Write-Host ""

# 步骤5: 运行数据库迁移
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "步骤5: 运行数据库迁移" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

if (Test-Path migrate_add_pgvector.py) {
    Write-Host "运行数据库迁移脚本..."
    & $pythonCmd migrate_add_pgvector.py
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ 数据库迁移完成" -ForegroundColor Green
    } else {
        Write-Host "❌ 数据库迁移失败" -ForegroundColor Red
        Write-Host "请检查数据库连接和权限"
        exit 1
    }
} else {
    Write-Host "⚠️  migrate_add_pgvector.py 不存在，跳过迁移" -ForegroundColor Yellow
}

Write-Host ""

# 步骤6: 运行测试
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "步骤6: 运行测试" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# 6.1 完整测试
Write-Host "6.1 运行完整测试 (test_all_remote.py)..." -ForegroundColor Yellow
if (Test-Path test_all_remote.py) {
    & $pythonCmd test_all_remote.py
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ 完整测试通过" -ForegroundColor Green
    } else {
        Write-Host "⚠️  完整测试有警告或错误（请查看输出）" -ForegroundColor Yellow
    }
} else {
    Write-Host "⚠️  test_all_remote.py 不存在" -ForegroundColor Yellow
}

Write-Host ""

# 6.2 功能测试
Write-Host "6.2 运行功能测试 (test_vector_features.py)..." -ForegroundColor Yellow
if (Test-Path test_vector_features.py) {
    & $pythonCmd test_vector_features.py
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ 功能测试通过" -ForegroundColor Green
    } else {
        Write-Host "⚠️  功能测试有警告或错误" -ForegroundColor Yellow
    }
} else {
    Write-Host "⚠️  test_vector_features.py 不存在" -ForegroundColor Yellow
}

Write-Host ""

# 6.3 API测试
Write-Host "6.3 运行API测试 (test_embedding_simple.py)..." -ForegroundColor Yellow
if (Test-Path test_embedding_simple.py) {
    & $pythonCmd test_embedding_simple.py
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ API测试通过" -ForegroundColor Green
    } else {
        Write-Host "⚠️  API测试有警告或错误" -ForegroundColor Yellow
    }
} else {
    Write-Host "⚠️  test_embedding_simple.py 不存在" -ForegroundColor Yellow
}

Write-Host ""

# 6.4 单元测试
Write-Host "6.4 运行单元测试 (test_unit.py)..." -ForegroundColor Yellow
if (Test-Path test_unit.py) {
    & $pythonCmd test_unit.py
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ 单元测试通过" -ForegroundColor Green
    } else {
        Write-Host "⚠️  单元测试有警告或错误" -ForegroundColor Yellow
    }
} else {
    Write-Host "⚠️  test_unit.py 不存在" -ForegroundColor Yellow
}

Write-Host ""

# 总结
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "部署和测试总结" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "✅ 部署完成！" -ForegroundColor Green
Write-Host ""
Write-Host "下一步："
Write-Host "1. 查看测试结果，确保所有测试通过"
Write-Host "2. 查看使用文档: PGVECTOR_README.md"
Write-Host "3. 集成到API: 参考 api_integration_example.py"
Write-Host "4. 开始使用向量数据库功能！"
Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan


