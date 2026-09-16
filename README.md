# 澄屋 | 清掃サービス見積アプリ

一般のお客様がスマートフォンから清掃サービスを選び、その場で料金を確認して見積依頼できるWebアプリです。

現段階ではデータベース、ログイン、決済、外部APIは接続していません。見積依頼はブラウザ内（localStorage）に保存し、確認画面を表示します。

## できること

- 8つの清掃サービスを 0〜10 個まで選択
- ＋ / − ボタンで数量を変更
- 数量変更と同時に小計・合計金額をリアルタイム計算
- 選択中のサービス、数量、小計、合計の確認
- お客様情報（名前、電話番号、メールアドレス、住所、希望作業日、備考）の入力
- 見積依頼後の受付内容確認

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

- Node.js 20 以上
- npm 10 以上（Node.js に同梱）

## ローカルでの起動方法

リポジトリを取得して依存関係をインストールします。

```bash
git clone https://github.com/willdamy325-ai/cleaning-estimate-app.git
cd cleaning-estimate-app
npm install
```

開発サーバーを起動します。

```bash
npm run dev
```

ブラウザで [http://localhost:3000](http://localhost:3000) を開きます。

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
  application/quoteService.ts     # 見積のユースケース
  domain/                         # 料金カタログ、計算、入力チェック
  infrastructure/repositories/    # 保存口（いまは localStorage）
  components/                     # UI部品
  features/quote/                 # 見積フロー画面
```

差し替え想定:

- `src/domain/catalog.ts` … サービス・料金マスタ。将来はDBから取得
- `src/infrastructure/repositories/quoteRepository.ts` … 保存インターフェース。API実装に交換
- `src/application/quoteService.ts` … 予約作成、顧客登録、通知、AI提案などを追加する場所

## 使っている技術

- Next.js 15（App Router）
- React 19
- TypeScript
- Tailwind CSS
- Vitest

## 今後の拡張で追加しないもの（現段階）

実装していません。

- データベース接続
- ログイン / 会員機能
- 決済
- 外部API / MCP / AI Agent の実行
