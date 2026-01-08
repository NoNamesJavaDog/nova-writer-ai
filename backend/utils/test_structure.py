"""
测试新代码结构的导入
从项目根目录运行: python -m backend.test_structure
或从 backend 目录运行: python test_structure.py
"""
import sys
import os

# 添加 backend 目录到路径（如果从 backend 目录直接运行）
if __name__ == '__main__' and os.path.dirname(__file__) == os.getcwd():
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

def test_imports():
    """测试所有模块的导入"""
    errors = []
    
    print("=" * 60)
    print("测试后端代码结构导入")
    print("=" * 60)
    
    # 测试核心模块
    print("\n1. 测试核心模块 (core/)...")
    try:
        from core.config import CORS_ORIGINS, DEBUG, DATABASE_URL
        print("   ✅ core.config 导入成功")
    except Exception as e:
        print(f"   ❌ core.config 导入失败: {e}")
        errors.append(f"core.config: {e}")
    
    try:
        from core.database import get_db, SessionLocal, Base
        print("   ✅ core.database 导入成功")
    except Exception as e:
        print(f"   ❌ core.database 导入失败: {e}")
        errors.append(f"core.database: {e}")
    
    try:
        from core.security import get_current_user, generate_uuid, generate_captcha
        print("   ✅ core.security 导入成功")
    except Exception as e:
        print(f"   ❌ core.security 导入失败: {e}")
        errors.append(f"core.security: {e}")
    
    # 测试模型
    print("\n2. 测试数据库模型 (models/)...")
    try:
        from models import User, Novel, Chapter
        print("   ✅ models 导入成功")
    except Exception as e:
        print(f"   ❌ models 导入失败: {e}")
        errors.append(f"models: {e}")
    
    # 测试模式
    print("\n3. 测试数据模式 (schemas/)...")
    try:
        from schemas import UserCreate, NovelResponse, ChapterResponse
        print("   ✅ schemas 导入成功")
    except Exception as e:
        print(f"   ❌ schemas 导入失败: {e}")
        errors.append(f"schemas: {e}")
    
    # 测试 AI 服务
    print("\n4. 测试 AI 服务 (services.ai/)...")
    try:
        from services.ai import generate_full_outline
        print("   ✅ services.ai 导入成功")
    except Exception as e:
        print(f"   ❌ services.ai 导入失败: {e}")
        errors.append(f"services.ai: {e}")
    
    # 测试任务服务
    print("\n5. 测试任务服务 (services.task/)...")
    try:
        from services.task import create_task, get_task_executor
        print("   ✅ services.task 导入成功")
    except Exception as e:
        print(f"   ❌ services.task 导入失败: {e}")
        errors.append(f"services.task: {e}")
    
    # 总结
    print("\n" + "=" * 60)
    if errors:
        print(f"❌ 发现 {len(errors)} 个导入错误:")
        for error in errors:
            print(f"   - {error}")
        return False
    else:
        print("✅ 所有模块导入成功！")
        return True

if __name__ == '__main__':
    success = test_imports()
    sys.exit(0 if success else 1)
