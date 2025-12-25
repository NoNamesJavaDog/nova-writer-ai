"""
测试向量嵌入服务
"""
import sys
import os

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.embedding_service import EmbeddingService
from config import GEMINI_API_KEY

def test_embedding_generation():
    """测试向量生成"""
    print("🧪 测试向量生成功能...")
    print(f"📋 API Key 已配置: {bool(GEMINI_API_KEY)}")
    
    try:
        service = EmbeddingService()
        print(f"✅ EmbeddingService 初始化成功")
        print(f"📦 使用模型: {service.model}")
        print(f"📏 向量维度: {service.dimension}")
        
        # 测试生成向量
        test_text = "这是一个测试文本，用于验证向量生成功能。"
        print(f"\n🔍 测试文本: {test_text}")
        
        print("⏳ 正在生成向量...")
        embedding = service.generate_embedding(test_text)
        
        print(f"✅ 向量生成成功！")
        print(f"📊 向量维度: {len(embedding)}")
        print(f"📈 前5个值: {embedding[:5]}")
        print(f"📉 后5个值: {embedding[-5:]}")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_text_chunking():
    """测试文本分块"""
    print("\n🧪 测试文本分块功能...")
    
    try:
        service = EmbeddingService()
        
        # 测试长文本分块
        long_text = """
        第一章：新的开始
        
        阳光透过窗户洒在桌面上，李小明缓缓睁开眼睛。今天是新学期的第一天，他既紧张又兴奋。
        
        他迅速洗漱完毕，穿上新校服，整理好书包。母亲已经准备好了早餐，父亲正在看报纸。
        
        "快吃吧，别迟到了。"母亲温柔地说。
        
        李小明点点头，匆匆吃完早餐，向父母告别后走出家门。
        
        走在路上，他的心情有些复杂。新的学校，新的同学，新的环境，一切都是未知的。
        
        不过，他很快就调整好了心态。毕竟，这是一个全新的开始，他应该以积极的态度去面对。
        
        学校很快就到了。大门敞开着，学生们三三两两地走进去。李小明深吸一口气，迈步走进了校园。
        
        这里将是他未来三年学习和生活的地方。他期待着在这里遇到新朋友，学到新知识，经历新的人生。
        """
        
        print(f"📝 原始文本长度: {len(long_text)} 字符")
        
        chunks = service._split_into_chunks(long_text, chunk_size=100)
        print(f"✅ 分块完成，共 {len(chunks)} 个段落")
        
        for i, chunk in enumerate(chunks, 1):
            print(f"  段落 {i}: {len(chunk)} 字符 - {chunk[:50]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_database_connection():
    """测试数据库连接（不实际插入数据）"""
    print("\n🧪 测试数据库连接...")
    
    try:
        from database import engine
        from sqlalchemy import text
        
        with engine.connect() as conn:
            # 检查 pgvector 扩展
            result = conn.execute(text("SELECT * FROM pg_extension WHERE extname = 'vector'"))
            if result.fetchone():
                print("✅ pgvector 扩展已安装")
            else:
                print("❌ pgvector 扩展未安装，请先运行迁移脚本")
                return False
            
            # 检查表是否存在
            tables = ['chapter_embeddings', 'character_embeddings', 
                     'world_setting_embeddings', 'foreshadowing_embeddings']
            
            for table in tables:
                result = conn.execute(text(f"""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = '{table}'
                    )
                """))
                if result.fetchone()[0]:
                    print(f"✅ 表 {table} 已存在")
                else:
                    print(f"❌ 表 {table} 不存在，请先运行迁移脚本")
                    return False
            
            return True
            
    except Exception as e:
        print(f"❌ 数据库连接测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("🧪 pgvector 向量嵌入服务测试")
    print("=" * 60)
    
    results = []
    
    # 测试1: 向量生成
    results.append(("向量生成", test_embedding_generation()))
    
    # 测试2: 文本分块
    results.append(("文本分块", test_text_chunking()))
    
    # 测试3: 数据库连接（可选，需要数据库配置）
    try:
        results.append(("数据库连接", test_database_connection()))
    except Exception as e:
        print(f"\n⚠️  数据库连接测试跳过: {str(e)}")
        print("   提示: 如果数据库未配置，这是正常的")
    
    # 汇总结果
    print("\n" + "=" * 60)
    print("📊 测试结果汇总")
    print("=" * 60)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{name}: {status}")
    
    all_passed = all(result for _, result in results)
    
    if all_passed:
        print("\n🎉 所有测试通过！")
    else:
        print("\n⚠️  部分测试失败，请检查上述错误信息")
    
    sys.exit(0 if all_passed else 1)

