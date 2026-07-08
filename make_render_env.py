"""
Render 用の環境変数を確認・生成するスクリプト

使い方: python make_render_env.py
"""
import json
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from config import Config  # noqa: E402

key_path = Path("service_account.json")
json_one_line = json.dumps(json.loads(key_path.read_text(encoding="utf-8")), ensure_ascii=False)

print("=== Render に設定する環境変数 ===")
print()
print("【SPREADSHEET_ID】以下をコピー")
print(Config.get_spreadsheet_id())
print()
print("【GOOGLE_SERVICE_ACCOUNT_JSON】文字数:", len(json_one_line))
print("（長いのでクリップボードにコピーするか、Render の Secret File を検討）")
print()
print("【確認ポイント】")
print("- SPREADSHEET_ID の「Zi6」は小文字の i（大文字 I ではない）")
print("- GOOGLE_SERVICE_ACCOUNT_JSON は1行 JSON（改行なし）")
print("- Render に SPREADSHEET_URL は不要（SPREADSHEET_ID だけでOK）")
print()
print("JSON をファイルに保存しました: render_service_account_oneline.txt")
Path("render_service_account_oneline.txt").write_text(json_one_line, encoding="utf-8")
