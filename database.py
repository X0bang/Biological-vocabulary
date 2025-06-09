import sqlite3
import os
from dotenv import load_dotenv

# 加载 .env 文件中的环境变量
load_dotenv()

def init_database():
    """
    初始化数据库，创建 words 表（如果不存在）。
    返回数据库连接和游标对象。
    """
    db_path = os.getenv("DB_PATH", "word_database.db")  # 从环境变量获取数据库路径，默认值作为备用
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS words (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                word TEXT UNIQUE NOT NULL,
                translation TEXT,
                phonetic TEXT,
                example TEXT,
                status TEXT DEFAULT '需复习',
                interval INTEGER DEFAULT 0,
                repetitions INTEGER DEFAULT 0,
                easiness_factor REAL DEFAULT 2.5
          )
        ''')

        conn.commit()
        print(f"数据库初始化成功，路径: {db_path}")
        return conn, cursor
    except Exception as e:
        raise RuntimeError(f"数据库初始化失败: {e}")

def close_database(conn):
    """
    关闭数据库连接。
    """
    conn.close()
