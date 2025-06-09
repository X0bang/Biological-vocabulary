import tkinter as tk
from tkinter import ttk, messagebox

def recitation_mode(conn, cursor, choice="1", output_text=None):
    """
    背诵模式，基于间隔重复（SM2 算法）显示需要复习的单词，并动态调整复习间隔。
    提供两种背诵方式：1. 显示英文并确认是否记住；2. 显示中文并输入英文。
    参数:
        conn: SQLite 数据库连接
        cursor: SQLite 数据库游标
        choice: 背诵模式（"1" 或 "2"）
        output_text: 主窗口的 ScrolledText，用于输出日志
    """
    # 查询需要复习的单词
    cursor.execute("SELECT * FROM words WHERE status = '需复习'")
    words_to_review = cursor.fetchall()
    
    if not words_to_review:
        if output_text:
            output_text.insert(tk.END, "没有需要复习的单词！\n")
        else:
            print("没有需要复习的单词！")
        return
    
    if output_text:
        output_text.insert(tk.END, f"共有 {len(words_to_review)} 个单词需要复习。\n")
    
    # 创建背诵窗口
    recitation_win = tk.Toplevel()
    recitation_win.title("背诵模式")
    recitation_win.geometry("400x400")
    recitation_win.grab_set()

    # 当前单词索引
    current_index = tk.IntVar(value=0)
    total_words = len(words_to_review)

    # 显示进度
    progress_label = ttk.Label(recitation_win, text=f"进度: 1/{total_words}")
    progress_label.pack(pady=5)

    # 显示单词或翻译
    word_label = ttk.Label(recitation_win, text="", wraplength=350, font=("Arial", 12))
    word_label.pack(pady=10)

    # 详细信息显示区域
    info_frame = ttk.LabelFrame(recitation_win, text="单词信息")
    info_frame.pack(pady=10, padx=10, fill=tk.X)
    info_label = ttk.Label(info_frame, text="", wraplength=350)
    info_label.pack(pady=5)

    # 输入框（用于模式 2）
    input_frame = ttk.Frame(recitation_win)
    input_frame.pack(pady=5)
    word_entry = ttk.Entry(input_frame, width=30)
    word_entry.pack(pady=5, side=tk.LEFT)
    word_entry.pack_forget()  # 默认隐藏

    def update_word_display():
        """更新当前单词的显示内容"""
        if current_index.get() >= total_words:
            output_text.insert(tk.END, "本次背诵结束！\n")
            recitation_win.destroy()
            return

        word_data = words_to_review[current_index.get()]
        progress_label.config(text=f"进度: {current_index.get() + 1}/{total_words}")
        
        if choice == "1":
            word_label.config(text=f"单词: {word_data[1]}")
            info_label.config(text="")
            word_entry.pack_forget()
            remembered_button.pack(side=tk.LEFT, padx=5)
            forgotten_button.pack(side=tk.LEFT, padx=5)
            submit_button.pack_forget()
        else:
            word_label.config(text=f"中文翻译: {word_data[2]}")
            info_label.config(text="")
            word_entry.pack(side=tk.LEFT, pady=5)
            remembered_button.pack_forget()
            forgotten_button.pack_forget()
            submit_button.pack(side=tk.LEFT, padx=5)
            word_entry.delete(0, tk.END)
            word_entry.focus()

    def process_response(quality):
        """处理用户响应并更新 SM2 参数"""
        word_data = words_to_review[current_index.get()]
        interval = word_data[6] if word_data[6] is not None else 0
        repetitions = word_data[7] if word_data[7] is not None else 0
        easiness_factor = word_data[8] if word_data[8] is not None else 2.5

        # 显示详细信息
        info_text = f"单词: {word_data[1]}\n翻译: {word_data[2]}\n音标: {word_data[3]}\n例句: {word_data[4]}"
        info_label.config(text=info_text)

        # SM2 算法更新
        if quality >= 3:
            if repetitions == 0:
                interval = 1
            elif repetitions == 1:
                interval = 6
            else:
                interval = int(interval * easiness_factor)
            repetitions += 1
            new_status = '已掌握' if repetitions >= 3 else '需复习'
        else:
            repetitions = 0
            interval = 1
            new_status = '需复习'

        easiness_factor = max(1.3, min(2.5, easiness_factor + 0.1 * (quality - 3)))

        cursor.execute("""
            UPDATE words 
            SET status = ?, interval = ?, repetitions = ?, easiness_factor = ?
            WHERE word = ?
        """, (new_status, interval, repetitions, easiness_factor, word_data[1]))
        conn.commit()

        if output_text:
            output_text.insert(tk.END, f"单词 '{word_data[1]}' 已标记为 {'已掌握' if quality == 4 else '需复习'}。\n")
            output_text.insert(tk.END, f"更新: 间隔={interval}, 复习次数={repetitions}, 易度因子={easiness_factor:.2f}\n")
        
        # 移动到下一个单词
        current_index.set(current_index.get() + 1)
        update_word_display()

    def on_remembered():
        """模式 1: 用户点击‘记住’"""
        process_response(4)

    def on_forgotten():
        """模式 1: 用户点击‘忘记’"""
        process_response(2)

    def on_submit():
        """模式 2: 用户提交输入的单词"""
        word_data = words_to_review[current_index.get()]
        user_input = word_entry.get().strip()
        if user_input.lower() == 'q':
            output_text.insert(tk.END, "退出背诵模式。\n")
            recitation_win.destroy()
            return
        
        quality = 4 if user_input.lower() == word_data[1].lower() else 2
        if output_text:
            output_text.insert(tk.END, "正确！\n" if quality == 4 else f"错误！正确答案是: {word_data[1]}\n")
        process_response(quality)

    # 按钮区域
    button_frame = ttk.Frame(recitation_win)
    button_frame.pack(pady=10)
    remembered_button = ttk.Button(button_frame, text="记住", command=on_remembered)
    forgotten_button = ttk.Button(button_frame, text="忘记", command=on_forgotten)
    submit_button = ttk.Button(button_frame, text="提交", command=on_submit)

    # 初始显示第一个单词
    update_word_display()

    recitation_win.protocol("WM_DELETE_WINDOW", lambda: [output_text.insert(tk.END, "退出背诵模式。\n"), recitation_win.destroy()])