
import sqlite3

def check_table_structure():
    conn = sqlite3.connect('medicine.db')
    cursor = conn.cursor()
    
    try:
        print("=" * 60)
        print("数据库表结构检查")
        print("=" * 60)
        
        # 获取所有表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        for table in tables:
            table_name = table[0]
            print(f"\n{table_name} 表结构:")
            print("-" * 60)
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()
            for col in columns:
                print(f"  {col[1]:<20} {col[2]:<15} 主键: {col[5]}")
    
    except Exception as e:
        print(f"错误: {str(e)}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    check_table_structure()
