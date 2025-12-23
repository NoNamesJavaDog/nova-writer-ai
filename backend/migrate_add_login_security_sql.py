"""数据库迁移脚本：使用 SQLAlchemy 添加登录安全相关字段"""
from sqlalchemy import text
from database import engine
import sys

def migrate():
    """添加登录安全相关字段到 users 表"""
    with engine.connect() as conn:
        try:
            # 开始事务
            trans = conn.begin()
            
            try:
                # 检查字段是否已存在，如果不存在则添加
                inspector_result = conn.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'users' 
                    AND column_name IN ('password_fail_count', 'captcha_fail_count', 'locked_until', 'last_fail_time')
                """))
                existing_columns = {row[0] for row in inspector_result}
                
                # 添加 password_fail_count
                if 'password_fail_count' not in existing_columns:
                    conn.execute(text("""
                        ALTER TABLE users 
                        ADD COLUMN password_fail_count INTEGER DEFAULT 0 NOT NULL
                    """))
                    print("✅ 添加 password_fail_count 字段")
                else:
                    print("ℹ️ password_fail_count 字段已存在")
                
                # 添加 captcha_fail_count
                if 'captcha_fail_count' not in existing_columns:
                    conn.execute(text("""
                        ALTER TABLE users 
                        ADD COLUMN captcha_fail_count INTEGER DEFAULT 0 NOT NULL
                    """))
                    print("✅ 添加 captcha_fail_count 字段")
                else:
                    print("ℹ️ captcha_fail_count 字段已存在")
                
                # 添加 locked_until
                if 'locked_until' not in existing_columns:
                    conn.execute(text("""
                        ALTER TABLE users 
                        ADD COLUMN locked_until BIGINT
                    """))
                    print("✅ 添加 locked_until 字段")
                else:
                    print("ℹ️ locked_until 字段已存在")
                
                # 添加 last_fail_time
                if 'last_fail_time' not in existing_columns:
                    conn.execute(text("""
                        ALTER TABLE users 
                        ADD COLUMN last_fail_time BIGINT
                    """))
                    print("✅ 添加 last_fail_time 字段")
                else:
                    print("ℹ️ last_fail_time 字段已存在")
                
                # 提交事务
                trans.commit()
                print("✅ 数据库迁移完成")
                
            except Exception as e:
                # 回滚事务
                trans.rollback()
                print(f"❌ 迁移失败: {e}")
                print("\n如果权限不足，请使用 PostgreSQL 超级用户手动执行以下 SQL:")
                print("""
ALTER TABLE users ADD COLUMN IF NOT EXISTS password_fail_count INTEGER DEFAULT 0 NOT NULL;
ALTER TABLE users ADD COLUMN IF NOT EXISTS captcha_fail_count INTEGER DEFAULT 0 NOT NULL;
ALTER TABLE users ADD COLUMN IF NOT EXISTS locked_until BIGINT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS last_fail_time BIGINT;
                """)
                sys.exit(1)
                
        except Exception as e:
            print(f"❌ 连接数据库失败: {e}")
            sys.exit(1)

if __name__ == "__main__":
    migrate()

