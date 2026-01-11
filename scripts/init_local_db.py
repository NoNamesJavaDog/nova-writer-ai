#!/usr/bin/env python3
"""本地数据库初始化脚本"""

import sys
import os

# 添加 backend 到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from sqlalchemy import create_engine, text
from database import Base
from models import *  # 导入所有模型
from core.config import DATABASE_URL

def init_database():
    """初始化数据库"""
    print("🚀 开始初始化数据库...")
    print(f"📍 数据库 URL: {DATABASE_URL}")

    try:
        # 创建数据库引擎
        engine = create_engine(DATABASE_URL, echo=True)

        # 测试连接
        print("\n📡 测试数据库连接...")
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"✅ 数据库连接成功！")
            print(f"   PostgreSQL 版本: {version}")

        # 创建 pgvector 扩展
        print("\n📦 创建 pgvector 扩展...")
        with engine.connect() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            conn.commit()
            print("✅ pgvector 扩展已创建")

        # 创建所有表
        print("\n📋 创建数据库表...")
        Base.metadata.create_all(bind=engine)
        print("✅ 所有表创建成功！")

        # 创建向量表
        print("\n🔢 创建向量存储表...")
        with engine.connect() as conn:
            # 章节向量表
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS chapter_embeddings (
                    id VARCHAR(36) PRIMARY KEY,
                    chapter_id VARCHAR(36) NOT NULL,
                    novel_id VARCHAR(36) NOT NULL,
                    title_embedding vector(768),
                    summary_embedding vector(768),
                    full_content_embedding vector(768),
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

            # 创建向量索引（HNSW）
            try:
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_chapter_embeddings_full_content
                    ON chapter_embeddings USING hnsw (full_content_embedding vector_cosine_ops)
                """))
                print("✅ 章节向量表创建成功")
            except Exception as e:
                print(f"⚠️  向量索引创建警告: {e}")

            conn.commit()

        # 验证表
        print("\n🔍 验证表结构...")
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            tables = [row[0] for row in result]
            print(f"✅ 已创建 {len(tables)} 个表:")
            for table in tables:
                print(f"   - {table}")

        print("\n🎉 数据库初始化完成！")
        return True

    except Exception as e:
        print(f"\n❌ 初始化失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = init_database()
    sys.exit(0 if success else 1)
