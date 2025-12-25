"""
简化的向量嵌入服务测试
用于快速验证 API 调用方式
"""
from google import genai
from config import GEMINI_API_KEY

def test_gemini_embedding_api():
    """测试 Gemini Embedding API 调用"""
    print("🧪 测试 Gemini Embedding API...")
    print(f"📋 API Key 配置: {bool(GEMINI_API_KEY)}")
    
    if not GEMINI_API_KEY:
        print("❌ GEMINI_API_KEY 未配置")
        return False
    
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        print("✅ Gemini 客户端初始化成功")
        
        # 尝试不同的 API 调用方式
        test_text = "这是一个测试文本"
        print(f"\n🔍 测试文本: {test_text}")
        print("\n尝试方法1: client.models.embed_content()...")
        
        try:
            # 方法1：直接调用 embed_content
            result = client.models.embed_content(
                model="models/text-embedding-004",
                content=test_text,
                task_type="RETRIEVAL_DOCUMENT"
            )
            print(f"✅ 方法1成功！")
            print(f"结果类型: {type(result)}")
            print(f"结果属性: {dir(result)}")
            
            # 尝试提取向量
            if hasattr(result, 'embedding'):
                embedding = result.embedding
                print(f"✅ 找到 embedding 属性，维度: {len(embedding) if isinstance(embedding, list) else 'N/A'}")
                return True
            elif hasattr(result, 'values'):
                embedding = result.values
                print(f"✅ 找到 values 属性，维度: {len(embedding) if isinstance(embedding, list) else 'N/A'}")
                return True
            else:
                print(f"⚠️  未找到 embedding 属性，尝试其他方式...")
                print(f"结果内容: {result}")
                
        except Exception as e1:
            print(f"❌ 方法1失败: {e1}")
            
            # 方法2：尝试使用 embed 方法
            print("\n尝试方法2: client.models.embed()...")
            try:
                result = client.models.embed(
                    model="models/text-embedding-004",
                    content=test_text
                )
                print(f"✅ 方法2成功！")
                print(f"结果: {result}")
                return True
            except Exception as e2:
                print(f"❌ 方法2失败: {e2}")
                
                # 方法3：尝试其他可能的调用方式
                print("\n尝试方法3: 查看可用方法...")
                print(f"client.models 的方法: {[m for m in dir(client.models) if not m.startswith('_')]}")
                
        return False
        
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("🧪 Gemini Embedding API 测试（简化版）")
    print("=" * 60)
    
    success = test_gemini_embedding_api()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ 测试成功！API 调用方式正确")
    else:
        print("❌ 测试失败！需要检查 API 调用方式")
        print("\n提示：")
        print("1. 检查 google-genai 库版本")
        print("2. 查看官方文档确认正确的 API 调用方式")
        print("3. 确认 embedding 模型的正确名称")
    print("=" * 60)

