from database import init_database, close_database
from word_manager import query_word, view_words, mark_word_status, batch_add_words
from recitation import recitation_mode
from file_reader import read_txt_files, detect_txt_files
from dotenv import load_dotenv

# 加载 .env 文件中的环境变量
load_dotenv()

def main():
    """
    主程序入口，初始化数据库并提供交互式菜单。
    """
    try:
        conn, cursor = init_database()
    except RuntimeError as e:
        print(f"无法启动程序: {e}")
        return
    
    # 启动时检测并读取 .txt 文件
    read_txt_files(conn, cursor)
    
    while True:
        print("\n=== 单词记忆系统 ===")
        print("1. 查询单词")
        print("2. 背诵模式")
        print("3. 查看单词列表")
        print("4. 标记单词状态")
        print("5. 检测单词本文件 (.txt)")
        print("6. 批量输入单词")
        print("7. 退出")
        choice = input("请选择功能 (1-7): ")
        
        if choice == "1":
            word = input("请输入要查询的单词: ").strip()
            if word:
                query_word(word, conn, cursor)
        elif choice == "2":
            recitation_mode(conn, cursor)
        elif choice == "3":
            view_words(cursor)
        elif choice == "4":
            mark_word_status(conn, cursor)
        elif choice == "5":
            detect_txt_files()
        elif choice == "6":
            batch_add_words(conn, cursor)
        elif choice == "7":
            print("感谢使用，再见！")
            close_database(conn)
            break
        else:
            print("无效选择，请重新输入！")

if __name__ == "__main__":
    main()
