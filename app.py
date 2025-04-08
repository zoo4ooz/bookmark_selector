from flask import Flask, render_template, request
from bs4 import BeautifulSoup

app = Flask(__name__)

# HTML文字列からブックマークを抽出
def parse_bookmarks(file_data):
    soup = BeautifulSoup(file_data, "html.parser")
    return [{"title": tag.string, "url": tag["href"]} for tag in soup.find_all("a")]

@app.route("/", methods=["GET", "POST"])
def index():
    bookmarks = []
    selected = []
    selected_links = []

    if request.method == "POST":
        # HTMLファイルをアップロードしてパース
        file = request.files.get("file")
        if file:
            bookmarks = parse_bookmarks(file.read())

        # 選択情報取得
        selected = request.form.getlist("selected")
        selected_links = [bm for bm in bookmarks if bm["url"] in selected]

        return render_template(
            "index.html",
            bookmarks=bookmarks,
            selected_urls=selected,
            selected_links=selected_links
        )

    return render_template("index.html", bookmarks=[], selected_urls=[], selected_links=[])

if __name__ == "__main__":
    # Docker経由でアクセス可能にするため、host="0.0.0.0" に設定
    app.run(host="0.0.0.0", port=5000, debug=True)
