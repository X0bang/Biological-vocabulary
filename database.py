import sqlite3
import os
from dotenv import load_dotenv

# 加载 .env 文件中的环境变量
load_dotenv()

def init_database():
    """
    初始化数据库，创建 words 表（如果不存在），并确保表结构正确。
    返回数据库连接和游标对象。
    """
    db_path = os.getenv("DB_PATH", "word_database.db")
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查当前表结构
        cursor.execute("PRAGMA table_info(words)")
        columns = [col[1] for col in cursor.fetchall()]
        
        # 如果存在 next_review_date 列，迁移到新表
        if 'next_review_date' in columns:
            cursor.execute('''
                CREATE TABLE words_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    word TEXT UNIQUE NOT NULL,
                    translation TEXT,
                    phonetic TEXT,
                    example TEXT,
                    status TEXT DEFAULT '未学习',
                    interval INTEGER DEFAULT 0,
                    repetitions INTEGER DEFAULT 0,
                    easiness_factor REAL DEFAULT 2.5
                )
            ''')
            cursor.execute('''
                INSERT INTO words_new (id, word, translation, phonetic, example, status, interval, repetitions, easiness_factor)
                SELECT id, word, translation, phonetic, example, status, interval, repetitions, easiness_factor FROM words
            ''')
            cursor.execute("DROP TABLE words")
            cursor.execute("ALTER TABLE words_new RENAME TO words")
            print("已移除 next_review_date 列并迁移数据")
        
        # 创建 words 表（如果不存在）
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS words (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                word TEXT UNIQUE NOT NULL,
                translation TEXT,
                phonetic TEXT,
                example TEXT,
                status TEXT DEFAULT '未学习',
                interval INTEGER DEFAULT 0,
                repetitions INTEGER DEFAULT 0,
                easiness_factor REAL DEFAULT 2.5
            )
        ''')

        # 更新旧数据状态
        cursor.execute("UPDATE words SET status = '未学习' WHERE status IS NULL OR status = '需复习'")
        
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