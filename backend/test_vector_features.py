"""
向量数据库功能测试脚本
用于测试所有向量相关功能的完整性
"""
import os
import sys
import time

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import DATABASE_URL
from services.embedding_service import EmbeddingService
from services.consistency_checker import ConsistencyChecker
from services.foreshadowing_matcher import ForeshadowingMatcher
from services.content_similarity_checker import ContentSimilarityChecker


def test_embedding_generation():
    """测试向量生成"""
    print("\n=== 测试1: 向量生成 ===")
    try:
        service = EmbeddingService()
        text = "这是一个测试文本，用于验证向量生成功能是否正常。"
        embedding = service.generate_embedding(text)
        print(f"✅ 向量生成成功")
        print(f"   维度: {len(embedding)}")
        print(f"   前5个值: {embedding[:5]}")
        return True
    except Exception as e:
        print(f"❌ 向量生成失败: {str(e)}")
        return False


def test_text_chunking():
    """测试文本分块"""
    print("\n=== 测试2: 文本分块 ===")
    try:
        service = EmbeddingService()
        text = "第一段。第二段！第三段？第四段。第五段！"
        chunks = service._split_into_chunks(text, chunk_size=10)
        print(f"✅ 文本分块成功")
        print(f"   原始文本长度: {len(text)}")
        print(f"   分块数量: {len(chunks)}")
        for i, chunk in enumerate(chunks[:3]):  # 只显示前3个
            print(f"   块 {i+1}: {chunk[:30]}...")
        return True
    except Exception as e:
        print(f"❌ 文本分块失败: {str(e)}")
        return False


def test_database_connection():
    """测试数据库连接"""
    print("\n=== 测试3: 数据库连接 ===")
    try:
        engine = create_engine(DATABASE_URL)
        Session = sessionmaker(bind=engine)
        db = Session()
        
        # 测试查询
        from sqlalchemy import text
        result = db.execute(text("SELECT 1")).fetchone()
        db.close()
        
        print(f"✅ 数据库连接成功")
        return True, Session
    except Exception as e:
        print(f"❌ 数据库连接失败: {str(e)}")
        return False, None


def test_table_existence(Session):
    """测试向量表是否存在"""
    print("\n=== 测试4: 向量表检查 ===")
    try:
        db = Session()
        from sqlalchemy import text
        
        tables = [
            "chapter_embeddings",
            "character_embeddings",
            "world_setting_embeddings",
            "foreshadowing_embeddings"
        ]
        
        all_exist = True
        for table in tables:
            result = db.execute(
                text(f"""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = '{table}'
                    )
                """)
            ).fetchone()
            
            exists = result[0] if result else False
            status = "✅" if exists else "❌"
            print(f"   {status} {table}: {'存在' if exists else '不存在'}")
            if not exists:
                all_exist = False
        
        db.close()
        
        if all_exist:
            print(f"✅ 所有向量表都存在")
        else:
            print(f"⚠️  部分向量表不存在，请运行迁移脚本")
        return all_exist
    except Exception as e:
        print(f"❌ 检查向量表失败: {str(e)}")
        return False


def test_pgvector_extension(Session):
    """测试pgvector扩展是否安装"""
    print("\n=== 测试5: pgvector扩展检查 ===")
    try:
        db = Session()
        from sqlalchemy import text
        
        result = db.execute(
            text("SELECT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector')")
        ).fetchone()
        
        db.close()
        
        exists = result[0] if result else False
        if exists:
            print(f"✅ pgvector扩展已安装")
        else:
            print(f"❌ pgvector扩展未安装，请运行迁移脚本")
        return exists
    except Exception as e:
        print(f"❌ 检查pgvector扩展失败: {str(e)}")
        return False


def test_service_initialization():
    """测试服务初始化"""
    print("\n=== 测试6: 服务初始化 ===")
    try:
        services = {
            "EmbeddingService": EmbeddingService(),
            "ConsistencyChecker": ConsistencyChecker(),
            "ForeshadowingMatcher": ForeshadowingMatcher(),
            "ContentSimilarityChecker": ContentSimilarityChecker()
        }
        
        all_ok = True
        for name, service in services.items():
            print(f"   ✅ {name} 初始化成功")
        
        print(f"✅ 所有服务初始化成功")
        return True
    except Exception as e:
        print(f"❌ 服务初始化失败: {str(e)}")
        return False


def main():
    """主测试函数"""
    print("=" * 60)
    print("向量数据库功能测试")
    print("=" * 60)
    
    results = []
    
    # 测试1: 向量生成
    results.append(("向量生成", test_embedding_generation()))
    
    # 测试2: 文本分块
    results.append(("文本分块", test_text_chunking()))
    
    # 测试3: 数据库连接
    db_ok, Session = test_database_connection()
    results.append(("数据库连接", db_ok))
    
    # 测试4-5: 需要数据库连接
    if db_ok and Session:
        results.append(("pgvector扩展", test_pgvector_extension(Session)))
        results.append(("向量表检查", test_table_existence(Session)))
    
    # 测试6: 服务初始化
    results.append(("服务初始化", test_service_initialization()))
    
    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{name}: {status}")
    
    print(f"\n总计: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！")
        return 0
    else:
        print("⚠️  部分测试失败，请检查配置和数据库状态")
        return 1


if __name__ == "__main__":
    sys.exit(main())


