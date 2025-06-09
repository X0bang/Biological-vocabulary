from openai import OpenAI
import os
from dotenv import load_dotenv

# 加载 .env 文件中的环境变量
load_dotenv()

# 获取 API 密钥和基础 URL，从环境变量读取
api_key = os.getenv("OPENAI_API_KEY")
base_url = os.getenv("OPENAI_BASE_URL")
model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")  # 默认模型为 gpt-4o-mini

# 检查 API 密钥是否提供
if not api_key:
    raise ValueError("未提供 OpenAI API 密钥。请在 .env 文件中设置 OPENAI_API_KEY。")

# 初始化 OpenAI 客户端，支持自定义 base_url
client = OpenAI(api_key=api_key, base_url=base_url)

def fetch_word_info(word):
    """
    使用 OpenAI API 查询单词信息，包括翻译、音标和例句。
    返回包含翻译、音标和例句的字典，若失败则返回 None。
    """
    try:
        # 构建提示词，请求模型提供单词的详细信息
        prompt = f"""
        我正在创建一个生物单词记忆系统，请提供以下关于生物单词 '{word}' 的信息：
        1. 中文翻译（简洁明了）
        2. 音标（国际音标格式，例如 /ˈɛk.səm.pəl/）
        3. 一个简单的英文例句（包含该单词）及其中文翻译
        用以下格式返回信息，确保内容准确且简洁：
        翻译: [中文翻译]
        音标: [音标]
        例句: [英文例句] | [例句中文翻译]
        如果单词无效或无法查询，请返回 '信息不可用'。
        """

        # 调用 OpenAI API
        response = client.chat.completions.create(
            model=model,  # 从环境变量读取模型名称
            messages=[
                {"role": "system", "content": "你是一个专业的英语助手，擅长提供单词的翻译和语言学习信息。"},
                {"role": "user", "content": prompt}
            ],
            max_tokens=150,
            temperature=0.5
        )

        # 解析 API 响应内容
        content = response.choices[0].message.content.strip()
        if "信息不可用" in content:
            print(f"无法获取单词 '{word}' 的信息。")
            return None

        # 提取翻译、音标和例句
        translation = ""
        phonetic = ""
        example = ""
        for line in content.splitlines():
            line = line.strip()
            if line.startswith("翻译:"):
                translation = line.replace("翻译:", "").strip()
            elif line.startswith("音标:"):
                phonetic = line.replace("音标:", "").strip()
            elif line.startswith("例句:"):
                example = line.replace("例句:", "").strip()

        if translation and phonetic and example:
            return {
                'translation': translation,
                'phonetic': phonetic,
                'example': example
            }
        else:
            print(f"解析单词 '{word}' 的信息时出错，返回内容不完整。")
            return None

    except Exception as e:
        print(f"OpenAI API 查询错误: {e}")
        return None
