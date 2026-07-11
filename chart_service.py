"""
月ごとの支出グラフ（LINE Flex Message）
"""

from kakeibo_logic import EXPENSE_CATEGORIES, format_month_label, format_yen

CATEGORY_COLORS = {
    "食費": "#F6D5DC",
    "日用品費": "#DDD0F0",
    "交際・娯楽費": "#F5D5C8",
    "その他": "#D4D4D4",
    # 旧カテゴリ（過去データ用）
    "外食": "#FFA94D",
    "交通費": "#4DABF7",
    "日用品": "#51CF66",
    "娯楽費": "#CC5DE8",
}


def build_monthly_chart_flex(summary: dict) -> dict:
    """月次支出サマリーから LINE Flex Message を作る"""
    label = format_month_label(summary["year_month"])
    expense = summary["expense"]
    categories = summary["expense_categories"]

    contents = [
        {
            "type": "text",
            "text": f"📊 {label}の支出",
            "weight": "bold",
            "size": "xl",
            "color": "#7A5568",
        },
        {"type": "separator", "margin": "md"},
        _summary_row("🛒 支出合計", format_yen(expense), "#E03131"),
    ]

    if categories:
        contents.append({"type": "separator", "margin": "lg"})
        contents.append(
            {
                "type": "text",
                "text": "カテゴリ別の内訳",
                "weight": "bold",
                "size": "md",
                "margin": "md",
                "color": "#6B5B7A",
            }
        )
        max_amount = max(categories.values())
        displayed = set()

        for category in EXPENSE_CATEGORIES:
            amount = categories.get(category, 0)
            if amount > 0:
                contents.append(_category_bar(category, amount, max_amount))
                displayed.add(category)

        for category, amount in sorted(categories.items()):
            if category not in displayed and amount > 0:
                contents.append(_category_bar(category, amount, max_amount))
    else:
        contents.append(
            {
                "type": "text",
                "text": "支出の記録はまだありません",
                "size": "sm",
                "color": "#868E96",
                "margin": "lg",
            }
        )

    return {
        "type": "bubble",
        "size": "mega",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": contents,
            "paddingAll": "16px",
        },
    }


def _summary_row(label: str, value: str, color: str) -> dict:
    return {
        "type": "box",
        "layout": "horizontal",
        "margin": "sm",
        "contents": [
            {"type": "text", "text": label, "size": "sm", "color": "#555555", "flex": 2},
            {
                "type": "text",
                "text": value,
                "size": "sm",
                "weight": "bold",
                "color": color,
                "align": "end",
                "flex": 3,
            },
        ],
    }


def _category_bar(category: str, amount: int, max_amount: int) -> dict:
    bar_flex = max(int(amount / max_amount * 10), 1)
    empty_flex = 10 - bar_flex
    color = CATEGORY_COLORS.get(category, "#ADB5BD")

    return {
        "type": "box",
        "layout": "vertical",
        "margin": "md",
        "contents": [
            {
                "type": "box",
                "layout": "horizontal",
                "contents": [
                    {"type": "text", "text": category, "size": "sm", "flex": 2},
                    {
                        "type": "text",
                        "text": format_yen(amount),
                        "size": "sm",
                        "align": "end",
                        "flex": 3,
                    },
                ],
            },
            {
                "type": "box",
                "layout": "horizontal",
                "margin": "xs",
                "contents": [
                    {
                        "type": "box",
                        "layout": "vertical",
                        "flex": bar_flex,
                        "backgroundColor": color,
                        "height": "12px",
                        "cornerRadius": "6px",
                    },
                    {"type": "box", "layout": "vertical", "flex": empty_flex},
                ],
            },
        ],
    }
