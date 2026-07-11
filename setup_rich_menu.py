"""
LINE リッチメニュー（6分割）のセットアップスクリプト

使い方:
    python setup_rich_menu.py

ボタン構成（2行×3列）:
    [食費] [日用品費] [交際・娯楽費]
    [その他] [今月のグラフ] [使い方]
"""

from pathlib import Path

from linebot import LineBotApi
from linebot.models import MessageAction, PostbackAction, RichMenu, RichMenuArea, RichMenuBounds, RichMenuSize
from PIL import Image, ImageDraw, ImageFont

from config import Config

MENU_WIDTH = 2500
MENU_HEIGHT = 1686
IMAGE_PATH = Path("rich_menu.png")
BACKGROUND_COLOR = "#FFF8F5"

COLS = 3
ROWS = 2
COL_WIDTH = MENU_WIDTH // COLS
ROW_HEIGHT = MENU_HEIGHT // ROWS

BUTTONS = [
  {"label": "食費", "kind": "category", "category": "食費", "color": "#F6D5DC", "text_color": "#5E3F4F", "row": 0, "col": 0},
  {"label": "日用品費", "kind": "category", "category": "日用品費", "color": "#DDD0F0", "text_color": "#524563", "row": 0, "col": 1},
  {"label": "交際・娯楽費", "kind": "category", "category": "交際・娯楽費", "color": "#F5D5C8", "text_color": "#6B5348", "row": 0, "col": 2},
  {"label": "その他", "kind": "category", "category": "その他", "color": "#E4E4E4", "text_color": "#555555", "row": 1, "col": 0},
  {"label": "今月のグラフ", "kind": "message", "text": "今月のグラフ", "color": "#C5DCE8", "text_color": "#3F5460", "row": 1, "col": 1},
  {"label": "使い方", "kind": "message", "text": "使い方", "color": "#CFE8DD", "text_color": "#3F544B", "row": 1, "col": 2},
]

BOLD_FONT_PATHS = [
    "C:/Windows/Fonts/BIZ-UDPGothicB.ttc",
    "C:/Windows/Fonts/YuGothB.ttc",
    "C:/Windows/Fonts/meiryob.ttc",
    "C:/Windows/Fonts/msgothic.ttc",
    "/System/Library/Fonts/ヒラギノ丸ゴ ProN W6.ttc",
    "/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc",
]

FONT_SIZE_MAX = 82
FONT_SIZE_MIN = 64


def load_menu_font(size: int = FONT_SIZE_MAX) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for font_path in BOLD_FONT_PATHS:
        if Path(font_path).exists():
            return ImageFont.truetype(font_path, size)
    return ImageFont.load_default()


def fit_font_for_label(
    draw: ImageDraw.ImageDraw,
    label: str,
    max_width: int,
    max_height: int,
) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """ボタン内に収まる最大サイズの太字フォントを選ぶ"""
    for size in range(FONT_SIZE_MAX, FONT_SIZE_MIN - 1, -2):
        font = load_menu_font(size)
        text_box = draw.textbbox((0, 0), label, font=font)
        text_width = text_box[2] - text_box[0]
        text_height = text_box[3] - text_box[1]
        if text_width <= max_width and text_height <= max_height:
            return font
    return load_menu_font(FONT_SIZE_MIN)


def button_bounds(row: int, col: int) -> tuple[int, int, int, int]:
    """ボタン領域（画像描画用）の座標を返す"""
    padding_x = 28
    padding_y = 24
    left = col * COL_WIDTH + padding_x
    top = row * ROW_HEIGHT + padding_y
    right = (col + 1) * COL_WIDTH - padding_x
    bottom = (row + 1) * ROW_HEIGHT - padding_y
    return left, top, right, bottom


def create_menu_image() -> Path:
    image = Image.new("RGB", (MENU_WIDTH, MENU_HEIGHT), BACKGROUND_COLOR)
    draw = ImageDraw.Draw(image)

    for button in BUTTONS:
        left, top, right, bottom = button_bounds(button["row"], button["col"])
        draw.rounded_rectangle([left, top, right, bottom], radius=40, fill=button["color"])

        text = button["label"]
        button_width = right - left
        button_height = bottom - top
        font = fit_font_for_label(draw, text, button_width - 24, button_height - 16)
        text_box = draw.textbbox((0, 0), text, font=font)
        text_width = text_box[2] - text_box[0]
        text_height = text_box[3] - text_box[1]
        x = left + (button_width - text_width) // 2
        y = top + (button_height - text_height) // 2
        draw.text((x, y), text, fill=button["text_color"], font=font)

    image.save(IMAGE_PATH)
    return IMAGE_PATH


def build_menu_action(button: dict) -> MessageAction | PostbackAction:
    """カテゴリはキーボードを開くPostback、それ以外はメッセージ送信"""
    if button["kind"] == "category":
        return PostbackAction(
            label=button["label"],
            data=f"category={button['category']}",
            input_option="openKeyboard",
        )
    return MessageAction(label=button["label"], text=button["text"])


def build_rich_menu() -> RichMenu:
    areas = []
    for button in BUTTONS:
        x = button["col"] * COL_WIDTH
        y = button["row"] * ROW_HEIGHT
        width = COL_WIDTH if button["col"] < COLS - 1 else MENU_WIDTH - COL_WIDTH * (COLS - 1)
        height = ROW_HEIGHT if button["row"] < ROWS - 1 else MENU_HEIGHT - ROW_HEIGHT * (ROWS - 1)

        areas.append(
            RichMenuArea(
                bounds=RichMenuBounds(x=x, y=y, width=width, height=height),
                action=build_menu_action(button),
            )
        )

    return RichMenu(
        size=RichMenuSize(width=MENU_WIDTH, height=MENU_HEIGHT),
        selected=False,
        name="家計簿メニュー6分割",
        chat_bar_text="メニュー",
        areas=areas,
    )


def setup_rich_menu() -> None:
    line_bot_api = LineBotApi(Config.LINE_CHANNEL_ACCESS_TOKEN)

    for menu_id in line_bot_api.get_rich_menu_list():
        line_bot_api.delete_rich_menu(menu_id.rich_menu_id)

    image_path = create_menu_image()
    rich_menu = build_rich_menu()
    rich_menu_id = line_bot_api.create_rich_menu(rich_menu=rich_menu)

    with image_path.open("rb") as image_file:
        line_bot_api.set_rich_menu_image(rich_menu_id, "image/png", image_file)

    line_bot_api.set_default_rich_menu(rich_menu_id)

    print("6分割リッチメニューの設定が完了しました。")
    print(f"Rich Menu ID: {rich_menu_id}")


if __name__ == "__main__":
    setup_rich_menu()
