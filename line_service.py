"""
LINE Messaging API 連携

Webhook で受け取ったメッセージを処理し、返信を送ります。
"""

from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import FlexSendMessage, FollowEvent, MessageEvent, TextMessage, TextSendMessage

from chart_service import build_monthly_chart_flex
from config import Config
from kakeibo_logic import (
    build_invalid_format_reply,
    build_monthly_summary_reply,
    build_no_graph_data_reply,
    build_record_reply,
    build_reset_reply,
    build_welcome_message,
    format_month_label,
    is_monthly_summary_request,
    is_reset_request,
    parse_graph_request,
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
    """
    user_message = event.message.text.strip()
    replies = build_replies(user_message)

    line_bot_api.reply_message(event.reply_token, replies)


def build_replies(text: str) -> list:
    """
    ユーザーのメッセージを処理し、LINE 返信メッセージのリストを作る。

    テキスト返信と Flex Message（グラフ）の両方に対応します。
    """
    try:
        # 「今月の家計」のリクエスト
        if is_monthly_summary_request(text):
            sheet = SheetService()
            income_total, expense_total = sheet.get_current_month_totals()
            return [TextSendMessage(text=build_monthly_summary_reply(income_total, expense_total))]

        # 月ごとのグラフ表示
        year_month = parse_graph_request(text)
        if year_month:
            sheet = SheetService()
            summary = sheet.get_month_summary(year_month)
            if summary["income"] == 0 and summary["expense"] == 0:
                return [TextSendMessage(text=build_no_graph_data_reply(year_month))]

            label = format_month_label(year_month)
            flex_contents = build_monthly_chart_flex(summary)
            return [
                FlexSendMessage(
                    alt_text=f"{label}の家計グラフ",
                    contents=flex_contents,
                )
            ]

        # 「家計簿リセット」のリクエスト
        if is_reset_request(text):
            sheet = SheetService()
            deleted_count = sheet.clear_current_month_transactions()
            return [TextSendMessage(text=build_reset_reply(deleted_count))]

        # 収入・支出の記録
        transaction = parse_transaction(text)
        if transaction:
            sheet = SheetService()
            sheet.ensure_headers()
            sheet.append_transaction(transaction)
            return [TextSendMessage(text=build_record_reply(transaction))]

    except SheetConnectionError as exc:
        return [TextSendMessage(text=exc.user_message)]

    # 形式が合わない場合
    return [TextSendMessage(text=build_invalid_format_reply())]


def process_message(text: str) -> str:
    """
    テキスト返信だけを取得する（テスト用）。

    Flex Message の場合は案内文を返します。
    """
    replies = build_replies(text)
    message = replies[0]
    if isinstance(message, FlexSendMessage):
        return message.alt_text
    return message.text
