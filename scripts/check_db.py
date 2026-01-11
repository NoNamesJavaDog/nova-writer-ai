#!/usr/bin/env python3
"""数据库连接检查脚本"""

import sys
import os

# 添加 backend 到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

try:
    from sqlalchemy import create_engine, text
    from core.config import DATABASE_URL

    print("🔍 检查数据库连接...")
    print(f"📍 数据库 URL: {DATABASE_URL}")
    print()

    # 创建引擎
    engine = create_engine(DATABASE_URL)

    # 测试连接
    with engine.connect() as conn:
        # 获取 PostgreSQL 版本
        result = conn.execute(text("SELECT version()"))
        version = result.fetchone()[0]
        print(f"✅ 数据库连接成功！")
        print(f"   版本: {version[:50]}...")
        print()

        # 检查 pgvector 扩展
        result = conn.execute(text("SELECT * FROM pg_extension WHERE extname = 'vector'"))
        if result.fetchone():
            print("✅ pgvector 扩展已安装")
        else:
            print("⚠️  pgvector 扩展未安装（运行初始化脚本会自动安装）")
        print()

        # 列出所有表
        result = conn.execute(text("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name
        """))
        tables = [row[0] for row in result]

        if tables:
            print(f"✅ 数据库包含 {len(tables)} 个表:")
            for table in tables:
                print(f"   - {table}")
        else:
            print("⚠️  数据库为空（请运行初始化脚本）")

    print()
    print("🎉 数据库状态正常！")
    sys.exit(0)

except Exception as e:
    print(f"❌ 数据库连接失败: {str(e)}")
    print()
    print("💡 常见原因:")
    print("   1. PostgreSQL 未运行")
    print("   2. DATABASE_URL 配置错误")
    print("   3. 数据库不存在")
    print("   4. 用户权限不足")
    print()
    print("🔧 建议:")
    print("   1. 检查 PostgreSQL 是否运行: docker ps | grep postgres")
    print("   2. 检查 backend/.env 中的 DATABASE_URL 配置")
    print("   3. 确保数据库已创建: psql -U postgres -c 'CREATE DATABASE novawrite_ai;'")
    sys.exit(1)
