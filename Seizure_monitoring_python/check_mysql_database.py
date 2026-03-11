
from sqlalchemy import create_engine, inspect, text
from config import DATABASE_URL, SessionLocal
from models import User, Patient, Todo, Notification, EegRecord

def check_mysql_database():
    print("=" * 60)
    print("MySQL数据库检查")
    print("=" * 60)
    
    # 创建数据库引擎
    engine = create_engine(DATABASE_URL)
    
    # 检查数据库是否连接成功
    print("\n1. 数据库连接状态:")
    print("   ✓ 数据库连接成功")
    print(f"   数据库位置: {DATABASE_URL}")
    
    # 检查表是否存在
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print("\n2. 数据库表列表:")
    for table in tables:
        print(f"   ✓ {table}")
    
    # 获取数据库会话
    db = SessionLocal()
    
    try:
        # 检查用户表
        print("\n" + "=" * 60)
        print("3. 用户表 (user) 数据:")
        print("=" * 60)
        users = db.query(User).all()
        if users:
            print(f"   总记录数: {len(users)}")
            print(f"   {'ID':<40} {'用户名':<12} {'密码':<12} {'名称':<12}")
            print("-" * 80)
            for user in users:
                print(f"   {user.id:<40} {user.username:<12} {user.password:<12} {user.name or '-':<12}")
        else:
            print("   ✓ 表为空")
        
        # 检查患者表
        print("\n" + "=" * 60)
        print("4. 患者表 (patient) 数据:")
        print("=" * 60)
        patients = db.query(Patient).all()
        if patients:
            print(f"   总记录数: {len(patients)}")
            print(f"   {'ID':<6} {'姓名':<12} {'年龄':<6} {'性别':<6} {'电话':<15}")
            print("-" * 50)
            for patient in patients:
                print(f"   {patient.id:<6} {patient.name or '-':<12} {patient.age or '-':<6} {patient.male or '-':<6} {patient.phone or '-':<15}")
        else:
            print("   ✓ 表为空")
        
        # 检查表
        print("\n" + "=" * 60)
        print("5. 待办事项表 (todo) 数据:")
        print("=" * 60)
        todos = db.query(Todo).all()
        if todos:
            print(f"   总记录数: {len(todos)}")
            print(f"   {'ID':<6} {'内容':<30} {'状态':<8} {'用户ID':<6}")
            print("-" * 50)
            for todo in todos:
                print(f"   {todo.id:<6} {todo.content[:25] or '-':<30} {str(todo.completed or '-'):<8} {str(todo.userId or '-'):<6}")
        else:
            print("   ✓ 表为空")
        
        # 检查通知表
        print("\n" + "=" * 60)
        print("6. 通知表 (notification) 数据:")
        print("=" * 60)
        notifications = db.query(Notification).all()
        if notifications:
            print(f"   总记录数: {len(notifications)}")
            print(f"   {'ID':<6} {'标题':<20} {'用户ID':<6}")
            print("-" * 40)
            for notification in notifications:
                print(f"   {notification.id:<6} {notification.title[:15] or '-':<20} {str(notification.userId or '-'):<6}")
        else:
            print("   ✓ 表为空")
        
        # 检查EEG记录表
        print("\n" + "=" * 60)
        print("7. EEG记录表 (eeg_record) 数据:")
        print("=" * 60)
        eeg_records = db.query(EegRecord).all()
        if eeg_records:
            print(f"   总记录数: {len(eeg_records)}")
            print(f"   {'ID':<6} {'患者ID':<8} {'文件名':<20}")
            print("-" * 40)
            for record in eeg_records:
                print(f"   {record.id:<6} {str(record.patientId or '-'):<8} {record.fileName[:15] or '-':<20}")
        else:
            print("   ✓ 表为空")
        
        # 检查表结构
        print("\n" + "=" * 60)
        print("8. 表结构检查:")
        print("=" * 60)
        for table in tables:
            columns = inspector.get_columns(table)
            print(f"\n   {table} 表字段:")
            for col in columns:
                print(f"     - {col['name']} ({col['type']})")
        
        print("\n" + "=" * 60)
        print("检查完成!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ 检查失败: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    check_mysql_database()
