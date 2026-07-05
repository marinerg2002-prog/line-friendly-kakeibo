"""
褒めてくれるやさしい家計簿 - メインアプリ

Flask で Web サーバーを起動し、LINE の Webhook を受け取ります。
"""

from flask import Flask, abort, request

from config import Config
from line_service import handle_webhook

# Flask アプリを作成
app = Flask(__name__)


@app.route("/", methods=["GET"])
def index():
    """動作確認用のトップページ"""
    return (
        "<h1>褒めてくれるやさしい家計簿</h1>"
        "<p>サーバーは正常に動いています。</p>"
        "<p>LINE Webhook URL: <code>/callback</code></p>"
    )


@app.route("/callback", methods=["POST"])
def callback():
    """
    LINE からの Webhook を受け取るエンドポイント。

    LINE Developers で Webhook URL に
    https://あなたのドメイン/callback
    を設定してください。
    """
    # LINE から送られてくる署名（改ざんチェック用）
    signature = request.headers.get("X-Line-Signature", "")

    # リクエストの本文
    body = request.get_data(as_text=True)

    if not signature:
        abort(400, "Missing signature")

    message, status_code = handle_webhook(body, signature)
    return message, status_code


if __name__ == "__main__":
    # ローカル開発用：python app.py で起動
    print(f"サーバーを起動します（ポート: {Config.FLASK_PORT}）")
    print("LINE Webhook URL: http://localhost:{}/callback".format(Config.FLASK_PORT))
    app.run(
        host="0.0.0.0",
        port=Config.FLASK_PORT,
        debug=Config.FLASK_DEBUG,
    )
