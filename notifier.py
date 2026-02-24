"""
推送通知模块
负责通过 PushPlus 发送微信消息
"""
import requests
from requests.exceptions import Timeout, ConnectionError, RequestException
from datetime import datetime
from config import get_no_proxy


class WeChatNotifier:
    """微信推送通知器，使用 PushPlus"""

    def __init__(self, token):
        """
        初始化通知器

        Args:
            token: PushPlus Token
        """
        self.token = token
        self.no_proxy = get_no_proxy()
        self.api_url = "http://www.pushplus.plus/send"

    def send_digest(self, hn_articles=None, gh_repos=None, show_customize_tip=False):
        """
        发送日报摘要到微信

        Args:
            hn_articles: HN 文章列表，每篇包含 title, url, summary
            gh_repos: GitHub Trending 项目列表，每个包含 name, url, description, stars, language
            show_customize_tip: 是否在日报末尾提示用户可自定义设置
        """
        if not self.token:
            print("[警告] 未配置 PUSHPLUS_TOKEN，跳过推送。")
            return

        print("[推送] 正在生成日报并推送...")

        title = self._format_title()
        body = self._format_body(hn_articles, gh_repos, show_customize_tip)

        data = {
            "token": self.token,
            "title": title,
            "content": body,
            "template": "markdown"
        }

        try:
            resp = requests.post(self.api_url, json=data, proxies=self.no_proxy, timeout=15)
            resp.raise_for_status()
            result = resp.json()
            if result.get("code") == 200:
                print(f"[成功] [{title}] 推送完成！")
            else:
                print(f"[失败] 推送被拒绝: {resp.text}")
        except Timeout as e:
            print(f"[错误] 推送请求超时: {e}")
        except ConnectionError as e:
            print(f"[错误] 无法连接到推送服务器: {e}")
        except requests.HTTPError as e:
            print(f"[错误] 推送HTTP错误 {resp.status_code}: {e}")
        except ValueError as e:
            print(f"[错误] 推送服务器返回了无效的JSON: {e}")
        except RequestException as e:
            print(f"[错误] 推送网络错误: {e}")

    def _format_title(self):
        """格式化推送标题"""
        today_str = datetime.now().strftime("%m月%d日")
        return f"{today_str} 技术日报"

    def _format_body(self, hn_articles, gh_repos, show_customize_tip):
        """格式化推送正文"""
        body = ""

        # Hacker News 部分
        if hn_articles:
            body += f"# Hacker News 精选 (Top {len(hn_articles)})\n---\n"
            for idx, item in enumerate(hn_articles, 1):
                body += f"## {idx}. {item['title']}\n"
                body += f"[原文链接]({item['url']})\n\n"
                body += f"{item['summary']}\n"
                body += "---\n\n"

        # GitHub Trending 部分
        if gh_repos:
            body += f"\n# GitHub Trending (Top {len(gh_repos)})\n---\n"
            for idx, repo in enumerate(gh_repos, 1):
                body += f"## {idx}. [{repo['name']}]({repo['url']})\n"
                body += f"- 语言: {repo['language']} | Stars: {repo['stars']:,}\n"
                body += f"- {repo['description'][:100]}\n\n"

        if show_customize_tip:
            body += "\n---\n"
            body += "## ✅ 首次默认配置已完成\n"
            body += "你现在可以**无需改代码**，直接在 GitHub 仓库中自定义日报参数：\n\n"
            body += "- `Settings → Secrets and variables → Actions → Variables`\n"
            body += "- 新建变量 `HN_TOP_COUNT`（例如 `8`）\n"
            body += "- 新建变量 `GITHUB_TOP_COUNT`（例如 `8`）\n"
            body += "- 新建变量 `SUMMARY_PROMPT_TEMPLATE`（需包含 `{title}` 和 `{content}`）\n\n"
            body += "配置后，下一次日报会自动按你的设置生成。\n"

        return body
