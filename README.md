# NSWER JAPAN FB

NMIXXを日本から応援する非公式ファンベースサイトです。GitHub Pagesへそのまま公開できる静的サイトとして構成しています。

## 運営方針

公開内容の唯一の管理元は、このリポジトリ内の `data/*.json`、`data/csv/*.csv`、`assets/` です。外部CMSや外部データベースは使用しません。

見た目、配色、文章、画像はNSWER JAPAN FB専用です。一方で、安定運営に必要な自動生成、検索、SEO、OGP、PWA、外部リンク検査、更新状況ページ、失敗時保護などは高機能ファンベースサイトと同等の構成にしています。

## 主な機能

- 日本語／韓国語／英語の表示切替
- スマートフォン対応、ダーク／ライト表示、サイト内検索、お気に入り、共有
- SEO、ページ別OGP、構造化データ、サイトマップ、PWA、オフライン画面
- 公式YouTubeの通常動画・Shorts・ライブ配信アーカイブを全履歴取得
- YouTube取得失敗時も前回の公開データを維持
- 音楽番組1位、Melon、Hanteo、ニュース、ディスコグラフィを静的ページへ自動生成
- JSON／CSV／画像だけで更新できるリポジトリ完結型運用
- GitHub Actionsによる生成、検査、外部リンク確認、全体更新

## 最初に読むファイル

- `docs/operations-manual.md`: 公開、日常運営、Actions、障害対応
- `docs/data-update-manual.md`: JSON／CSVの項目と更新例
- `docs/feature-parity.md`: 高機能サイトとして維持している機能一覧
- `docs/migration-and-test-report.md`: 構成、移行方針、検査内容
- `docs/image-assets-guide.md`: 画像の差し替えルール
- `docs/youtube-full-sync.md`: YouTube全履歴取得の実行方法と安全設計
- `DELETE_OLD_FILES_BEFORE_UPLOAD.md`: 既存リポジトリへ上書きする際の削除対象

## 基本コマンド

```bash
python3 scripts/build-content.py
bash scripts/run-prepublish-checks.sh
python3 scripts/import-csv.py news
```

Python 3.12、Node.js 22、Pillowを推奨します。YouTube取得をローカルで行う場合は、JavaScript対応を含む最新の `yt-dlp[default]` が必要です。
