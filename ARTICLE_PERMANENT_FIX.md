# ニュース記事・GitHub Pages恒久修正

前回の修正は生成済みHTMLだけだったため、Build Repository Contentで元に戻っていました。
この版では生成元と生成スクリプトを修正しています。

## 修正内容
- GitHub Pagesのプロジェクト配下でCSS・画像・リンクが正しく表示される相対パスへ変更
- 記事本文に指定画像3枚を追加
- data/news.json と data/csv/news.csv に画像記述を保存
- Build Repository Contentを再実行しても修正が維持される
- service-worker.jsを再生成してキャッシュ名を更新

## 反映方法
ZIP内をリポジトリ直下へ上書きし、Build Repository Contentを1回実行してください。
公開後はCtrl+F5でハード再読み込みしてください。
