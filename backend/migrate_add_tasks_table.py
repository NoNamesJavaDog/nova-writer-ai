"""数据库迁移：添加 tasks 表"""
from sqlalchemy import text
from database import engine

def migrate():
    """添加 tasks 表"""
    with engine.connect() as conn:
        try:
            # 开始事务
            trans = conn.begin()
            
            # 检查表是否已存在
            inspector_result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_name = 'tasks'
            """))
            if inspector_result.fetchone():
                print("ℹ️ tasks 表已存在")
                trans.commit()
                return
            
            # 创建 tasks 表
            conn.execute(text("""
                CREATE TABLE tasks (
                    id VARCHAR(36) PRIMARY KEY,
                    novel_id VARCHAR(36) NOT NULL,
                    user_id VARCHAR(36) NOT NULL,
                    task_type VARCHAR(50) NOT NULL,
                    task_data TEXT,
                    status VARCHAR(20) NOT NULL DEFAULT 'pending',
                    progress INTEGER NOT NULL DEFAULT 0,
                    progress_message TEXT,
                    result TEXT,
                    error_message TEXT,
                    created_at BIGINT NOT NULL,
                    updated_at BIGINT NOT NULL,
                    started_at BIGINT,
                    completed_at BIGINT,
                    FOREIGN KEY (novel_id) REFERENCES novels(id) ON DELETE CASCADE,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """))
            
            # 创建索引
            conn.execute(text("CREATE INDEX idx_tasks_novel_id ON tasks(novel_id)"))
            conn.execute(text("CREATE INDEX idx_tasks_user_id ON tasks(user_id)"))
            conn.execute(text("CREATE INDEX idx_tasks_status ON tasks(status)"))
            conn.execute(text("CREATE INDEX idx_tasks_created_at ON tasks(created_at DESC)"))
            
            trans.commit()
            print("✅ tasks 表创建成功")
            
        except Exception as e:
            trans.rollback()
            print(f"❌ 迁移失败: {e}")
            raise

if __name__ == "__main__":
    migrate()

