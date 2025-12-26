"""测试创建小说 - 详细错误信息"""
import requests
import json
import traceback

BASE_URL = "http://127.0.0.1:8000/api"

try:
    # 1. 注册用户
    print("=" * 60)
    print("1. 注册用户")
    print("=" * 60)
    register_data = {
        "username": "test_detailed_user",
        "email": "test_detailed@test.com",
        "password": "test123456"
    }
    r = requests.post(f"{BASE_URL}/auth/register", json=register_data, timeout=10)
    print(f"状态码: {r.status_code}")
    print(f"响应: {r.text[:200]}")
    
    if r.status_code == 200:
        token = r.json().get("access_token")
        print(f"✅ 注册成功")
    else:
        print("尝试登录...")
        login_data = {
            "username_or_email": "test_detailed_user",
            "password": "test123456"
        }
        r = requests.post(f"{BASE_URL}/auth/login", json=login_data, timeout=10)
        if r.status_code == 200:
            token = r.json().get("access_token")
            print(f"✅ 登录成功")
        else:
            print(f"❌ 登录失败: {r.status_code} - {r.text}")
            exit(1)
    
    # 2. 创建小说
    print("\n" + "=" * 60)
    print("2. 创建小说")
    print("=" * 60)
    headers = {"Authorization": f"Bearer {token}"}
    novel_data = {
        "title": "测试小说详细",
        "genre": "玄幻",
        "synopsis": "这是一个详细的测试小说"
    }
    print(f"请求数据: {json.dumps(novel_data, ensure_ascii=False)}")
    
    r2 = requests.post(
        f"{BASE_URL}/novels",
        json=novel_data,
        headers=headers,
        timeout=10
    )
    print(f"状态码: {r2.status_code}")
    print(f"响应头: {dict(r2.headers)}")
    print(f"响应内容: {r2.text}")
    
    if r2.status_code == 200:
        novel = r2.json()
        print(f"\n✅ 创建小说成功")
        print(f"小说ID: {novel.get('id')}")
        print(f"标题: {novel.get('title')}")
        print(f"类型: {novel.get('genre')}")
    else:
        print(f"\n❌ 创建小说失败")
        try:
            error_detail = r2.json()
            print(f"错误详情: {json.dumps(error_detail, ensure_ascii=False, indent=2)}")
        except:
            print(f"错误文本: {r2.text}")
        exit(1)
    
    # 3. 测试同步端点
    print("\n" + "=" * 60)
    print("3. 测试同步端点")
    print("=" * 60)
    novel_id = novel.get('id')
    r3 = requests.post(
        f"{BASE_URL}/novels/{novel_id}/sync",
        headers=headers,
        timeout=30
    )
    print(f"状态码: {r3.status_code}")
    print(f"响应: {r3.text[:200]}")
    
    if r3.status_code == 200:
        print("✅ 同步成功")
    else:
        print(f"⚠️ 同步失败: {r3.status_code} - {r3.text[:200]}")
    
    # 4. 测试 AI 端点（任务创建）
    print("\n" + "=" * 60)
    print("4. 测试 AI 端点（任务创建）")
    print("=" * 60)
    task_data = {
        "task_type": "generate_outline",
        "novel_id": novel_id,
        "params": {
            "title": novel.get('title'),
            "genre": novel.get('genre'),
            "synopsis": novel.get('synopsis')
        }
    }
    r4 = requests.post(
        f"{BASE_URL}/tasks/create",
        json=task_data,
        headers=headers,
        timeout=10
    )
    print(f"状态码: {r4.status_code}")
    print(f"响应: {r4.text[:200]}")
    
    if r4.status_code == 200:
        task_info = r4.json()
        print(f"✅ 任务创建成功: {task_info.get('task_id')}")
    else:
        print(f"⚠️ 任务创建失败（可能需要 Gemini API 配置）: {r4.status_code}")
    
    print("\n" + "=" * 60)
    print("✅ 所有测试完成")
    print("=" * 60)
    
except Exception as e:
    print(f"\n❌ 测试异常: {type(e).__name__}: {e}")
    traceback.print_exc()
    exit(1)

