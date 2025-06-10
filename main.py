import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from database import init_database, close_database
from word_manager import query_word, view_words, mark_word_status, batch_add_words, view_mastery_level
from recitation import recitation_mode
from file_reader import read_txt_files, detect_txt_files
from Modify_vocabulary import modify_word_info
from dotenv import load_dotenv

# 加载 .env 文件中的环境变量
load_dotenv()

class WordMemoryApp:
    def __init__(self, root):
        self.root = root
        self.root.title("单词记忆系统")
        self.root.geometry("800x600")

        try:
            self.conn, self.cursor = init_database()
        except RuntimeError as e:
            messagebox.showerror("错误", f"无法启动程序: {e}")
            self.root.quit()
            return

        # 启动时检测并读取 .txt 文件
        read_txt_files(self.conn, self.cursor)

        # 创建主框架
        self.create_main_frame()
        
    def create_main_frame(self):
        # 顶部功能按钮区
        button_frame = ttk.Frame(self.root)
        button_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        buttons = [
            ("查询单词", self.query_word_window),
            ("背诵模式", self.recitation_mode_window),
            ("查看单词列表", self.view_words),
            ("查看掌握程度", self.view_mastery_level),
            ("标记单词状态", self.mark_status_window),
            ("修改单词信息", self.modify_word_window),
            ("检测单词本文件 (.txt)", self.detect_files),
            ("批量输入单词", self.batch_add_window),
            ("退出", self.quit_app)
        ]

        for text, command in buttons:
            btn = ttk.Button(button_frame, text=text, command=command)
            btn.pack(side=tk.LEFT, padx=5)

        # 底部文本显示区
        self.output_text = scrolledtext.ScrolledText(self.root, wrap=tk.WORD, height=30, width=90)
        self.output_text.pack(padx=5, pady=5, fill=tk.BOTH, expand=True)

        # 重定向 print 输出到文本框
        import sys
        sys.stdout = TextRedirector(self.output_text)

    def clear_output(self):
        self.output_text.delete(1.0, tk.END)

    def query_word_window(self):
        self.clear_output()
        # 创建查询单词的子窗口
        query_win = tk.Toplevel(self.root)
        query_win.title("查询单词")
        query_win.geometry("300x150")

        ttk.Label(query_win, text="请输入要查询的单词：").pack(pady=5)
        word_entry = ttk.Entry(query_win, width=30)
        word_entry.pack(pady=5)

        def submit():
            word = word_entry.get().strip()
            if word:
                query_word(word, self.conn, self.cursor)
            else:
                messagebox.showwarning("警告", "请输入单词！")
            query_win.destroy()

        ttk.Button(query_win, text="查询", command=submit).pack(pady=5)

    def recitation_mode_window(self):
        self.clear_output()
        # 弹出选择背诵方式的窗口
        rec_win = tk.Toplevel(self.root)
        rec_win.title("选择背诵方式")
        rec_win.geometry("300x200")

        ttk.Label(rec_win, text="请选择背诵方式：").pack(pady=10)
        mode_var = tk.StringVar(value="1")
        ttk.Radiobutton(rec_win, text="1. 显示英文，确认是否记住", value="1", variable=mode_var).pack(pady=5)
        ttk.Radiobutton(rec_win, text="2. 显示中文，输入英文单词", value="2", variable=mode_var).pack(pady=5)

        def start_recitation():
            choice = mode_var.get()
            rec_win.destroy()
            # 调用背诵模式，需要传递选择和 GUI 上下文
            self.run_recitation(choice)

        ttk.Button(rec_win, text="开始背诵", command=start_recitation).pack(pady=10)

    def run_recitation(self, choice):
        self.clear_output()
        recitation_mode(self.conn, self.cursor, choice=choice, output_text=self.output_text)

    def view_words(self):
        self.clear_output()
        view_words(self.cursor)

    def view_mastery_level(self):
        self.clear_output()
        view_mastery_level(self.cursor, self.output_text)

    def mark_status_window(self):
        self.clear_output()
        # 创建标记状态的子窗口
        mark_win = tk.Toplevel(self.root)
        mark_win.title("标记单词状态")
        mark_win.geometry("300x250")

        ttk.Label(mark_win, text="请输入单词 ID：").pack(pady=5)
        id_entry = ttk.Entry(mark_win, width=10)
        id_entry.pack(pady=5)

        ttk.Label(mark_win, text="选择状态：").pack(pady=5)
        status_var = tk.StringVar(value="1")
        ttk.Radiobutton(mark_win, text="1. 未学习", value="1", variable=status_var).pack(pady=5)
        ttk.Radiobutton(mark_win, text="2. 学习中", value="2", variable=status_var).pack(pady=5)
        ttk.Radiobutton(mark_win, text="3. 待巩固", value="3", variable=status_var).pack(pady=5)
        ttk.Radiobutton(mark_win, text="4. 已掌握", value="4", variable=status_var).pack(pady=5)

        def submit():
            try:
                word_id = int(id_entry.get())
                status = status_var.get()
                self.cursor.execute("SELECT * FROM words WHERE id = ?", (word_id,))
                word = self.cursor.fetchone()
                if not word:
                    messagebox.showerror("错误", "无效的 ID！")
                    return
                status_map = {'1': '未学习', '2': '学习中', '3': '待巩固', '4': '已掌握'}
                new_status = status_map.get(status, '未学习')
                if new_status == '已掌握':
                    self.cursor.execute("UPDATE words SET status = ?, easiness_factor = ? WHERE id = ?", 
                                      (new_status, 2.8, word_id))
                else:
                    self.cursor.execute("UPDATE words SET status = ? WHERE id = ?", (new_status, word_id))
                self.conn.commit()
                messagebox.showinfo("成功", f"单词 '{word[1]}' 已标记为 '{new_status}'。")
                self.clear_output()
                view_words(self.cursor)
            except ValueError:
                messagebox.showerror("错误", "请输入有效的 ID！")
            mark_win.destroy()

        ttk.Button(mark_win, text="确认", command=submit).pack(pady=10)

    def detect_files(self):
        self.clear_output()
        detect_txt_files(self.conn, self.cursor, self.output_text)

    def batch_add_window(self):
        self.clear_output()
        # 创建批量输入单词的子窗口
        batch_win = tk.Toplevel(self.root)
        batch_win.title("批量输入单词")
        batch_win.geometry("400x300")

        ttk.Label(batch_win, text="请输入单词（每行一个）：").pack(pady=5)
        text_input = scrolledtext.ScrolledText(batch_win, wrap=tk.WORD, height=10, width=40)
        text_input.pack(pady=5)

        def submit():
            words = text_input.get(1.0, tk.END).strip().splitlines()
            words = [w.strip() for w in words if w.strip()]
            if not words:
                messagebox.showwarning("警告", "未输入任何单词！")
                return
            for word in words:
                self.cursor.execute("SELECT word FROM words WHERE word = ?", (word,))
                if self.cursor.fetchone():
                    self.output_text.insert(tk.END, f"单词 '{word}' 已存在，跳过添加。\n")
                    continue
                word_info = query_word(word, self.conn, self.cursor)
                if word_info:
                    self.output_text.insert(tk.END, f"单词 '{word}' 已成功添加到数据库。\n")
                else:
                    self.output_text.insert(tk.END, f"查询单词 '{word}' 失败，仅保存单词到数据库。\n")
                    self.cursor.execute("INSERT INTO words (word, status) VALUES (?, '未学习')", (word,))
                    self.conn.commit()
            self.output_text.insert(tk.END, "批量添加完成！\n")
            batch_win.destroy()

        ttk.Button(batch_win, text="提交", command=submit).pack(pady=10)

    def modify_word_window(self):
        self.clear_output()
        # 创建修改单词信息的子窗口
        modify_win = tk.Toplevel(self.root)
        modify_win.title("修改单词信息")
        modify_win.geometry("500x500")
        modify_win.grab_set()

        # 查找方式选择
        ttk.Label(modify_win, text="选择查找方式：").pack(pady=5)
        search_mode = tk.StringVar(value="id")
        ttk.Radiobutton(modify_win, text="按 ID 查找", value="id", variable=search_mode).pack(pady=5)
        ttk.Radiobutton(modify_win, text="按单词查找", value="word", variable=search_mode).pack(pady=5)

        # 输入框
        ttk.Label(modify_win, text="请输入 ID 或单词：").pack(pady=5)
        search_entry = ttk.Entry(modify_win, width=30)
        search_entry.pack(pady=5)

        # 预览结果显示
        preview_frame = ttk.LabelFrame(modify_win, text="预览")
        preview_frame.pack(pady=10, padx=10, fill=tk.X)
        preview_label = ttk.Label(preview_frame, text="请点击预览以显示信息", wraplength=400)
        preview_label.pack(pady=5, padx=5)

        # 新翻译和例句输入
        ttk.Label(modify_win, text="新翻译（留空保留原值）：").pack(pady=5)
        translation_entry = ttk.Entry(modify_win, width=50)
        translation_entry.pack(pady=5)

        ttk.Label(modify_win, text="新例句（留空保留原值）：").pack(pady=5)
        example_entry = ttk.Entry(modify_win, width=50)
        example_entry.pack(pady=5)

        # 存储当前单词 ID（用于提交修改）
        current_word_id = tk.IntVar(value=0)

        def preview():
            search_value = search_entry.get().strip()
            if not search_value:
                messagebox.showwarning("警告", "请输入 ID 或单词！")
                return

            try:
                if search_mode.get() == "id":
                    word_id = int(search_value)
                    self.cursor.execute("SELECT id, word, translation, example FROM words WHERE id = ?", (word_id,))
                else:
                    self.cursor.execute("SELECT id, word, translation, example FROM words WHERE word = ?", (search_value,))
                
                word_data = self.cursor.fetchone()
                if not word_data:
                    messagebox.showerror("错误", f"{'ID' if search_mode.get() == 'id' else '单词'} '{search_value}' 不存在！")
                    preview_label.config(text="未找到记录")
                    return

                word_id, word, translation, example = word_data
                preview_text = f"ID: {word_id}\n单词: {word}\n翻译: {translation}\n例句: {example}"
                preview_label.configure(text=preview_text)
                current_word_id.set(word_id)
                
                # 填充输入框以便于修改
                translation_entry.delete(0, tk.END)
                translation_entry.insert(0, translation or "")
                example_entry.delete(0, tk.END)
                example_entry.insert(0, example or "")

            except ValueError:
                messagebox.showerror("错误", "请输入有效的 ID！")
            except Exception as e:
                messagebox.showerror("错误", f"查询失败: {e}")

        def submit():
            if not current_word_id.get():
                messagebox.showerror("错误", "请先预览以选择有效单词！")
                return

            try:
                word_id = current_word_id.get()
                new_translation = translation_entry.get().strip() or None
                new_example = example_entry.get().strip() or None

                success = modify_word_info(self.conn, self.cursor, word_id, new_translation, new_example)
                
                if success:
                    messagebox.showinfo("成功", "单词信息已更新！")
                    self.clear_output()
                    view_words(self.cursor)
                else:
                    messagebox.showerror("错误", "修改失败，请检查输入！")
                modify_win.destroy()
            except Exception as e:
                messagebox.showerror("错误", f"提交失败: {e}")

        # 按钮区域
        button_frame = ttk.Frame(modify_win)
        button_frame.pack(pady=10)
        ttk.Button(button_frame, text="预览", command=preview).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="提交", command=submit).pack(side=tk.LEFT, padx=5)

    def quit_app(self):
        close_database(self.conn)
        self.root.quit()

# 重定向窗口
class TextRedirector:
    def __init__(self, text_widget):
        self.text_widget = text_widget
        self.max_lines = 1000
    
    def write(self, text):
        self.text_widget.insert(tk.END, text)
        self.text_widget.see(tk.END)
        line_count = int(self.text_widget.index('end-1c').split('.')[0])
        if line_count > self.max_lines:
            self.text_widget.delete(1.0, f"{line_count - self.max_lines}.0")

    def flush(self):
        pass

if __name__ == "__main__":
    root = tk.Tk()
    app = WordMemoryApp(root)
    root.mainloop()