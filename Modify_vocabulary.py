import sqlite3
from tkinter import messagebox

def modify_word_info(conn, cursor, word_id, new_translation=None, new_example=None):
    """
    修改数据库中指定单词的翻译或例句。
    参数:
        conn: SQLite 数据库连接
        cursor: SQLite 数据库游标
        word_id: 单词的 ID
        new_translation: 新翻译（可选）
        new_example: 新例句（可选）
    返回:
        bool: 修改是否成功
    """
    try:
        # 检查单词 ID 是否存在
        cursor.execute("SELECT word, translation, example FROM words WHERE id = ?", (word_id,))
        word_data = cursor.fetchone()
        if not word_data:
            print(f"ID {word_id} 对应的单词不存在！")
            return False

        word, current_translation, current_example = word_data
        # 使用新值或保留原值
        translation = new_translation.strip() if new_translation else current_translation
        example = new_example.strip() if new_example else current_example

        # 如果没有任何修改，直接返回
        if translation == current_translation and example == current_example:
            print(f"单词 '{word}' 未作任何修改。")
            return False

        # 更新数据库
        cursor.execute("""
            UPDATE words 
            SET translation = ?, example = ?
            WHERE id = ?
        """, (translation, example, word_id))
        conn.commit()

        print(f"单词 '{word}' 已更新：")
        if new_translation:
            print(f"翻译: {current_translation} -> {translation}")
        if new_example:
            print(f"例句: {current_example} -> {example}")
        return True

    except sqlite3.Error as e:
        print(f"数据库错误: {e}")
        return False
    except Exception as e:
        print(f"修改单词信息时出错: {e}")
        return False