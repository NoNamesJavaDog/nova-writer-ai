"""测试创建小说 API"""
import requests
import json

BASE_URL = "http://127.0.0.1:8000/api"

# 注册用户
register_data = {
    "username": "test_novel_user",
    "email": "test_novel@test.com",
    "password": "test123456"
}

print("1. 注册用户...")
r = requests.post(f"{BASE_URL}/auth/register", json=register_data)
print(f"   状态码: {r.status_code}")
if r.status_code == 200:
    token = r.json().get("access_token")
    print(f"   ✅ 注册成功，token: {token[:20]}...")
else:
    print(f"   ❌ 注册失败: {r.text}")
    # 尝试登录
    login_data = {
        "username": "test_novel_user",
        "password": "test123456"
    }
    r = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    if r.status_code == 200:
        token = r.json().get("access_token")
        print(f"   ✅ 登录成功，token: {token[:20]}...")
    else:
        print(f"   ❌ 登录也失败: {r.text}")
        exit(1)

# 创建小说
headers = {"Authorization": f"Bearer {token}"}
novel_data = {
    "title": "测试小说",
    "genre": "玄幻",
    "synopsis": "这是一个测试小说"
}

print("\n2. 创建小说...")
r2 = requests.post(f"{BASE_URL}/novels", json=novel_data, headers=headers)
print(f"   状态码: {r2.status_code}")
print(f"   响应: {r2.text}")

if r2.status_code != 200:
    print("\n❌ 创建小说失败")
    exit(1)
else:
    print("\n✅ 创建小说成功")
    novel = r2.json()
    print(f"   小说ID: {novel.get('id')}")
    print(f"   标题: {novel.get('title')}")

