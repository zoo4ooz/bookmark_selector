from flask import Flask, render_template, request
from bs4 import BeautifulSoup
import json
import os
import requests
from dotenv import load_dotenv
from datetime import datetime

# .envファイルの読み込み
load_dotenv()

# 環境変数取得
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

# 必須な設定がない場合はエラーを出す
if not NOTION_TOKEN or not NOTION_DATABASE_ID:
    raise ValueError("❗環境変数 NOTION_TOKEN または NOTION_DATABASE_ID が未設定です")

# Flask アプリ初期化
app = Flask(__name__)

# Safari ブックマークのHTMLからリンクを抽出
def parse_bookmarks(file_data):
    soup = BeautifulSoup(file_data, "html.parser")
    return [{"title": tag.string, "url": tag["href"]} for tag in soup.find_all("a")]

# Notion APIにブックマークを送信
def send_to_notion(bookmarks):
    url = "https://api.notion.com/v1/pages"
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }

    today_str = datetime.today().strftime("%Y-%m-%d")  # ISO 8601形式に対応した日付文字列

    for bm in bookmarks:
        data = {
            "parent": {"database_id": NOTION_DATABASE_ID},
            "properties": {
                "Title": {
                    "title": [{
                        "text": {"content": bm["title"]}
                    }]
                },
                "URL": {
                    "url": bm["url"]
                },
                "Added Date": {
                    "date": { "start": today_str }  # ← ここで日付を追加！
                }
            }
        }

        try:
            response = requests.post(url, headers=headers, json=data, timeout=10)
            print(f"📤 Sending: {bm['title']}")
            print("Response:", response.status_code, response.text)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"❌ Error sending: {bm['title']} -> {e}")

# メインルート
@app.route("/", methods=["GET", "POST"])
def index():
    bookmarks = []
    selected = []
    selected_links = []

    if request.method == "POST":
        file = request.files.get("file")
        hidden = request.form.get("hidden_bookmarks")

        if file:
            bookmarks = parse_bookmarks(file.read())
        elif hidden:
            bookmarks = json.loads(hidden)

        selected = request.form.getlist("selected")
        selected_links = [bm for bm in bookmarks if bm["url"] in selected]

        # ✅ Notionに送信ボタンが押された場合のみ送信
        if "send_to_notion" in request.form and selected_links:
            send_to_notion(selected_links)

        return render_template(
            "index.html",
            bookmarks=bookmarks,
            selected_urls=selected,
            selected_links=selected_links
        )

    return render_template("index.html", bookmarks=[], selected_urls=[], selected_links=[])

# サーバー起動
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)