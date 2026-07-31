# 上書き前に削除する旧ファイル

既存リポジトリに以下が残っている場合は、先に削除してください。

```text
.github/workflows/sync-notion.yml
scripts/sync-notion-content.py
data/notion-config.json
docs/notion-sync-setup.md
assets/notion/
data/backups/notion/
```

その後、このZIPの内容をリポジトリ直下へ上書きします。`.github`は隠しフォルダなので、GitHub画面でアップロードできない場合は専用ZIPの各YAMLを手動作成してください。
