# やさしい家計簿

LINE のトーク画面だけで、収入・支出を記録し、今月の家計状況を確認できる家計簿ツールです。  
黒字なら褒め、赤字でもやさしい言葉で返信します。

---

## 1. 全体構成

```
ユーザー（LINE）
    ↓ メッセージ送信（+250000 給料 など）
LINE Platform
    ↓ Webhook（POST /callback）
Flask（app.py）
    ↓
line_service.py … メッセージ受信・返信
    ↓
kakeibo_logic.py … 解析・カテゴリ分類・褒め/やさしいメッセージ生成
    ↓
sheet_service.py … Google スプレッドシートへ保存・集計
    ↓
Google スプレッドシート（データ保存）
```

| ファイル | 役割 |
|---------|------|
| `app.py` | Flask サーバー。Webhook エンドポイント `/callback` を提供 |
| `config.py` | `.env` から環境変数を読み込む |
| `line_service.py` | LINE API とのやり取り（受信・返信） |
| `sheet_service.py` | Google スプレッドシートへの保存・集計 |
| `kakeibo_logic.py` | 家計簿のロジック（解析・分類・メッセージ生成） |

---

## 2. 必要なファイル一覧

```
line-friendly-kakeibo/
├─ app.py                 # メインアプリ（Flask）
├─ config.py              # 設定読み込み
├─ line_service.py        # LINE 連携
├─ sheet_service.py       # スプレッドシート連携
├─ kakeibo_logic.py       # 家計簿ロジック
├─ requirements.txt       # Python パッケージ一覧
├─ .env.example           # 環境変数のサンプル
├─ .env                   # 実際の環境変数（自分で作成）
├─ service_account.json   # Google サービスアカウント鍵（自分で取得）
└─ README.md              # このファイル
```

---

## 3. 各ファイルのコード

コードはリポジトリ内の各 `.py` ファイルに記載されています。

- **kakeibo_logic.py** … `+金額 内容` / `-金額 内容` の解析、カテゴリ自動分類、褒め・やさしいメッセージ
- **sheet_service.py** … スプレッドシートへの追記、今月の収入・支出集計
- **line_service.py** … Webhook 処理、LINE への返信
- **app.py** … Flask 起動、`/callback` エンドポイント

---

## 4. Google スプレッドシート側で準備すること

### 4-1. スプレッドシートを作成

1. [Google スプレッドシート](https://sheets.google.com/) を開く
2. 「空白」をクリックして新規作成
3. 1行目に以下のヘッダーを入力（アプリが自動で作る場合もあります）

   | A | B | C | D | E |
   |---|---|---|---|---|
   | 日付 | 区分 | 内容 | 金額 | カテゴリ |

4. ブラウザの URL から **スプレッドシート ID** をコピー  
   `https://docs.google.com/spreadsheets/d/【ここがID】/edit`

### 4-2. Google Cloud でサービスアカウントを作成

1. [Google Cloud Console](https://console.cloud.google.com/) にアクセス
2. 新しいプロジェクトを作成（または既存を選択）
3. **API とサービス** → **ライブラリ** で以下を有効化
   - Google Sheets API
   - Google Drive API
4. **API とサービス** → **認証情報** → **認証情報を作成** → **サービスアカウント**
5. サービスアカウントを作成後、**キー** タブ → **鍵を追加** → **JSON**
6. ダウンロードした JSON を `service_account.json` としてプロジェクトフォルダに置く

### 4-3. スプレッドシートをサービスアカウントと共有

1. `service_account.json` 内の `client_email`（例: `xxx@xxx.iam.gserviceaccount.com`）をコピー
2. スプレッドシートの **共有** ボタンをクリック
3. そのメールアドレスを **編集者** として追加

---

## 5. LINE Developers 側で準備すること

### 5-1. チャネル作成

1. [LINE Developers](https://developers.line.biz/) にログイン
2. **プロバイダー** を作成（初回のみ）
3. **新規チャネル作成** → **Messaging API** を選択
4. 必要事項を入力してチャネルを作成

### 5-2. 必要な値を取得

**Messaging API** タブで以下を確認・設定：

| 項目 | 用途 | 設定場所 |
|------|------|----------|
| チャネルシークレット | Webhook 署名検証 | `.env` の `LINE_CHANNEL_SECRET` |
| チャネルアクセストークン | メッセージ返信 | `.env` の `LINE_CHANNEL_ACCESS_TOKEN` |

- **チャネルアクセストークン** は「発行」ボタンで取得

### 5-3. Webhook 設定（ngrok 起動後に行う）

1. **Webhook URL** に `https://xxxx.ngrok-free.app/callback` を設定（後述）
2. **Webhookの利用** を **オン**
3. **応答メッセージ** を **オフ**（Bot が返信するため）
4. **あいさつメッセージ** も **オフ** 推奨

### 5-4. 友だち追加

1. **Messaging API** タブの **QRコード** をスマホの LINE で読み取り
2. 公式アカウントを友だち追加

---

## 6. ローカルで実行する手順

### 6-1. Python のインストール

[Python 公式サイト](https://www.python.org/downloads/) から Python 3.10 以上をインストール。  
インストール時に **「Add Python to PATH」** にチェックを入れてください。

### 6-2. プロジェクトのセットアップ

```powershell
# プロジェクトフォルダへ移動
cd C:\Users\user\Desktop\line-friendly-kakeibo

# 仮想環境を作成（推奨）
python -m venv venv

# 仮想環境を有効化（Windows PowerShell）
.\venv\Scripts\Activate.ps1

# パッケージをインストール
pip install -r requirements.txt
```

### 6-3. 環境変数ファイルを作成

```powershell
# .env.example をコピーして .env を作成
copy .env.example .env
```

`.env` をテキストエディタで開き、実際の値を入力：

```env
LINE_CHANNEL_ACCESS_TOKEN=（LINE Developers で取得したトークン）
LINE_CHANNEL_SECRET=（LINE Developers のチャネルシークレット）
GOOGLE_SERVICE_ACCOUNT_FILE=service_account.json
SPREADSHEET_ID=（スプレッドシートの ID）
FLASK_PORT=5000
FLASK_DEBUG=True
```

### 6-4. サーバー起動

```powershell
python app.py
```

ブラウザで `http://localhost:5000` を開き、「サーバーは正常に動いています」と表示されれば OK です。

---

## 7. ngrok を使って LINE の Webhook URL に設定する手順

LINE はインターネット上の HTTPS URL しか Webhook に設定できないため、ローカル PC を一時的に公開する **ngrok** を使います。

### 7-1. ngrok のインストール

1. [ngrok 公式サイト](https://ngrok.com/) でアカウント作成
2. [ダウンロードページ](https://ngrok.com/download) から Windows 版をインストール
3. ダッシュボードの **Authtoken** をコピーし、以下を実行：

```powershell
ngrok config add-authtoken あなたのAuthtoken
```

### 7-2. ngrok でトンネルを開く

**別の PowerShell ウィンドウ** を開き（`app.py` は起動したまま）：

```powershell
ngrok http 5000
```

表示例：

```
Forwarding  https://abc123.ngrok-free.app -> http://localhost:5000
```

### 7-3. LINE Developers に Webhook URL を設定

1. LINE Developers → 対象チャネル → **Messaging API**
2. **Webhook URL** に以下を入力（末尾は `/callback` 必須）  
   `https://abc123.ngrok-free.app/callback`
3. **更新** → **検証** ボタンで「成功」と出れば OK
4. **Webhookの利用** を **オン** にする

> **注意**: ngrok 無料版は起動のたびに URL が変わります。URL が変わったら LINE Developers の Webhook URL も更新してください。

---

## 8. 動作確認の方法

### 8-1. 収入・支出の記録

LINE で Bot に以下を送信：

```
+250000 給料
+3200 メルカリ
-2450 スーパー
-580 カフェ
```

期待される返信例：

```
支出を記録しました！

内容：スーパー
金額：2,450円
カテゴリ：食費
```

スプレッドシートに行が追加されていることも確認してください。

### 8-2. 今月の家計

```
今月の家計
```

期待される返信例（黒字の場合）：

```
今月の家計状況です。

収入：253,200円
支出：3,030円
残り：250,170円

今月は大きく黒字です！
収入も支出もきちんと記録できています。
この調子で、無理なく家計管理を続けられています。
```

### 8-3. 入力形式エラー

```
250000 給料
```

（先頭に `+` がない場合）→ 入力形式の案内メッセージが返る

### 8-4. ローカルでロジックだけ試す（任意）

```powershell
python -c "from line_service import process_message; print(process_message('+1000 お祝い'))"
```

---

## 9. よく起きるエラーと対処法

| エラー・症状 | 原因 | 対処法 |
|-------------|------|--------|
| `Invalid signature` | チャネルシークレットが間違っている | `.env` の `LINE_CHANNEL_SECRET` を再確認 |
| Bot が返信しない | Webhook がオフ / URL が間違い | LINE Developers で Webhook をオン、URL が `/callback` 付きか確認 |
| `SpreadsheetNotFound` / `<Response [404]>` | スプレッドシート ID 間違い、または **サービスアカウント未共有** | `.env` の ID を確認。**共有** に `service_account.json` の `client_email` を **編集者** として追加（404 でも権限不足のことが多い） |
| `PermissionError`（Google） | サービスアカウントに共有していない | スプレッドシートを `client_email` に編集者として共有 |
| `FileNotFoundError: service_account.json` | JSON 鍵ファイルがない | Google Cloud から鍵をダウンロードし、プロジェクトフォルダに配置 |
| ngrok 検証が失敗 | Flask が起動していない | `python app.py` を先に起動してから ngrok と検証 |
| ngrok URL が変わった | 無料版の仕様 | 新 URL を LINE Webhook に再設定 |
| `ModuleNotFoundError` | パッケージ未インストール | `pip install -r requirements.txt` を実行 |
| PowerShell で venv が有効化できない | 実行ポリシーの制限 | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` を実行 |

### デバッグのヒント

- Flask 起動中のターミナルにエラーが出ていないか確認
- LINE Developers の **Webhook** → **検証** で接続テスト
- スプレッドシートに手動で1行書いて、サービスアカウントの共有が効いているか確認

---

## 入力ルール（参考）

| 形式 | 例 | 判定 |
|------|------|------|
| `+金額 内容` | `+250000 給料` | 収入 |
| `-金額 内容` | `-2450 スーパー` | 支出 |
| `今月の家計` | `今月の家計` | 今月の集計 |

## カテゴリ自動分類（参考）

| 内容キーワード | カテゴリ |
|---------------|---------|
| 給料 | 給料 |
| メルカリ、お祝い | 臨時収入 |
| スーパー、カフェ | 食費 |
| 電車 | 交通費 |
| Amazon | 日用品 |
| 映画 | 娯楽費 |
| それ以外 | その他 |

---

## ライセンス

個人学習・利用を想定したサンプルプロジェクトです。
