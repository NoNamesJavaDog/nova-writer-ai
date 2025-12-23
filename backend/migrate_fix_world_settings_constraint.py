#!/usr/bin/env python3
"""修复 world_settings 表的 category 字段约束"""
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from config import DATABASE_URL

def migrate():
    """修复 world_settings 表的约束"""
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        try:
            # 开始事务
            trans = conn.begin()
            
            # 删除旧的约束（如果存在）
            print("删除旧的 category 约束...")
            conn.execute(text("""
                DO $$
                BEGIN
                    -- 删除可能存在的旧约束
                    IF EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'check_category' AND conrelid = 'world_settings'::regclass) THEN
                        ALTER TABLE world_settings DROP CONSTRAINT check_category;
                    END IF;
                    
                    IF EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'world_settings_category_check' AND conrelid = 'world_settings'::regclass) THEN
                        ALTER TABLE world_settings DROP CONSTRAINT world_settings_category_check;
                    END IF;
                END $$;
            """))
            
            # 添加新的约束
            print("添加新的 category 约束...")
            conn.execute(text("""
                ALTER TABLE world_settings 
                ADD CONSTRAINT check_category 
                CHECK (category IN ('地理', '社会', '魔法/科技', '历史', '其他'));
            """))
            
            # 提交事务
            trans.commit()
            print("✅ 约束修复完成！")
            
            # 验证约束
            result = conn.execute(text("""
                SELECT conname, pg_get_constraintdef(oid) 
                FROM pg_constraint 
                WHERE conrelid = 'world_settings'::regclass 
                AND contype = 'c';
            """))
            
            print("\n当前约束定义：")
            for row in result:
                print(f"  约束名称: {row[0]}")
                print(f"  约束定义: {row[1]}")
            
        except Exception as e:
            trans.rollback()
            print(f"❌ 迁移失败: {e}")
            raise
        finally:
            conn.close()

if __name__ == "__main__":
    migrate()

