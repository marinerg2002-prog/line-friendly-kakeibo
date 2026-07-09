"""
月ごとの家計グラフ（LINE Flex Message）

スプレッドシートの集計データを、LINE 画面上で見やすいグラフにします。
"""

from kakeibo_logic import format_month_label, format_yen

# カテゴリごとの棒グラフの色
CATEGORY_COLORS = {
    "食費": "#FF6B6B",
    "外食": "#FFA94D",
    "交通費": "#4DABF7",
    "日用品": "#51CF66",
    "娯楽費": "#CC5DE8",
    "給料": "#339AF0",
    "臨時収入": "#22B8CF",
    "その他": "#ADB5BD",
}


def build_monthly_chart_flex(summary: dict) -> dict:
    """
    月次家計サマリーから LINE Flex Message（バブル）を作る。

    summary の形式:
        {
            "year_month": "2026-07",
            "income": 250000,
            "expense": 35000,
            "balance": 215000,
            "expense_categories": {"食費": 10000, "外食": 5000, ...},
        }
    """
    label = format_month_label(summary["year_month"])
    income = summary["income"]
    expense = summary["expense"]
    balance = summary["balance"]
    categories = summary["expense_categories"]

    contents = [
        {
            "type": "text",
            "text": f"📊 {label}の家計",
            "weight": "bold",
            "size": "xl",
            "color": "#1DB446",
        },
        {"type": "separator", "margin": "md"},
        _summary_row("💰 収入", format_yen(income), "#2B8A3E"),
        _summary_row("🛒 支出", format_yen(expense), "#E03131"),
        _summary_row("💵 残り", format_yen(balance), "#1971C2"),
    ]

    if categories:
        contents.append({"type": "separator", "margin": "lg"})
        contents.append(
            {
                "type": "text",
                "text": "支出の内訳",
                "weight": "bold",
                "size": "md",
                "margin": "md",
            }
        )
        max_amount = max(categories.values())
        sorted_categories = sorted(categories.items(), key=lambda item: item[1], reverse=True)

        for category, amount in sorted_categories:
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
    """収入・支出・残りのサマリー行を作る"""
    return {
        "type": "box",
        "layout": "horizontal",
        "margin": "sm",
        "contents": [
            {
                "type": "text",
                "text": label,
                "size": "sm",
                "color": "#555555",
                "flex": 2,
            },
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
    """カテゴリ別の棒グラフ1行を作る"""
    # 棒の長さ（flex 1〜10）
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
                    {
                        "type": "text",
                        "text": category,
                        "size": "sm",
                        "flex": 2,
                    },
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
                    {
                        "type": "box",
                        "layout": "vertical",
                        "flex": empty_flex,
                    },
                ],
            },
        ],
    }
