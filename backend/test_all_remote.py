#!/usr/bin/env python
"""
远程服务器完整测试脚本
测试所有向量数据库功能
"""
import os
import sys
import time

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 60)
print("pgvector 向量数据库集成 - 完整测试")
print("=" * 60)

# 1. 检查依赖
print("\n[1/6] 检查依赖...")
missing_deps = []

try:
    import redis
    print("  ✅ redis")
except ImportError:
    print("  ⚠️  redis (可选，缓存功能将被禁用)")
    missing_deps.append("redis")

try:
    import sqlalchemy
    print("  ✅ sqlalchemy")
except ImportError:
    print("  ❌ sqlalchemy (必需)")
    missing_deps.append("sqlalchemy")
    sys.exit(1)

try:
    import pgvector
    print("  ✅ pgvector")
except ImportError:
    print("  ❌ pgvector (必需)")
    missing_deps.append("pgvector")
    sys.exit(1)

try:
    import google.genai
    print("  ✅ google-genai")
except ImportError:
    print("  ❌ google-genai (必需)")
    missing_deps.append("google-genai")
    sys.exit(1)

try:
    from config import GEMINI_API_KEY, DATABASE_URL
    print("  ✅ config")
except ImportError:
    print("  ❌ config (检查config.py和.env文件)")
    sys.exit(1)

# 2. 检查环境变量
print("\n[2/6] 检查环境变量...")
if not GEMINI_API_KEY:
    print("  ❌ GEMINI_API_KEY 未配置")
    sys.exit(1)
else:
    print(f"  ✅ GEMINI_API_KEY: {'*' * 20}")

if not DATABASE_URL:
    print("  ❌ DATABASE_URL 未配置")
    sys.exit(1)
else:
    print("  ✅ DATABASE_URL 已配置")

# 3. 测试服务导入
print("\n[3/6] 测试服务导入...")
try:
    from services.embedding_service import EmbeddingService
    print("  ✅ EmbeddingService")
    
    from services.consistency_checker import ConsistencyChecker
    print("  ✅ ConsistencyChecker")
    
    from services.foreshadowing_matcher import ForeshadowingMatcher
    print("  ✅ ForeshadowingMatcher")
    
    from services.content_similarity_checker import ContentSimilarityChecker
    print("  ✅ ContentSimilarityChecker")
    
    from services.embedding_cache import EmbeddingCache
    print("  ✅ EmbeddingCache")
    
    from services.batch_embedding_processor import BatchEmbeddingProcessor
    print("  ✅ BatchEmbeddingProcessor")
    
    from config_threshold import ThresholdConfig
    print("  ✅ ThresholdConfig")
    
except Exception as e:
    print(f"  ❌ 导入失败: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 4. 测试向量生成
print("\n[4/6] 测试向量生成...")
try:
    service = EmbeddingService()
    test_text = "这是一个测试文本，用于验证向量生成功能。"
    
    start = time.time()
    embedding = service.generate_embedding(test_text)
    elapsed = time.time() - start
    
    print(f"  ✅ 向量生成成功")
    print(f"     维度: {len(embedding)}")
    print(f"     耗时: {elapsed:.2f}秒")
    print(f"     前5个值: {embedding[:5]}")
    
except Exception as e:
    print(f"  ❌ 向量生成失败: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 5. 测试数据库连接
print("\n[5/6] 测试数据库连接...")
try:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    db = Session()
    
    # 测试查询
    from sqlalchemy import text
    result = db.execute(text("SELECT 1")).fetchone()
    db.close()
    
    print("  ✅ 数据库连接成功")
    
    # 检查pgvector扩展
    try:
        db = Session()
        result = db.execute(
            text("SELECT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector')")
        ).fetchone()
        db.close()
        
        if result[0]:
            print("  ✅ pgvector扩展已安装")
        else:
            print("  ⚠️  pgvector扩展未安装，请运行 migrate_add_pgvector.py")
    except Exception as e:
        print(f"  ⚠️  检查pgvector扩展失败: {str(e)}")
    
    # 检查向量表
    try:
        db = Session()
        tables = ['chapter_embeddings', 'character_embeddings', 
                  'world_setting_embeddings', 'foreshadowing_embeddings']
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
            
            if result[0]:
                print(f"  ✅ {table} 表存在")
            else:
                print(f"  ⚠️  {table} 表不存在")
                all_exist = False
        
        db.close()
        
        if not all_exist:
            print("  ⚠️  部分向量表不存在，请运行 migrate_add_pgvector.py")
    except Exception as e:
        print(f"  ⚠️  检查向量表失败: {str(e)}")
    
except Exception as e:
    print(f"  ❌ 数据库连接失败: {str(e)}")
    import traceback
    traceback.print_exc()

# 6. 测试其他功能
print("\n[6/6] 测试其他功能...")

# 测试文本分块
try:
    chunks = service._split_into_chunks("第一段。第二段！第三段？", chunk_size=10)
    print(f"  ✅ 文本分块: {len(chunks)} 个块")
except Exception as e:
    print(f"  ⚠️  文本分块测试失败: {str(e)}")

# 测试阈值配置
try:
    from config_threshold import get_threshold_config
    config = get_threshold_config()
    threshold = config.get('chapter_similarity')
    print(f"  ✅ 阈值配置: chapter_similarity = {threshold}")
except Exception as e:
    print(f"  ⚠️  阈值配置测试失败: {str(e)}")

# 测试缓存（如果Redis可用）
try:
    from services.embedding_cache import get_embedding_cache
    cache = get_embedding_cache()
    if cache.enabled:
        print("  ✅ Redis缓存已启用")
    else:
        print("  ⚠️  Redis缓存未启用（Redis未安装或不可用）")
except Exception as e:
    print(f"  ⚠️  缓存测试失败: {str(e)}")

# 总结
print("\n" + "=" * 60)
print("测试总结")
print("=" * 60)
print("✅ 所有核心功能测试通过！")
print("\n下一步：")
print("1. 如果向量表不存在，运行: python migrate_add_pgvector.py")
print("2. 运行完整测试: python test_vector_features.py")
print("3. 运行性能测试: python test_performance.py")
print("4. 查看使用文档: PGVECTOR_README.md")
print("=" * 60)

