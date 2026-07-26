# 画像素材一覧と更新方針

## 今回差し替えた画像

- ホーム集合写真：NMIXX日本公式ファンクラブ掲載写真
- メンバー6人：NMIXX日本公式ファンクラブの同一シリーズ写真
- Heavy Serenade／Fe3O4: FORWARD／Fe3O4: STICK OUT／A Midsummer NMIXX’s Dream／Funky Glitter Christmas／ENTWURF：JYP公式ディスコグラフィ掲載ジャケット
- TIC TIC／Caution：JYP公式リリース案内掲載ジャケット
- ZERO FRONTIER IN JAPAN：日本公式サイトの公演・グッズ画像

素材の対応関係は `data/image-manifest.json` に記録しています。

## 更新時のルール

1. JYP公式、NMIXX公式、日本公式サイト・ファンクラブの順に探します。
2. 検索結果のサムネイルやファン転載画像は保存しません。
3. メンバー写真は6人すべて同一シリーズで揃えます。
4. 元画像は縦横比を維持し、JPEGはプログレッシブ形式で圧縮します。
5. ニュース画像を差し替えた後は `python3 scripts/build-content.py` を実行してOGPを再生成します。
6. 掲載可否や二次利用条件が変更された場合は、該当画像を削除して公式ページへのリンク表示へ切り替えます。
