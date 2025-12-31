"""
性能测试脚本
用于测试向量生成、存储和检索的性能
"""
import os
import sys
import time
import statistics

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import DATABASE_URL
from services.embedding_service import EmbeddingService
from services.consistency_checker import ConsistencyChecker


def test_embedding_generation_performance():
    """测试向量生成性能"""
    print("\n=== 性能测试1: 向量生成 ===")
    
    service = EmbeddingService()
    test_texts = [
        "这是一个测试文本，用于验证向量生成性能。",
        "向量数据库可以用于语义搜索和相似度匹配。",
        "人工智能技术在自然语言处理领域有广泛应用。",
        "文本嵌入是将文本转换为数值向量的过程。",
        "相似度计算可以帮助找到语义相近的内容。"
    ]
    
    times = []
    for i, text in enumerate(test_texts):
        start = time.time()
        try:
            embedding = service.generate_embedding(text)
            elapsed = time.time() - start
            times.append(elapsed)
            print(f"   文本 {i+1}: {elapsed:.2f}秒 (维度: {len(embedding)})")
        except Exception as e:
            print(f"   ❌ 文本 {i+1} 失败: {str(e)}")
    
    if times:
        avg_time = statistics.mean(times)
        min_time = min(times)
        max_time = max(times)
        print(f"\n   平均时间: {avg_time:.2f}秒")
        print(f"   最短时间: {min_time:.2f}秒")
        print(f"   最长时间: {max_time:.2f}秒")
        return avg_time
    return None


def test_text_chunking_performance():
    """测试文本分块性能"""
    print("\n=== 性能测试2: 文本分块 ===")
    
    service = EmbeddingService()
    # 生成一个较长的测试文本
    long_text = "。" * 1000 + "这是一个较长的测试文本。" * 50
    
    start = time.time()
    chunks = service._split_into_chunks(long_text, chunk_size=500)
    elapsed = time.time() - start
    
    print(f"   文本长度: {len(long_text)} 字符")
    print(f"   分块数量: {len(chunks)}")
    print(f"   处理时间: {elapsed:.4f}秒")
    print(f"   平均每块: {len(long_text) / len(chunks):.0f} 字符")
    
    return elapsed


def test_storage_performance(Session):
    """测试向量存储性能（需要数据库连接）"""
    print("\n=== 性能测试3: 向量存储 ===")
    
    try:
        db = Session()
        service = EmbeddingService()
        
        # 使用测试数据（注意：需要有效的章节ID和小说ID）
        test_content = "这是一个测试章节内容。" * 100
        
        start = time.time()
        try:
            # 注意：这里需要有效的ID，否则会失败
            # service.store_chapter_embedding(
            #     db=db,
            #     chapter_id="test-chapter-id",
            #     novel_id="test-novel-id",
            #     content=test_content
            # )
            # elapsed = time.time() - start
            # print(f"   存储时间: {elapsed:.2f}秒")
            print("   ⚠️  需要有效的章节ID和小说ID才能测试存储性能")
            print("   （跳过实际存储测试）")
            elapsed = None
        except Exception as e:
            print(f"   ⚠️  存储测试失败: {str(e)}")
            elapsed = None
        finally:
            db.close()
        
        return elapsed
    except Exception as e:
        print(f"   ❌ 数据库连接失败: {str(e)}")
        return None


def test_retrieval_performance(Session):
    """测试检索性能（需要数据库连接）"""
    print("\n=== 性能测试4: 相似度检索 ===")
    
    try:
        db = Session()
        service = EmbeddingService()
        
        # 检查是否有数据
        from sqlalchemy import text
        result = db.execute(
            text("SELECT COUNT(*) FROM chapter_embeddings")
        ).fetchone()
        
        count = result[0] if result else 0
        
        if count == 0:
            print("   ⚠️  数据库中没有向量数据，无法测试检索性能")
            print("   （请先创建一些章节并存储向量）")
            db.close()
            return None
        
        query_text = "这是一个测试查询文本"
        
        start = time.time()
        try:
            # 需要有效的novel_id
            # similar = service.find_similar_chapters(
            #     db=db,
            #     novel_id="test-novel-id",
            #     query_text=query_text,
            #     limit=5
            # )
            # elapsed = time.time() - start
            # print(f"   检索时间: {elapsed:.2f}秒")
            # print(f"   找到 {len(similar)} 个相似章节")
            print("   ⚠️  需要有效的novel_id才能测试检索性能")
            print(f"   （数据库中有 {count} 个章节向量）")
            elapsed = None
        except Exception as e:
            print(f"   ⚠️  检索测试失败: {str(e)}")
            elapsed = None
        finally:
            db.close()
        
        return elapsed
    except Exception as e:
        print(f"   ❌ 数据库连接失败: {str(e)}")
        return None


def test_context_retrieval_performance(Session):
    """测试智能上下文检索性能"""
    print("\n=== 性能测试5: 智能上下文检索 ===")
    
    try:
        db = Session()
        checker = ConsistencyChecker()
        
        start = time.time()
        try:
            # 需要有效的novel_id
            # context = checker.get_relevant_context_text(
            #     db=db,
            #     novel_id="test-novel-id",
            #     current_chapter_title="测试章节",
            #     current_chapter_summary="测试摘要",
            #     max_chapters=3
            # )
            # elapsed = time.time() - start
            # print(f"   检索时间: {elapsed:.2f}秒")
            # print(f"   上下文长度: {len(context)} 字符")
            print("   ⚠️  需要有效的novel_id才能测试上下文检索性能")
            elapsed = None
        except Exception as e:
            print(f"   ⚠️  上下文检索测试失败: {str(e)}")
            elapsed = None
        finally:
            db.close()
        
        return elapsed
    except Exception as e:
        print(f"   ❌ 数据库连接失败: {str(e)}")
        return None


def main():
    """主测试函数"""
    print("=" * 60)
    print("向量数据库性能测试")
    print("=" * 60)
    
    results = {}
    
    # 测试1: 向量生成
    results["向量生成"] = test_embedding_generation_performance()
    
    # 测试2: 文本分块
    results["文本分块"] = test_text_chunking_performance()
    
    # 测试3-5: 需要数据库连接
    try:
        engine = create_engine(DATABASE_URL)
        Session = sessionmaker(bind=engine)
        
        results["向量存储"] = test_storage_performance(Session)
        results["相似度检索"] = test_retrieval_performance(Session)
        results["上下文检索"] = test_context_retrieval_performance(Session)
    except Exception as e:
        print(f"\n⚠️  数据库连接失败，跳过需要数据库的测试: {str(e)}")
    
    # 总结
    print("\n" + "=" * 60)
    print("性能测试总结")
    print("=" * 60)
    
    for name, result in results.items():
        if result:
            print(f"{name}: {result:.2f}秒")
        else:
            print(f"{name}: 未测试（需要配置或数据）")
    
    print("\n性能基准建议:")
    print("- 向量生成: < 3秒/次（取决于API响应时间）")
    print("- 文本分块: < 0.01秒（本地处理，应该很快）")
    print("- 向量存储: < 1秒（包括向量生成和数据库写入）")
    print("- 相似度检索: < 0.5秒（使用索引，应该很快）")
    print("- 上下文检索: < 2秒（包括检索和格式化）")


if __name__ == "__main__":
    main()


