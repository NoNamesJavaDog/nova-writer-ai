"""数据库连接配置"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 延迟导入 config，避免循环依赖
try:
    from .config import DATABASE_URL
except ImportError:
    # 如果作为包导入失败，尝试直接导入
    import os
    from dotenv import load_dotenv
    load_dotenv()
    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:novawrite_db_2024@localhost:5432/novawrite_ai"
    )

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

