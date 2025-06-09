import os
from word_manager import query_word

def read_txt_files(conn, cursor):
    """
    启动时检测并读取当前目录下的 .txt 文件中的单词，支持重复检查。
    仅处理文件名中包含 'word' 或 'Word' 关键词的文件。
    """
    print("\n=== 检测并读取 .txt 文件中的单词 ===")
    # 过滤文件名中包含 'word' 或 'Word' 的 .txt 文件
    txt_files = [f for f in os.listdir('.') if f.endswith('.txt') and ('word' in f.lower())]
    
    if not txt_files:
        print("当前目录下未找到文件名中包含 'word' 或 'Word' 的 .txt 文件。")
        return
    
    print(f"找到 {len(txt_files)} 个 .txt 文件：{', '.join(txt_files)}")
    total_words = 0
    added_words = 0
    
    for txt_file in txt_files:
        print(f"正在读取文件: {txt_file}")
        try:
            with open(txt_file, 'r', encoding='utf-8') as file:
                words = [line.strip() for line in file if line.strip()]
            print(f"文件 {txt_file} 中读取了 {len(words)} 个单词。")
            total_words += len(words)
            
            for word in words:
                cursor.execute("SELECT word FROM words WHERE word = ?", (word,))
                if cursor.fetchone():
                    print(f"单词 '{word}' 已存在，跳过添加。")
                    continue
                
                word_info = query_word(word, conn, cursor)
                if word_info:
                    print(f"单词 '{word}' 已成功添加到数据库。")
                    added_words += 1
                else:
                    print(f"查询单词 '{word}' 失败，仅保存单词到数据库。")
                    cursor.execute("""
                        INSERT INTO words (word, status) 
                        VALUES (?, '需复习')
                    """, (word,))
                    conn.commit()
                    added_words += 1
        except Exception as e:
            print(f"读取文件 {txt_file} 时出错: {e}")
    
    print(f"读取完成！共读取 {total_words} 个单词，成功添加到数据库 {added_words} 个。")

def detect_txt_files():
    """
    检测当前目录下是否有 .txt 文件，并显示文件列表和单词数量。
    仅显示文件名中包含 'word' 或 'Word' 关键词的文件。
    """
    print("\n=== 检测单词本文件 (.txt) ===")
    # 过滤文件名中包含 'word' 或 'Word' 的 .txt 文件
    txt_files = [f for f in os.listdir('.') if f.endswith('.txt') and ('word' in f.lower())]
    
    if not txt_files:
        print("当前目录下未找到文件名中包含 'word' 或 'Word' 的 .txt 文件。")
        return
    
    print(f"找到 {len(txt_files)} 个 .txt 文件：")
    for idx, txt_file in enumerate(txt_files, 1):
        try:
            with open(txt_file, 'r', encoding='utf-8') as file:
                words = [line.strip() for line in file if line.strip()]
            print(f"{idx}. {txt_file} - 包含 {len(words)} 个单词")
        except Exception as e:
            print(f"{idx}. {txt_file} - 读取错误: {e}")
