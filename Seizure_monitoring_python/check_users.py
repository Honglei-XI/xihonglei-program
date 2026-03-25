import sqlite3

# 连接到SQLite数据库
conn = sqlite3.connect('medicine.db')

# 创建游标对象
cursor = conn.cursor()

# 检查表是否存在
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user';")
table_exists = cursor.fetchone()

if table_exists:
    print("用户表存在")
    # 查询用户表中的数据
    cursor.execute("SELECT id, username, password, name FROM user;")
    users = cursor.fetchall()
    
    if users:
        print("\n用户表中的数据:")
        print("ID\t用户名\t密码\t\t名称")
        print("-" * 50)
        for user in users:
            print(f"{user[0]}\t{user[1]}\t{user[2]}\t\t{user[3]}")
    else:
        print("\n用户表为空，没有预设的用户账户")
else:
    print("用户表不存在")

# 关闭游标和连接
cursor.close()
conn.close()
