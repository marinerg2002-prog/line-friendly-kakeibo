"""
Google スプレッドシート連携

gspread を使って、家計データの保存と今月の集計を行います。
"""

import json
from datetime import datetime
from pathlib import Path

import gspread
from google.oauth2.service_account import Credentials

from config import Config
from kakeibo_logic import Transaction

# Google Sheets API で必要な権限
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

# スプレッドシートの列名（1行目のヘッダー）
HEADERS = ["日付", "区分", "内容", "金額", "カテゴリ"]


class SheetConnectionError(Exception):
    """スプレッドシート接続に失敗したときのエラー（ユーザー向けメッセージ付き）"""

    def __init__(self, user_message: str):
        self.user_message = user_message
        super().__init__(user_message)


def _load_service_account_info() -> dict:
    """
    サービスアカウントの JSON を読み込む。
    クラウド: 環境変数 GOOGLE_SERVICE_ACCOUNT_JSON
    ローカル: service_account.json
    """
    if Config.GOOGLE_SERVICE_ACCOUNT_JSON:
        return json.loads(Config.GOOGLE_SERVICE_ACCOUNT_JSON)

    key_path = Path(Config.GOOGLE_SERVICE_ACCOUNT_FILE)
    if not key_path.exists():
        raise FileNotFoundError(
            f"認証ファイルが見つかりません: {Config.GOOGLE_SERVICE_ACCOUNT_FILE}"
        )

    with key_path.open(encoding="utf-8") as file:
        return json.load(file)


def _get_credentials() -> Credentials:
    """Google API 用の認証情報を作成する"""
    return Credentials.from_service_account_info(
        _load_service_account_info(),
        scopes=SCOPES,
    )


def _get_service_account_email() -> str:
    """共有先メールアドレス（client_email）を取得する"""
    try:
        info = _load_service_account_info()
        return info.get("client_email", "（client_email が見つかりません）")
    except (FileNotFoundError, json.JSONDecodeError):
        return "（認証情報が設定されていません）"


def _build_spreadsheet_hint(client: gspread.Client, spreadsheet_id: str) -> str:
    """
    接続失敗時、サービスアカウントがアクセスできる
    スプレッドシートがあれば正しい ID を案内する。
    """
    try:
        spreadsheets = client.list_spreadsheet_files()
    except Exception:
        return ""

    if not spreadsheets:
        return ""

    lines = ["\n\n【ヒント】アクセス可能なスプレッドシート:"]
    for sheet in spreadsheets[:3]:
        mark = " ← おそらくこちら" if sheet["id"] != spreadsheet_id else ""
        lines.append(f"・{sheet['name']}  ID: {sheet['id']}{mark}")

    lines.append("\n診断コマンド: python check_sheets.py")
    return "\n".join(lines)


class SheetService:
    """スプレッドシートへの読み書きを担当するクラス"""

    def __init__(self):
        """サービスアカウントで Google スプレッドシートに接続する"""
        spreadsheet_id = Config.get_spreadsheet_id()
        if not spreadsheet_id:
            raise SheetConnectionError(
                "スプレッドシート ID が設定されていません。\n"
                ".env の SPREADSHEET_ID に ID を設定してください。"
            )

        try:
            credentials = _get_credentials()
        except FileNotFoundError:
            raise SheetConnectionError(
                "Google の認証情報が設定されていません。\n"
                "ローカル: service_account.json を配置\n"
                "クラウド: GOOGLE_SERVICE_ACCOUNT_JSON を環境変数に設定"
            ) from None
        except json.JSONDecodeError:
            raise SheetConnectionError(
                "GOOGLE_SERVICE_ACCOUNT_JSON の形式が正しくありません。\n"
                "service_account.json を1行の JSON に圧縮して、\n"
                "Render の環境変数に貼り付け直してください。"
            ) from None

        client = gspread.authorize(credentials)

        try:
            self.spreadsheet = client.open_by_key(spreadsheet_id)
        except gspread.SpreadsheetNotFound as exc:
            service_email = _get_service_account_email()
            hint = _build_spreadsheet_hint(client, spreadsheet_id)
            raise SheetConnectionError(
                "スプレッドシートに接続できませんでした。\n\n"
                f"設定中の ID: {spreadsheet_id}\n\n"
                "よくある原因：\n"
                "1. SPREADSHEET_ID が間違っている（1文字の typo でも 404 になります）\n"
                "2. スプレッドシートがサービスアカウントと共有されていない\n"
                "3. Google Sheets API / Drive API が有効になっていない\n\n"
                f"【確認】スプレッドシートの「共有」に\n"
                f"{service_email}\n"
                "を「編集者」として追加してください。"
                f"{hint}"
            ) from exc

        self.worksheet = self.spreadsheet.sheet1

    def ensure_headers(self) -> None:
        """
        1行目にヘッダー行があるか確認し、なければ作成する。
        初回セットアップ時に便利です。
        """
        first_row = self.worksheet.row_values(1)
        if first_row != HEADERS:
            self.worksheet.update("A1:E1", [HEADERS])

    def append_transaction(self, transaction: Transaction) -> None:
        """1件の収入/支出をスプレッドシートの末尾に追加する"""
        row = [
            transaction.date,
            transaction.kind,
            transaction.description,
            transaction.amount,
            transaction.category,
        ]
        self.worksheet.append_row(row, value_input_option="USER_ENTERED")

    def clear_all_transactions(self) -> int:
        """
        2行目以降の記録をすべて削除する（ヘッダー行は残す）。

        Returns:
            削除した記録の件数
        """
        self.ensure_headers()
        row_count = self.worksheet.row_count
        deleted_count = max(row_count - 1, 0)

        if row_count > 1:
            self.worksheet.delete_rows(2, row_count)

        return deleted_count

    def get_current_month_totals(self) -> tuple[int, int]:
        """
        今月の収入合計と支出合計を計算して返す。

        Returns:
            (収入合計, 支出合計) のタプル
        """
        records = self.worksheet.get_all_records()
        current_month = datetime.now().strftime("%Y-%m")

        income_total = 0
        expense_total = 0

        for record in records:
            date_str = str(record.get("日付", ""))
            kind = str(record.get("区分", ""))
            amount = record.get("金額", 0)

            if not date_str.startswith(current_month):
                continue

            try:
                amount = int(amount)
            except (ValueError, TypeError):
                continue

            if kind == "収入":
                income_total += amount
            elif kind == "支出":
                expense_total += amount

        return income_total, expense_total
