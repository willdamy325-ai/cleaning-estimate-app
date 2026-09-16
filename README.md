# 澄屋 | 清掃サービス見積アプリ

一般のお客様がスマートフォンから清掃サービスを選び、その場で料金を確認して見積依頼できるWebアプリです。

## できること

- 8つの清掃サービスを 0〜10 個まで選択
- ＋ / − ボタンで数量を変更
- 数量変更と同時に小計・合計金額をリアルタイム計算
- 選択中のサービス、数量、小計、合計の確認
- お客様情報（名前、電話番号、メールアドレス、住所、希望作業日、備考）の入力
- 見積依頼後の受付内容確認
- 見積依頼を Neon Postgres へ永続保存
- Resend を使った管理者への新規依頼メール通知
- 認証付き管理画面で依頼一覧・詳細を確認
- 対応ステータス（新規・連絡済み・予約確定・完了・キャンセル）の更新

## 料金

| サービス | 料金 |
| --- | ---: |
| 通常エアコン | 7,000円 |
| お掃除機能付きエアコン | 12,000円 |
| 浴室 | 12,000円 |
| 洗面所 | 6,000円 |
| レンジフード | 12,000円 |
| キッチン | 12,000円 |
| トイレ | 6,000円 |
| 洗濯機 | 20,000円 |

## 必要環境

- Node.js 20.9 以上
- npm 10 以上（Node.js に同梱）

## ローカルでの起動方法

リポジトリを取得して依存関係をインストールします。

```bash
git clone https://github.com/willdamy325-ai/cleaning-estimate-app.git
cd cleaning-estimate-app
npm install
```

`.env.example` を参考に `.env.local` を作成し、後述の環境変数を設定します。Neon の SQL Editor で `database/schema.sql` を実行してから、開発サーバーを起動します。

```bash
npm run dev
```

ブラウザで [http://localhost:3000](http://localhost:3000) を開きます。

管理画面は [http://localhost:3000/admin](http://localhost:3000/admin) です。

本番相当のビルド確認は次のコマンドです。

```bash
npm run build
npm start
```

単体テスト（料金計算・入力チェック）は次のコマンドです。

```bash
npm test
```

## 構成

後からデータベース、予約管理、顧客管理、外部API、MCP、AI Agent を追加しやすいよう、層を分けています。

```
src/
  app/                            # 画面ルート（Next.js App Router）
  app/api/                        # 見積保存・管理者認証・ステータス更新API
  application/quoteService.ts     # 見積のユースケース
  domain/                         # 料金カタログ、計算、入力チェック
  infrastructure/                 # Neon、Resend、認証、リポジトリ
  components/                     # UI部品
  features/quote/                 # 見積フロー画面
database/
  schema.sql                      # Neonへ適用するテーブル定義
```

## 使っている技術

- Next.js 16（App Router）
- React 19
- TypeScript
- Tailwind CSS
- Vitest
- Neon Serverless Postgres
- Resend Email API

## Vercel・外部サービスの設定

### 1. Neon Postgres

Neon は Vercel Marketplace から利用できるサーバーレス Postgres です。無料枠から開始できます。

1. Vercel Dashboard で対象プロジェクトを開く
2. `Storage` または `Marketplace` から **Neon** を追加
3. `Create New Neon Account` と Free プランを選び、対象プロジェクトへ接続
4. Neon Dashboard の `SQL Editor` を開く
5. `database/schema.sql` の内容を貼り付けて実行
6. Vercel の Environment Variables に `DATABASE_URL` が追加されていることを確認

既存の Neon を使う場合は、接続文字列を `DATABASE_URL` に設定します。`POSTGRES_URL` も代替名として利用できます。

### 2. Resend メール通知

Resend は Vercel Marketplace と連携でき、無料枠から開始できます。

1. Vercel Marketplace から **Resend** を追加
2. アカウントを作成し、対象プロジェクトへ接続
3. Resend で送信元ドメインを追加し、案内された DNS レコードを設定
4. ドメインが `Verified` になったことを確認
5. `RESEND_API_KEY` が Vercel に追加されていることを確認
6. `EMAIL_FROM` と `ADMIN_NOTIFICATION_EMAIL` を設定

`EMAIL_FROM` には検証済みドメインのアドレス（例: `澄屋 <notification@example.com>`）を指定します。

### 3. 管理画面認証

管理画面は単一管理者向けの環境変数認証です。ログイン成功後は、署名付き・HttpOnly・SameSite Cookie を8時間だけ保持します。

安全な値はローカル端末で生成できます。

```bash
openssl rand -base64 32  # ADMIN_PASSWORD 用
openssl rand -hex 32     # ADMIN_SESSION_SECRET 用
```

生成した値を Vercel の Environment Variables に設定してください。値をリポジトリへコミットしないでください。

### 必要な Environment Variables

| 変数名 | 必須 | 内容 |
| --- | --- | --- |
| `DATABASE_URL` | 必須 | Neon の接続文字列（Marketplace連携時は自動設定） |
| `RESEND_API_KEY` | 通知に必須 | Resend APIキー（Marketplace連携時は自動設定） |
| `EMAIL_FROM` | 通知に必須 | 検証済みドメインの送信元 |
| `ADMIN_NOTIFICATION_EMAIL` | 通知に必須 | 通知先。複数の場合はカンマ区切り |
| `ADMIN_USERNAME` | 必須 | 管理画面のユーザー名 |
| `ADMIN_PASSWORD` | 必須 | 十分に長いランダムなパスワード |
| `ADMIN_SESSION_SECRET` | 必須 | Cookie署名用の32文字以上のランダム値 |
| `APP_URL` | 推奨 | 本番URL。通知メールの管理画面リンクに使用 |

設定後は Vercel で再デプロイしてください。Production・Preview・Development のうち、利用する環境それぞれに値を設定します。

## 管理画面

本番URLの `/admin`（例: `https://example.com/admin`）へアクセスし、`ADMIN_USERNAME` と `ADMIN_PASSWORD` でログインします。

- 見積依頼は新しい順に表示
- 各依頼からサービス、数量、小計、合計、お客様情報を確認
- ステータスを選ぶと即時保存
- 電話番号とメールアドレスから直接連絡可能

## 動作確認

```bash
npm test
npm run lint
npm run build
```

実際の保存・メール通知を確認する場合は、Neon と Resend の環境変数を設定して次を確認します。

1. トップページでサービスとお客様情報を入力して送信
2. 完了画面に受付番号と依頼内容が表示される
3. Neon の `quote_requests` テーブルに行が追加される
4. 管理者メールに通知が届く
5. `/admin` にログインし、依頼の詳細とステータス更新を確認
