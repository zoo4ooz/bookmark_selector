from flask import Flask, render_template, request
from bs4 import BeautifulSoup
import json
import os
from dotenv import load_dotenv
import requests

load_dotenv()

app = Flask(__name__)

NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

def parse_bookmarks(file_data):
    soup = BeautifulSoup(file_data, "html.parser")
    return [{"title": tag.string, "url": tag["href"]} for tag in soup.find_all("a")]

def send_to_notion(bookmarks):
    url = "https://api.notion.com/v1/pages"
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }

    for bm in bookmarks:
        data = {
            "parent": { "database_id": NOTION_DATABASE_ID },
            "properties": {
                "Title": {
                    "title": [{
                        "text": { "content": bm["title"] }
                    }]
                },
                "URL": {
                    "url": bm["url"]
                },
                "Read Status": {
                    "select": { "name": "Unread" }
                }
            }
        }
        response = requests.post(url, headers=headers, json=data)
        if not response.ok:
            print(f"❌ Error sending: {bm['title']}, status: {response.status_code}, message: {response.text}")

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

        # ✅ ここで送信ボタンが押されていればNotionに送信
        if "send_to_notion" in request.form:
            send_to_notion(selected_links)

        return render_template(
            "index.html",
            bookmarks=bookmarks,
            selected_urls=selected,
            selected_links=selected_links
        )

    return render_template("index.html", bookmarks=[], selected_urls=[], selected_links=[])

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)