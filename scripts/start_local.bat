@echo off
chcp 65001 >nul
echo ========================================
echo 🚀 NovaWrite AI - 本地启动脚本
echo ========================================
echo.

REM 检查是否在项目根目录
if not exist "backend\" (
    echo ❌ 错误: 请在项目根目录运行此脚本
    pause
    exit /b 1
)

REM 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: 未安装 Python 或 Python 不在 PATH 中
    pause
    exit /b 1
)

echo.
echo 📋 步骤 1/5: 检查环境配置
echo ========================================

REM 检查后端 .env
if not exist "backend\.env" (
    echo ⚠️  警告: backend\.env 不存在，复制模板...
    copy "backend\.env.example" "backend\.env"
    echo.
    echo 📝 请编辑 backend\.env 文件，设置以下配置:
    echo    - GEMINI_API_KEY（必填）
    echo    - DATABASE_URL（如果不是默认值）
    echo.
    pause
)

REM 检查微服务 .env
if not exist "nova-ai-service\.env" (
    echo ⚠️  警告: nova-ai-service\.env 不存在，复制模板...
    copy "nova-ai-service\.env.example" "nova-ai-service\.env"
    echo.
    echo 📝 请编辑 nova-ai-service\.env 文件，设置 GEMINI_API_KEY
    echo.
    pause
)

echo ✅ 环境配置检查完成
echo.

echo 📋 步骤 2/5: 初始化数据库
echo ========================================
cd backend
python ..\scripts\init_local_db.py
if errorlevel 1 (
    echo.
    echo ❌ 数据库初始化失败！
    echo 💡 请检查:
    echo    1. PostgreSQL 是否正在运行
    echo    2. DATABASE_URL 配置是否正确
    echo    3. 数据库用户是否有创建表的权限
    cd ..
    pause
    exit /b 1
)
cd ..

echo.
echo ✅ 数据库初始化完成
echo.

echo 📋 步骤 3/5: 启动 AI 微服务 (端口 8001)
echo ========================================
start "AI Microservice" cmd /k "cd nova-ai-service && python -m venv venv 2>nul && call venv\Scripts\activate && pip install -r requirements.txt -q && uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload"

echo ⏳ 等待 AI 微服务启动 (15秒)...
timeout /t 15 /nobreak >nul

echo.
echo 📋 步骤 4/5: 启动主应用后端 (端口 8000)
echo ========================================
start "Backend" cmd /k "cd backend && python -m venv venv 2>nul && call venv\Scripts\activate && pip install -r requirements.txt -q && uvicorn main:app --host 0.0.0.0 --port 8000 --reload"

echo ⏳ 等待主应用启动 (10秒)...
timeout /t 10 /nobreak >nul

echo.
echo 📋 步骤 5/5: 验证服务状态
echo ========================================
echo.
echo 🔍 检查 AI 微服务 (http://localhost:8001)...
curl -s http://localhost:8001/health >nul 2>&1
if errorlevel 1 (
    echo ⚠️  AI 微服务可能还未完全启动，请稍等片刻
) else (
    echo ✅ AI 微服务运行正常
)

echo.
echo 🔍 检查主应用 (http://localhost:8000)...
curl -s http://localhost:8000/health >nul 2>&1
if errorlevel 1 (
    echo ⚠️  主应用可能还未完全启动，请稍等片刻
) else (
    echo ✅ 主应用运行正常
)

echo.
echo ========================================
echo 🎉 启动完成！
echo ========================================
echo.
echo 📡 服务访问地址:
echo    AI 微服务:  http://localhost:8001
echo    API 文档:   http://localhost:8001/docs
echo    主应用:     http://localhost:8000
echo    主应用文档: http://localhost:8000/docs
echo.
echo 💡 提示:
echo    - 所有服务都在独立窗口运行
echo    - 关闭窗口即可停止对应服务
echo    - 修改代码会自动重新加载 (--reload 模式)
echo.
pause
