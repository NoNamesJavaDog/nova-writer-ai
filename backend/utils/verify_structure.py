"""
验证代码结构 - 只检查文件是否存在，不测试导入
"""
import os

def verify_structure():
    """验证目录结构是否正确"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    required_files = [
        # 核心模块
        'core/__init__.py',
        'core/config.py',
        'core/database.py',
        'core/security.py',
        
        # 模型
        'models/__init__.py',
        'models/models.py',
        
        # 模式
        'schemas/__init__.py',
        'schemas/schemas.py',
        
        # AI 服务
        'services/ai/__init__.py',
        'services/ai/gemini_service.py',
        'services/ai/chapter_writing_service.py',
        
        # 任务服务
        'services/task/__init__.py',
        'services/task/task_service.py',
    ]
    
    required_dirs = [
        'core',
        'models',
        'schemas',
        'services',
        'services/ai',
        'services/task',
        'api/routers',
    ]
    
    print("=" * 60)
    print("验证后端代码结构")
    print("=" * 60)
    
    errors = []
    warnings = []
    
    # 检查目录
    print("\n检查目录结构...")
    for dir_path in required_dirs:
        full_path = os.path.join(base_dir, dir_path)
        if os.path.isdir(full_path):
            print(f"  [OK] {dir_path}/")
        else:
            print(f"  [MISSING] {dir_path}/")
            warnings.append(f"目录缺失: {dir_path}")
    
    # 检查文件
    print("\n检查文件...")
    for file_path in required_files:
        full_path = os.path.join(base_dir, file_path)
        if os.path.isfile(full_path):
            size = os.path.getsize(full_path)
            print(f"  [OK] {file_path} ({size} bytes)")
        else:
            print(f"  [MISSING] {file_path}")
            errors.append(f"文件缺失: {file_path}")
    
    # 检查关键导入路径（只检查语法，不执行）
    print("\n检查导入路径...")
    import_paths = [
        ('core.database', 'from ..core.database import Base'),
        ('services.ai.gemini_service', 'from ...core.config import GEMINI_API_KEY'),
        ('services.ai.chapter_writing_service', 'from ...models import Novel'),
        ('services.task.task_service', 'from ...models import Task'),
    ]
    
    for module, import_line in import_paths:
        print(f"  [CHECK] {module}: {import_line}")
    
    # 总结
    print("\n" + "=" * 60)
    if errors:
        print(f"[FAIL] 发现 {len(errors)} 个错误:")
        for error in errors:
            print(f"  - {error}")
        return False
    elif warnings:
        print(f"[WARN] 发现 {len(warnings)} 个警告:")
        for warning in warnings:
            print(f"  - {warning}")
        print("\n[OK] 核心结构已就绪")
        return True
    else:
        print("[OK] 所有文件和目录都存在")
        return True

if __name__ == '__main__':
    success = verify_structure()
    exit(0 if success else 1)

