# NSWER JAPAN FB データ更新マニュアル

最終更新: 2026-07-26

## 1. Notion更新を優先する

通常の更新は、Notionの `NSWER JAPAN FB 管理` 配下にある対象データベースで行います。項目を入力して `公開` をオンにした後、GitHub Actionsの `Sync Notion Content` を実行してください。

Notionが空、権限不足、通信エラーの場合は既存JSONを維持します。緊急時や一括修正では、以下のJSON編集方法を使用できます。設定方法は `docs/notion-sync-setup.md` を参照してください。

## 2. JSON編集の共通ルール

- 文字列は半角のダブルクォート `"` で囲む。
- 配列の各項目、オブジェクトの各項目の間にカンマを入れる。
- 最後の項目の後にはカンマを付けない。
- 改行を含めたい場合は `\n` を使う。
- 画像パスは原則 `assets/` から始める。
- 内部ページは `news.html` のような相対URLにする。
- 外部リンクは `https://` から入力する。
- 同じ配列内で `slug`、`id`、`anchor` を重複させない。
- `generatedAt` と `source` は既存値のままでもよい。CSV取込時は自動更新される。

編集後は次を実行します。

```bash
python3 scripts/build-content.py
bash scripts/run-prepublish-checks.sh
```

GitHubだけで作業する場合はActionsの `Build Repository Content` と `Check Site` を実行します。

## 3. 管理ファイル早見表

| 内容 | 管理元 | 表示先 |
|---|---|---|
| メンバープロフィール | `data/members.json` | `members.html` |
| ニュース | `data/news.json` | `news.html`、`articles/*.html` |
| スケジュール | `data/schedule.json` | `schedule.html`、ICS |
| ディスコグラフィ | `data/discography.json` | `discography.html` |
| MV | `data/mv.json` | `mv.html` |
| 音楽番組1位 | `data/records.json` | `music-show-wins.html` |
| Melon記録 | `data/records.json` | `melon-records.html` |
| Hanteo記録 | `data/records.json` | `hanteo-records.html` |
| その他チャート | `data/records.json` | `records.html` |
| ストリーミング | `data/streaming-guide.json` | `streaming.html` |
| 投票 | `data/voting-guide.json` | `voting.html` |
| 掛け声 | `data/chants.json` | `chants.html` |
| 公式リンク | `data/official-links.json` | `links.html`、共通表示 |
| ホーム表示 | `data/homepage.json` | `index.html` |
| 基本テーマ | `data/site-theme.json` | 全ページ |
| カムバックテーマ | `data/comeback-themes.json` | 全ページ |
| YouTube | `data/youtube-channels.json` | `youtube.html` |
| グループ紹介 | `data/about.json` | `about.html` |
| 連絡先 | `data/contact.json` | `contact.html` |

## 4. メンバープロフィール

管理元: `data/members.json` の `members`

主な項目:

| 項目 | 内容 |
|---|---|
| `slug` | 半角英小文字の識別子。例: `lily` |
| `name` | 英字表記 |
| `koreanName` | 韓国語表記 |
| `japaneseName` | 日本語表記 |
| `birthDate` | `YYYY-MM-DD` |
| `birthDateLabel` | 画面表示用の誕生日 |
| `birthPlace` | 出生地 |
| `realName` | 本名 |
| `shortDescription` | 一覧用の短い紹介 |
| `profile` | 詳細紹介 |
| `colorName` / `colorCode` | メンバーカラー表示 |
| `previewImage` | 一覧画像 |
| `detailImage` | 詳細画像 |
| `desktopImage` | PC表示向け画像。省略時は他画像を使用 |
| `anchor` | `lily-profile` など |
| `order` | 表示順。小さい順 |
| `personalUrl` | 個人公式リンクがある場合 |
| `ambassador` | アンバサダー情報など。なければ空欄 |

追加例:

```json
{
  "slug": "lily",
  "name": "LILY",
  "koreanName": "릴리",
  "japaneseName": "リリー",
  "birthDate": "2002-10-17",
  "birthDateLabel": "2002.10.17",
  "birthPlace": "Australia",
  "realName": "Lily Jin Morrow",
  "keywords": "LILY リリー 릴리",
  "shortDescription": "メンバー紹介文",
  "profile": "詳細な紹介文",
  "colorName": "Violet",
  "colorCode": "#8f7cff",
  "previewImage": "assets/members/lily.jpg",
  "detailImage": "assets/members/lily-detail.jpg",
  "desktopImage": "assets/members/lily-desktop.jpg",
  "anchor": "lily-profile",
  "order": 1,
  "personalUrl": "",
  "ambassador": ""
}
```

画像がPCで切れる場合は、`desktopImage` に横長または余白のある別画像を設定します。

## 5. ニュース

管理元: `data/news.json` の `news`

生成後、`articles/<slug>.html` が作られます。

| 項目 | 内容 |
|---|---|
| `slug` | 記事URL。半角英小文字、数字、ハイフン |
| `date` | `YYYY.MM.DD` |
| `category` | `release`、`notice`、`event` など |
| `label` | カードに表示する短い英字 |
| `title` | 記事タイトル |
| `text` | 本文・概要。改行は `\n` |
| `image` | 記事画像 |
| `sourceLink` | 公式案内へのURL |
| `sourceLabel` | リンクボタンの表示 |

```json
{
  "slug": "new-release-information",
  "date": "2026.08.01",
  "category": "release",
  "label": "RELEASE",
  "title": "新しいお知らせ",
  "text": "1行目。\n2行目。",
  "image": "assets/news/new-release-information.jpg",
  "sourceLink": "https://example.com/official-information",
  "sourceLabel": "公式案内を見る"
}
```

新しい記事を上に表示したい場合は、配列の先頭へ追加します。`slug` を変更するとURLも変わるため、公開後は原則変更しません。

## 6. スケジュール

管理元: `data/schedule.json` の `events`

| 項目 | 内容 |
|---|---|
| `id` | 一意の識別子 |
| `title` | 予定名 |
| `date` | 基準日 `YYYY-MM-DD` |
| `start` | 終日なら空欄。時刻ありはISO 8601推奨 |
| `end` | 終了日時。終日1日だけなら空欄 |
| `category` | `event`、`release`、`notice`、`Birthday` など |
| `type` | `LIVE`、`RELEASE`、`FC` など |
| `description` | 詳細 |
| `link` | 関連ページ |
| `linkLabel` | ボタン表示 |
| `image` | 任意画像 |
| `source` | 通常は `repository` |

### 終日イベント

```json
{
  "id": "example-event",
  "title": "イベント名",
  "date": "2026-08-01",
  "start": "",
  "end": "",
  "category": "event",
  "type": "EVENT",
  "description": "イベント説明",
  "link": "news.html",
  "linkLabel": "詳細を見る",
  "image": "assets/news/example-event.jpg",
  "source": "repository"
}
```

### 時刻ありイベント

日本時間を明確にするため、`+09:00` を付けます。

```json
{
  "id": "example-live",
  "title": "公演名",
  "date": "2026-08-08",
  "start": "2026-08-08T17:30:00+09:00",
  "end": "2026-08-08T20:00:00+09:00",
  "category": "event",
  "type": "LIVE",
  "description": "OPEN 16:30 / START 17:30",
  "link": "fan-services.html#tour",
  "linkLabel": "公演情報を見る",
  "image": "assets/news/example-live.jpg",
  "source": "repository"
}
```

複数日イベントでは、`date` を開始日、`end` を終了日の `YYYY-MM-DD` として登録できます。

メンバー誕生日とNMIXXのデビュー記念日は画面側でも毎年自動補完します。同じ日・同じ内容を手動登録した場合は、重複を避ける処理があります。

## 7. ディスコグラフィ

管理元: `data/discography.json`

### `categories`

作品分類です。`key`、見出し、説明、表示順の基準を管理します。

### `releases`

| 項目 | 内容 |
|---|---|
| `anchor` / `slug` | ページ内リンク用識別子 |
| `title` | 作品名 |
| `releaseDate` | 発売日 |
| `category` | `categories` の `key` と一致させる |
| `categoryName` | 表示名 |
| `mark` / `badge` | カードの補助表示 |
| `type` | Mini Album、Singleなど |
| `description` | 作品説明 |
| `tracks` | 曲順配列 |
| `appleMusic` / `spotify` / `lineMusic` | 配信リンク |
| `youtube` | MVや公式プレイリスト |
| `purchase` | 購入リンク |
| `cover` | ジャケット画像 |
| `order` | 表示順 |
| `published` | 公開する場合 `true` |

曲名だけを登録する場合は、次の文字列配列が最も簡単です。

```json
"tracks": [
  "Track One",
  "Track Two"
]
```

曲ごとに動画や注記を付ける場合は、詳細形式も使用できます。

```json
"tracks": [
  {"no": "01", "title": "Track One", "video": "https://www.youtube.com/watch?v=VIDEO_ID"},
  {"no": "02", "title": "Track Two", "note": "Title Track"}
]
```

既存作品のリンクを修正するときは、作品全体を削除せず対象URLだけ変更します。

## 8. MV

管理元: `data/mv.json`

MV、パフォーマンス、公式映像を曲ごとに管理します。主な項目は曲名、動画IDまたはURL、公開日、サムネイル、作品、表示順です。YouTube自動取得データとは別で、主要MV一覧を固定管理したい場合に使用します。

## 9. 音楽番組1位記録

管理元: `data/records.json` の `musicShowWins`

```json
{
  "title": "曲名 - Music Bank",
  "song": "曲名",
  "date": "2026-08-20",
  "program": "Music Bank",
  "description": "1位記録の説明。",
  "videoUrl": "https://www.youtube.com/watch?v=VIDEO_ID",
  "image": "assets/discography/album.jpg",
  "order": 22,
  "videoLabel": "アンコール・受賞映像を見る"
}
```

同じ曲・同じ番組でも受賞日が異なる場合は別項目にします。`order` は通算順です。

## 10. Melon記録

管理元: `data/records.json` の `melonRecords`

主な項目:

- `title` / `song`
- `releaseDate`
- `top100Peak`: TOP100最高位。記録なしは `0`
- `dailyPeak`: 日間最高位
- `top100PeakDate` / `dailyPeakDate`
- `firstDayUL`: 初日ユニークリスナー
- `peakUL`: 最高ユニークリスナー
- `description`
- `mvUrl`
- `image`
- `order`

数値はカンマなしの整数で入力します。例: `239400`

## 11. Hanteo記録

管理元: `data/records.json` の `hanteoRecords`

```json
{
  "releaseDate": "2026-05-11",
  "album": "Album Name",
  "type": "5th EP",
  "titleTrack": "Title Track",
  "firstDay": 100000,
  "firstWeek": 500000,
  "image": "assets/discography/album.jpg",
  "record": "必要な場合だけ記録ラベル"
}
```

枚数は整数で入力します。最高記録などの強調が必要な場合だけ `record` を追加します。

## 12. その他チャート記録

管理元: `data/records.json` の `otherChartRecords`

YouTube Music、Spotify、Billboardなど、専用ページ以外の記録を登録します。チャート名、期間、順位、増減、再生数、出典URL、画像を項目として追加できます。新しい形式を追加する場合は、既存の表示スクリプトが読むキーと合わせてください。

## 13. ストリーミングガイド

管理元: `data/streaming-guide.json` の `guides`

主な項目:

- `type`: サービス識別子
- `title` / `subtitle`
- `description`
- `preparation`: 事前準備
- `points`: 注意点の配列
- `steps`: 手順配列
- `link` / `buttonLabel`
- `icon`
- `note`
- `anchor`
- `order`

手順画像は `assets/streaming/` に保存し、各ステップ内の画像項目へ登録します。サービス仕様が変わった場合は、画面だけでなく説明文と注意点も更新してください。

## 14. 投票ガイド

管理元: `data/voting-guide.json`

### `status`

現在の投票状況や注意書きを表示します。

### `programs`

音楽番組ごとの集計、事前投票、当日投票、使用アプリを管理します。NMIXXが参加対象でない番組は追加しません。

### `apps`

投票アプリの説明、アイコン、タグ、App Store、Google Play、画像手順を管理します。画像は `assets/voting/` に保存します。

アプリ仕様は変更されるため、更新日を `status.lastChecked` に記録してください。

## 15. 掛け声

管理元: `data/chants.json`

`categories` で時期や作品分類を作り、`chants` に各曲を登録します。

推奨項目:

- `slug`
- `title`
- `release`
- `category`
- `official`: 公式なら `true`、独自整理なら `false`
- `videoUrl`
- `sourceUrl`
- `text`
- `image`
- `note`
- `order`

公式情報が確認できない場合は、推測を公式扱いせず `official: false` とし、注意書きと出典を付けます。

## 16. 公式リンク

管理元: `data/official-links.json` の `links`

| 項目 | 内容 |
|---|---|
| `title` | サイト・SNS名 |
| `category` | 公式、音楽、ファンベースなど |
| `categoryOrder` | カテゴリー順 |
| `order` | カテゴリー内の順番 |
| `url` | URL |
| `subtitle` / `description` | 補足 |
| `label` | ボタン表示 |
| `icon` | 画像パス |
| `iconText` | 画像がない場合の文字 |
| `anchor` | ページ内リンク |

リンク変更後は `Check External Links` も手動実行します。

## 17. ホームページ表示

管理元: `data/homepage.json` の `items`

ホームのヒーロー、注目カード、数値、ボタン、案内を部品単位で管理します。既存項目の `slug` と `type` は表示スクリプトが使用するため、役割を変えない限り維持してください。

主な項目:

- `slug` / `type`
- `englishLabel`
- `heading` / `title`
- `description` / `note`
- `number` / `value` / `subLabel`
- `buttonLabel` / `linkUrl`
- `secondaryButtonLabel` / `secondaryLinkUrl`
- `thirdButtonLabel` / `thirdLinkUrl`
- `image` / `icon`
- `anchor` / `order`

空欄のボタンは表示されません。

## 18. サイト全体テーマ

管理元: `data/site-theme.json` の `theme`

色は6桁のHEX形式で入力します。

- `background` / `background2`
- `card` / `card2`
- `primary` / `primarySoft`
- `secondary`
- `accent`
- `blue`
- `text` / `muted`
- `lightBackground` / `lightCard` / `lightText`

例: `"primary": "#8f7cff"`

## 19. カムバック別テーマ

管理元: `data/comeback-themes.json`

1. `themes` に新しいテーマを追加する。
2. `activeTheme` をそのテーマの `key` に変更する。
3. 生成処理を実行する。

```json
{
  "key": "new-comeback",
  "name": "New Comeback",
  "release": "Album Name",
  "startDate": "2026-08-01",
  "endDate": "",
  "colors": {
    "background": "#101020",
    "background2": "#181832",
    "card": "#202044",
    "primary": "#8877ff",
    "secondary": "#ff77aa",
    "accent": "#66ddcc"
  }
}
```

`startDate` と `endDate` は運営上の記録です。実際に使うテーマは `activeTheme` で明示します。

## 20. CSVで一括更新

テンプレート:

- `data/csv/news.csv`
- `data/csv/schedule.csv`
- `data/csv/music-show-wins.csv`

重要: CSV取込は対象配列を全件置き換えます。追加分だけのCSVを取り込むと、既存データが消えます。必ず既存分を含む完成版CSVを用意してください。

```bash
python3 scripts/import-csv.py news
python3 scripts/import-csv.py schedule
python3 scripts/import-csv.py wins
python3 scripts/build-content.py
bash scripts/run-prepublish-checks.sh
```

安全機能:

- データ行が空なら中止
- テンプレートの例示文字が残っていれば中止
- 必須項目と日付形式を検査
- 元JSONを `data/backups/` に保存
- 一時ファイル完成後にJSONを置換

CSVはExcel、Googleスプレッドシートなどで編集できます。保存形式はUTF-8 CSVを推奨します。

## 21. YouTube手動更新

通常は `Sync YouTube` が `data/youtube-channels.json` を更新します。

全自動取得が失敗した場合も前回データは残ります。急ぎで追加する場合は、対象チャンネルの `videos` 配列へ次の形式で追加します。

```json
{
  "videoId": "VIDEO_ID",
  "title": "動画タイトル",
  "url": "https://www.youtube.com/watch?v=VIDEO_ID",
  "thumbnail": "https://i.ytimg.com/vi/VIDEO_ID/hqdefault.jpg",
  "publishedAt": "2026-08-01T09:00:00.000Z",
  "videoType": "video",
  "duration": 180,
  "channelKey": "nmixx"
}
```

`videoType` は `video`、`short`、`live` のいずれかです。`totalVideos` と `typeCounts` も実データに合わせて更新します。

次回の自動取得時に同じ動画IDが見つかれば、自動データへ統合されます。

## 22. 画像管理

推奨形式:

- 写真: JPGまたはWebP
- 透過アイコン: PNGまたはWebP
- OGP元画像: 横長で十分な解像度

推奨ルール:

- 半角英小文字、数字、ハイフン
- 日本語や空白を避ける
- 同名上書きはブラウザキャッシュに注意
- 不要画像を削除する前に全参照を検索する

画像を差し替えても表示が変わらない場合は、ファイル名を変更してJSON側も更新する方法が確実です。

## 23. スマートフォンで安全に更新するコツ

- 長いJSONを最初から書かず、直前の項目を複製する。
- 1回のコミットでは1種類のデータだけ変更する。
- 画像アップロードとJSON更新を分ける場合、画像を先に追加する。
- コミット直後にActionsを確認する。
- エラー時は追加した部分だけを戻し、再度小さく更新する。

## 24. 更新後の確認

1. `Build Repository Content` が成功。
2. `Check Site` が成功。
3. 対象ページを開く。
4. 画像、日付、リンク、改行を確認。
5. スマートフォン幅を確認。
6. 言語切替を確認。
7. ニュースの場合は記事URLとOGPを確認。
8. 予定の場合はGoogleカレンダーとICS登録を確認。
9. テーマ変更の場合はダーク・ライト両方を確認。
