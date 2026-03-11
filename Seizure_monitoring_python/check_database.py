
import sqlite3

def check_database():
    print("=" * 60)
    print("数据库检查")
    print("=" * 60)
    
    # 连接到SQLite数据库
    conn = sqlite3.connect('medicine.db')
    cursor = conn.cursor()
    
    try:
        # 获取所有表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print("\n1. 数据库表列表:")
        for table in tables:
            print(f"   ✓ {table[0]}")
        
        # 检查用户表
        print("\n" + "=" * 60)
        print("2. 用户表 (user) 数据:")
        print("=" * 60)
        cursor.execute("SELECT id, username, password, name FROM user;")
        users = cursor.fetchall()
        if users:
            print(f"   总记录数: {len(users)}")
            print(f"   {'ID':<40} {'用户名':<12} {'密码':<12} {'名称':<12}")
            print("-" * 80)
            for user in users:
                print(f"   {user[0]:<40} {user[1]:<12} {user[2]:<12} {user[3] or '-':<12}")
        else:
            print("   ✓ 表为空")
        
        # 检查患者表
        print("\n" + "=" * 60)
        print("3. 患者表 (patient) 数据:")
        print("=" * 60)
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='patient';")
        if cursor.fetchone():
            cursor.execute("SELECT id, name, age, gender, phone FROM patient;")
            patients = cursor.fetchall()
            if patients:
                print(f"   总记录数: {len(patients)}")
                print(f"   {'ID':<40} {'姓名':<12} {'年龄':<6} {'性别':<6} {'电话':<15}")
                print("-" * 80)
                for patient in patients:
                    print(f"   {patient[0]:<40} {patient[1] or '-':<12} {str(patient[2] or '-'):<6} {patient[3] or '-':<6} {patient[4] or '-':<15}")
            else:
                print("   ✓ 表为空")
        else:
            print("   ✗ 表不存在")
        
        # 检查待办事项表
        print("\n" + "=" * 60)
        print("4. 待办事项表 (todo) 数据:")
        print("=" * 60)
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='todo';")
        if cursor.fetchone():
            cursor.execute("SELECT id, title, status, userId FROM todo;")
            todos = cursor.fetchall()
            if todos:
                print(f"   总记录数: {len(todos)}")
                print(f"   {'ID':<40} {'标题':<20} {'状态':<8} {'用户ID':<40}")
                print("-" * 100)
                for todo in todos:
                    print(f"   {todo[0]:<40} {todo[1] or '-':<20} {str(todo[2] or '-'):<8} {todo[3] or '-':<40}")
            else:
                print("   ✓ 表为空")
        else:
            print("   ✗ 表不存在")
        
        # 检查通知表
        print("\n" + "=" * 60)
        print("5. 通知表 (notification) 数据:")
        print("=" * 60)
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='notification';")
        if cursor.fetchone():
            cursor.execute("SELECT id, title, read, userId FROM notification;")
            notifications = cursor.fetchall()
            if notifications:
                print(f"   总记录数: {len(notifications)}")
                print(f"   {'ID':<40} {'标题':<20} {'已读':<6} {'用户ID':<40}")
                print("-" * 100)
                for notification in notifications:
                    print(f"   {notification[0]:<40} {notification[1] or '-':<20} {str(notification[2] or '-'):<6} {notification[3] or '-':<40}")
            else:
                print("   ✓ 表为空")
        else:
            print("   ✗ 表不存在")
        
        # 检查EEG记录表
        print("\n" + "=" * 60)
        print("6. EEG记录表 (eegrecord) 数据:")
        print("=" * 60)
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='eegrecord';")
        if cursor.fetchone():
            cursor.execute("SELECT id, patientId, patientName, riskLevel FROM eegrecord;")
            eeg_records = cursor.fetchall()
            if eeg_records:
                print(f"   总记录数: {len(eeg_records)}")
                print(f"   {'ID':<40} {'患者ID':<40} {'患者姓名':<12} {'风险等级':<8}")
                print("-" * 100)
                for record in eeg_records:
                    print(f"   {record[0]:<40} {record[1] or '-':<40} {record[2] or '-':<12} {str(record[3] or '-'):<8}")
            else:
                print("   ✓ 表为空")
        else:
            print("   ✗ 表不存在")
        
        print("\n" + "=" * 60)
        print("检查完成!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ 检查失败: {str(e)}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    check_database()
