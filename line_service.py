"""
LINE Messaging API 連携

Webhook で受け取ったメッセージを処理し、返信を送ります。
"""

from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import FollowEvent, MessageEvent, TextMessage, TextSendMessage

from config import Config
from kakeibo_logic import (
    build_invalid_format_reply,
    build_monthly_summary_reply,
    build_record_reply,
    build_welcome_message,
    is_monthly_summary_request,
    parse_transaction,
)
from sheet_service import SheetConnectionError, SheetService

# LINE API のクライアントを初期化
line_bot_api = LineBotApi(Config.LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(Config.LINE_CHANNEL_SECRET)


def handle_webhook(body: str, signature: str) -> tuple[str, int]:
    """
    LINE から送られてきた Webhook を処理する。

    Args:
        body: リクエストの本文（JSON文字列）
        signature: X-Line-Signature ヘッダーの値

    Returns:
        (レスポンスメッセージ, HTTPステータスコード) のタプル
    """
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        # 署名が一致しない = 不正なリクエスト
        return "Invalid signature", 400

    return "OK", 200


@handler.add(FollowEvent)
def handle_follow(event):
    """
    友だち追加（フォロー）されたときの処理。
    使い方ガイドを自動返信する。
    """
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=build_welcome_message()),
    )


@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
    """
    テキストメッセージを受け取ったときの処理。

    1. 「今月の家計」→ 今月の集計を返す
    2. 「+金額 内容」「-金額 内容」→ 記録して返信
    3. それ以外 → 入力形式の案内を返す
    """
    user_message = event.message.text.strip()
    reply_text = process_message(user_message)

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text),
    )


def process_message(text: str) -> str:
    """
    ユーザーのメッセージを処理し、返信テキストを生成する。

    この関数はテストしやすいように、LINE 送信部分と分離しています。
    """
    try:
        # 「今月の家計」のリクエスト
        if is_monthly_summary_request(text):
            sheet = SheetService()
            income_total, expense_total = sheet.get_current_month_totals()
            return build_monthly_summary_reply(income_total, expense_total)

        # 収入・支出の記録
        transaction = parse_transaction(text)
        if transaction:
            sheet = SheetService()
            sheet.ensure_headers()
            sheet.append_transaction(transaction)
            return build_record_reply(transaction)
    except SheetConnectionError as exc:
        return exc.user_message

    # 形式が合わない場合
    return build_invalid_format_reply()
