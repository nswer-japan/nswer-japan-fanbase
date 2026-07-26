#!/usr/bin/env python3
from __future__ import annotations
import json,re,sys
from pathlib import Path
from urllib.parse import urlsplit, unquote
ROOT=Path(__file__).resolve().parents[1]
TEXT_EXT={'.html','.js','.mjs','.py','.json','.md','.txt','.css','.xml','.webmanifest','.yml','.yaml','.sh','.csv','.ics'}
FORBIDDEN=[r'(?i)rescene',r'リセンヌ',r'리센느',r'(?i)plus\s*chat',r'(?i)the\s+show',r'(?i)bigc',r'\bWONI\b',r'\bLIV\b',r'\bMINAMI\b',r'\bMAY\b',r'\bZENA\b',r'(?i)scenedrome',r'(?i)love\s+attack',r'(?i)pretty\s+girl',r'(?i)lip\s+bomb',r'(?i)busy\s+boy',r'(?i)glow\s+up',r'(?i)pinball',r'(?i)remember\s+a\s+scene',r'(?i)scent\s*·\s*scene',r'香りと記憶',r'香りを通じて',r'(?i)artist/nswer/',r'(?i)nswer-fb\.jp',r'(?i)x\.com/nswer_japan',r'(?i)instagram\.com/nswer_japan',r'(?i)tiktok\.com/@?nswer[._]japan']
IGNORE_DIRS={'.git','node_modules'}
errors=[]
SELF=Path(__file__).resolve()
for p in ROOT.rglob('*'):
 if not p.is_file() or p.resolve()==SELF or any(part in IGNORE_DIRS for part in p.parts): continue
 if p.suffix.lower()=='.json':
  try: json.loads(p.read_text(encoding='utf-8'))
  except Exception as e: errors.append(f'JSON error {p.relative_to(ROOT)}: {e}')
 if p.suffix.lower() in TEXT_EXT:
  s=p.read_text(encoding='utf-8',errors='ignore')
  for pat in FORBIDDEN:
   if re.search(pat,s): errors.append(f'Forbidden text {pat}: {p.relative_to(ROOT)}')
for p in ROOT.rglob('*.html'):
 if any(part in IGNORE_DIRS for part in p.parts): continue
 s=p.read_text(encoding='utf-8',errors='ignore')
 for attr,url in re.findall(r'\b(src|href)=["\']([^"\']+)["\']',s,re.I):
  if not url or '${' in url or '{{' in url or url.startswith(('#','mailto:','tel:','javascript:','data:','webcal:','http://','https://','//')): continue
  clean=unquote(urlsplit(url).path)
  if not clean: continue
  target=((ROOT/clean.lstrip('/')) if clean.startswith('/') else (p.parent/clean)).resolve()
  try: target.relative_to(ROOT.resolve())
  except ValueError: errors.append(f'Path escapes root: {p.relative_to(ROOT)} -> {url}'); continue
  if not target.exists(): errors.append(f'Missing local target: {p.relative_to(ROOT)} -> {url}')
# required managed files
for rel in ['data/members.json','data/news.json','data/schedule.json','data/discography.json','data/records.json','data/streaming-guide.json','data/voting-guide.json','data/chants.json','data/official-links.json','data/homepage.json','data/site-theme.json','data/comeback-themes.json','data/notion-config.json']:
 if not (ROOT/rel).exists(): errors.append(f'Missing required data: {rel}')
if errors:
 print(f'検査エラー {len(errors)}件')
 for e in errors[:200]: print('-',e)
 sys.exit(1)
print('サイト検査に合格しました。')
