#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JST = timezone(timedelta(hours=9))
MAPPINGS = {
    "members.json": ("NSWER_MEMBERS", "members-data.js"),
    "news.json": ("NSWER_NEWS_PAYLOAD", "news-data.js"),
    "schedule.json": ("NSWER_SCHEDULE", "schedule-data.js"),
    "discography.json": ("NSWER_DISCOGRAPHY", "discography-data.js"),
    "records.json": ("NSWER_RECORDS", "records-data.js"),
    "streaming-guide.json": ("NSWER_STREAMING_GUIDE", "streaming-guide-data.js"),
    "voting-guide.json": ("NSWER_VOTING_GUIDE", "voting-guide-data.js"),
    "chants.json": ("NSWER_CHANTS", "chants-data.js"),
    "official-links.json": ("NSWER_OFFICIAL_LINKS", "official-links-data.js"),
    "homepage.json": ("NSWER_HOMEPAGE", "homepage-data.js"),
    "about.json": ("NSWER_ABOUT", "about-data.js"),
    "contact.json": ("NSWER_CONTACT", "contact-data.js"),
    "mv.json": ("NSWER_MV", "mv-data.js"),
}


def write_js(src: str, global_name: str, dest: str) -> None:
    obj = json.loads((ROOT / "data" / src).read_text(encoding="utf-8"))
    compact = json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
    if src == "news.json":
        text = f"window.{global_name}={compact};window.NSWER_NEWS=window.{global_name}.news||[];\n"
    elif src == "schedule.json":
        text = (
            f"window.NSWER_SCHEDULE_PAYLOAD={compact};"
            "window.NSWER_SCHEDULE=window.NSWER_SCHEDULE_PAYLOAD.events||[];"
            "window.NSWER_SCHEDULE_GENERATED_AT=window.NSWER_SCHEDULE_PAYLOAD.generatedAt||'';\n"
        )
    else:
        text = f"window.{global_name}={compact};\n"
    (ROOT / "data" / dest).write_text(text, encoding="utf-8")


def valid_color(value: object, fallback: str) -> str:
    text = str(value or "").strip()
    return text if re.fullmatch(r"#[0-9a-fA-F]{6}", text) else fallback


def build_theme() -> None:
    site = json.loads((ROOT / "data/site-theme.json").read_text(encoding="utf-8")).get("theme", {})
    comeback = json.loads((ROOT / "data/comeback-themes.json").read_text(encoding="utf-8"))
    active_key = str(comeback.get("activeTheme") or "default")
    active = next((item for item in comeback.get("themes", []) if item.get("key") == active_key), {})
    colors = {**site, **active.get("colors", {})}
    values = {
        "bg": valid_color(colors.get("background"), "#080b16"),
        "bg2": valid_color(colors.get("background2"), "#10162a"),
        "card": valid_color(colors.get("card"), "#151c33"),
        "card2": valid_color(colors.get("card2"), "#1d2542"),
        "primary": valid_color(colors.get("primary"), "#8f7cff"),
        "primary_soft": valid_color(colors.get("primarySoft"), "#c4b8ff"),
        "secondary": valid_color(colors.get("secondary"), "#ff71b8"),
        "accent": valid_color(colors.get("accent"), "#58e0d1"),
        "blue": valid_color(colors.get("blue"), "#72b7ff"),
        "text": valid_color(colors.get("text"), "#f8f9ff"),
        "muted": valid_color(colors.get("muted"), "#b8bfd6"),
        "light_bg": valid_color(colors.get("lightBackground"), "#f6f7ff"),
        "light_card": valid_color(colors.get("lightCard"), "#ffffff"),
        "light_text": valid_color(colors.get("lightText"), "#171a2b"),
    }
    css = f"""/* Auto-generated from repository theme data. Active theme: {active_key}. */
:root{{--bg:{values['bg']};--bg2:{values['bg2']};--card:{values['card']};--card2:{values['card2']};--pink:{values['primary']};--pink-soft:{values['primary_soft']};--purple:{values['secondary']};--green:{values['accent']};--blue:{values['blue']};--text:{values['text']};--muted:{values['muted']};--border:color-mix(in srgb,{values['primary']} 22%,transparent);--header-bg:color-mix(in srgb,{values['bg']} 90%,transparent);--header-border:color-mix(in srgb,{values['primary']} 14%,transparent);--hover-bg:color-mix(in srgb,{values['primary']} 9%,transparent);--soft-bg:color-mix(in srgb,{values['text']} 5%,transparent);--shadow:0 18px 48px color-mix(in srgb,#050711 68%,transparent)}}
body{{background:radial-gradient(circle at 8% 7%,color-mix(in srgb,var(--pink) 20%,transparent),transparent 29%),radial-gradient(circle at 92% 12%,color-mix(in srgb,var(--purple) 14%,transparent),transparent 31%),radial-gradient(circle at 82% 88%,color-mix(in srgb,var(--blue) 8%,transparent),transparent 30%),linear-gradient(145deg,var(--bg) 0%,var(--bg2) 48%,var(--bg) 100%)!important}}
.card,.news-card{{background:linear-gradient(145deg,color-mix(in srgb,var(--card) 96%,transparent),color-mix(in srgb,var(--bg2) 90%,transparent))}}.hero,.page-header,.focus-card{{background:radial-gradient(circle at 88% 8%,color-mix(in srgb,var(--pink) 24%,transparent),transparent 31%),radial-gradient(circle at 12% 93%,color-mix(in srgb,var(--purple) 14%,transparent),transparent 36%),linear-gradient(135deg,color-mix(in srgb,var(--card2) 94%,transparent),color-mix(in srgb,var(--bg2) 90%,transparent))}}.logo span,.hero h1 span{{background:linear-gradient(120deg,var(--pink),var(--pink-soft),var(--purple));-webkit-background-clip:text;-webkit-text-fill-color:transparent}}.btn-primary{{background:linear-gradient(120deg,var(--pink),var(--pink-soft) 58%,var(--purple))}}
html.light-mode{{--bg:{values['light_bg']};--bg2:color-mix(in srgb,{values['light_bg']} 88%,{values['primary_soft']});--card:{values['light_card']};--card2:color-mix(in srgb,{values['light_card']} 92%,{values['primary_soft']});--text:{values['light_text']};--muted:color-mix(in srgb,{values['light_text']} 66%,transparent);--header-bg:color-mix(in srgb,{values['light_card']} 92%,transparent);--soft-bg:color-mix(in srgb,{values['primary']} 6%,{values['light_card']});--border:color-mix(in srgb,{values['primary']} 20%,transparent)}}
"""
    (ROOT / "css/theme.css").write_text(css, encoding="utf-8")
    manifest_path = ROOT / "manifest.webmanifest"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["background_color"] = values["bg"]
        manifest["theme_color"] = values["bg"]
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def build_search() -> None:
    pages = []
    for path in sorted(ROOT.glob("*.html")):
        if path.name in {"404.html", "offline.html", "article.html", "sync-status.html", "external-links.html", "analytics.html"}:
            continue
        source = path.read_text(encoding="utf-8", errors="ignore")
        title = re.search(r"<title>(.*?)</title>", source, re.S)
        desc = re.search(r"<meta[^>]+name=[\"']description[\"'][^>]+content=[\"'](.*?)[\"']", source, re.S)
        clean = re.sub(r"<script[\s\S]*?</script>|<style[\s\S]*?</style>|<[^>]+>", " ", source)
        clean = re.sub(r"\s+", " ", clean).strip()[:2500]
        pages.append({
            "type": "page",
            "title": re.sub(r"\s+", " ", title.group(1)).strip() if title else path.stem,
            "summary": desc.group(1) if desc else "",
            "url": path.name,
            "keywords": clean,
            "image": "assets/group/nmixx-group.jpg",
        })
    mappings = [
        ("members.json", "members", "name", "members.html#"),
        ("news.json", "news", "title", "articles/"),
        ("discography.json", "releases", "title", "discography.html#"),
        ("schedule.json", "events", "title", "schedule.html#"),
    ]
    for rel, key, title_field, url_prefix in mappings:
        obj = json.loads((ROOT / "data" / rel).read_text(encoding="utf-8"))
        for row in obj.get(key, []):
            slug = row.get("anchor") or row.get("slug") or row.get("id", "")
            url = f"{url_prefix}{slug}" + (".html" if rel == "news.json" else "")
            pages.append({
                "type": rel.removesuffix(".json"),
                "title": row.get(title_field, "Untitled"),
                "summary": row.get("text") or row.get("description") or row.get("shortDescription") or "",
                "url": url,
                "keywords": " ".join(str(value) for value in row.values() if isinstance(value, (str, int, float))),
                "image": row.get("image") or row.get("cover") or row.get("previewImage") or "assets/group/nmixx-group.jpg",
            })
    (ROOT / "data/search-index.json").write_text(
        json.dumps({"generatedAt": datetime.now(JST).isoformat(), "items": pages}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    for src, (global_name, dest) in MAPPINGS.items():
        write_js(src, global_name, dest)
    build_theme()
    build_search()
    subprocess.run(["node", "scripts/render-record-pages.mjs"], cwd=ROOT, check=True)
    subprocess.run([sys.executable, "scripts/sync-site-shell.py"], cwd=ROOT, check=True)
    subprocess.run([sys.executable, "scripts/generate-seo.py"], cwd=ROOT, check=True)
    subprocess.run([sys.executable, "scripts/generate-pwa.py"], cwd=ROOT, check=True)
    print("リポジトリ内データから表示ファイルを生成しました。")


if __name__ == "__main__":
    main()
