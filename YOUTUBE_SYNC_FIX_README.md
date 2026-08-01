# NMIXX YouTube 3カテゴリー全履歴同期 修正版

## 上書きするファイル

- `.github/workflows/sync-youtube.yml`
- `scripts/sync-youtube-channels.mjs`
- `scripts/test-youtube-sync.py`
- `data/youtube-channels.json`
- `youtube.html`

## 取得仕様

- NMIXX Official の `/videos` を件数上限なしで取得 → `video`
- NMIXX Official の `/shorts` を件数上限なしで取得 → `short`
- NMIXX Official の `/streams` を件数上限なしで取得 → `live`
- 同じ動画IDが複数タブにある場合は `live > short > video` の優先順位で1件に統合
- 初回または `historyComplete: false` の場合は、recent指定でも必ず全履歴同期
- 全履歴取得後は6時間ごとに直近分を確認し、既存全履歴へ統合
- 毎週日曜と手動 `full_history: true` は3タブを全件再取得
- 3タブのどれかが失敗した場合は、既存の完全履歴を削除しない
- 全タブが失敗した場合はJSONを変更しない

## 分類仕様

動画の長さでは分類しません。YouTubeの掲載タブを分類の正本にします。

- `/videos` → 動画
- `/shorts` → ショート
- `/streams` → ライブ

これにより、短い通常動画や長いShortsの誤分類を防ぎます。

## 実行順

1. 5ファイルをリポジトリの同じ場所へ上書きしてmainへコミット
2. Actions → Sync YouTube
3. Run workflow
4. `full_history: true`
5. 実行後、ログに「動画○ / ショート○ / ライブ○」が出ることを確認
6. Check Siteを確認
