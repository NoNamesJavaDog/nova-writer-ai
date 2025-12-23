"""数据库迁移脚本：添加登录安全相关字段"""
from sqlalchemy import text
from database import engine

def migrate():
    """添加登录安全相关字段到 users 表"""
    with engine.connect() as conn:
        try:
            # 添加密码失败次数字段
            conn.execute(text("""
                ALTER TABLE users 
                ADD COLUMN IF NOT EXISTS password_fail_count INTEGER DEFAULT 0 NOT NULL
            """))
            print("✅ 添加 password_fail_count 字段")
            
            # 添加验证码失败次数字段
            conn.execute(text("""
                ALTER TABLE users 
                ADD COLUMN IF NOT EXISTS captcha_fail_count INTEGER DEFAULT 0 NOT NULL
            """))
            print("✅ 添加 captcha_fail_count 字段")
            
            # 添加锁定到期时间字段
            conn.execute(text("""
                ALTER TABLE users 
                ADD COLUMN IF NOT EXISTS locked_until BIGINT
            """))
            print("✅ 添加 locked_until 字段")
            
            # 添加最后失败时间字段
            conn.execute(text("""
                ALTER TABLE users 
                ADD COLUMN IF NOT EXISTS last_fail_time BIGINT
            """))
            print("✅ 添加 last_fail_time 字段")
            
            conn.commit()
            print("✅ 数据库迁移完成")
        except Exception as e:
            print(f"❌ 迁移失败: {e}")
            conn.rollback()
            raise

if __name__ == "__main__":
    migrate()

