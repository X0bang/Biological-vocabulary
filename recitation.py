def recitation_mode(conn, cursor):
    """
    背诵模式，基于间隔重复（SM2 算法）显示需要复习的单词，并动态调整复习间隔。
    提供两种背诵方式：1. 显示英文并确认是否记住；2. 显示中文并输入英文。
    """
    print("\n=== 背诵模式（基于间隔重复） ===")
    print("请选择背诵方式：")
    print("1. 显示英文，确认是否记住")
    print("2. 显示中文，输入英文单词")
    choice = input("请输入选项 (1 或 2): ")
    
    # 查询所有单词，检查需要复习的单词（状态为“需复习”）
    cursor.execute("SELECT * FROM words WHERE status = '需复习'")
    all_words = cursor.fetchall()
    
    if not all_words:
        print("没有需要复习的单词！")
        return
    
    # 过滤需要复习的单词（这里简化处理，假设每次背诵从头开始，未来可基于累计计数或时间）
    words_to_review = all_words  # 暂不实现复杂的“间隔已到”逻辑，实际应用中可进一步筛选
    print(f"共有 {len(words_to_review)} 个单词需要复习。")
    
    for word_data in words_to_review:
        # 获取当前单词的间隔、复习次数和易度因子
        interval = word_data[6] if word_data[6] is not None else 0  # 字段索引需根据数据库调整
        repetitions = word_data[7] if word_data[7] is not None else 0
        easiness_factor = word_data[8] if word_data[8] is not None else 2.5
        
        if choice == '1':
            # 方式1：显示英文，确认是否记住
            print(f"\n单词: {word_data[1]}")
            input("按回车查看详细信息...")
            print(f"翻译: {word_data[2]}")
            print(f"音标: {word_data[3]}")
            print(f"例句: {word_data[4]}")
            
            # 询问用户是否记住，获取评分（简化版：y=4 表示记住，n=2 表示忘记）
            status = input("是否记住了？(y/n): ").lower()
            if status == 'y':
                quality = 4  # 表示记住
                print(f"单词 '{word_data[1]}' 已标记为 '已掌握'。")
            else:
                quality = 2  # 表示忘记
                print(f"单词 '{word_data[1]}' 仍标记为 '需复习'。")
        
        elif choice == '2':
            # 方式2：显示中文，要求输入英文
            print(f"\n中文翻译: {word_data[2]}")
            user_input = input("请输入英文单词 (输入 'q' 退出): ")
            
            if user_input.lower() == 'q':
                print("退出背诵模式。")
                break
                
            if user_input.lower() == word_data[1].lower():  # 不区分大小写比较
                quality = 4  # 表示记住
                print("正确！")
                print(f"单词: {word_data[1]}")
                print(f"音标: {word_data[3]}")
                print(f"例句: {word_data[4]}")
                print(f"单词 '{word_data[1]}' 已标记为 '已掌握'。")
            else:
                quality = 2  # 表示忘记
                print(f"错误！正确答案是: {word_data[1]}")
                print(f"音标: {word_data[3]}")
                print(f"例句: {word_data[4]}")
                print(f"单词 '{word_data[1]}' 仍标记为 '需复习'。")
        else:
            print("无效选项，返回默认方式（显示英文）。")
            choice = '1'
            continue
            
        # 根据 SM2 算法更新间隔、复习次数和易度因子
        if quality >= 3:  # 记住（答对）
            if repetitions == 0:
                interval = 1  # 第一次复习后间隔为1
            elif repetitions == 1:
                interval = 6  # 第二次复习后间隔为6
            else:
                interval = int(interval * easiness_factor)  # 后续间隔按易度因子增长
            repetitions += 1
            # 更新状态为“已掌握”（可选，也可以保持“需复习”直到达到一定复习次数）
            new_status = '已掌握' if repetitions >= 3 else '需复习'
        else:  # 忘记（答错）
            repetitions = 0  # 重置复习次数
            interval = 1  # 重置间隔为1
            new_status = '需复习'
        
        # 更新易度因子（答对增加，答错减少）
        easiness_factor = max(1.3, min(2.5, easiness_factor + 0.1 * (quality - 3)))
        
        # 更新数据库中的单词信息
        cursor.execute("""
            UPDATE words 
            SET status = ?, interval = ?, repetitions = ?, easiness_factor = ?
            WHERE word = ?
        """, (new_status, interval, repetitions, easiness_factor, word_data[1]))
        conn.commit()
        
        print(f"更新: 间隔={interval}, 复习次数={repetitions}, 易度因子={easiness_factor:.2f}")

    print("本次背诵结束！")
