"""检查 main.py 的导入"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    print("正在导入 main 模块...")
    import main
    print("✅ main 模块导入成功")
    print(f"✅ FastAPI app 已创建: {main.app}")
except Exception as e:
    print(f"❌ 导入失败: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

