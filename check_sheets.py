"""
Google スプレッドシート接続の診断スクリプト

使い方: python check_sheets.py
"""

import json
from pathlib import Path

import gspread

from config import Config

TARGET_ID = Config.get_spreadsheet_id()


def main():
    key_path = Path(Config.GOOGLE_SERVICE_ACCOUNT_FILE)
    with key_path.open(encoding="utf-8") as file:
        sa = json.load(file)

    email = sa["client_email"]
    project = sa["project_id"]

    print("=== Google スプレッドシート接続診断 ===")
    print()
    print(f"サービスアカウント: {email}")
    print(f"GCP プロジェクト:   {project}")
    print(f"設定中の ID:        {TARGET_ID}")
    print()

    client = gspread.service_account(filename=str(key_path))
    files = client.list_spreadsheet_files()

    print(f"アクセス可能なスプレッドシート: {len(files)} 件")
    if files:
        for file in files:
            mark = " <- 設定中" if file["id"] == TARGET_ID else ""
            print(f"  - {file['name']}  (ID: {file['id']}){mark}")
    else:
        print("  （なし）")

    print()

    if not files:
        print("【判定】サービスアカウントがアクセスできるスプレッドシートがありません。")
        print()
        print("次の手順を実行してください：")
        print("1. Google スプレッドシートを開く")
        print("2. 右上の「共有」をクリック")
        print("3. 次のメールアドレスを「編集者」として追加:")
        print(f"   {email}")
        print("4. 「送信」をクリック")
        print("5. このスクリプトを再実行: python check_sheets.py")
        return

    found = any(f["id"] == TARGET_ID for f in files)
    if not found:
        print("【判定】設定中の SPREADSHEET_ID が間違っています（typo の可能性）。")
        print()
        print("対処法: .env の SPREADSHEET_ID を上記一覧の ID に修正してください。")
        return

    spreadsheet = client.open_by_key(TARGET_ID)
    print(f"【成功】接続 OK: 「{spreadsheet.title}」")


if __name__ == "__main__":
    main()
