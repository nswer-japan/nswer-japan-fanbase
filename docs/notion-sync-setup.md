# NSWER JAPAN FB Notion同期設定

## 構成

NSWER用Notionは他サイト用環境とは別のワークスペース、Integration、Token、データソースIDで動作します。サイトのCSSやデザインは共有せず、同期・画像保存・失敗時保護の仕組みだけを同等にしています。

管理ページは `NSWER JAPAN FB 管理` です。データソースIDは `data/notion-config.json` に登録済みです。

## GitHubへ登録するSecret

GitHubリポジトリで次の順に開きます。

1. `Settings`
2. `Secrets and variables`
3. `Actions`
4. `New repository secret`

以下を登録します。

```text
Name: NSWER_NOTION_TOKEN
Secret: NSWER専用Notion IntegrationのInternal Integration Secret
```

他サイト用のTokenは使用しないでください。

## Notion側の共有

Notionの `NSWER JAPAN FB 管理` ページを開き、接続メニューからNSWER専用Integrationを追加します。親ページを共有すると、配下の管理データベースへアクセスできます。

## 同期の実行

GitHubの `Actions` から `Sync Notion Content` を選び、`Run workflow` を押します。通常は3時間ごとにも自動実行されます。

同期対象は次のとおりです。

- ニュース
- スケジュール
- メンバープロフィール
- ディスコグラフィ
- 音楽番組1位記録
- チャート・販売記録
- ストリーミング／投票／掛け声
- 公式リンク
- ホームページ表示
- サイトテーマ
- カムバックテーマ

## 安全設計

- Notionが空のデータベースは既存JSONを上書きしません。
- 一部のデータベース取得に失敗しても、成功したデータだけを反映します。
- 更新前JSONは `data/backups/notion/` へ最大10世代保存します。
- Notionへアップロードした画像は `assets/notion/` へ保存します。
- HEIC／HEIF画像はJPGへ変換します。
- ファンベース所有のX、Instagram、TikTok URLは公式リンク同期時にも除外します。
- サイトテーマとカムバックテーマはNSWER専用データベースのみを参照します。

## データソースを作り直した場合

通常はVariablesの登録は不要です。データベースを作り直してIDが変わった場合は、`data/notion-config.json` を更新するか、GitHub Actions Variablesへ `NSWER_NOTION_..._DATA_SOURCE_ID` を登録してください。Variablesが設定されている場合は、JSONよりVariablesが優先されます。

## 手動復旧

Notion同期に失敗しても、公開中のJSONは残ります。緊急時は `data/*.json` を直接編集して `Build Repository Content` を実行してください。
