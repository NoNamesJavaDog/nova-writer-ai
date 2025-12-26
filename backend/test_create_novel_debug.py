"""测试创建小说 API - 详细调试"""
import sys
import traceback
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

try:
    # 注册用户
    print("1. 注册用户...")
    r = client.post("/api/auth/register", json={
        "username": "test_debug_user",
        "email": "test_debug@test.com",
        "password": "test123456"
    })
    print(f"   状态码: {r.status_code}")
    if r.status_code == 200:
        token = r.json().get("access_token")
        print(f"   ✅ 注册成功")
    else:
        print(f"   ❌ 注册失败: {r.text}")
        # 尝试登录
        r = client.post("/api/auth/login", json={
            "username": "test_debug_user",
            "password": "test123456"
        })
        if r.status_code == 200:
            token = r.json().get("access_token")
            print(f"   ✅ 登录成功")
        else:
            print(f"   ❌ 登录也失败: {r.text}")
            sys.exit(1)
    
    # 创建小说
    print("\n2. 创建小说...")
    headers = {"Authorization": f"Bearer {token}"}
    novel_data = {
        "title": "测试小说",
        "genre": "玄幻",
        "synopsis": "这是一个测试小说"
    }
    
    r2 = client.post("/api/novels", json=novel_data, headers=headers)
    print(f"   状态码: {r2.status_code}")
    print(f"   响应: {r2.text}")
    
    if r2.status_code != 200:
        print("\n❌ 创建小说失败")
        sys.exit(1)
    else:
        print("\n✅ 创建小说成功")
        novel = r2.json()
        print(f"   小说ID: {novel.get('id')}")
        print(f"   标题: {novel.get('title')}")

except Exception as e:
    print(f"\n❌ 异常: {type(e).__name__}: {e}")
    traceback.print_exc()
    sys.exit(1)

