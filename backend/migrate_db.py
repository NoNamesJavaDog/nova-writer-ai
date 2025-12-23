"""数据库迁移：添加登录安全字段"""
from database import engine
from sqlalchemy import text

def migrate():
    conn = engine.connect()
    trans = conn.begin()
    try:
        # 检查字段是否已存在
        result = conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'users' 
            AND column_name IN ('password_fail_count', 'captcha_fail_count', 'locked_until', 'last_fail_time')
        """))
        existing = {row[0] for row in result}
        
        if 'password_fail_count' not in existing:
            conn.execute(text("ALTER TABLE users ADD COLUMN password_fail_count INTEGER DEFAULT 0"))
            print("✅ Added password_fail_count")
        
        if 'captcha_fail_count' not in existing:
            conn.execute(text("ALTER TABLE users ADD COLUMN captcha_fail_count INTEGER DEFAULT 0"))
            print("✅ Added captcha_fail_count")
        
        if 'locked_until' not in existing:
            conn.execute(text("ALTER TABLE users ADD COLUMN locked_until BIGINT"))
            print("✅ Added locked_until")
        
        if 'last_fail_time' not in existing:
            conn.execute(text("ALTER TABLE users ADD COLUMN last_fail_time BIGINT"))
            print("✅ Added last_fail_time")
        
        trans.commit()
        print("✅ Migration completed successfully")
    except Exception as e:
        trans.rollback()
        print(f"❌ Migration failed: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()

