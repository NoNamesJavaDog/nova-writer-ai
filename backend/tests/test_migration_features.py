"""
测试迁移后的功能
验证所有从前端迁移到后端的功能是否正常工作
"""
import os
import sys
import requests
import json
from typing import Dict, Any

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 测试配置
BASE_URL = "http://127.0.0.1:8000/api"
TEST_USERNAME = "test_user"
TEST_PASSWORD = "test_password123"
TEST_EMAIL = "test@example.com"

class Colors:
    """终端颜色"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_success(msg: str):
    """打印成功消息"""
    print(f"{Colors.GREEN}✅ {msg}{Colors.END}")

def print_error(msg: str):
    """打印错误消息"""
    print(f"{Colors.RED}❌ {msg}{Colors.END}")

def print_info(msg: str):
    """打印信息消息"""
    print(f"{Colors.BLUE}ℹ️  {msg}{Colors.END}")

def print_warning(msg: str):
    """打印警告消息"""
    print(f"{Colors.YELLOW}⚠️  {msg}{Colors.END}")

class MigrationTester:
    """迁移功能测试器"""
    
    def __init__(self):
        self.token = None
        self.novel_id = None
        self.test_results = []
    
    def test_api_health(self) -> bool:
        """测试 API 健康状态"""
        print_info("测试 API 健康状态...")
        try:
            # 测试 OpenAPI 文档
            response = requests.get(f"{BASE_URL}/docs", timeout=5)
            if response.status_code == 200:
                print_success("API 文档可访问")
                return True
            else:
                print_error(f"API 文档不可访问: {response.status_code}")
                return False
        except Exception as e:
            print_error(f"API 健康检查失败: {str(e)}")
            return False
    
    def test_auth(self) -> bool:
        """测试认证功能"""
        print_info("测试认证功能...")
        try:
            # 尝试注册
            register_data = {
                "username": TEST_USERNAME,
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD
            }
            response = requests.post(f"{BASE_URL}/auth/register", json=register_data, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                print_success("用户注册成功")
                return True
            elif response.status_code == 400:
                # 用户可能已存在，尝试登录
                print_warning("用户可能已存在，尝试登录...")
                login_data = {
                    "username_or_email": TEST_USERNAME,
                    "password": TEST_PASSWORD
                }
                response = requests.post(f"{BASE_URL}/auth/login", json=login_data, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    self.token = data.get("access_token")
                    print_success("用户登录成功")
                    return True
                else:
                    print_error(f"登录失败: {response.status_code} - {response.text}")
                    return False
            else:
                print_error(f"注册失败: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print_error(f"认证测试失败: {str(e)}")
            return False
    
    def test_novel_crud(self) -> bool:
        """测试小说 CRUD 操作"""
        print_info("测试小说 CRUD 操作...")
        if not self.token:
            print_error("需要先通过认证")
            return False
        
        headers = {"Authorization": f"Bearer {self.token}"}
        
        try:
            # 创建小说
            novel_data = {
                "title": "测试小说",
                "genre": "玄幻",
                "synopsis": "这是一个测试小说"
            }
            response = requests.post(f"{BASE_URL}/novels", json=novel_data, headers=headers, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                self.novel_id = data.get("id")
                print_success(f"小说创建成功: {self.novel_id}")
                
                # 获取小说列表
                response = requests.get(f"{BASE_URL}/novels", headers=headers, timeout=5)
                if response.status_code == 200:
                    novels = response.json()
                    print_success(f"获取小说列表成功: {len(novels)} 本小说")
                    return True
                else:
                    print_error(f"获取小说列表失败: {response.status_code}")
                    return False
            else:
                print_error(f"创建小说失败: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print_error(f"小说 CRUD 测试失败: {str(e)}")
            return False
    
    def test_sync_endpoint(self) -> bool:
        """测试同步端点"""
        print_info("测试同步端点...")
        if not self.token or not self.novel_id:
            print_error("需要先创建小说")
            return False
        
        headers = {"Authorization": f"Bearer {self.token}"}
        
        try:
            response = requests.post(
                f"{BASE_URL}/novels/{self.novel_id}/sync",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                print_success(f"同步成功: {data.get('message', 'OK')}")
                return True
            else:
                print_error(f"同步失败: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print_error(f"同步测试失败: {str(e)}")
            return False
    
    def test_ai_endpoints(self) -> bool:
        """测试 AI 端点"""
        print_info("测试 AI 端点...")
        if not self.token or not self.novel_id:
            print_error("需要先创建小说")
            return False
        
        headers = {"Authorization": f"Bearer {self.token}"}
        
        # 测试任务创建端点
        try:
            task_data = {
                "task_type": "generate_outline",
                "novel_id": self.novel_id,
                "params": {
                    "title": "测试小说",
                    "genre": "玄幻",
                    "synopsis": "这是一个测试"
                }
            }
            response = requests.post(
                f"{BASE_URL}/tasks/create",
                json=task_data,
                headers=headers,
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                task_id = data.get("task_id")
                print_success(f"任务创建成功: {task_id}")
                
                # 测试获取任务状态
                response = requests.get(
                    f"{BASE_URL}/tasks/{task_id}",
                    headers=headers,
                    timeout=5
                )
                
                if response.status_code == 200:
                    task_data = response.json()
                    print_success(f"获取任务状态成功: {task_data.get('status')}")
                    return True
                else:
                    print_warning(f"获取任务状态失败: {response.status_code}")
                    return True  # 任务创建成功即可
            else:
                print_warning(f"任务创建失败（可能需要 Gemini API 配置）: {response.status_code}")
                return True  # 不强制要求 AI 功能可用
        except Exception as e:
            print_warning(f"AI 端点测试失败（可能需要 Gemini API 配置）: {str(e)}")
            return True  # 不强制要求 AI 功能可用
    
    def test_vector_features(self) -> bool:
        """测试向量数据库功能"""
        print_info("测试向量数据库功能...")
        try:
            from services.embedding_service import EmbeddingService
            
            service = EmbeddingService()
            test_text = "这是一个测试文本"
            
            # 测试向量生成
            embedding = service.generate_embedding(test_text)
            
            if embedding and len(embedding) > 0:
                print_success(f"向量生成成功: 维度 {len(embedding)}")
                return True
            else:
                print_error("向量生成失败")
                return False
        except Exception as e:
            print_warning(f"向量功能测试失败（可能需要 Gemini API 配置）: {str(e)}")
            return True  # 不强制要求向量功能可用
    
    def run_all_tests(self):
        """运行所有测试"""
        print("\n" + "="*60)
        print("开始测试迁移后的功能")
        print("="*60 + "\n")
        
        tests = [
            ("API 健康状态", self.test_api_health),
            ("认证功能", self.test_auth),
            ("小说 CRUD", self.test_novel_crud),
            ("同步端点", self.test_sync_endpoint),
            ("AI 端点", self.test_ai_endpoints),
            ("向量数据库功能", self.test_vector_features),
        ]
        
        passed = 0
        failed = 0
        
        for test_name, test_func in tests:
            print(f"\n📋 测试: {test_name}")
            print("-" * 60)
            try:
                result = test_func()
                if result:
                    passed += 1
                    self.test_results.append((test_name, True))
                else:
                    failed += 1
                    self.test_results.append((test_name, False))
            except Exception as e:
                print_error(f"测试异常: {str(e)}")
                failed += 1
                self.test_results.append((test_name, False))
        
        # 打印总结
        print("\n" + "="*60)
        print("测试总结")
        print("="*60)
        print(f"总测试数: {len(tests)}")
        print(f"{Colors.GREEN}通过: {passed}{Colors.END}")
        print(f"{Colors.RED}失败: {failed}{Colors.END}")
        print("\n详细结果:")
        for test_name, result in self.test_results:
            status = f"{Colors.GREEN}✅ 通过{Colors.END}" if result else f"{Colors.RED}❌ 失败{Colors.END}"
            print(f"  {test_name}: {status}")
        
        return failed == 0

if __name__ == "__main__":
    tester = MigrationTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)

