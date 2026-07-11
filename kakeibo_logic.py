"""
家計簿のロジック（メッセージ解析・カテゴリ分類・返信メッセージ生成）

支出のみを記録する家計簿のロジックをまとめています。
"""

import re
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

# 金額のみ（例: 580）
AMOUNT_ONLY_PATTERN = re.compile(r"^\d+$")

# 支出カテゴリ（リッチメニューと一致）
EXPENSE_CATEGORIES = [
    "食費",
    "日用品費",
    "交際・娯楽費",
    "その他",
]

# 改善前のカテゴリ名を①〜④へ集約する
LEGACY_CATEGORY_MAP = {
    "食費": "食費",
    "外食": "食費",
    "日用品": "日用品費",
    "日用品費": "日用品費",
    "娯楽費": "交際・娯楽費",
    "交際・娯楽費": "交際・娯楽費",
    "交通費": "その他",
    "その他": "その他",
}

# 「7月のグラフ」などを判定
GRAPH_REQUEST_PATTERN = re.compile(
    r"^(?:今月のグラフ|(?:(?P<year>\d{4})年)?(?P<month>\d{1,2})月のグラフ)$"
)


@dataclass
class Transaction:
    """1件の支出を表すデータ"""

    date: str
    kind: str          # 常に「支出」
    description: str   # カテゴリ名と同じ
    amount: int
    category: str


def format_yen(amount: int) -> str:
    """金額を「1,234円」のように見やすく表示する"""
    return f"{amount:,}円"


def normalize_category(category: str) -> str:
    """カテゴリ名を①〜④のいずれかに統一する"""
    return LEGACY_CATEGORY_MAP.get(category.strip(), "その他")


def summarize_expense_categories(raw: dict[str, int]) -> dict[str, int]:
    """支出カテゴリを①〜④だけに集約する"""
    summarized = {category: 0 for category in EXPENSE_CATEGORIES}
    for category, amount in raw.items():
        normalized = normalize_category(category)
        summarized[normalized] += amount
    return {category: amount for category, amount in summarized.items() if amount > 0}


def parse_amount(text: str) -> Optional[int]:
    """数字のみの金額を解析する（例: 580）"""
    text = text.strip()
    if not AMOUNT_ONLY_PATTERN.match(text):
        return None
    return int(text)


def parse_category_selection(text: str) -> Optional[str]:
    """リッチメニューから送られたカテゴリ名を判定する"""
    text = text.strip()
    if text in EXPENSE_CATEGORIES:
        return text
    return None


def create_expense(category: str, amount: int) -> Transaction:
    """支出データを作成する"""
    return Transaction(
        date=datetime.now().strftime("%Y-%m-%d"),
        kind="支出",
        description=category,
        amount=amount,
        category=category,
    )


def is_monthly_summary_request(text: str) -> bool:
    """「今月の家計」というメッセージかどうかを判定する"""
    return text.strip() == "今月の家計"


def is_help_request(text: str) -> bool:
    """「使い方」というメッセージかどうかを判定する"""
    return text.strip() == "使い方"


def is_reset_request(text: str) -> bool:
    """「リセット」というメッセージかどうかを判定する"""
    return text.strip() == "リセット"


def parse_graph_request(text: str) -> Optional[str]:
    """グラフ表示リクエストを「YYYY-MM」形式で返す"""
    text = text.strip()
    match = GRAPH_REQUEST_PATTERN.match(text)
    if not match:
        return None

    if text == "今月のグラフ":
        return datetime.now().strftime("%Y-%m")

    month = int(match.group("month"))
    year_str = match.group("year")
    year = int(year_str) if year_str else datetime.now().year
    return f"{year}-{month:02d}"


def format_month_label(year_month: str) -> str:
    """「2026-07」->「2026年7月」に変換する"""
    year, month = year_month.split("-")
    return f"{int(year)}年{int(month)}月"


def build_category_prompt(category: str) -> str:
    """カテゴリ選択後、金額入力を促すメッセージ"""
    return (
        f"📝 {category}の記録\n\n"
        "金額を入力してください（数字のみ）\n"
        "例：580"
    )


def build_record_reply(transaction: Transaction) -> str:
    """支出を記録したときの LINE 返信メッセージ"""
    return (
        "🛒 支出を記録しました！\n\n"
        f"📂 カテゴリ：{transaction.category}\n"
        f"💵 金額：{format_yen(transaction.amount)}"
    )


def build_monthly_summary_reply(summary: dict) -> str:
    """今月の支出サマリーを組み立てる"""
    expense_total = summary["expense"]
    categories = summary["expense_categories"]

    lines = [
        "📊 今月の支出状況です。",
        "",
        f"🛒 合計：{format_yen(expense_total)}",
        "",
    ]

    if categories:
        lines.append("【カテゴリ別】")
        for category in EXPENSE_CATEGORIES:
            amount = categories.get(category, 0)
            if amount > 0:
                lines.append(f"・{category}：{format_yen(amount)}")
        lines.append("")
        lines.append("きちんと記録できています ✨")
    else:
        lines.append("まだ今月の支出記録がありません。")
        lines.append("リッチメニューから記録してみてください 🌱")

    return "\n".join(lines)


def build_no_graph_data_reply(year_month: str) -> str:
    """対象月に記録がないときのメッセージ"""
    label = format_month_label(year_month)
    return (
        f"📊 {label}の支出記録はまだありません。\n\n"
        "リッチメニューから記録してから、\n"
        "もう一度グラフを見てみてください。"
    )


def build_reset_reply(deleted_count: int) -> str:
    """今月分の家計簿リセット完了メッセージ"""
    month_label = f"{datetime.now().month}月"

    if deleted_count == 0:
        return (
            f"🔄 {month_label}の家計簿をリセットしました。\n\n"
            f"削除する{month_label}の記録はありませんでした。\n"
            "また新しい記録から始められます ✨"
        )

    return (
        f"🔄 {month_label}の家計簿をリセットしました。\n\n"
        f"🗑️ 削除した記録：{deleted_count}件（{month_label}分のみ）\n\n"
        "※ 以前の月の記録は残っています。\n"
        "また新しい記録から始めていきましょう 🌱"
    )


def build_invalid_format_reply() -> str:
    """入力形式が間違っているときの案内"""
    return (
        "❓ 入力を確認してください。\n\n"
        "📝【支出を記録する場合】\n"
        "1. リッチメニューでカテゴリを選ぶ\n"
        "   （食費 / 日用品費 / 交際・娯楽費 / その他）\n"
        "2. 金額を数字のみで送る\n"
        "   例：580\n\n"
        "📈【今月のグラフ】\n"
        "リッチメニューの「今月のグラフ」をタップ\n\n"
        "❓【使い方】\n"
        "リッチメニューの「使い方」をタップ\n\n"
        "🔄【今月の記録を消す場合】\n"
        "「リセット」と送ってください。"
    )


def build_welcome_message() -> str:
    """友だち追加時・使い方のガイド"""
    return (
        "👋 友だち追加ありがとうございます！\n"
        "「褒めてくれるやさしい家計簿」です ✨\n\n"
        "━━━━━━━━━━━━━━\n"
        "📝 支出の記録方法\n"
        "━━━━━━━━━━━━━━\n\n"
        "1. 下のメニューでカテゴリを選ぶ\n"
        "   ①食費（食材・外食・お弁当）\n"
        "   ②日用品費\n"
        "   ③交際・娯楽費\n"
        "   ④その他\n\n"
        "2. 金額を数字のみで送る\n"
        "   例：580\n\n"
        "━━━━━━━━━━━━━━\n"
        "📈 今月のグラフ\n"
        "━━━━━━━━━━━━━━\n\n"
        "メニューの「今月のグラフ」で\n"
        "支出の内訳を確認できます。\n\n"
        "━━━━━━━━━━━━━━\n"
        "🔄 今月のリセット\n"
        "━━━━━━━━━━━━━━\n\n"
        "「リセット」で今月分だけ\n"
        "記録を削除できます。\n\n"
        "さっそく記録してみてください！ 🌱"
    )
