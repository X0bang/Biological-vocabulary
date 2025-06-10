import tkinter as tk

def query_word(word, conn, cursor):
    """
    查询单词，支持从数据库读取或在线查询并保存。
    返回单词信息，或在查询失败时返回 None。
    
    Args:
        word (str): 要查询的单词。
        conn (sqlite3.Connection): 数据库连接对象。
        cursor (sqlite3.Cursor): 数据库游标对象。
    
    Returns:
        dict or None: 包含单词信息的字典（translation, phonetic, example），查询失败返回 None。
    
    Raises:
        sqlite3.Error: 数据库操作失败时抛出。
    """
    cursor.execute("SELECT * FROM words WHERE word = ?", (word,))
    result = cursor.fetchone()
    if result:
        print(f"\n单词: {result[1]}")
        print(f"翻译: {result[2]}")
        print(f"音标: {result[3]}")
        print(f"例句: {result[4]}")
        print(f"状态: {result[5]}")
        return result
    else:
        from api import fetch_word_info
        print(f"单词 '{word}' 未在数据库中找到，正在查询在线信息...")
        word_info = fetch_word_info(word)
        if word_info:
            cursor.execute("""
                INSERT INTO words (word, translation, phonetic, example, status)
                VALUES (?, ?, ?, ?, '未学习')
            """, (word, word_info['translation'], word_info['phonetic'], word_info['example']))
            conn.commit()
            print(f"单词 '{word}' 已成功添加到数据库。")
            print(f"翻译: {word_info['translation']}")
            print(f"音标: {word_info['phonetic']}")
            print(f"例句: {word_info['example']}")
            print("状态: 未学习")
            return word_info
        else:
            return None

def view_words(cursor):
    """
    查看数据库中的所有单词列表。
    
    Args:
        cursor (sqlite3.Cursor): 数据库游标对象。
    """
    print("\n=== 单词列表 ===")
    cursor.execute("SELECT * FROM words")
    words = cursor.fetchall()
    if not words:
        print("数据库中没有单词！")
        return
    for word in words:
        print(f"ID: {word[0]}, 单词: {word[1]}, 翻译: {word[2]}, 状态: {word[5]}")

def view_mastery_level(cursor, output_text=None):
    """
    查看所有单词的掌握程度，包括 ID、单词、翻译、状态、复习次数、易度因子。
    
    Args:
        cursor (sqlite3.Cursor): 数据库游标对象。
        output_text (tk.ScrolledText, optional): 主窗口的 ScrolledText，用于输出日志。
    """
    msg = "\n=== 单词掌握程度 ==="
    if output_text:
        output_text.insert(tk.END, msg + "\n")
    else:
        print(msg)
        
    cursor.execute("SELECT id, word, translation, status, repetitions, easiness_factor FROM words")
    words = cursor.fetchall()
    if not words:
        msg = "数据库中没有单词！"
        if output_text:
            output_text.insert(tk.END, msg + "\n")
        else:
            print(msg)
        return
    
    for word in words:
        msg = (
            f"ID: {word[0]}, 单词: {word[1]}, 翻译: {word[2]}, "
            f"状态: {word[3]}, 复习次数: {word[4]}, 易度因子: {word[5]:.2f}\n"
        )
        if output_text:
            output_text.insert(tk.END, msg)
        else:
            print(msg)

def mark_word_status(conn, cursor):
    """
    标记单词状态（未学习/学习中/待巩固/已掌握）。
    
    Args:
        conn (sqlite3.Connection): 数据库连接对象。
        cursor (sqlite3.Cursor): 数据库游标对象。
    """
    print("\n=== 标记单词状态 ===")
    view_words(cursor)
    word_id = input("请输入要标记的单词 ID (或输入 '取消' 返回): ")
    if word_id.lower() == '取消':
        return
    try:
        word_id = int(word_id)
        cursor.execute("SELECT * FROM words WHERE id = ?", (word_id,))
        word = cursor.fetchone()
        if not word:
            print("无效的 ID！")
            return
        print(f"当前单词: {word[1]}")
        status = input("设置状态为 (1: 未学习, 2: 学习中, 3: 待巩固, 4: 已掌握): ")
        status_map = {'1': '未学习', '2': '学习中', '3': '待巩固', '4': '已掌握'}
        if status in status_map:
            if status == '4':  # 已掌握
                cursor.execute("UPDATE words SET status = ?, easiness_factor = ? WHERE id = ?", 
                              (status_map[status], 2.8, word_id))
            else:
                cursor.execute("UPDATE words SET status = ? WHERE id = ?", (status_map[status], word_id))
            print(f"单词 '{word[1]}' 已标记为 '{status_map[status]}'。")
            conn.commit()
        else:
            print("无效选择！")
    except ValueError:
        print("请输入有效的 ID！")

def batch_add_words(conn, cursor):
    """
    批量手动输入单词，每行一个，支持重复检查。
    
    Args:
        conn (sqlite3.Connection): 数据库连接对象。
        cursor (sqlite3.Cursor): 数据库游标对象。
    """
    print("\n=== 批量输入单词 ===")
    print("请输入单词（每行一个），直接按回车结束输入：")
    words = []
    while True:
        word = input().strip()
        if word == "":
            break
        if word:
            words.append(word)
    
    if not words:
        print("未输入任何单词！")
        return
    
    print(f"输入了 {len(words)} 个单词，正在查询并添加到数据库...")
    for word in words:
        cursor.execute("SELECT word FROM words WHERE word = ?", (word,))
        if cursor.fetchone():
            print(f"单词 '{word}' 已存在，跳过添加。")
            continue
        
        word_info = query_word(word, conn, cursor)
        if word_info:
            print(f"单词 '{word}' 已成功添加到数据库。")
        else:
            print(f"查询单词 '{word}' 失败，仅保存单词到数据库。")
            cursor.execute("INSERT INTO words (word, status) VALUES (?, '未学习')", (word,))
            conn.commit()

    print("批量添加完成！")