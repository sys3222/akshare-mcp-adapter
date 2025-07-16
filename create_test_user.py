#!/usr/bin/env python3
"""
创建测试用户脚本
"""

import sys
from sqlalchemy.orm import Session
from core.database import SessionLocal, User, create_db_and_tables
from core.security import get_password_hash

def create_test_user():
    """创建测试用户"""
    # 确保数据库和表存在
    create_db_and_tables()
    
    # 创建数据库会话
    db: Session = SessionLocal()
    
    try:
        # 检查用户是否已存在
        existing_user = db.query(User).filter(User.username == "test").first()
        if existing_user:
            print("✅ 测试用户 'test' 已存在")
            return
        
        # 创建新用户
        hashed_password = get_password_hash("test123")
        new_user = User(
            username="test",
            hashed_password=hashed_password
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        print("✅ 测试用户创建成功!")
        print("   用户名: test")
        print("   密码: test123")
        
    except Exception as e:
        print(f"❌ 创建用户失败: {e}")
        db.rollback()
    finally:
        db.close()

def create_admin_user():
    """创建管理员用户"""
    # 确保数据库和表存在
    create_db_and_tables()
    
    # 创建数据库会话
    db: Session = SessionLocal()
    
    try:
        # 检查用户是否已存在
        existing_user = db.query(User).filter(User.username == "admin").first()
        if existing_user:
            print("✅ 管理员用户 'admin' 已存在")
            return
        
        # 创建新用户
        hashed_password = get_password_hash("admin123")
        new_user = User(
            username="admin",
            hashed_password=hashed_password
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        print("✅ 管理员用户创建成功!")
        print("   用户名: admin")
        print("   密码: admin123")
        
    except Exception as e:
        print(f"❌ 创建管理员用户失败: {e}")
        db.rollback()
    finally:
        db.close()

def list_users():
    """列出所有用户"""
    db: Session = SessionLocal()
    
    try:
        users = db.query(User).all()
        if not users:
            print("📝 数据库中没有用户")
            return
        
        print("📝 数据库中的用户:")
        for user in users:
            print(f"   ID: {user.id}, 用户名: {user.username}")
            
    except Exception as e:
        print(f"❌ 查询用户失败: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    print("🔧 用户管理工具")
    print("=" * 50)
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "test":
            create_test_user()
        elif command == "admin":
            create_admin_user()
        elif command == "list":
            list_users()
        else:
            print("❌ 未知命令")
            print("用法: python create_test_user.py [test|admin|list]")
    else:
        # 默认创建测试用户和管理员用户
        create_test_user()
        create_admin_user()
        list_users()
