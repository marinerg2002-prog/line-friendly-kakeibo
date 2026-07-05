"""
家計簿のロジック（メッセージ解析・カテゴリ分類・返信メッセージ生成）

LINE から送られたテキストを解析し、収入/支出の判定や
今月の家計サマリー、褒め・やさしいメッセージを作ります。
"""

import re
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

# 「+250000 給料」「-2450 スーパー」の形式を判定する正規表現
TRANSACTION_PATTERN = re.compile(r"^([+-])(\d+)\s+(.+)$")

# 内容（キーワード）→ カテゴリ の対応表
CATEGORY_MAP = {
    "給料": "給料",
    "メルカリ": "臨時収入",
    "お祝い": "臨時収入",
    "スーパー": "食費",
    "カフェ": "食費",
    "電車": "交通費",
    "Amazon": "日用品",
    "映画": "娯楽費",
}


@dataclass
class Transaction:
    """1件の収入または支出を表すデータ"""

    date: str          # 日付（例: 2026-07-02）
    kind: str          # 区分（「収入」または「支出」）
    description: str   # 内容（例: スーパー）
    amount: int        # 金額（正の整数）
    category: str      # カテゴリ（例: 食費）


def format_yen(amount: int) -> str:
    """金額を「1,234円」のように見やすく表示する"""
    return f"{amount:,}円"


def classify_category(description: str) -> str:
    """
    内容（説明文）からカテゴリを自動判定する。
    対応表にない場合は「その他」とする。
    """
    return CATEGORY_MAP.get(description.strip(), "その他")


def parse_transaction(text: str) -> Optional[Transaction]:
    """
    「+金額 内容」または「-金額 内容」を解析する。

    成功したら Transaction を返し、形式が合わなければ None を返す。
    """
    text = text.strip()
    match = TRANSACTION_PATTERN.match(text)
    if not match:
        return None

    sign, amount_str, description = match.groups()
    amount = int(amount_str)

    if sign == "+":
        kind = "収入"
    else:
        kind = "支出"

    category = classify_category(description)

    return Transaction(
        date=datetime.now().strftime("%Y-%m-%d"),
        kind=kind,
        description=description.strip(),
        amount=amount,
        category=category,
    )


def is_monthly_summary_request(text: str) -> bool:
    """「今月の家計」というメッセージかどうかを判定する"""
    return text.strip() == "今月の家計"


def build_record_reply(transaction: Transaction) -> str:
    """収入・支出を記録したときの LINE 返信メッセージを作る"""
    if transaction.kind == "収入":
        return (
            "収入を記録しました！\n\n"
            f"内容：{transaction.description}\n"
            f"金額：{format_yen(transaction.amount)}\n"
            f"分類：{transaction.category}"
        )

    return (
        "支出を記録しました！\n\n"
        f"内容：{transaction.description}\n"
        f"金額：{format_yen(transaction.amount)}\n"
        f"カテゴリ：{transaction.category}"
    )


def build_praise_message(balance: int) -> str:
    """
    黒字のとき、残り金額に応じた褒めメッセージを返す。

    - 1〜999円: ギリギリ黒字
    - 1,000〜9,999円: しっかり黒字
    - 10,000円以上: 大きな黒字
    """
    if balance >= 10000:
        return (
            "すごいです！\n"
            "大きな黒字です。\n"
            "家計管理がかなり上手にできています。"
        )
    if balance >= 1000:
        return (
            "いい感じです！\n"
            "今月はしっかり黒字で管理できています。"
        )
    return (
        "ギリギリでも黒字を守れています！\n"
        "最後まで記録できているのがすごいです。"
    )


def build_deficit_message(balance: int) -> str:
    """
    赤字のとき、責めずにやさしいメッセージを返す。
    balance はマイナス値（例: -3200）
    """
    deficit = abs(balance)
    return (
        f"今月は{format_yen(deficit)}だけマイナスです。\n\n"
        "でも、支出を記録できているだけで大きな前進です。\n"
        "来月は少し調整すれば、黒字に近づけそうです。"
    )


def build_monthly_summary_reply(income_total: int, expense_total: int) -> str:
    """今月の家計サマリーと、黒字/赤字に応じたメッセージを組み立てる"""
    balance = income_total - expense_total

    lines = [
        "今月の家計状況です。",
        "",
        f"収入：{format_yen(income_total)}",
        f"支出：{format_yen(expense_total)}",
        f"残り：{format_yen(balance)}",
        "",
    ]

    if balance >= 0:
        if balance >= 10000:
            lines.append("今月は大きく黒字です！")
            lines.append("収入も支出もきちんと記録できています。")
            lines.append("この調子で、無理なく家計管理を続けられています。")
        else:
            lines.append(build_praise_message(balance))
    else:
        lines.append(build_deficit_message(balance))

    return "\n".join(lines)


def build_invalid_format_reply() -> str:
    """入力形式が間違っているときの案内メッセージ"""
    return (
        "入力形式を確認してください。\n\n"
        "【記録する場合】\n"
        "+金額 内容（収入）\n"
        "-金額 内容（支出）\n\n"
        "例：\n"
        "+250000 給料\n"
        "-2450 スーパー\n\n"
        "【今月の集計を見る場合】\n"
        "「今月の家計」と送ってください。"
    )


def build_welcome_message() -> str:
    """友だち追加時に送る使い方ガイド"""
    return (
        "友だち追加ありがとうございます！\n"
        "「褒めてくれるやさしい家計簿」です。\n\n"
        "━━━━━━━━━━━━━━\n"
        "📝 収入・支出の記録\n"
        "━━━━━━━━━━━━━━\n\n"
        "収入：\n"
        "+金額 内容\n\n"
        "支出：\n"
        "-金額 内容\n\n"
        "例：\n"
        "+250000 給料\n"
        "+3200 メルカリ\n"
        "-2450 スーパー\n"
        "-580 カフェ\n\n"
        "━━━━━━━━━━━━━━\n"
        "📊 今月の家計を確認\n"
        "━━━━━━━━━━━━━━\n\n"
        "「今月の家計」と送ると、\n"
        "収入・支出・残り金額をお知らせします。\n\n"
        "黒字なら褒めます。\n"
        "赤字でも、やさしい言葉でお返しします。\n\n"
        "さっそく記録してみてください！"
    )
