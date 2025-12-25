"""
数据库迁移脚本：添加 pgvector 扩展和向量存储表

使用方法：
    python migrate_add_pgvector.py

此脚本将：
1. 安装 pgvector 扩展
2. 创建章节向量表 (chapter_embeddings)
3. 创建角色向量表 (character_embeddings)
4. 创建世界观向量表 (world_setting_embeddings)
5. 创建伏笔向量表 (foreshadowing_embeddings)
6. 创建相应的索引
"""

import sys
import os
from sqlalchemy import create_engine, text
from config import DATABASE_URL

def run_migration():
    """执行迁移"""
    print("🚀 开始执行 pgvector 迁移...")
    
    # 创建数据库连接
    engine = create_engine(DATABASE_URL)
    
    try:
        with engine.connect() as conn:
            # 开始事务
            trans = conn.begin()
            
            try:
                # 1. 安装 pgvector 扩展
                print("📦 步骤 1/6: 安装 pgvector 扩展...")
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
                print("✅ pgvector 扩展安装成功")
                
                # 2. 创建章节向量表
                print("📦 步骤 2/6: 创建 chapter_embeddings 表...")
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS chapter_embeddings (
                        id VARCHAR(36) PRIMARY KEY,
                        chapter_id VARCHAR(36) NOT NULL REFERENCES chapters(id) ON DELETE CASCADE,
                        novel_id VARCHAR(36) NOT NULL REFERENCES novels(id) ON DELETE CASCADE,
                        full_content_embedding vector(768),
                        paragraph_embeddings vector(768)[],
                        embedding_model VARCHAR(50) DEFAULT 'models/text-embedding-004',
                        chunk_count INTEGER DEFAULT 0,
                        created_at BIGINT NOT NULL,
                        updated_at BIGINT NOT NULL,
                        CONSTRAINT chapter_embeddings_chapter_fk FOREIGN KEY (chapter_id) REFERENCES chapters(id) ON DELETE CASCADE,
                        CONSTRAINT chapter_embeddings_novel_fk FOREIGN KEY (novel_id) REFERENCES novels(id) ON DELETE CASCADE
                    )
                """))
                
                # 创建索引
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_chapter_embeddings_chapter_id 
                    ON chapter_embeddings(chapter_id)
                """))
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_chapter_embeddings_novel_id 
                    ON chapter_embeddings(novel_id)
                """))
                
                # 向量相似度索引 - 使用 IVFFlat（适合小到中等规模数据）
                # 注意：IVFFlat 需要先有一些数据才能创建，所以我们先创建基本索引
                # 实际使用时可以根据数据量选择 IVFFlat 或 HNSW
                print("✅ chapter_embeddings 表创建成功")
                
                # 3. 创建角色向量表
                print("📦 步骤 3/6: 创建 character_embeddings 表...")
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS character_embeddings (
                        id VARCHAR(36) PRIMARY KEY,
                        character_id VARCHAR(36) UNIQUE NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
                        novel_id VARCHAR(36) NOT NULL REFERENCES novels(id) ON DELETE CASCADE,
                        full_description_embedding vector(768),
                        embedding_model VARCHAR(50) DEFAULT 'models/text-embedding-004',
                        created_at BIGINT NOT NULL,
                        updated_at BIGINT NOT NULL,
                        CONSTRAINT character_embeddings_character_fk FOREIGN KEY (character_id) REFERENCES characters(id) ON DELETE CASCADE,
                        CONSTRAINT character_embeddings_novel_fk FOREIGN KEY (novel_id) REFERENCES novels(id) ON DELETE CASCADE
                    )
                """))
                
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_character_embeddings_character_id 
                    ON character_embeddings(character_id)
                """))
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_character_embeddings_novel_id 
                    ON character_embeddings(novel_id)
                """))
                print("✅ character_embeddings 表创建成功")
                
                # 4. 创建世界观向量表
                print("📦 步骤 4/6: 创建 world_setting_embeddings 表...")
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS world_setting_embeddings (
                        id VARCHAR(36) PRIMARY KEY,
                        world_setting_id VARCHAR(36) UNIQUE NOT NULL REFERENCES world_settings(id) ON DELETE CASCADE,
                        novel_id VARCHAR(36) NOT NULL REFERENCES novels(id) ON DELETE CASCADE,
                        full_description_embedding vector(768),
                        embedding_model VARCHAR(50) DEFAULT 'models/text-embedding-004',
                        created_at BIGINT NOT NULL,
                        updated_at BIGINT NOT NULL,
                        CONSTRAINT world_setting_embeddings_world_setting_fk FOREIGN KEY (world_setting_id) REFERENCES world_settings(id) ON DELETE CASCADE,
                        CONSTRAINT world_setting_embeddings_novel_fk FOREIGN KEY (novel_id) REFERENCES novels(id) ON DELETE CASCADE
                    )
                """))
                
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_world_setting_embeddings_world_setting_id 
                    ON world_setting_embeddings(world_setting_id)
                """))
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_world_setting_embeddings_novel_id 
                    ON world_setting_embeddings(novel_id)
                """))
                print("✅ world_setting_embeddings 表创建成功")
                
                # 5. 创建伏笔向量表
                print("📦 步骤 5/6: 创建 foreshadowing_embeddings 表...")
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS foreshadowing_embeddings (
                        id VARCHAR(36) PRIMARY KEY,
                        foreshadowing_id VARCHAR(36) UNIQUE NOT NULL REFERENCES foreshadowings(id) ON DELETE CASCADE,
                        novel_id VARCHAR(36) NOT NULL REFERENCES novels(id) ON DELETE CASCADE,
                        content_embedding vector(768),
                        embedding_model VARCHAR(50) DEFAULT 'models/text-embedding-004',
                        created_at BIGINT NOT NULL,
                        updated_at BIGINT NOT NULL,
                        CONSTRAINT foreshadowing_embeddings_foreshadowing_fk FOREIGN KEY (foreshadowing_id) REFERENCES foreshadowings(id) ON DELETE CASCADE,
                        CONSTRAINT foreshadowing_embeddings_novel_fk FOREIGN KEY (novel_id) REFERENCES novels(id) ON DELETE CASCADE
                    )
                """))
                
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_foreshadowing_embeddings_foreshadowing_id 
                    ON foreshadowing_embeddings(foreshadowing_id)
                """))
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_foreshadowing_embeddings_novel_id 
                    ON foreshadowing_embeddings(novel_id)
                """))
                print("✅ foreshadowing_embeddings 表创建成功")
                
                # 6. 创建向量相似度索引
                # 注意：IVFFlat 索引需要先有数据才能创建，我们会在有数据后通过另一个脚本创建
                # 或者使用 HNSW（不需要数据就能创建，但性能稍差）
                print("📦 步骤 6/6: 创建向量相似度索引（HNSW）...")
                
                try:
                    # 为章节向量创建 HNSW 索引（更适合生产环境）
                    conn.execute(text("""
                        CREATE INDEX IF NOT EXISTS idx_chapter_full_embedding_hnsw 
                        ON chapter_embeddings USING hnsw (full_content_embedding vector_cosine_ops)
                        WITH (m = 16, ef_construction = 64)
                    """))
                    print("✅ chapter_embeddings 向量索引创建成功")
                except Exception as e:
                    print(f"⚠️  章节向量索引创建失败（可能已有索引）: {e}")
                
                try:
                    conn.execute(text("""
                        CREATE INDEX IF NOT EXISTS idx_character_embedding_hnsw 
                        ON character_embeddings USING hnsw (full_description_embedding vector_cosine_ops)
                        WITH (m = 16, ef_construction = 64)
                    """))
                    print("✅ character_embeddings 向量索引创建成功")
                except Exception as e:
                    print(f"⚠️  角色向量索引创建失败（可能已有索引）: {e}")
                
                try:
                    conn.execute(text("""
                        CREATE INDEX IF NOT EXISTS idx_world_setting_embedding_hnsw 
                        ON world_setting_embeddings USING hnsw (full_description_embedding vector_cosine_ops)
                        WITH (m = 16, ef_construction = 64)
                    """))
                    print("✅ world_setting_embeddings 向量索引创建成功")
                except Exception as e:
                    print(f"⚠️  世界观向量索引创建失败（可能已有索引）: {e}")
                
                try:
                    conn.execute(text("""
                        CREATE INDEX IF NOT EXISTS idx_foreshadowing_embedding_hnsw 
                        ON foreshadowing_embeddings USING hnsw (content_embedding vector_cosine_ops)
                        WITH (m = 16, ef_construction = 64)
                    """))
                    print("✅ foreshadowing_embeddings 向量索引创建成功")
                except Exception as e:
                    print(f"⚠️  伏笔向量索引创建失败（可能已有索引）: {e}")
                
                # 提交事务
                trans.commit()
                print("\n🎉 迁移完成！所有表已创建。")
                
            except Exception as e:
                # 回滚事务
                trans.rollback()
                print(f"\n❌ 迁移失败，已回滚: {e}")
                raise
                
    except Exception as e:
        print(f"\n❌ 数据库连接失败: {e}")
        sys.exit(1)
    finally:
        engine.dispose()

if __name__ == "__main__":
    run_migration()

