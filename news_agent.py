import os
import time
import requests
import httpx
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI

# 2025.12.08

# 1. 初始化设置
load_dotenv()
api_key = os.getenv("DEEPSEEK_API_KEY")
pushplus_token = os.getenv("PUSHPLUS_TOKEN")

REQUEST_TIMEOUT = 10
JINA_TIMEOUT = 20
PUSHPLUS_TIMEOUT = 15

# --- 网络配置 ---
http_client = httpx.Client(trust_env=False)
client = None

if api_key:
    client = OpenAI(
        api_key=api_key,
        base_url="https://api.deepseek.com",
        http_client=http_client
    )

NO_PROXY = {
    "http": None,
    "https": None,
}
# ----------------

def get_top_n_stories(n=5):
    """获取 Hacker News 排行榜前 N 名的文章"""
    print(f"[系统] 正在查询 HN 排行榜前 {n} 名...")
    try:
        top_ids = requests.get("https://hacker-news.firebaseio.com/v0/topstories.json", proxies=NO_PROXY, timeout=REQUEST_TIMEOUT).json()
        
        stories = []
        for sid in top_ids[:n]:
            item = requests.get(f"https://hacker-news.firebaseio.com/v0/item/{sid}.json", proxies=NO_PROXY, timeout=REQUEST_TIMEOUT).json()
            if 'url' in item:
                stories.append({
                    'title': item.get('title'),
                    'url': item.get('url'),
                    'score': item.get('score', 0)
                })
            else:
                print(f"[跳过] 无链接文章: {item.get('title')}")
        
        return stories
    except Exception as e:
        print(f"[错误] 获取列表失败: {e}")
        return []

def fetch_content_with_jina(url):
    """利用 Jina Reader 抓取内容"""
    if not url: return ""
    print(f"[阅读] 正在抓取: {url} ...")
    jina_url = f"https://r.jina.ai/{url}"
    try:
        response = requests.get(jina_url, proxies=NO_PROXY, timeout=JINA_TIMEOUT)
        return response.text
    except Exception as e:
        print(f"   -> 读取失败: {e}")
        return ""

def summarize_article(title, content):
    """单篇文章总结"""
    if not client:
        return "未配置 DEEPSEEK_API_KEY，无法生成 AI 总结，请直接阅读原文。"

    print(f"[思考] 正在总结: {title} ...")
    
    prompt = f"""
    请为 Hacker News 的热门文章撰写微型简报。
    标题: {title}
    内容: {content[:6000]} 
    
    请输出 Markdown 格式，包含：
    1. **一句话核心**：它是什么？
    2. **关键点**：3个以内的技术要点或观点。
    (保持简洁，不要废话，不要使用任何表情符号)
    """

    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            stream=False
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"总结失败: {e}"

def send_wechat_digest(content_list):
    """汇总推送所有日报到微信"""
    if not pushplus_token:
        print("[警告] 未配置 PUSHPLUS_TOKEN，跳过推送。")
        return

    print("[推送] 正在生成日报并推送...")
    
    # 标题：12月08日 Hacker News 日报
    today_str = datetime.now().strftime("%m月%d日")
    final_title = f"{today_str} Hacker News 日报"
    
    # 正文头部：去掉表情
    final_body = f"# Hacker News 精选 (Top {len(content_list)})\n---\n"
    
    for idx, item in enumerate(content_list, 1):
        final_body += f"## {idx}. {item['title']}\n"
        # 链接去掉 🔗
        final_body += f"[原文链接]({item['url']})\n\n"
        final_body += f"{item['summary']}\n"
        final_body += "---\n\n" 

    url = "http://www.pushplus.plus/send"
    data = {
        "token": pushplus_token,
        "title": final_title,
        "content": final_body,
        "template": "markdown"
    }
    
    try:
        resp = requests.post(url, json=data, proxies=NO_PROXY, timeout=PUSHPLUS_TIMEOUT)
        result = resp.json()
        if result.get("code") == 200:
            print(f"[成功] [{final_title}] 推送完成！")
        else:
            print(f"[失败] 推送被拒绝: {result}")
    except Exception as e:
        print(f"[错误] 推送网络错误: {e}")

# --- 主程序 ---
if __name__ == "__main__":
    print("[系统] Agent 开始工作...")

    if not api_key:
        print("[警告] 未配置 DEEPSEEK_API_KEY，将跳过 AI 总结。")
    
    # 获取前 5 篇
    stories = get_top_n_stories(n=5)
    
    digest_data = []
    
    for story in stories:
        content = fetch_content_with_jina(story['url'])
        
        if len(content) < 100:
            summary = "无法抓取正文，请直接点击链接查看。"
        else:
            summary = summarize_article(story['title'], content)
            
        digest_data.append({
            'title': story['title'],
            'url': story['url'],
            'summary': summary
        })
        
        time.sleep(1)

    if digest_data:
        send_wechat_digest(digest_data)
    else:
        print("[系统] 今天没有抓取到有效新闻。")
