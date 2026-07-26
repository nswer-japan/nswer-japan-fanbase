#!/usr/bin/env python3
from __future__ import annotations
import re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
HS='<!-- SITE-HEADER-START -->';HE='<!-- SITE-HEADER-END -->';FS='<!-- SITE-FOOTER-START -->';FE='<!-- SITE-FOOTER-END -->'
header=(ROOT/'templates/site-header.html').read_text(encoding='utf-8').strip(); footer=(ROOT/'templates/site-footer.html').read_text(encoding='utf-8').strip()
def prefix(p): return '' if p.parent==ROOT else '../'
def render(t,p,repl):
 t=t.replace('{{ROOT}}',p)
 for k,v in repl.items(): t=t.replace('{{'+k+'}}',v)
 return t
count=0
for p in sorted(ROOT.rglob('*.html')):
 if 'templates' in p.parts or 'artifacts' in p.parts or p.name=='offline.html': continue
 s=p.read_text(encoding='utf-8'); rel=p.relative_to(ROOT).as_posix(); pre=prefix(p)
 repl={'MUSIC_OPEN':' open' if p.name in {'discography.html','mv.html','youtube.html','records.html','music-show-wins.html','melon-records.html','hanteo-records.html'} else '', 'LINKS_OPEN':' open' if p.name in {'links.html','fan-services.html','contact.html'} else '', 'SEARCH_CURRENT':' aria-current="page"' if p.name=='search.html' else '', 'FOOTER_NOTE':'公式情報はNMIXXおよび所属事務所・各主催者の案内もあわせてご確認ください。','YEAR_ATTR':'data-year'}
 h=f'{HS}\n{render(header,pre,repl)}\n{HE}'; f=f'{FS}\n{render(footer,pre,repl)}\n{FE}'
 if HS not in s or HE not in s or FS not in s or FE not in s: continue
 n=re.sub(re.escape(HS)+r'[\s\S]*?'+re.escape(HE),h,s,count=1)
 n=re.sub(re.escape(FS)+r'[\s\S]*?'+re.escape(FE),f,n,count=1)
 if n!=s: p.write_text(n,encoding='utf-8'); count+=1
print(f'共通ヘッダー・フッターを同期しました: {count}ページ')
