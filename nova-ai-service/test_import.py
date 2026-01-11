"""测试导入脚本 - 验证所有模块可以正常导入"""

import sys
import traceback


def test_imports():
    """测试所有关键模块的导入"""
    print("=" * 60)
    print("测试模块导入...")
    print("=" * 60)

    modules_to_test = [
        "app.config",
        "app.api.dependencies",
        "app.api.v1",
        "app.api.v1.health",
        "app.api.v1.outline",
        "app.api.v1.chapter",
        "app.api.v1.analysis",
        "app.core.providers",
        "app.schemas.requests",
        "app.schemas.responses",
    ]

    failed = []
    succeeded = []

    for module_name in modules_to_test:
        try:
            __import__(module_name)
            succeeded.append(module_name)
            print(f"[OK] {module_name}")
        except Exception as e:
            failed.append((module_name, str(e)))
            print(f"[FAIL] {module_name}")
            print(f"  错误: {str(e)}")
            traceback.print_exc()

    print("\n" + "=" * 60)
    print(f"导入测试完成: {len(succeeded)} 成功, {len(failed)} 失败")
    print("=" * 60)

    if failed:
        print("\n失败的模块:")
        for module, error in failed:
            print(f"  - {module}: {error}")
        return False
    else:
        print("\n所有模块导入成功！")
        return True


def test_app_creation():
    """测试 FastAPI 应用创建"""
    print("\n" + "=" * 60)
    print("测试 FastAPI 应用创建...")
    print("=" * 60)

    try:
        # 需要先设置一个临时的 GEMINI_API_KEY 以避免配置错误
        import os
        os.environ.setdefault("GEMINI_API_KEY", "test_key")

        from app.main import app

        print(f"[OK] 应用创建成功")
        print(f"  应用标题: {app.title}")
        print(f"  应用版本: {app.version}")

        # 列出所有路由
        print("\n注册的路由:")
        for route in app.routes:
            if hasattr(route, 'methods'):
                methods = ', '.join(route.methods)
                print(f"  {methods:10} {route.path}")

        return True
    except Exception as e:
        print(f"[FAIL] 应用创建失败: {str(e)}")
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # 测试导入
    import_success = test_imports()

    # 测试应用创建
    app_success = test_app_creation()

    # 总结
    print("\n" + "=" * 60)
    if import_success and app_success:
        print("[SUCCESS] 所有测试通过！")
        print("=" * 60)
        sys.exit(0)
    else:
        print("[FAILED] 部分测试失败")
        print("=" * 60)
        sys.exit(1)
