# YouTube全履歴同期

最終更新: 2026-07-27

## 対象

NMIXX公式YouTubeチャンネルの次の公開タブを取得します。

- 通常動画
- Shorts
- ライブ配信・配信アーカイブ

動画本体はダウンロードせず、動画ID、タイトル、URL、サムネイル、公開日時、種類、長さなどの公開メタデータだけを保存します。

## 初回実行

修正版を `main` ブランチへアップロードすると、`historyComplete: false` を検知して全履歴同期が自動実行されます。手動で実行する場合は次の手順です。

1. GitHubリポジトリの `Actions` を開く。
2. `Sync YouTube` を選択する。
3. `Run workflow` を押す。
4. `full_history` をオンにして実行する。
5. Actionsが成功したら `data/youtube-channels.json` を開く。
6. `historyComplete: true` と `lastFullSyncAt` が入っていることを確認する。

初回の全履歴取得が済んでいない場合、毎日の `Sync All Site Data` も自動的に完全同期を選びます。

## 更新頻度

- 6時間ごと: 直近の通常動画180件、Shorts 120件、配信100件を確認し、全履歴へ統合
- 毎週日曜: 件数上限なしで3タブを最後まで再取得
- 手動実行: `full_history` をオンにすると件数上限なし

## データを失わない仕組み

- 全タブが取得できなければ既存JSONを削除しない。
- 一部タブが失敗した場合は、前回の全履歴を保持したまま成功分だけ更新する。
- 一時ファイルへ書き込み、完成後にだけ本番JSONと置き換える。
- 通常動画・Shorts・配信に同じ動画が現れても、動画IDで1件へ統合する。
- 完全同期前の同梱データには `historyComplete: false` を設定している。

## 表示

`youtube.html` は全件を一度に描画せず、24件ずつ表示します。検索と通常動画・Shorts・ライブの絞り込みは保存済みの全履歴を対象にします。

## 失敗時

Actionsの再実行を先に試してください。失敗しても最後に成功した `data/youtube-channels.json` は維持されます。

YouTube側の仕様変更で継続的に失敗する場合は、Actions内でインストールされる `yt-dlp[default]` のnightly版とNode.js 22のログを確認します。
