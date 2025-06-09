import os
import tkinter as tk
from tkinter import messagebox
from word_manager import query_word

def read_txt_files(conn, cursor, output_text=None):
    """
    检测并读取当前目录下的 .txt 文件中的单词，支持重复检查，查询意思并添加到数据库。
    仅处理文件名中包含 'word' 或 'Word' 关键词的文件。
    参数:
        conn: SQLite 数据库连接
        cursor: SQLite 数据库游标
        output_text: 主窗口的 ScrolledText，用于输出日志（可选）
    """
    msg = "\n=== 检测并读取 .txt 文件中的单词 ===\n"
    if output_text:
        output_text.insert(tk.END, msg)
    else:
        print(msg)
    
    txt_files = [f for f in os.listdir('.') if f.endswith('.txt') and ('word' in f.lower())]
    
    if not txt_files:
        msg = "当前目录下未找到文件名中包含 'word' 或 'Word' 的 .txt 文件。\n"
        if output_text:
            output_text.insert(tk.END, msg)
        else:
            print(msg)
        return
    
    msg = f"找到 {len(txt_files)} 个 .txt 文件：{', '.join(txt_files)}\n"
    if output_text:
        output_text.insert(tk.END, msg)
    else:
        print(msg)
    
    total_words = 0
    added_words = 0
    
    for txt_file in txt_files:
        msg = f"正在读取文件: {txt_file}\n"
        if output_text:
            output_text.insert(tk.END, msg)
        else:
            print(msg)
        
        try:
            with open(txt_file, 'r', encoding='utf-8') as file:
                words = [line.strip() for line in file if line.strip()]
            msg = f"文件 {txt_file} 中读取了 {len(words)} 个单词。\n"
            if output_text:
                output_text.insert(tk.END, msg)
            else:
                print(msg)
            total_words += len(words)
            
            for word in words:
                cursor.execute("SELECT word FROM words WHERE word = ?", (word,))
                if cursor.fetchone():
                    msg = f"单词 '{word}' 已存在，跳过添加。\n"
                    if output_text:
                        output_text.insert(tk.END, msg)
                    else:
                        print(msg)
                    continue
                
                try:
                    word_info = query_word(word, conn, cursor)
                    if word_info:
                        msg = f"单词 '{word}' 已成功添加到数据库。\n"
                        if output_text:
                            output_text.insert(tk.END, msg)
                        else:
                            print(msg)
                        added_words += 1
                    else:
                        msg = f"查询单词 '{word}' 失败，仅保存单词到数据库。\n"
                        if output_text:
                            output_text.insert(tk.END, msg)
                        else:
                            print(msg)
                        cursor.execute("""
                            INSERT INTO words (word, status) 
                            VALUES (?, '需复习')
                        """, (word,))
                        conn.commit()
                        added_words += 1
                except Exception as e:
                    msg = f"处理单词 '{word}' 时出错: {e}\n"
                    if output_text:
                        output_text.insert(tk.END, msg)
                    else:
                        print(msg)
        except Exception as e:
            msg = f"读取文件 {txt_file} 时出错: {e}\n"
            if output_text:
                output_text.insert(tk.END, msg)
            else:
                print(msg)
    
    msg = f"读取完成！共读取 {total_words} 个单词，成功添加到数据库 {added_words} 个。\n"
    if output_text:
        output_text.insert(tk.END, msg)
    else:
        print(msg)

def detect_txt_files(conn, cursor, output_text):
    """
    检测当前目录下的 .txt 文件，显示文件列表和单词数量，并支持导入到数据库。
    仅处理文件名中包含 'word' 或 'Word' 关键词的文件。
    参数:
        conn: SQLite 数据库连接
        cursor: SQLite 数据库游标
        output_text: 主窗口的 ScrolledText，用于输出日志
    """
    output_text.insert(tk.END, "\n=== 检测单词本文件 (.txt) ===\n")
    txt_files = [f for f in os.listdir('.') if f.endswith('.txt') and ('word' in f.lower())]
    
    if not txt_files:
        output_text.insert(tk.END, "当前目录下未找到文件名中包含 'word' 或 'Word' 的 .txt 文件。\n")
        return
    
    output_text.insert(tk.END, f"找到 {len(txt_files)} 个 .txt 文件：\n")
    file_word_counts = []
    
    for idx, txt_file in enumerate(txt_files, 1):
        try:
            with open(txt_file, 'r', encoding='utf-8') as file:
                words = [line.strip() for line in file if line.strip()]
            file_word_counts.append((txt_file, words))
            output_text.insert(tk.END, f"{idx}. {txt_file} - 包含 {len(words)} 个单词\n")
        except Exception as e:
            output_text.insert(tk.END, f"{idx}. {txt_file} - 读取错误: {e}\n")
    
    # 询问用户是否导入
    if file_word_counts:
        total_words = sum(len(words) for _, words in file_word_counts)
        if messagebox.askyesno("导入确认", f"检测到 {len(file_word_counts)} 个文件，共 {total_words} 个单词。\n是否导入到数据库？"):
            read_txt_files(conn, cursor, output_text)
        else:
            output_text.insert(tk.END, "用户取消导入。\n")