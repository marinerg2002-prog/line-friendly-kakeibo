"""
LINE Messaging API 連携
"""

from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import FlexSendMessage, FollowEvent, MessageEvent, PostbackEvent, TextMessage, TextSendMessage

from chart_service import build_monthly_chart_flex
from config import Config
from kakeibo_logic import (
    build_invalid_format_reply,
    build_monthly_summary_reply,
    build_no_graph_data_reply,
    build_record_reply,
    build_reset_reply,
    build_welcome_message,
    create_expense,
    format_month_label,
    is_help_request,
    is_monthly_summary_request,
    is_reset_request,
    parse_amount,
    parse_category_selection,
    parse_graph_request,
    parse_postback_category,
)
from sheet_service import SheetConnectionError, SheetService

line_bot_api = LineBotApi(Config.LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(Config.LINE_CHANNEL_SECRET)

# カテゴリ選択後、金額入力待ちの状態（user_id -> カテゴリ名）
pending_categories: dict[str, str] = {}


def handle_webhook(body: str, signature: str) -> tuple[str, int]:
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        return "Invalid signature", 400
    return "OK", 200


def select_expense_category(user_id: str, category: str) -> None:
    """カテゴリを選択し、金額入力待ちにする（案内メッセージは送らない）"""
    pending_categories[user_id] = category


@handler.add(FollowEvent)
def handle_follow(event):
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=build_welcome_message()),
    )


@handler.add(PostbackEvent)
def handle_postback(event):
    category = parse_postback_category(event.postback.data)
    if not category:
        return

    select_expense_category(event.source.user_id, category)


@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
    user_message = event.message.text.strip()
    user_id = event.source.user_id
    replies = build_replies(user_message, user_id)
    if replies:
        line_bot_api.reply_message(event.reply_token, replies)


def build_replies(text: str, user_id: str) -> list:
    """ユーザーのメッセージを処理し、返信メッセージのリストを作る"""
    try:
        if is_monthly_summary_request(text):
            sheet = SheetService()
            summary = sheet.get_month_summary(sheet.current_year_month())
            return [TextSendMessage(text=build_monthly_summary_reply(summary))]

        year_month = parse_graph_request(text)
        if year_month:
            sheet = SheetService()
            summary = sheet.get_month_summary(year_month)
            if summary["expense"] == 0:
                return [TextSendMessage(text=build_no_graph_data_reply(year_month))]

            label = format_month_label(year_month)
            return [
                FlexSendMessage(
                    alt_text=f"{label}の支出グラフ",
                    contents=build_monthly_chart_flex(summary),
                )
            ]

        if is_help_request(text):
            pending_categories.pop(user_id, None)
            return [TextSendMessage(text=build_welcome_message())]

        if is_reset_request(text):
            pending_categories.pop(user_id, None)
            sheet = SheetService()
            deleted_count = sheet.clear_current_month_transactions()
            return [TextSendMessage(text=build_reset_reply(deleted_count))]

        category = parse_category_selection(text)
        if category:
            select_expense_category(user_id, category)
            return []

        amount = parse_amount(text)
        if amount is not None and user_id in pending_categories:
            category = pending_categories.pop(user_id)
            transaction = create_expense(category, amount)
            sheet = SheetService()
            sheet.ensure_headers()
            sheet.append_transaction(transaction)
            return [TextSendMessage(text=build_record_reply(transaction))]

        if amount is not None and user_id not in pending_categories:
            return [
                TextSendMessage(
                    text="先にリッチメニューでカテゴリを選んでから、\n金額を入力してください。"
                )
            ]

    except SheetConnectionError as exc:
        return [TextSendMessage(text=exc.user_message)]

    pending_categories.pop(user_id, None)
    return [TextSendMessage(text=build_invalid_format_reply())]


def process_message(text: str, user_id: str = "test_user") -> str:
    """テスト用：テキスト返信を取得する"""
    replies = build_replies(text, user_id)
    if not replies:
        return ""
    message = replies[0]
    if isinstance(message, FlexSendMessage):
        return message.alt_text
    return message.text
