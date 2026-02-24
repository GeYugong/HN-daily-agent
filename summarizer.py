"""
总结模块
负责调用 DeepSeek API 生成文章摘要
"""
import httpx
from openai import OpenAI


class Summarizer:
    """文章总结器，使用 DeepSeek API"""

    def __init__(self, api_key, prompt_template):
        """
        初始化总结器

        Args:
            api_key: DeepSeek API Key
            prompt_template: 摘要提示词模板，必须包含 {title} 和 {content} 占位符
        """
        self.api_key = api_key
        self.prompt_template = prompt_template
        self.http_client = httpx.Client(trust_env=False)
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com",
            http_client=self.http_client
        )

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        """关闭 HTTP 客户端，释放资源"""
        if self.http_client:
            self.http_client.close()

    def summarize(self, title, content):
        """
        为单篇文章生成摘要

        Args:
            title: 文章标题
            content: 文章内容

        Returns:
            str: 摘要内容，失败返回错误信息
        """
        print(f"[思考] 正在总结: {title} ...")

        article_content = content[:6000]
        prompt = self.prompt_template.format(title=title, content=article_content)

        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                stream=False
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"总结失败: {e}"
