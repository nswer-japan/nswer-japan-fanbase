# 記事ページ修正パッチ

このパッチでは次を修正しています。

- `articles/n-mixx-store-benefits-venue-lucky-draw.html` のリンク切れ/表示崩れ修正
- 記事内に案内画像3枚を追加
- `data/news-data.js` の記事サムネイルを差し替え
- `assets/news/` に画像3枚を追加

## 反映方法

ZIP内のファイルをリポジトリ直下へフォルダ構造を保ったまま上書きしてください。

その後 GitHub Actions で公開用ワークフローを1回実行してください。
