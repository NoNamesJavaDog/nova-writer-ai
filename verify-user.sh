#!/bin/bash
# Verify user exists in database

cd /opt/novawrite-ai/backend
source ../venv/bin/activate

python << 'PYTHON_SCRIPT'
from database import SessionLocal
from models import User

db = SessionLocal()
try:
    user = db.query(User).filter(User.username == 'lanf').first()
    if user:
        print(f"✅ 用户验证成功！")
        print(f"   用户名: {user.username}")
        print(f"   邮箱: {user.email}")
        print(f"   用户ID: {user.id}")
        print(f"   创建时间: {user.created_at}")
    else:
        print("❌ 用户不存在")
finally:
    db.close()
PYTHON_SCRIPT


