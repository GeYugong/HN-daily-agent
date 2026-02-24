"""
配置模块
负责环境变量加载和网络配置初始化
"""
import os
from typing import Dict, Optional
from dotenv import load_dotenv

# 模块导入时自动加载环境变量
load_dotenv()

# 禁用代理的常量配置
_NO_PROXY: Dict[str, Optional[str]] = {"http": None, "https": None}

DEFAULT_TOP_COUNT = 5

DEFAULT_SUMMARY_PROMPT_TEMPLATE = """
请为 Hacker News 的热门文章撰写微型简报。
标题: {title}
内容: {content}

请输出 Markdown 格式，包含：
1. **一句话核心**：它是什么？
2. **关键点**：3个以内的技术要点或观点。
(保持简洁，不要废话，不要使用任何表情符号)
""".strip()


def get_deepseek_key() -> str:
    """获取 DeepSeek API Key"""
    key = os.getenv("DEEPSEEK_API_KEY")
    if not key:
        raise ValueError("环境变量 DEEPSEEK_API_KEY 未设置")
    return key


def get_pushplus_token() -> str:
    """获取 PushPlus Token"""
    token = os.getenv("PUSHPLUS_TOKEN")
    if not token:
        raise ValueError("环境变量 PUSHPLUS_TOKEN 未设置")
    return token


def get_no_proxy() -> Dict[str, Optional[str]]:
    """获取 NO_PROXY 配置字典，用于禁用代理"""
    return _NO_PROXY


def _get_positive_int_env(var_name: str, default: int) -> int:
    """读取正整数环境变量，非法值时回退默认值"""
    raw_value = os.getenv(var_name)
    if raw_value is None or not raw_value.strip():
        return default

    try:
        parsed = int(raw_value)
        if parsed <= 0:
            raise ValueError
        return parsed
    except ValueError:
        print(f"[配置警告] {var_name}={raw_value!r} 非法，已回退默认值 {default}")
        return default


def get_hn_top_count() -> int:
    """获取 HN 抓取数量"""
    return _get_positive_int_env("HN_TOP_COUNT", DEFAULT_TOP_COUNT)


def get_github_top_count() -> int:
    """获取 GitHub Trending 抓取数量"""
    return _get_positive_int_env("GITHUB_TOP_COUNT", DEFAULT_TOP_COUNT)


def get_summary_prompt_template() -> str:
    """获取摘要提示词模板"""
    prompt = os.getenv("SUMMARY_PROMPT_TEMPLATE")
    if prompt and prompt.strip():
        return prompt.strip()
    return DEFAULT_SUMMARY_PROMPT_TEMPLATE
