def query_word(word, conn, cursor):
    """
    查询单词，支持从数据库读取或在线查询并保存。
    返回单词信息，或在查询失败时返回 None。
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
                VALUES (?, ?, ?, ?, '需复习')
            """, (word, word_info['translation'], word_info['phonetic'], word_info['example']))
            conn.commit()
            print(f"单词 '{word}' 已成功添加到数据库。")
            print(f"翻译: {word_info['translation']}")
            print(f"音标: {word_info['phonetic']}")
            print(f"例句: {word_info['example']}")
            print("状态: 需复习")
            return word_info
        else:
            return None

def view_words(cursor):
    """
    查看数据库中的所有单词列表。
    """
    print("\n=== 单词列表 ===")
    cursor.execute("SELECT * FROM words")
    words = cursor.fetchall()
    if not words:
        print("数据库中没有单词！")
        return
    for word in words:
        print(f"ID: {word[0]}, 单词: {word[1]}, 翻译: {word[2]}, 状态: {word[5]}")

def mark_word_status(conn, cursor):
    """
    标记单词状态（需复习/已掌握）。
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
        status = input(f"设置单词 '{word[1]}' 的状态为 (1: 需复习, 2: 已掌握): ")
        if status == '1':
            cursor.execute("UPDATE words SET status = '需复习' WHERE id = ?", (word_id,))
            print(f"单词 '{word[1]}' 已标记为 '需复习'。")
        elif status == '2':
            cursor.execute("UPDATE words SET status = '已掌握' WHERE id = ?", (word_id,))
            print(f"单词 '{word[1]}' 已标记为 '已掌握'。")
        else:
            print("无效选择！")
        conn.commit()
    except ValueError:
        print("请输入有效的 ID！")

def batch_add_words(conn, cursor):
    """
    批量手动输入单词，每行一个，支持重复检查。
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
            cursor.execute("""
                INSERT INTO words (word, status) 
                VALUES (?, '需复习')
            """, (word,))
            conn.commit()

    print("批量添加完成！")
