"""
Hacker News 日报 Agent
主入口：协调各模块完成每日新闻抓取、总结和推送
"""
import time
from config import (
    DEFAULT_SUMMARY_PROMPT_TEMPLATE,
    DEFAULT_TOP_COUNT,
    get_deepseek_key,
    get_github_top_count,
    get_hn_top_count,
    get_pushplus_token,
    get_summary_prompt_template,
)
from hn_fetcher import HNFetcher
from github_trending import GitHubTrendingFetcher
from summarizer import Summarizer
from notifier import WeChatNotifier


def main():
    """主流程"""
    print("[系统] Agent 开始工作...")

    try:
        # 1. 初始化配置
        api_key = get_deepseek_key()
        pushplus_token = get_pushplus_token()
        hn_top_count = get_hn_top_count()
        github_top_count = get_github_top_count()
        prompt_template = get_summary_prompt_template()

        if "{title}" not in prompt_template or "{content}" not in prompt_template:
            print("[配置警告] SUMMARY_PROMPT_TEMPLATE 必须包含 {title} 和 {content}，已回退默认提示词。")
            prompt_template = DEFAULT_SUMMARY_PROMPT_TEMPLATE

        should_show_customize_tip = (
            hn_top_count == DEFAULT_TOP_COUNT
            and github_top_count == DEFAULT_TOP_COUNT
            and prompt_template == DEFAULT_SUMMARY_PROMPT_TEMPLATE
        )

        # 2. 创建各模块实例
        hn_fetcher = HNFetcher()
        gh_fetcher = GitHubTrendingFetcher()

        # 使用 context manager 确保 Summarizer 资源正确释放
        with Summarizer(api_key, prompt_template) as summarizer:
            notifier = WeChatNotifier(pushplus_token)

            # 3. 获取 HN 文章列表
            stories = hn_fetcher.get_top_stories(n=hn_top_count)

            # 获取 GitHub Trending 项目
            gh_repos = gh_fetcher.get_trending_repos(n=github_top_count)

            digest_data = []

            # 4. 处理每篇 HN 文章
            for story in stories:
                content = hn_fetcher.fetch_content(story['url'])

                if len(content) < 100:
                    summary = "无法抓取正文，请直接点击链接查看。"
                else:
                    summary = summarizer.summarize(story['title'], content)

                digest_data.append({
                    'title': story['title'],
                    'url': story['url'],
                    'summary': summary
                })

                time.sleep(1)

            # 5. 推送日报（HN 文章 + GitHub Trending）
            if digest_data or gh_repos:
                notifier.send_digest(
                    digest_data,
                    gh_repos,
                    show_customize_tip=should_show_customize_tip,
                )
            else:
                print("[系统] 今天没有抓取到有效新闻。")

    except ValueError as e:
        print(f"[配置错误] {e}")
        print("[提示] 请检查 .env 文件中的环境变量配置")
        return
    except Exception as e:
        print(f"[错误] Agent 运行失败: {e}")
        return


if __name__ == "__main__":
    main()
