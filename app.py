from flask import Flask, request, jsonify, render_template
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote
import os

app = Flask(__name__)

HEADERS = {
    "User-Agent":
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36",
    "Accept-Language": "ja,en;q=0.9",
    "Referer": "https://danryoku.com/"
}

session = requests.Session()
session.headers.update(HEADERS)

# 本地代理（线上不设置环境变量即可）
# 尝试加载代理配置
try:
    from proxy import PROXIES
    if PROXIES:
        session.proxies.update(PROXIES)
        print("✅ 使用本地代理")
except ImportError:
    print("ℹ️ 未检测到代理配置，直连")

TIMEOUT = (10, 60)


def fetch(url):
    try:
        return session.get(url, timeout=TIMEOUT)
    except Exception as e:
        print("fetch error:", url, e)
        return None


# ======================
# 列表解析（标题 + 链接 + 缩略图 + 分页）
# ======================
def parse_list_page(url):
    resp = fetch(url)
    if not resp:
        return [], None, None

    soup = BeautifulSoup(resp.text, "lxml")

    items = []

    # 遍历每个文章块 article
    for article in soup.select("article.dynamic-content-template"):
        # 找标题链接
        a = article.select_one("h2.gb-headline a")
        if not a:
            continue

        # 找缩略图
        img = article.select_one("figure img")

        items.append({
            "title": a.get_text(strip=True),
            "url": a.get("href"),
            "thumb": img.get("src") if img else ""
            # "thumb":  ""
        })

    pagination = {
        "pages": [],
        "current": 1,
        "last": None  # 最后一页页码
    }

    nav = soup.select_one("div.nav-links")
    if nav:
        # 当前页
        current_span = nav.select_one("span.page-numbers.current")
        if current_span:
            try:
                current_text = ''.join(filter(str.isdigit, current_span.get_text()))
                pagination["current"] = int(current_text)
            except:
                pagination["current"] = 1

        # 所有普通页码 a 标签
        page_links = []
        for a in nav.select("a.page-numbers"):
            cls = a.get("class", [])
            if "prev" in cls or "next" in cls:
                continue  # 忽略上一页 / 下一页
            text = ''.join(filter(str.isdigit, a.get_text()))
            if text:
                page_links.append({
                    "num": int(text),
                    "url": a.get("href")
                })

        pagination["pages"] = page_links

        # 最后一页
        if page_links:
            pagination["last"] = page_links[-1]["num"]

    return items, pagination


# ======================
# 详情页解析（只解析图片）
# ======================
# def parse_detail_page(url):
#     resp = fetch(url)
#     if not resp:
#         return []
#
#     soup = BeautifulSoup(resp.text, "lxml")
#     images = []
#
#     for img in soup.select("div.dynamic-entry-content img"):
#         images.append({
#             "title": img.get("title"),
#             "url": img.get("src")
#         })
#
#     return images

def parse_detail_page(url):
    """解析单个详情页，包括分页"""
    images = []
    current_url = url
    retry_count = 0

    while current_url:
        resp = fetch(current_url)
        if not resp:
            retry_count += 1
            if retry_count > 3:
                break
            continue

        soup = BeautifulSoup(resp.text, "lxml")

        # 获取本页图片
        for img in soup.select("div.dynamic-entry-content img"):
            images.append({
                "title": img.get("title") or "",
                "url": img.get("src")
            })

        # 查找下一页链接
        nav_right = soup.select_one("div.nav-right a")
        if nav_right and nav_right.get("href"):
            current_url = nav_right.get("href")
        else:
            break

    return images

# ======================
# Flask 路由
# ======================

@app.route("/")
def index():
    return render_template("index.html")


# 分类（只返回列表）
@app.route("/api/category")
def api_category():
    url = request.args.get("url")
    items,  pagination = parse_list_page(url)
    return jsonify({
        "items": items,
        "pagination": pagination
    })


# 搜索（只返回列表）
@app.route("/api/search")
def api_search():
    q = request.args.get("q", "")
    page = request.args.get("page", "1")
    url = f"https://danryoku.com/page/{page}/?s={quote(q)}"
    items,  pagination = parse_list_page(url)
    return jsonify({
        "items": items,
        "pagination": pagination
    })


# RANDOM（单页面 → 直接当详情）
@app.route("/api/random")
def api_random():
    url = "https://danryoku.com/random-photobook"
    return jsonify(parse_detail_page(url))


# 详情页
@app.route("/api/detail")
def api_detail():
    url = request.args.get("url")
    return jsonify(parse_detail_page(url))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
