# 今回の更新内容（2026-07-26）

## 方針

- サイトの見た目、CSS、ページ構成はNSWER JAPAN FB独自のものを維持。
- 自動更新、画像保存、失敗時保護などの内部処理だけを強化。
- NSWER専用Notionと他サイト用環境は完全分離。

## 実施内容

### ファンベースSNSリンク

お問い合わせ、公式リンク、SEO構造化データ、検索用データから、ファンベース所有のX・Instagram・TikTokリンクを削除しました。NMIXX公式、日本公式、日本公式ファンクラブへのリンクは残しています。

同期後に誤って戻らないよう、Notion公式リンク同期にも禁止URL検査を追加しました。

### Heavy Serenade

ディスコグラフィへ次のリンクを追加しました。

- 公式配信サービス一覧
- Apple Music
- Spotify
- YouTube Music
- 公式MV
- 購入ページ

収録曲は6曲を掲載しています。

### 音楽番組1位

NMIXXの音楽番組1位記録を23件へ更新しました。

- Love Me Like This: 1冠
- DASH: 4冠
- See that?: 3冠
- KNOW ABOUT ME: 3冠
- Blue Valentine: 10冠
- Heavy Serenade: 2冠

各記録に日付、番組、得点、説明を設定しました。

### Notion同期

`Sync Notion Content` を追加しました。

- 3時間ごとの自動同期
- 手動実行
- 空データベースでは既存JSONを維持
- 一部取得失敗時も他の成功データを反映
- 更新前JSONを最大10世代保存
- Notion画像をGitHub内へ保存
- HEIC／HEIFをJPGへ変換
- NSWER専用サイトテーマ・カムバックテーマを同期

### YouTube

既存の `Sync YouTube` を維持しました。

- 6時間ごとの自動取得
- 手動実行
- 取得失敗時は前回の動画JSONを維持

## GitHubで必要な設定

Notion自動同期を動かすには、Repository secret `NSWER_NOTION_TOKEN` が必要です。詳細は `docs/notion-sync-setup.md` を確認してください。
