"""测试数据库连接和表结构"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal, engine
from models import Base, Novel, User
from sqlalchemy import inspect

print("=" * 60)
print("测试数据库连接")
print("=" * 60)

try:
    # 测试连接
    db = SessionLocal()
    print("✅ 数据库连接成功")
    
    # 检查表是否存在
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print(f"\n数据库中的表: {tables}")
    
    if 'novels' in tables:
        print("✅ novels 表存在")
        # 检查表结构
        columns = inspector.get_columns('novels')
        print("\nnovels 表结构:")
        for col in columns:
            print(f"  - {col['name']}: {col['type']} (nullable={col['nullable']})")
    else:
        print("❌ novels 表不存在")
    
    if 'users' in tables:
        print("\n✅ users 表存在")
        # 检查用户数量
        user_count = db.query(User).count()
        print(f"用户数量: {user_count}")
    else:
        print("\n❌ users 表不存在")
    
    # 尝试创建一个测试小说（不提交）
    print("\n" + "=" * 60)
    print("测试创建 Novel 对象")
    print("=" * 60)
    
    test_user = db.query(User).first()
    if test_user:
        print(f"找到测试用户: {test_user.username} (ID: {test_user.id})")
        
        # 创建 Novel 对象（不提交）
        test_novel = Novel(
            id="test-id-12345",
            user_id=test_user.id,
            title="测试小说",
            genre="测试",
            synopsis="测试",
            full_outline="",
            created_at=1234567890,
            updated_at=1234567890
        )
        print("✅ Novel 对象创建成功")
        print(f"  ID: {test_novel.id}")
        print(f"  Title: {test_novel.title}")
        print(f"  User ID: {test_novel.user_id}")
        
        # 检查是否有验证错误
        from sqlalchemy.exc import IntegrityError
        try:
            db.add(test_novel)
            db.flush()  # 不提交，只刷新
            print("✅ Novel 对象可以添加到数据库")
            db.rollback()  # 回滚
        except IntegrityError as e:
            print(f"⚠️ 完整性错误（可能是 ID 冲突）: {e}")
            db.rollback()
        except Exception as e:
            print(f"❌ 错误: {type(e).__name__}: {e}")
            db.rollback()
    else:
        print("❌ 没有找到用户")
    
    db.close()
    print("\n✅ 测试完成")
    
except Exception as e:
    print(f"\n❌ 测试失败: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

