import tkinter as tk
from tkinter import ttk, messagebox
import random

def recitation_mode(conn, cursor, choice="1", output_text=None):
    """
    背诵模式，基于间隔重复（SM2 算法）显示需要复习的单词，优先易度因子低的单词。
    提供两种背诵方式：
    1. 显示英文，询问是否认识，显示信息后确认记忆正确性或继续。
    2. 显示中文，输入英文单词。
    
    参数:
        conn: SQLite 数据库连接
        cursor: SQLite 数据库游标
        choice: 背诵模式（"1" 或 "2"）
        output_text: 主窗口的 ScrolledText，用于输出日志
    """
    # 查询需要复习的单词（状态不为“已掌握”）
    cursor.execute("SELECT * FROM words WHERE status != '已掌握' ORDER BY easiness_factor ASC, repetitions ASC")
    words_to_review = cursor.fetchall()
    
    # 如果没有需要复习的单词
    if not words_to_review:
        cursor.execute("SELECT COUNT(*) FROM words")
        total_words = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM words WHERE status = '已掌握'")
        mastered_words = cursor.fetchone()[0]
        if total_words > 0 and total_words == mastered_words:
            msg = "所有单词均已掌握，学习完成！\n"
        else:
            msg = "当前没有需要复习的单词！\n"
        if output_text:
            output_text.insert(tk.END, msg)
        else:
            print(msg)
        return
    
    # 随机打乱单词列表（保留排序优先级）
    words_to_review = list(words_to_review)
    random.shuffle(words_to_review)
    
    if output_text:
        output_text.insert(tk.END, f"共有 {len(words_to_review)} 个单词需要复习。\n")
    
    # 创建背诵窗口
    recitation_win = tk.Toplevel()
    recitation_win.title("背诵模式")
    recitation_win.geometry("400x500")
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

    # 按钮框架
    button_frame = ttk.Frame(recitation_win)
    button_frame.pack(pady=10)

    def update_word_display():
        """更新当前单词的显示内容"""
        if current_index.get() >= total_words:
            cursor.execute("SELECT * FROM words WHERE status != '已掌握'")
            if not cursor.fetchall():
                output_text.insert(tk.END, "所有单词均已掌握，学习完成！\n")
            else:
                output_text.insert(tk.END, "本次背诵结束！\n")
            recitation_win.destroy()
            return

        word_data = words_to_review[current_index.get()]
        progress_label.config(text=f"进度: {current_index.get() + 1}/{total_words}")
        
        # 清空按钮
        for widget in button_frame.winfo_children():
            widget.destroy()

        if choice == "1":
            word_label.config(text=f"单词: {word_data[1]}")
            info_label.config(text="你认识这个单词吗？")
            word_entry.pack_forget()
            ttk.Button(button_frame, text="认识", command=lambda: on_known(word_data)).pack(side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text="不认识", command=lambda: on_unknown(word_data)).pack(side=tk.LEFT, padx=5)
        else:
            word_label.config(text=f"中文翻译: {word_data[2]}")
            info_label.config(text="")
            word_entry.pack(side=tk.LEFT, pady=5)
            ttk.Button(button_frame, text="提交", command=on_submit).pack(side=tk.LEFT, padx=5)
            word_entry.delete(0, tk.END)
            word_entry.focus()

    def show_word_info(word_data):
        """显示单词的详细信息"""
        info_text = f"单词: {word_data[1]}\n翻译: {word_data[2]}\n音标: {word_data[3]}\n例句: {word_data[4]}"
        info_label.config(text=info_text)

    def on_known(word_data):
        """模式 1: 用户选择‘认识’"""
        show_word_info(word_data)
        # 清空按钮并显示新按钮
        for widget in button_frame.winfo_children():
            widget.destroy()
        word_label.config(text=f"单词: {word_data[1]}")
        info_label.config(text=info_label.cget("text") + "\n\n你的记忆正确吗？")
        ttk.Button(button_frame, text="正确", command=lambda: process_response(4), style="Green.TButton").pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="不正确", command=lambda: process_response(2), style="Red.TButton").pack(side=tk.LEFT, padx=5)

    def on_unknown(word_data):
        """模式 1: 用户选择‘不认识’"""
        show_word_info(word_data)
        # 清空按钮并显示继续按钮
        for widget in button_frame.winfo_children():
            widget.destroy()
        ttk.Button(button_frame, text="继续", command=lambda: process_response(2), style="Blue.TButton").pack(side=tk.LEFT, padx=5)

    def process_response(quality):
        """处理用户响应并更新 SM2 参数"""
        word_data = words_to_review[current_index.get()]
        interval = word_data[6] if word_data[6] is not None else 0
        repetitions = word_data[7] if word_data[7] is not None else 0
        easiness_factor = word_data[8] if word_data[8] is not None else 2.5

        # SM2 算法更新
        if quality >= 3:
            if repetitions == 0:
                interval = 1
            elif repetitions == 1:
                interval = 6
            else:
                interval = int(interval * easiness_factor)
            repetitions += 1
        else:
            repetitions = 0
            interval = 1

        easiness_factor = max(1.3, min(2.8, easiness_factor + 0.1 * (quality - 3)))

        # 确定状态
        if easiness_factor >= 2.8:
            new_status = '已掌握'
        elif repetitions >= 3 and easiness_factor >= 2.0:
            new_status = '待巩固'
        elif repetitions > 0:
            new_status = '学习中'
        else:
            new_status = '未学习'

        cursor.execute("""
            UPDATE words 
            SET status = ?, interval = ?, repetitions = ?, easiness_factor = ?
            WHERE word = ?
        """, (new_status, interval, repetitions, easiness_factor, word_data[1]))
        conn.commit()

        if output_text:
            output_text.insert(tk.END, f"单词 '{word_data[1]}' 已标记为 {new_status}。\n")
            output_text.insert(tk.END, f"更新: 间隔={interval}, 复习次数={repetitions}, 易度因子={easiness_factor:.2f}\n")
        
        # 移动到下一个单词
        current_index.set(current_index.get() + 1)
        update_word_display()

    def on_submit():
        """模式 2: 用户提交输入的单词"""
        word_data = words_to_review[current_index.get()]
        user_input = word_entry.get().strip()
        if not user_input:
            messagebox.showwarning("警告", "请输入单词！")
            word_entry.focus()
            return
        if user_input.lower() == 'q':
            output_text.insert(tk.END, "退出背诵模式。\n")
            recitation_win.destroy()
            return
        
        quality = 4 if user_input.lower() == word_data[1].lower() else 2
        if output_text:
            output_text.insert(tk.END, "正确！\n" if quality == 4 else f"错误！正确答案是: {word_data[1]}\n")
        show_word_info(word_data)
        # 添加继续按钮
        for widget in button_frame.winfo_children():
            widget.destroy()
        ttk.Button(button_frame, text="继续", command=lambda: process_response(quality), style="Blue.TButton").pack(side=tk.LEFT, padx=5)
        word_entry.configure(state='disabled')  # 禁用输入框

    # 配置按钮样式
    style = ttk.Style()
    style.configure("Green.TButton", background="green", foreground="white")
    style.configure("Red.TButton", background="red", foreground="white")
    style.configure("Blue.TButton", background="blue", foreground="white")

    # 绑定 Enter 键到“继续”按钮
    def on_return(event):
        if button_frame.winfo_children() and button_frame.winfo_children()[0].cget("text") == "继续":
            process_response(2)
    
    recitation_win.bind('<Return>', on_return)

    # 初始显示第一个单词
    update_word_display()

    recitation_win.protocol("WM_DELETE_WINDOW", lambda: [output_text.insert(tk.END, "退出背诵模式。\n"), recitation_win.destroy()])