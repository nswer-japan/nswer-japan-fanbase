# NSWER JAPAN FB 運営マニュアル

最終更新: 2026-07-27

## 1. このサイトの運営方式

NSWER JAPAN FBは、GitHub Pages向けの静的サイトです。日常更新はNSWER専用Notionから行い、同期後のJSON・画像・HTMLをGitHubリポジトリへ保存します。他サイト側とはワークスペース、Integration、Token、データソースID、テーマを分離しています。

NotionやYouTubeの取得に失敗しても、公開中のJSONを削除・空配列へ置換しないフェイルセーフ構成です。緊急時は従来どおり `data/*.json` またはCSVを直接編集できます。

更新の基本は次の流れです。

1. Notionの対象データベースを編集し、`公開` をオンにする。
2. Actionsの `Sync Notion Content` を実行する。通常は3時間ごとにも自動同期される。
3. YouTubeは `Sync YouTube` が6時間ごとに新着を確認し、毎週と手動実行時には全公開履歴を再取得する。
4. 同期後に生成・検査を行い、成功した内容だけをGitHub Pagesで公開する。
5. Notion障害時は `data/*.json` を直接編集し、`Build Repository Content` を実行する。

初回設定は `docs/notion-sync-setup.md` を確認してください。

## 2. 管理元と自動生成物

### 直接編集するもの

| 種類 | 場所 | 用途 |
|---|---|---|
| 基本データ | `data/*.json` | メンバー、ニュース、予定、作品、記録、ガイド、リンク、ホーム表示など |
| CSVテンプレート | `data/csv/*.csv` | ニュース、予定、音楽番組1位を表形式で一括更新 |
| 画像 | `assets/` | メンバー、作品、ニュース、投票、ストリーミング、OGP素材 |
| 共通部品 | `templates/` | 一部ページの共通ヘッダー・フッター |
| デザイン基礎 | `css/` | レイアウトやページ固有のスタイル |
| 動作 | `js/` | 表示、検索、言語、共有、お気に入りなど |

### 原則として直接編集しないもの

次のファイルは生成処理で上書きされます。修正は管理元JSON、テンプレート、または生成スクリプトへ行ってください。

- `data/*-data.js`
- `data/search-index.json`
- `data/seo-status.json`
- `data/nswer-schedule.ics`
- `articles/*.html`
- `music-show-wins.html`
- `melon-records.html`
- `hanteo-records.html`
- `assets/ogp/`
- `sitemap.xml`
- `robots.txt`
- `service-worker.js`
- `css/theme.css`

## 3. フォルダ構成

| フォルダ | 内容 |
|---|---|
| `.github/workflows/` | Notion同期、YouTube取得、自動生成、検査、全体同期、外部リンク検査 |
| `assets/members/` | メンバー画像 |
| `assets/discography/` | ジャケット画像 |
| `assets/news/` | ニュース画像 |
| `assets/voting/` | 投票アプリと手順画像 |
| `assets/streaming/` | ストリーミング手順画像 |
| `assets/group/` | グループ共通画像 |
| `assets/notion/` | Notionから期限付きURLを経由して保存した画像 |
| `data/` | 運営データと生成データ |
| `data/csv/` | CSV取込用テンプレート |
| `docs/` | 運営資料 |
| `scripts/` | Notion同期、生成、検査、YouTube自動取得、CSV取込 |
| `templates/` | 共通ヘッダー・フッター |

## 4. GitHub Pagesへの初回公開

### 4.1 上書き前の準備

既存リポジトリへ上書きする場合は、旧ファイルを残したまま追加しないでください。旧ページ、旧画像、旧Actionsが残る可能性があります。

安全な方法は次のどちらかです。

- 新しい空のリポジトリへアップロードする。
- 既存リポジトリの内容をローカルで新構成へ完全に置き換え、1回のコミットで更新する。

既存ドメインを使用する場合、現在の `CNAME` は `nswerjapan.jp` です。GitHub標準URLだけで運用する場合は、アップロード前に `CNAME` を削除します。

### 4.2 GitHub上書き用ZIPを使う手順

1. ZIPを展開する。
2. ZIP内のファイルとフォルダを、リポジトリのルートへ配置する。
3. `.github`、`.nojekyll`、`.gitignore` など、先頭がドットのファイルも含める。
4. 旧ファイルが残っていないことを確認する。
5. `main` ブランチへコミットする。
6. GitHubの `Settings` → `Pages` を開く。
7. `Build and deployment` を `Deploy from a branch` にする。
8. ブランチを `main`、フォルダを `/(root)` にする。
9. Actionsの `Check Site` が成功することを確認する。
10. 公開URLでスマートフォンとPCの主要ページを確認する。

## 5. 日常更新の標準手順

### 5.1 スマートフォンからJSONを編集する

1. GitHubで対象リポジトリを開く。
2. `data` フォルダから対象JSONを開く。
3. 鉛筆アイコンを押す。
4. 既存項目を複製し、内容を変更する。
5. カンマ、ダブルクォート、画像パスを確認する。
6. `Commit changes` を押す。
7. `Actions` → `Build Repository Content` → `Run workflow` を実行する。
8. 続いて `Check Site` の成功を確認する。

データまたは画像を通常のコミットで変更した場合、`Build Repository Content` は自動でも起動します。手動実行は、生成を確実にやり直したい場合に使用します。

### 5.2 PCで更新する

```bash
git pull
# dataやassetsを編集
bash scripts/run-prepublish-checks.sh
git add .
git commit -m "content: update news and schedule"
git push
```

生成処理が変更したファイルも一緒にコミットします。

### 5.3 画像だけ追加した場合

画像を追加しただけでは、その画像はページに表示されません。対応するJSONの `image`、`cover`、`previewImage` などへパスを登録し、生成処理を実行してください。

ファイル名は半角英数字とハイフンを推奨します。

例: `assets/news/heavy-serenade-release.jpg`

## 6. GitHub Actions

### Build Repository Content

用途: JSON、画像、テンプレート、スクリプトの変更から表示用ファイルを生成します。

主な処理:

- JSONから表示用JavaScriptを生成
- アクティブなカムバックテーマから `css/theme.css` を生成
- 音楽番組1位、Melon、Hanteoページを生成
- ニュース記事を生成
- 共通ヘッダー・フッターを同期
- 検索、SEO、OGP、サイトマップ、PWAを更新
- 検査後、生成物を自動コミット

Actions自身のコミットでは再生成ジョブを起動しないため、無限ループを防止しています。

### Sync YouTube

用途: NMIXX公式チャンネルの通常動画、Shorts、ライブ配信アーカイブを取得します。

実行:

- 6時間ごと: 直近分を確認し、全履歴アーカイブへ追加・更新
- 毎週日曜: 通常動画・Shorts・配信タブを上限なしで全件再取得
- 手動: `full_history` をオンにすると全公開履歴を再取得
- 初回: `historyComplete` が未完了なら、`Sync All Site Data` でも自動的に全履歴取得

安全策:

- 全履歴取得時は `--playlist-end` を使わず、各タブの最後まで取得する。
- 完全な新データができるまで既存JSONを書き換えない。
- 全取得に失敗した場合は前回データを維持する。
- 一部タブだけ失敗した場合は、前回の全履歴を残したまま成功分だけ更新する。
- 同じ動画IDは通常動画・Shorts・配信タブ間で重複させない。
- `historyComplete` と `lastFullSyncAt` で全履歴取得の完了状態を記録する。
- 24件ずつ追加表示するため、全動画を保存しても初期表示を重くしにくい。

初回アップロード時は `historyComplete: false` を検知して自動的に全履歴同期します。すぐに再取得したい場合はActionsで `Sync YouTube` を開き、`Run workflow` → `full_history: true` を実行してください。

### Check Site

用途: 公開前の読み取り専用検査です。

実行: `main` へのpush、Pull Request、手動。

検査内容:

- JSON構文
- 必須管理ファイル
- 内部リンクと画像参照
- 旧サイト固有語や対象外番組名の残存
- JavaScript、Node.jsスクリプト、Pythonの構文
- 生成処理、SEO、PWA

### Check External Links

用途: 公式サイト、SNS、ストア、YouTubeなどの外部リンクを定期確認します。

実行: 週1回、または手動。

結果:

- `data/external-link-report.json`
- `.external-link-issue.md`（Issue作成用の本文）

外部サイト側のアクセス制限により、実際には有効でも403などになる場合があります。レポートだけで削除せず、ブラウザでも確認してください。

### Sync All Site Data

用途: YouTube取得、全生成、全検査、コミットを1回で行います。

実行: 毎日1回、または手動。

YouTubeが失敗しても前回データを使って残りの生成・検査を続行します。

## 7. 自動更新に失敗した場合

### 7.1 JSON編集後にBuildが失敗

よくある原因:

- 項目間のカンマ不足
- 末尾の不要なカンマ
- ダブルクォートの閉じ忘れ
- 存在しない画像パス
- `slug` や `id` の重複
- 日付形式の誤り

Actionsログの最初のエラーを確認し、該当JSONを修正して再実行します。公開済みサイトは、最後に成功した状態を維持します。

### 7.2 YouTubeだけ失敗

前回の `data/youtube-channels.json` は消えません。まず `Sync YouTube` を手動で再実行します。継続的に失敗する場合は、データ更新マニュアルの「YouTube手動更新」を使用します。

### 7.3 生成物だけ壊れた

管理元JSONが正しければ、次を実行して再生成します。

```bash
python3 scripts/build-content.py
bash scripts/run-prepublish-checks.sh
```

生成物だけを個別修正しないでください。次回生成で上書きされます。

### 7.4 CSV取込を間違えた

CSV取込前のJSONは `data/backups/` に自動保存されます。このフォルダはGit管理対象外です。誤って置き換えた場合はバックアップを元のJSONへ戻します。

## 8. テーマ運用

### サイト全体の基本色

`data/site-theme.json` の `theme` を編集します。ここにはダーク表示、ライト表示、文字、カード、アクセントの基本色があります。

### カムバック別テーマ

`data/comeback-themes.json` にカムバックごとのテーマを登録し、`activeTheme` に使用する `key` を指定します。

```json
{
  "activeTheme": "heavy-serenade",
  "themes": [
    {
      "key": "heavy-serenade",
      "name": "Heavy Serenade",
      "colors": {
        "background": "#070a14",
        "primary": "#7382ff",
        "secondary": "#ff6ea8",
        "accent": "#75e4d4"
      }
    }
  ]
}
```

生成すると `css/theme.css`、各ページのブラウザテーマ色、`manifest.webmanifest` のPWAテーマ色が更新されます。元へ戻す場合は `activeTheme` を `default` にします。

## 9. 多言語表示

表示切替は `js/i18n.js` が担当します。日本語を基準に、韓国語と英語の固定UI辞書を持ち、動的データも表示言語に合わせて処理します。

新しい固定見出しやボタンを追加した場合は、3言語分の辞書キーも追加してください。人名、作品名、外部サイト名など、翻訳しない固有名詞は共通表記で構いません。

## 10. SEO・OGP・PWA

`python3 scripts/build-content.py` で次を更新します。

- canonical URL
- robots指定
- OGPとXカード
- WebSite、Organization、WebPage、NewsArticle、BreadcrumbList構造化データ
- `sitemap.xml`
- `robots.txt`
- ページ別1200×630 OGP画像
- `manifest.webmanifest`
- `service-worker.js`
- `data/seo-status.json`

ニュース記事のOGPは、ニュースJSONの画像とタイトルから生成します。公開前にOGP画像が `assets/ogp/` に作成されているか確認してください。

## 11. バックアップと復元

推奨:

- 大きな更新前にGitHubでブランチを作る。
- リリース前のコミットへタグを付ける。
- ZIP完全版をローカルにも保管する。
- CSV取込前は自動バックアップの作成を確認する。

GitHub上で問題が起きた場合は、正常だったコミットをRevertするか、そのコミットのファイルを復元します。

## 12. 公開前チェックリスト

- サイト名が `NSWER JAPAN FB` になっている。
- メンバーが6人で、誕生日と画像が正しい。
- デビュー記念日が2月22日になっている。
- 新しいニュース記事が開ける。
- スケジュールの時刻とカレンダー登録が正しい。
- 作品の曲順とストアリンクが正しい。
- 音楽番組1位、Melon、Hanteoの件数が意図どおり。
- 対象外番組や不要アプリが表示されない。
- スマートフォンで横スクロールや画像切れがない。
- 日本語、韓国語、英語の切替が動く。
- ダーク、ライト、端末連動が動く。
- 検索、お気に入り、共有が動く。
- `Check Site` が成功している。
- GitHub Pagesの公開URLで404や古いページが残っていない。

## 13. リリース後の確認

GitHub Pages反映後は、最低限次のページを実機で確認してください。

- `index.html`
- `members.html`
- `news.html` と最新記事
- `schedule.html`
- `discography.html`
- `records.html`
- `streaming.html`
- `voting.html`
- `youtube.html`
- `search.html`
- `offline.html`

ブラウザキャッシュで旧表示が残る場合は、再読み込み、サイトデータ削除、またはPWAの再インストールを行います。
