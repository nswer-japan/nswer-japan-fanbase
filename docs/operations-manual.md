# NSWER JAPAN FB 運営マニュアル

## 基本方針

このサイトはGitHub Pages向けの静的サイトです。公開内容は `data/`、`assets/`、`templates/` を管理元とし、外部CMSや外部データベースには依存しません。

日常更新はGitHubのWeb編集、GitHub Mobile、またはローカルPCから行えます。YouTube公開動画だけはGitHub Actionsが公式チャンネルから自動取得します。取得に失敗しても、公開中の一覧を削除・空配列へ置換しません。

## 日常更新

1. 対象の `data/*.json` または `data/csv/*.csv` を編集する。
2. 画像が必要な場合は `assets/` の該当フォルダへ追加する。
3. `main`へ保存する。
4. `Build Repository Content` が自動実行される。
5. Actionsで `Check Site` が成功したことを確認する。

CSVを使う場合は、ローカルまたはActions環境で次を実行します。

```bash
python3 scripts/import-csv.py news
python3 scripts/build-content.py
```

## YouTube

- 6時間ごと：新着確認
- 毎週日曜：全履歴再確認
- 手動実行：Actionsの `Sync YouTube` で `full_history` をオン
- 対象：通常動画、Shorts、ライブ配信アーカイブ
- 失敗時：既存データを維持

## 全体更新

Actionsの `Sync All Site Data` は、YouTube取得、全生成、検査、コミットをまとめて実行します。全履歴を取り直す場合は `full_youtube_history` をオンにします。

## 主なフォルダ

| パス | 用途 |
|---|---|
| `data/` | サイト本文、記録、リンク、設定 |
| `data/csv/` | 表形式で更新するテンプレート |
| `assets/` | メンバー、ニュース、作品、ガイド画像 |
| `templates/` | 共通ヘッダー・フッター |
| `scripts/` | 生成、検査、YouTube取得、CSV取込 |
| `.github/workflows/` | 自動生成、YouTube、検査、外部リンク、全体更新 |
| `docs/` | 運営・更新マニュアル |

## 公開前確認

```bash
bash scripts/run-prepublish-checks.sh
```

以下を確認します。

- JSONの構文と必須データ
- 内部リンクと画像参照
- JavaScript／Python構文
- 音楽番組1位記録
- YouTube同期の失敗時保護
- ファンベース所有SNSリンクの残存
- 外部CMS関連の実行ファイルや設定が存在しないこと

## GitHub上書き時

古い同期ファイルがリポジトリに残ると、不要なActionsが表示されます。`DELETE_OLD_FILES_BEFORE_UPLOAD.md`に記載した旧ファイルを削除してから上書きしてください。
