
import mysql.connector
from sqlalchemy import create_engine
from config import DATABASE_URL, engine, Base
from models import User, Patient, Todo, Notification, EegRecord
from datetime import datetime

def create_mysql_database():
    """创建MySQL数据库"""
    print("=" * 60)
    print("创建MySQL数据库")
    print("=" * 60)
    
    # 从DATABASE_URL中提取连接信息
    import re
    # 处理空密码的情况
    match = re.match(r"mysql\+pymysql://(\w+):?([^@]*)@(\w+):(\d+)/(\w+)", DATABASE_URL)
    if match:
        user, password, host, port, dbname = match.groups()
        print(f"  连接信息: {user}@{host}:{port}/{dbname}")
        print(f"  密码: {'空' if not password else '******'}")
    else:
        print("  ✗ 数据库URL格式错误")
        return False
    
    # 连接到MySQL服务器
    try:
        # 使用指定的密码
        conn = mysql.connector.connect(
            host=host,
            port=int(port),
            user=user,
            password='12345'
        )
        cursor = conn.cursor()
        
        # 创建数据库
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {dbname} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
        print(f"  ✓ 数据库 {dbname} 创建成功")
        
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"  ✗ 数据库创建失败: {str(e)}")
        return False

def recreate_tables():
    """重新创建表结构"""
    print("\n" + "=" * 60)
    print("重新创建表结构")
    print("=" * 60)
    
    try:
        # 先手动删除所有表，包括那些不在模型定义中的表
        from sqlalchemy import text
        with engine.connect() as conn:
            # 禁用外键约束
            conn.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
            
            # 删除所有可能存在的表
            tables_to_drop = [
                'eeg_analysis_result',
                'eeg_record',
                'notification',
                'todo',
                'patient',
                'user'
            ]
            
            for table in tables_to_drop:
                try:
                    conn.execute(text(f"DROP TABLE IF EXISTS {table}"))
                    print(f"  ✓ 表 {table} 已删除")
                except Exception as e:
                    print(f"  ⚠ 表 {table} 删除失败: {str(e)}")
            
            # 重新启用外键约束
            conn.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
            conn.commit()
        
        # 创建新表
        Base.metadata.create_all(bind=engine)
        print("  ✓ 新表已创建")
        return True
    except Exception as e:
        print(f"  ✗ 表创建失败: {str(e)}")
        return False

def insert_test_data():
    """插入测试数据"""
    print("\n" + "=" * 60)
    print("插入测试数据")
    print("=" * 60)
    
    from config import SessionLocal
    db = SessionLocal()
    
    try:
        # 插入测试用户
        admin_user = User(
            id="cd862cb0-ddac-4922-bcda-d3161449498b",
            username="admin",
            name="管理员",
            password="admin123",
            userStatus=1,
            phone="13800138000",
            email="admin@example.com",
            createTime=datetime.now(),
            updateTime=datetime.now()
        )
        
        test_user = User(
            id="6a4deb88-d43e-4ce1-a030-f4f0a64f35bd",
            username="test",
            name="测试用户",
            password="test123",
            userStatus=1,
            phone="13900139000",
            email="test@example.com",
            createTime=datetime.now(),
            updateTime=datetime.now()
        )
        
        db.add(admin_user)
        db.add(test_user)
        db.commit()
        
        print("  ✓ 测试用户已插入")
        print(f"    管理员: admin / admin123")
        print(f"    测试用户: test / test123")
        
        # 插入测试患者
        test_patient = Patient(
            id=1,
            name="张三",
            age="35",
            male="男",
            phone="13700137000",
            address="北京市海淀区",
            doctorId="1",
            departmentId="1",
            diagnosis="癫痫",
            text="癫痫患者，需要定期检查",
            createTime=datetime.now().date(),
            updateTime=datetime.now().date()
        )
        
        db.add(test_patient)
        db.commit()
        print("  ✓ 测试患者已插入")
        
        return True
    except Exception as e:
        db.rollback()
        print(f"  ✗ 测试数据插入失败: {str(e)}")
        return False
    finally:
        db.close()

def main():
    """主函数"""
    # 创建数据库
    if not create_mysql_database():
        print("\n✗ 数据库创建失败，退出")
        return
    
    # 重新创建表
    if not recreate_tables():
        print("\n✗ 表创建失败，退出")
        return
    
    # 插入测试数据
    if not insert_test_data():
        print("\n✗ 测试数据插入失败，退出")
        return
    
    print("\n" + "=" * 60)
    print("数据库重建完成！")
    print("=" * 60)
    print("\n使用以下信息登录系统：")
    print("  管理员账户: admin / admin123")
    print("  测试账户: test / test123")

if __name__ == "__main__":
    main()
