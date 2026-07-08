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


@app.route("/diagnose", methods=["GET"])
def diagnose():
    """
    接続診断用（Render の環境変数設定を確認する）。
    秘密情報（トークン等）は表示しません。
    """
    import json

    from sheet_service import SheetConnectionError, SheetService, _get_service_account_email

    lines = [
        "<h1>接続診断</h1>",
        "<ul>",
        f"<li>SPREADSHEET_ID: <code>{Config.get_spreadsheet_id()}</code></li>",
        f"<li>GOOGLE_SERVICE_ACCOUNT_JSON 設定: {'あり' if Config.GOOGLE_SERVICE_ACCOUNT_JSON else 'なし'}</li>",
        f"<li>service_account.json ファイル: {'あり' if __import__('pathlib').Path(Config.GOOGLE_SERVICE_ACCOUNT_FILE).exists() else 'なし'}</li>",
    ]

    if Config.GOOGLE_SERVICE_ACCOUNT_JSON:
        try:
            json.loads(Config.GOOGLE_SERVICE_ACCOUNT_JSON)
            lines.append("<li>JSON 形式: OK</li>")
        except json.JSONDecodeError as exc:
            lines.append(f"<li>JSON 形式: <strong>NG</strong> ({exc})</li>")

    try:
        email = _get_service_account_email()
        lines.append(f"<li>サービスアカウント: <code>{email}</code></li>")
    except Exception as exc:
        lines.append(f"<li>サービスアカウント: 取得失敗 ({exc})</li>")

    lines.append("</ul>")

    try:
        sheet = SheetService()
        lines.append(f"<p><strong>接続結果: 成功</strong>（{sheet.spreadsheet.title}）</p>")
    except SheetConnectionError as exc:
        lines.append(f"<p><strong>接続結果: 失敗</strong></p><pre>{exc.user_message}</pre>")
    except Exception as exc:
        lines.append(f"<p><strong>接続結果: エラー</strong> ({type(exc).__name__}: {exc})</p>")

    return "\n".join(lines)
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
