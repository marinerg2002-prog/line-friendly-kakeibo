"""
設定ファイル

.env ファイルから環境変数を読み込み、アプリ全体で使えるようにします。
"""

import os
import re

from dotenv import load_dotenv

# .env ファイルを読み込む（同じフォルダにある前提）
load_dotenv()


def normalize_spreadsheet_id(value: str) -> str:
    """
    スプレッドシート ID を正規化する。

    次のような入力にも対応します：
    - 1EYd3U4_dRZgVsc_MH3sC9uioWehjvAVBgZI6SxyVknE
    - https://docs.google.com/spreadsheets/d/1EYd3U4.../edit
    """
    if not value:
        return ""

    value = value.strip().strip('"').strip("'")

    # URL が貼られている場合は ID 部分だけ取り出す
    match = re.search(r"/spreadsheets/d/([a-zA-Z0-9-_]+)", value)
    if match:
        return match.group(1)

    return value


class Config:
    """アプリで使う設定値をまとめたクラス"""

    # LINE Messaging API
    LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "")
    LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET", "")

    # Google スプレッドシート
    GOOGLE_SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE", "service_account.json")
    # クラウド用: service_account.json の中身を1行の JSON 文字列で設定
    GOOGLE_SERVICE_ACCOUNT_JSON = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "")
    SPREADSHEET_ID = normalize_spreadsheet_id(os.getenv("SPREADSHEET_ID", ""))
    # SPREADSHEET_URL が設定されていれば、そちらを優先して ID を取得
    SPREADSHEET_URL = os.getenv("SPREADSHEET_URL", "")

    # Flask
    FLASK_PORT = int(os.getenv("FLASK_PORT", "5000"))
    FLASK_DEBUG = os.getenv("FLASK_DEBUG", "True").lower() == "true"

    @classmethod
    def get_spreadsheet_id(cls) -> str:
        """スプレッドシート ID を取得する（URL 設定時は URL から抽出）"""
        if cls.SPREADSHEET_URL:
            return normalize_spreadsheet_id(cls.SPREADSHEET_URL)
        return cls.SPREADSHEET_ID
