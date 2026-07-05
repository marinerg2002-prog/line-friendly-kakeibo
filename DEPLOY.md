# クラウドデプロイ手順

PC を閉じても LINE が使えるようにするための手順です。  
**初心者向けには Render（無料）** をおすすめします。

---

## 全体の流れ

```
1. GitHub にコードをアップロード
2. Render で Web サービスを作成
3. 環境変数を設定（LINE トークン、スプレッドシート ID など）
4. デプロイ完了後、LINE の Webhook URL を更新
5. ngrok とローカルの Flask は不要になる
```

---

## 事前準備

### 必要なもの

- [GitHub](https://github.com/) アカウント
- [Render](https://render.com/) アカウント（GitHub でログイン可）
- すでに動いている LINE チャネルと Google スプレッドシート

### デプロイ用ファイル（すでにプロジェクトに含まれています）

| ファイル | 役割 |
|---------|------|
| `Procfile` | 本番サーバー（gunicorn）の起動コマンド |
| `render.yaml` | Render の設定（任意） |

---

## ステップ 1: GitHub にコードを上げる

### 1-1. GitHub でリポジトリを作成

1. GitHub にログイン
2. **New repository** をクリック
3. 名前例: `line-friendly-kakeibo`
4. **Create repository**

### 1-2. ローカルから push

PowerShell でプロジェクトフォルダへ移動：

```powershell
cd C:\Users\user\Desktop\line-friendly-kakeibo

git init
git add .
git commit -m "Initial commit: LINE家計簿アプリ"
git branch -M main
git remote add origin https://github.com/あなたのユーザー名/line-friendly-kakeibo.git
git push -u origin main
```

> **重要**: `.env` と `service_account.json` は `.gitignore` に入っているので GitHub には上がりません（安全です）。

---

## ステップ 2: service_account.json を環境変数用に変換

クラウドには `service_account.json` ファイルを置けないため、**環境変数** にします。

### 手順

1. `service_account.json` をメモ帳で開く
2. 中身を **1行** にする（改行を削除してつなげる）
   - または [jsonformatter.org](https://jsonformatter.org/json-minify) で Minify
3. できた1行 JSON をコピーしておく（後で Render に貼り付けます）

例（実際はもっと長い）：

```json
{"type":"service_account","project_id":"...","private_key":"-----BEGIN PRIVATE KEY-----\n..."}
```

この値を `GOOGLE_SERVICE_ACCOUNT_JSON` として設定します。

---

## ステップ 3: Render でデプロイ（おすすめ）

### 3-1. Web サービスを作成

1. [Render Dashboard](https://dashboard.render.com/) にログイン
2. **New +** → **Web Service**
3. GitHub リポジトリ `line-friendly-kakeibo` を選択
4. 以下を設定：

| 項目 | 値 |
|------|-----|
| Name | `line-friendly-kakeibo` |
| Region | Singapore（日本に近い） |
| Branch | `main` |
| Runtime | `Python 3` |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `gunicorn app:app --bind 0.0.0.0:$PORT` |
| Instance Type | **Free** |

### 3-2. 環境変数を設定

**Environment** セクションで **Add Environment Variable**：

| Key | Value |
|-----|-------|
| `LINE_CHANNEL_ACCESS_TOKEN` | LINE Developers のトークン |
| `LINE_CHANNEL_SECRET` | LINE Developers のシークレット |
| `SPREADSHEET_ID` | スプレッドシート ID |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | ステップ2でコピーした1行 JSON |
| `FLASK_DEBUG` | `False` |

### 3-3. デプロイ

**Create Web Service** をクリック。  
数分待つと **Live** になり、URL が表示されます：

```
https://line-friendly-kakeibo.onrender.com
```

ブラウザで開き、「サーバーは正常に動いています」と表示されれば OK。

---

## ステップ 4: LINE の Webhook URL を更新

1. [LINE Developers](https://developers.line.biz/) → 対象チャネル
2. **Messaging API** タブ
3. **Webhook URL** を変更：

```
https://line-friendly-kakeibo.onrender.com/callback
```

（Render で表示された URL + `/callback`）

4. **更新** → **検証** で「成功」を確認
5. **Webhookの利用** を **オン**

### もう不要になるもの

- ローカルの `python app.py`
- `ngrok`

---

## ステップ 5: 動作確認

LINE から以下を送信：

```
-580 カフェ
今月の家計
```

返信が来て、スプレッドシートに記録されれば完了です。

---

## Render 無料プランの注意点

| 項目 | 内容 |
|------|------|
| スリープ | 15分間アクセスがないとスリープ |
| 起動時間 | スリープ後の最初のメッセージは **30秒〜1分** かかることがある |
| 常時起動 | 無料では不可。有料プラン（月 $7〜）で常時起動 |

家計簿の用途なら、少し待っても使える無料プランで十分なことが多いです。

---

## Railway でデプロイする場合（代替）

1. [Railway](https://railway.app/) に GitHub でログイン
2. **New Project** → **Deploy from GitHub repo**
3. リポジトリを選択
4. **Variables** に Render と同じ環境変数を設定
5. **Settings** → **Networking** → **Generate Domain**
6. Webhook URL: `https://xxxx.up.railway.app/callback`

> Railway は無料枠に制限があり、クレジットカード登録が必要な場合があります。

---

## Google Cloud Run でデプロイする場合（上級者向け）

常時起動・安定性を重視する場合向け。手順が長いため概要のみ：

1. Google Cloud プロジェクト作成
2. Cloud Run API を有効化
3. `Dockerfile` を作成してコンテナ化
4. `gcloud run deploy` でデプロイ
5. 環境変数を Secret Manager で管理

初心者の最初のデプロイには **Render をおすすめ** します。

---

## よくあるエラー

| 症状 | 対処 |
|------|------|
| デプロイ失敗 | Render の **Logs** タブでエラー内容を確認 |
| LINE 検証失敗 | URL 末尾が `/callback` か、サービスが **Live** か確認 |
| スプレッドシート接続失敗 | `GOOGLE_SERVICE_ACCOUNT_JSON` が1行 JSON か確認 |
| 最初の返信が遅い | Render 無料プランのスリープ。2通目以降は速い |

---

## チェックリスト

- [ ] GitHub にコードを push（`.env` は含めない）
- [ ] Render で Web サービス作成
- [ ] 環境変数 5 つを設定
- [ ] デプロイ成功（Live 表示）
- [ ] LINE Webhook URL を `https://xxx.onrender.com/callback` に変更
- [ ] Webhook 検証が成功
- [ ] LINE から記録・集計が動く
