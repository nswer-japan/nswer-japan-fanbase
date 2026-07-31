# NSWER JAPAN FB データ更新マニュアル

## 管理元

サイトの内容はすべてリポジトリ内で管理します。

- JSON：細かい項目や多言語、リンク、画像を管理
- CSV：ニュース、スケジュール、音楽番組1位などを表形式で一括管理
- 画像：`assets/`へ保存

## 主なJSON

| ファイル | 内容 |
|---|---|
| `data/news.json` | ニュース |
| `data/schedule.json` | スケジュール |
| `data/members.json` | メンバー |
| `data/discography.json` | 作品、収録曲、配信・購入リンク |
| `data/records.json` | 音楽番組1位、Melon、Hanteo、その他記録 |
| `data/mv.json` | MVとYouTube取得結果 |
| `data/streaming-guide.json` | ストリーミングガイド |
| `data/voting-guide.json` | 投票ガイド |
| `data/chants.json` | 掛け声 |
| `data/official-links.json` | NMIXX公式、日本公式、公式FCのリンク |
| `data/homepage.json` | ホーム表示 |
| `data/site-theme.json` | NSWER標準デザイン |
| `data/comeback-themes.json` | カムバック別デザイン |

## CSV取込

```bash
python3 scripts/import-csv.py news
python3 scripts/import-csv.py schedule
python3 scripts/import-csv.py wins
python3 scripts/import-csv.py discography
python3 scripts/import-csv.py links
python3 scripts/import-csv.py updates
```

取込前に既存JSONは `data/backups/` へ保存されます。CSVが空、必須項目不足、例示行が残っている場合は既存JSONを変更しません。

## 画像

画像は期限付きURLを使わず、必ずリポジトリへ保存します。

- メンバー：`assets/members/`
- 集合写真：`assets/group/`
- 作品：`assets/discography/`
- ニュース：`assets/news/`
- ストリーミング：`assets/streaming/`
- 投票：`assets/voting/`

JSONにはリポジトリ内の相対パスを記載します。

## 更新後

```bash
python3 scripts/build-content.py
bash scripts/run-prepublish-checks.sh
```

GitHubのWeb編集で保存した場合は、Actionsが自動で生成と検査を行います。
