#!/usr/bin/env python3
"""创建初始用户脚本（简化版，直接使用 bcrypt）"""
import sys
import time
import uuid
import bcrypt
from sqlalchemy.orm import Session
from database import SessionLocal
from models import User

def create_user(username: str, password: str, email: str = None):
    """创建用户"""
    if email is None:
        email = f"{username}@example.com"
    
    # 创建数据库会话
    db = SessionLocal()
    
    try:
        # 检查用户是否已存在
        existing_user = db.query(User).filter(
            (User.username == username) | (User.email == email.lower())
        ).first()
        
        if existing_user:
            print(f"❌ 用户 '{username}' 或邮箱 '{email}' 已存在")
            return False
        
        # 使用 bcrypt 加密密码
        password_bytes = password.encode('utf-8')
        password_hash = bcrypt.hashpw(password_bytes, bcrypt.gensalt()).decode('utf-8')
        
        # 创建新用户
        user_id = str(uuid.uuid4())
        now = int(time.time() * 1000)
        
        user = User(
            id=user_id,
            username=username,
            email=email.lower(),
            password_hash=password_hash,
            created_at=now,
            last_login_at=None
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        print(f"✅ 用户创建成功！")
        print(f"   用户名: {user.username}")
        print(f"   邮箱: {user.email}")
        print(f"   用户ID: {user.id}")
        print(f"   创建时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(user.created_at / 1000))}")
        
        return True
        
    except Exception as e:
        db.rollback()
        print(f"❌ 创建用户失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("用法: python create_user_simple.py <用户名> <密码> [邮箱]")
        print("示例: python create_user_simple.py lanf Gauss_234 lanf@example.com")
        sys.exit(1)
    
    username = sys.argv[1]
    password = sys.argv[2]
    email = sys.argv[3] if len(sys.argv) > 3 else None
    
    print(f"正在创建用户: {username}")
    success = create_user(username, password, email)
    sys.exit(0 if success else 1)


