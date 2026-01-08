"""
简单测试脚本 - 从 backend 目录直接运行
python test_structure_simple.py
"""
import sys
import os

# 确保 backend 在路径中
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

print("=" * 60)
print("测试后端代码结构导入")
print("=" * 60)

errors = []

# 测试核心模块
print("\n1. 测试核心模块 (core/)...")
try:
    from core.config import CORS_ORIGINS, DEBUG
    print("   ✅ core.config 导入成功")
except Exception as e:
    print(f"   ❌ core.config 导入失败: {e}")
    errors.append(f"core.config: {e}")

try:
    from core.database import get_db, SessionLocal
    print("   ✅ core.database 导入成功")
except Exception as e:
    print(f"   ❌ core.database 导入失败: {e}")
    errors.append(f"core.database: {e}")

try:
    from core.security import generate_uuid
    print("   ✅ core.security 导入成功 (generate_uuid)")
except Exception as e:
    print(f"   ❌ core.security 导入失败: {e}")
    errors.append(f"core.security: {e}")

# 测试模型
print("\n2. 测试数据库模型 (models/)...")
try:
    from models.models import User, Novel
    print("   ✅ models.models 导入成功")
except Exception as e:
    print(f"   ❌ models.models 导入失败: {e}")
    errors.append(f"models.models: {e}")

try:
    from models import User, Novel
    print("   ✅ models (通过 __init__) 导入成功")
except Exception as e:
    print(f"   ⚠️  models (通过 __init__) 导入失败: {e}")
    # 不添加到 errors，因为可能是相对导入问题

# 测试模式
print("\n3. 测试数据模式 (schemas/)...")
try:
    from schemas.schemas import UserCreate
    print("   ✅ schemas.schemas 导入成功")
except Exception as e:
    print(f"   ❌ schemas.schemas 导入失败: {e}")
    errors.append(f"schemas.schemas: {e}")

# 测试 AI 服务
print("\n4. 测试 AI 服务 (services.ai/)...")
try:
    from services.ai.gemini_service import generate_full_outline
    print("   ✅ services.ai.gemini_service 导入成功")
except Exception as e:
    print(f"   ❌ services.ai.gemini_service 导入失败: {e}")
    errors.append(f"services.ai.gemini_service: {e}")

# 测试任务服务
print("\n5. 测试任务服务 (services.task/)...")
try:
    from services.task.task_service import create_task
    print("   ✅ services.task.task_service 导入成功")
except Exception as e:
    print(f"   ❌ services.task.task_service 导入失败: {e}")
    errors.append(f"services.task.task_service: {e}")

# 总结
print("\n" + "=" * 60)
if errors:
    print(f"❌ 发现 {len(errors)} 个导入错误:")
    for error in errors:
        print(f"   - {error}")
    print("\n⚠️  注意: 某些错误可能是缺少依赖导致的（如 bcrypt, email-validator）")
    sys.exit(1)
else:
    print("✅ 所有模块导入成功！")
    sys.exit(0)

