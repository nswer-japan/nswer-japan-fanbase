# NSWER JAPAN FB

NMIXXを日本から応援する非公式ファンベースサイトです。GitHub Pagesへそのまま公開できる静的サイトとして構成しています。

## 特徴

- 管理元はリポジトリ内のJSON・CSV・画像
- 日本語／韓国語／英語の表示切替
- スマートフォン対応、ダーク／ライト表示、サイト内検索、お気に入り、共有
- SEO、ページ別OGP、構造化データ、サイトマップ、PWA、オフライン画面
- 公式YouTubeチャンネルの公開コンテンツをGitHub Actionsで自動取得
- 自動取得失敗時も前回データを維持
- 音楽番組1位、Melon、Hanteo、ニュース記事などを静的ページへ自動生成

## 最初に読むファイル

- `docs/運営マニュアル.md`: 公開、日常運営、Actions、障害対応
- `docs/データ更新マニュアル.md`: 各JSON／CSVの項目と更新例
- `docs/移行設計・検査レポート.md`: 構成比較、移行方針、検査内容
- `DELETE_OLD_FILES_BEFORE_UPLOAD.md`: 既存リポジトリへ上書きする際の注意

## 基本コマンド

```bash
# JSONから表示用ファイルを生成
python3 scripts/build-content.py

# 生成・構文・リンク・画像・禁止文字列をまとめて検査
bash scripts/run-prepublish-checks.sh

# CSVをJSONへ取り込む例
python3 scripts/import-csv.py news
```

Python 3.12、Node.js 22、Pillowが推奨環境です。YouTube取得をローカルで行う場合のみ `yt-dlp` が必要です。
