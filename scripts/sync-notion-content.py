#!/usr/bin/env python3
"""Sync NSWER JAPAN FB content from its dedicated Notion workspace.

Design goals:
- Never erase existing repository data when Notion is empty or unavailable.
- Merge Notion rows into the existing JSON, so migration can happen gradually.
- Download Notion-hosted images because signed URLs expire.
- Keep the visual layer NSWER-specific; only data/update infrastructure is shared.
"""
from __future__ import annotations

import hashlib
import json
import mimetypes
import os
import re
import shutil
import sys
import tempfile
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
ASSETS = ROOT / "assets" / "notion"
CONFIG_PATH = DATA / "notion-config.json"
TOKEN = os.environ.get("NSWER_NOTION_TOKEN") or os.environ.get("NOTION_TOKEN")
API_BASE = os.environ.get("NOTION_API_BASE", "https://api.notion.com").rstrip("/")
USER_AGENT = "NSWER-JAPAN-FB/1.0"

if not TOKEN:
    raise SystemExit("NSWER_NOTION_TOKEN が設定されていません。GitHub ActionsのRepository secretへ登録してください。")

CONFIG = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
NOTION_VERSION = os.environ.get("NSWER_NOTION_VERSION", CONFIG.get("notionVersion", "2026-03-11"))
SOURCE_IDS = CONFIG.get("dataSources", {})


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def notion_request(path: str, *, method: str = "GET", body: dict[str, Any] | None = None) -> dict[str, Any]:
    data = json.dumps(body).encode("utf-8") if body is not None else None
    request = urllib.request.Request(
        f"{API_BASE}{path}",
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Notion-Version": NOTION_VERSION,
            "Content-Type": "application/json",
            "User-Agent": USER_AGENT,
        },
    )
    last_error: Exception | None = None
    for attempt in range(1, 4):
        try:
            with urllib.request.urlopen(request, timeout=45) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            detail = error.read().decode("utf-8", errors="replace")
            if error.code not in {429, 500, 502, 503, 504} or attempt == 3:
                raise RuntimeError(f"Notion API {error.code} {path}: {detail}") from error
            last_error = error
        except (urllib.error.URLError, TimeoutError) as error:
            last_error = error
            if attempt == 3:
                break
        time.sleep(attempt * 1.5)
    raise RuntimeError(f"Notion API request failed: {path}: {last_error}")


def source_id(name: str) -> str:
    env_key = f"NSWER_NOTION_{re.sub(r'(?<!^)(?=[A-Z])', '_', name).upper()}_DATA_SOURCE_ID"
    value = os.environ.get(env_key) or SOURCE_IDS.get(name)
    if not value:
        raise RuntimeError(f"Notion data source ID is missing: {name} ({env_key})")
    return str(value).replace("collection://", "").strip()


def query_pages(name: str) -> list[dict[str, Any]]:
    data_source_id = source_id(name)
    pages: list[dict[str, Any]] = []
    cursor: str | None = None
    while True:
        body: dict[str, Any] = {"page_size": 100}
        if cursor:
            body["start_cursor"] = cursor
        payload = notion_request(f"/v1/data_sources/{urllib.parse.quote(data_source_id)}/query", method="POST", body=body)
        pages.extend(row for row in payload.get("results", []) if row.get("object") == "page")
        if not payload.get("has_more") or not payload.get("next_cursor"):
            break
        cursor = payload["next_cursor"]
    return pages


def prop(page: dict[str, Any], name: str) -> dict[str, Any]:
    value = (page.get("properties") or {}).get(name)
    return value if isinstance(value, dict) else {}


def text_from_property(value: dict[str, Any]) -> str:
    kind = value.get("type")
    items = value.get(kind) if kind in {"title", "rich_text"} else None
    if not isinstance(items, list):
        for candidate in (value.get("title"), value.get("rich_text")):
            if isinstance(candidate, list):
                items = candidate
                break
    if isinstance(items, list):
        return "".join(str(item.get("plain_text") or ((item.get("text") or {}).get("content")) or "") for item in items).strip()
    if kind == "formula":
        formula = value.get("formula") or {}
        return str(formula.get(formula.get("type")) or "").strip()
    return ""


def text(page: dict[str, Any], name: str) -> str:
    return text_from_property(prop(page, name))


def checkbox(page: dict[str, Any], name: str) -> bool:
    value = prop(page, name)
    return bool(value.get("checkbox") if value.get("type") == "checkbox" else value.get("checkbox", False))


def select(page: dict[str, Any], name: str) -> str:
    value = prop(page, name)
    for key in ("select", "status"):
        item = value.get(key)
        if isinstance(item, dict):
            return str(item.get("name") or "").strip()
    multi = value.get("multi_select")
    if isinstance(multi, list) and multi:
        return str(multi[0].get("name") or "").strip()
    return ""


def number(page: dict[str, Any], name: str, default: float | int | None = None) -> float | int | None:
    value = prop(page, name).get("number")
    return value if isinstance(value, (int, float)) else default


def date_value(page: dict[str, Any], name: str) -> tuple[str, str]:
    value = prop(page, name).get("date")
    if not isinstance(value, dict):
        return "", ""
    return str(value.get("start") or ""), str(value.get("end") or "")


def url_value(page: dict[str, Any], name: str) -> str:
    value = prop(page, name)
    direct = value.get("url")
    if isinstance(direct, str):
        return direct.strip()
    return text_from_property(value)


def file_entries(page: dict[str, Any], names: Iterable[str]) -> list[dict[str, str]]:
    for name in names:
        value = prop(page, name)
        files = value.get("files")
        if not isinstance(files, list):
            continue
        output = []
        for item in files:
            file_data = item.get("file") or item.get("external") or {}
            file_url = str(file_data.get("url") or "")
            if file_url.startswith(("http://", "https://")):
                output.append({"url": file_url, "name": str(item.get("name") or name)})
        if output:
            return output
    return []


def is_public(page: dict[str, Any]) -> bool:
    return checkbox(page, "公開")


def slugify(value: str, fallback: str = "item") -> str:
    normalized = unicodedata.normalize("NFKC", value).lower().strip()
    normalized = re.sub(r"[\s_]+", "-", normalized)
    normalized = re.sub(r"[^a-z0-9가-힣ぁ-んァ-ヶ一-龠-]+", "", normalized)
    normalized = re.sub(r"-+", "-", normalized).strip("-")
    return normalized or fallback


def load_json(name: str) -> dict[str, Any]:
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def backup_and_write(name: str, payload: dict[str, Any]) -> bool:
    target = DATA / name
    old_text = target.read_text(encoding="utf-8") if target.exists() else ""
    old_payload = json.loads(old_text) if old_text else None
    compare_old = dict(old_payload or {})
    compare_new = dict(payload)
    compare_old.pop("generatedAt", None)
    compare_new.pop("generatedAt", None)
    if compare_old == compare_new:
        payload["generatedAt"] = (old_payload or {}).get("generatedAt", payload.get("generatedAt", now_iso()))
        return False
    backup_dir = DATA / "backups" / "notion"
    backup_dir.mkdir(parents=True, exist_ok=True)
    if target.exists():
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        shutil.copy2(target, backup_dir / f"{target.stem}-{stamp}.json")
        backups = sorted(backup_dir.glob(f"{target.stem}-*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        for stale in backups[10:]:
            stale.unlink(missing_ok=True)
    payload["generatedAt"] = now_iso()
    text_value = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=target.parent, delete=False) as handle:
        handle.write(text_value)
        temp_name = handle.name
    json.loads(Path(temp_name).read_text(encoding="utf-8"))
    os.replace(temp_name, target)
    return True


def merge_items(existing: list[dict[str, Any]], incoming: list[dict[str, Any]], key: Callable[[dict[str, Any]], str]) -> list[dict[str, Any]]:
    merged = [dict(item) for item in existing]
    positions = {key(item): index for index, item in enumerate(merged) if key(item)}
    for item in incoming:
        item_key = key(item)
        if item_key and item_key in positions:
            base = dict(merged[positions[item_key]])
            base.update({k: v for k, v in item.items() if v not in (None, "") or k in {"published", "公開"}})
            merged[positions[item_key]] = base
        else:
            positions[item_key] = len(merged)
            merged.append(item)
    return merged


def _extension(name: str, content_type: str, url: str) -> str:
    for candidate in (Path(name.split("?")[0]).suffix.lower(), Path(urllib.parse.urlparse(url).path).suffix.lower()):
        if candidate in {".jpg", ".jpeg", ".png", ".webp", ".gif", ".avif", ".heic", ".heif"}:
            return ".jpg" if candidate == ".jpeg" else candidate
    guessed = mimetypes.guess_extension(content_type.split(";")[0].strip()) if content_type else None
    return ".jpg" if guessed in {None, ".jpe", ".jpeg"} else guessed


def download_image(entry: dict[str, str], directory: str, stem: str) -> str:
    request = urllib.request.Request(entry["url"], headers={"User-Agent": USER_AGENT, "Accept": "image/avif,image/webp,image/*,*/*;q=0.8"})
    with urllib.request.urlopen(request, timeout=60) as response:
        content = response.read()
        content_type = response.headers.get("content-type", "")
    if len(content) < 32:
        raise RuntimeError("downloaded image is unexpectedly small")
    path_suffix = Path(urllib.parse.urlparse(entry["url"]).path).suffix.lower()
    known_image_suffixes = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".avif", ".heic", ".heif"}
    if not content_type.lower().startswith("image/") and path_suffix not in known_image_suffixes:
        raise RuntimeError(f"URL is not an image ({content_type or 'unknown content type'})")
    extension = _extension(entry.get("name", ""), content_type, entry["url"])
    if extension in {".heic", ".heif"}:
        try:
            from PIL import Image
            from pillow_heif import register_heif_opener
            register_heif_opener()
            with tempfile.NamedTemporaryFile(suffix=extension, delete=False) as source:
                source.write(content)
                source_name = source.name
            try:
                with Image.open(source_name) as image:
                    image = image.convert("RGB")
                    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as target:
                        target_name = target.name
                    image.save(target_name, "JPEG", quality=92, optimize=True)
                content = Path(target_name).read_bytes()
                extension = ".jpg"
            finally:
                Path(source_name).unlink(missing_ok=True)
                if "target_name" in locals():
                    Path(target_name).unlink(missing_ok=True)
        except Exception as error:
            raise RuntimeError(f"HEIC conversion failed: {error}") from error
    digest = hashlib.sha256(content).hexdigest()[:12]
    output_dir = ASSETS / directory
    output_dir.mkdir(parents=True, exist_ok=True)
    clean_stem = slugify(stem, "image")[:80]
    output = output_dir / f"{clean_stem}-{digest}{extension}"
    output.write_bytes(content)
    for old in output_dir.glob(f"{clean_stem}-*"):
        if old != output:
            old.unlink(missing_ok=True)
    return output.relative_to(ROOT).as_posix()


def resolve_image(page: dict[str, Any], property_names: Iterable[str], directory: str, stem: str, fallback: str = "") -> str:
    entries = file_entries(page, property_names)
    if entries:
        try:
            return download_image(entries[0], directory, stem)
        except Exception as error:
            print(f"WARN image download failed ({stem}): {error}", file=sys.stderr)
    for name in ("画像URL", "ジャケットURL"):
        candidate = url_value(page, name)
        if candidate:
            if candidate.startswith(("assets/", "images/")):
                return candidate
            if candidate.startswith(("http://", "https://")):
                try:
                    return download_image({"url": candidate, "name": name}, directory, stem)
                except Exception as error:
                    print(f"WARN external image download failed ({stem}): {error}", file=sys.stderr)
    return fallback


def sync_news(pages: list[dict[str, Any]]) -> bool:
    current = load_json("news.json")
    old_by_title = {item.get("title", ""): item for item in current.get("news", [])}
    incoming = []
    category_key = {"お知らせ": "notice", "カムバック": "comeback", "公演": "event", "記録": "record", "ファンクラブ": "fanclub"}
    for page in pages:
        if not is_public(page):
            continue
        title = text(page, "タイトル")
        start, _ = date_value(page, "公開日")
        if not title or not start:
            continue
        old = old_by_title.get(title, {})
        slug = text(page, "スラッグ") or old.get("slug") or slugify(title, page["id"].replace("-", ""))
        label = select(page, "カテゴリ") or old.get("label", "お知らせ")
        incoming.append({
            **old,
            "slug": slug,
            "date": start[:10].replace("-", "."),
            "category": category_key.get(label, slugify(label, "notice")),
            "label": label,
            "title": title,
            "text": text(page, "概要") or text(page, "日本語") or old.get("text", ""),
            "image": resolve_image(page, ["画像"], "news", slug, old.get("image", "")),
            "sourceLink": url_value(page, "公式URL") or old.get("sourceLink", ""),
            "sourceLabel": "公式案内を見る",
            "notionPageId": page.get("id", ""),
            "notionUrl": page.get("url", ""),
            "important": checkbox(page, "重要"),
        })
    if not incoming:
        print("SKIP news: no public Notion rows; existing data preserved")
        return False
    merged = merge_items(current.get("news", []), incoming, lambda x: str(x.get("slug") or x.get("title")))
    merged.sort(key=lambda x: str(x.get("date", "")), reverse=True)
    return backup_and_write("news.json", {**current, "source": "notion+repository-fallback", "news": merged})


def sync_schedule(pages: list[dict[str, Any]]) -> bool:
    current = load_json("schedule.json")
    incoming = []
    type_map = {"出演": "LIVE", "発売": "RELEASE", "投票": "VOTE", "誕生日": "BIRTHDAY", "ファンクラブ": "FC", "その他": "OTHER"}
    for page in pages:
        if not is_public(page):
            continue
        title = text(page, "予定名")
        start, _ = date_value(page, "開始")
        end, _ = date_value(page, "終了")
        if not title or not start:
            continue
        category = select(page, "カテゴリ") or "その他"
        page_id = str(page.get("id", ""))
        incoming.append({
            "id": f"notion-{page_id.replace('-', '')}",
            "title": title,
            "date": start[:10],
            "start": start,
            "end": end,
            "category": category,
            "type": type_map.get(category, "OTHER"),
            "description": text(page, "説明") or text(page, "日本語"),
            "location": text(page, "場所"),
            "link": url_value(page, "公式URL"),
            "linkLabel": "公式案内を見る",
            "image": resolve_image(page, ["画像"], "schedule", page_id, ""),
            "source": "notion",
            "notionPageId": page_id,
            "notionUrl": page.get("url", ""),
        })
    if not incoming:
        print("SKIP schedule: no public Notion rows; existing data preserved")
        return False
    merged = merge_items(current.get("events", []), incoming, lambda x: str(x.get("notionPageId") or f"{x.get('title')}|{x.get('start') or x.get('date')}"))
    merged.sort(key=lambda x: (str(x.get("start") or x.get("date") or ""), str(x.get("title", ""))))
    return backup_and_write("schedule.json", {**current, "source": "notion+repository-fallback", "events": merged})


def sync_members(pages: list[dict[str, Any]]) -> bool:
    current = load_json("members.json")
    old_by_name = {str(item.get("name", "")).upper(): item for item in current.get("members", [])}
    incoming = []
    for page in pages:
        if not is_public(page):
            continue
        name = text(page, "名前").upper()
        if not name:
            continue
        old = old_by_name.get(name, {})
        birth, _ = date_value(page, "誕生日")
        slug = old.get("slug") or slugify(name)
        image = resolve_image(page, ["画像"], "members", slug, old.get("previewImage", ""))
        incoming.append({
            **old,
            "slug": slug,
            "name": name,
            "japaneseName": text(page, "日本語") or old.get("japaneseName", ""),
            "koreanName": text(page, "韓国語") or old.get("koreanName", ""),
            "realName": text(page, "本名") or old.get("realName", ""),
            "birthDate": birth[:10] or old.get("birthDate", ""),
            "birthDateLabel": (birth[:10].replace("-", ".") if birth else old.get("birthDateLabel", "")),
            "keywords": text(page, "ポジション") or old.get("keywords", ""),
            "shortDescription": text(page, "紹介文") or old.get("shortDescription", ""),
            "profile": text(page, "紹介文") or old.get("profile", ""),
            "previewImage": image,
            "detailImage": image,
            "order": int(number(page, "表示順", old.get("order", 9999)) or 9999),
            "notionPageId": page.get("id", ""),
        })
    if not incoming:
        print("SKIP members: no public Notion rows; existing data preserved")
        return False
    merged = merge_items(current.get("members", []), incoming, lambda x: str(x.get("name", "")).upper())
    merged.sort(key=lambda x: (int(x.get("order", 9999)), str(x.get("name", ""))))
    return backup_and_write("members.json", {**current, "source": "notion+repository-fallback", "members": merged})


def discography_category(value: str) -> str:
    return {"Album": "full", "EP": "mini", "Single": "single", "Digital": "digital", "OST": "digital"}.get(value, "digital")


def sync_discography(pages: list[dict[str, Any]]) -> bool:
    current = load_json("discography.json")
    old_by_title = {item.get("title", ""): item for item in current.get("releases", [])}
    incoming = []
    for page in pages:
        if not is_public(page):
            continue
        title = text(page, "作品名")
        release_date, _ = date_value(page, "発売日")
        if not title or not release_date:
            continue
        old = old_by_title.get(title, {})
        kind = select(page, "種別") or old.get("type", "Digital")
        slug = old.get("slug") or slugify(title, page["id"].replace("-", ""))
        tracks = [line.strip() for line in re.split(r"[\r\n]+", text(page, "収録曲")) if line.strip()]
        cover = resolve_image(page, ["ジャケット"], "discography", slug, old.get("cover", ""))
        incoming.append({
            **old,
            "anchor": old.get("anchor") or slug,
            "slug": slug,
            "title": title,
            "releaseDate": release_date[:10],
            "category": discography_category(kind),
            "categoryName": kind,
            "type": kind,
            "description": text(page, "説明") or text(page, "日本語") or old.get("description", ""),
            "tracks": tracks or old.get("tracks", []),
            "appleMusic": url_value(page, "Apple Music") or old.get("appleMusic", ""),
            "spotify": url_value(page, "Spotify") or old.get("spotify", ""),
            "youtube": url_value(page, "YouTube") or old.get("youtube", ""),
            "youtubeMusic": url_value(page, "YouTube Music") or old.get("youtubeMusic", ""),
            "officialLink": url_value(page, "公式配信一覧") or old.get("officialLink", ""),
            "purchase": url_value(page, "購入URL") or old.get("purchase", ""),
            "cover": cover,
            "order": int(number(page, "表示順", old.get("order", 9999)) or 9999),
            "published": True,
            "themeId": text(page, "テーマID") or old.get("themeId", ""),
            "notionPageId": page.get("id", ""),
        })
    if not incoming:
        print("SKIP discography: no public Notion rows; existing data preserved")
        return False
    merged = merge_items(current.get("releases", []), incoming, lambda x: str(x.get("title", "")))
    merged.sort(key=lambda x: (int(x.get("order", 9999)), str(x.get("releaseDate", ""))), reverse=True)
    return backup_and_write("discography.json", {**current, "source": "notion+repository-fallback", "releases": merged})


def sync_wins(pages: list[dict[str, Any]]) -> bool:
    current = load_json("records.json")
    incoming = []
    for page in pages:
        if not is_public(page):
            continue
        title = text(page, "記録名")
        song = text(page, "楽曲")
        win_date, _ = date_value(page, "受賞日")
        program = select(page, "番組")
        if not song or not win_date or not program:
            continue
        score = number(page, "スコア", 0) or 0
        count = int(number(page, "回数", 9999) or 9999)
        page_id = str(page.get("id", ""))
        incoming.append({
            "title": title or f"{song} - {program}",
            "song": song,
            "date": win_date[:10],
            "program": program,
            "score": int(score),
            "description": text(page, "備考") or f"「{song}」で{program}の1位を獲得（{int(score):,}点）。",
            "videoUrl": url_value(page, "アンコールURL"),
            "sourceUrl": url_value(page, "アンコールURL"),
            "image": resolve_image(page, ["画像"], "wins", page_id, ""),
            "order": count,
            "videoLabel": "受賞・アンコールを見る",
            "notionPageId": page_id,
        })
    if not incoming:
        print("SKIP musicShowWins: no public Notion rows; existing data preserved")
        return False
    merged = merge_items(current.get("musicShowWins", []), incoming, lambda x: f"{x.get('date')}|{x.get('program')}|{x.get('song')}")
    merged.sort(key=lambda x: (int(x.get("order", 9999)), str(x.get("date", ""))))
    return backup_and_write("records.json", {**current, "source": "notion+repository-fallback", "musicShowWins": merged})


def sync_charts(pages: list[dict[str, Any]]) -> bool:
    current = load_json("records.json")
    incoming = []
    for page in pages:
        if not is_public(page):
            continue
        title = text(page, "記録名")
        record_date, _ = date_value(page, "記録日")
        if not title:
            continue
        incoming.append({
            "title": title,
            "type": select(page, "種別") or "その他",
            "song": text(page, "楽曲・作品"),
            "date": record_date[:10],
            "rank": number(page, "順位"),
            "value": number(page, "数値"),
            "change": number(page, "増減"),
            "unit": text(page, "単位"),
            "peak": checkbox(page, "最高記録"),
            "description": text(page, "備考"),
            "sourceUrl": url_value(page, "出典URL"),
            "notionPageId": page.get("id", ""),
        })
    if not incoming:
        print("SKIP charts: no public Notion rows; existing data preserved")
        return False
    merged = merge_items(current.get("otherChartRecords", []), incoming, lambda x: str(x.get("notionPageId") or f"{x.get('title')}|{x.get('date')}"))
    merged.sort(key=lambda x: str(x.get("date", "")), reverse=True)
    return backup_and_write("records.json", {**current, "source": "notion+repository-fallback", "otherChartRecords": merged})


def sync_guides(pages: list[dict[str, Any]]) -> bool:
    streaming = load_json("streaming-guide.json")
    voting = load_json("voting-guide.json")
    chants = load_json("chants.json")
    stream_rows, vote_rows, chant_rows = [], [], []
    for page in pages:
        if not is_public(page):
            continue
        title = text(page, "ガイド名")
        kind = select(page, "種別")
        if not title or not kind:
            continue
        order = int(number(page, "表示順", 9999) or 9999)
        page_id = str(page.get("id", ""))
        base = {
            "title": title,
            "subtitle": text(page, "対象"),
            "description": text(page, "日本語"),
            "note": text(page, "注意事項"),
            "link": url_value(page, "公式URL"),
            "order": order,
            "notionPageId": page_id,
        }
        icon = resolve_image(page, ["アイコン"], "guide-icons", page_id, "")
        images = file_entries(page, ["画像"])
        step_image = ""
        if images:
            try:
                step_image = download_image(images[0], "guides", page_id)
            except Exception as error:
                print(f"WARN guide image failed ({title}): {error}", file=sys.stderr)
        if kind == "ストリーミング":
            stream_rows.append({**base, "type": "音楽ストリーミング", "icon": icon, "buttonLabel": "公式ページを開く", "steps": ([{"title": "ガイド画像", "text": base["description"], "image": step_image}] if step_image else [])})
        elif kind == "投票":
            vote_rows.append({**base, "icon": icon, "tags": [base["subtitle"]] if base["subtitle"] else [], "guide": {"steps": ([{"title": "投票ガイド", "text": base["description"], "image": step_image}] if step_image else []), "note": base["note"]}})
        elif kind == "掛け声":
            chant_rows.append({**base, "song": title, "category": "latest", "lyrics": base["description"], "image": step_image, "anchor": slugify(title)})
    changed = False
    if stream_rows:
        merged = merge_items(streaming.get("guides", []), stream_rows, lambda x: str(x.get("title", "")))
        merged.sort(key=lambda x: (int(x.get("order", 9999)), str(x.get("title", ""))))
        changed |= backup_and_write("streaming-guide.json", {**streaming, "source": "notion+repository-fallback", "guides": merged})
    else:
        print("SKIP streaming guides: no public Notion rows")
    if vote_rows:
        merged = merge_items(voting.get("apps", []), vote_rows, lambda x: str(x.get("title", "")))
        merged.sort(key=lambda x: (int(x.get("order", 9999)), str(x.get("title", ""))))
        changed |= backup_and_write("voting-guide.json", {**voting, "source": "notion+repository-fallback", "apps": merged})
    else:
        print("SKIP voting guides: no public Notion rows")
    if chant_rows:
        merged = merge_items(chants.get("chants", []), chant_rows, lambda x: str(x.get("song") or x.get("title", "")))
        merged.sort(key=lambda x: (int(x.get("order", 9999)), str(x.get("title", ""))))
        changed |= backup_and_write("chants.json", {**chants, "source": "notion+repository-fallback", "chants": merged})
    else:
        print("SKIP chants: no public Notion rows")
    return changed


FANBASE_SOCIAL_DENY = re.compile(r"(?:x\.com/nswer_japan|instagram\.com/nswer_japan|tiktok\.com/@?nswer[._]japan)", re.I)


def sync_official_links(pages: list[dict[str, Any]]) -> bool:
    current = load_json("official-links.json")
    incoming = []
    for page in pages:
        if not is_public(page):
            continue
        title = text(page, "リンク名")
        link = url_value(page, "URL")
        if not title or not link:
            continue
        if FANBASE_SOCIAL_DENY.search(link):
            print(f"SKIP prohibited fanbase SNS link: {title} / {link}")
            continue
        category = select(page, "カテゴリ") or "その他"
        page_id = str(page.get("id", ""))
        incoming.append({
            "title": title,
            "category": category,
            "categoryOrder": {"NMIXX公式": 10, "日本公式": 20, "SNS": 30, "音楽配信": 40, "ファンクラブ": 50}.get(category, 90),
            "order": int(number(page, "表示順", 9999) or 9999),
            "url": link,
            "subtitle": text(page, "日本語"),
            "description": text(page, "説明"),
            "label": title.upper(),
            "icon": resolve_image(page, ["アイコン"], "official-links", page_id, ""),
            "iconText": "",
            "anchor": slugify(title, page_id.replace("-", "")),
            "notionPageId": page_id,
        })
    if not incoming:
        print("SKIP officialLinks: no public Notion rows; existing data preserved")
        return False
    merged = merge_items(current.get("links", []), incoming, lambda x: str(x.get("url") or x.get("title")))
    merged = [item for item in merged if not FANBASE_SOCIAL_DENY.search(str(item.get("url", "")))]
    merged.sort(key=lambda x: (int(x.get("categoryOrder", 9999)), int(x.get("order", 9999)), str(x.get("title", ""))))
    return backup_and_write("official-links.json", {**current, "source": "notion+repository-fallback", "links": merged})


def sync_homepage(pages: list[dict[str, Any]]) -> bool:
    current = load_json("homepage.json")
    old_by_title = {item.get("title", ""): item for item in current.get("items", [])}
    incoming = []
    for page in pages:
        if not is_public(page):
            continue
        title = text(page, "項目名")
        if not title:
            continue
        old = old_by_title.get(title, {})
        page_id = str(page.get("id", ""))
        incoming.append({
            **old,
            "slug": old.get("slug") or slugify(title, page_id.replace("-", "")),
            "title": title,
            "type": select(page, "種別") or old.get("type", "カード"),
            "heading": text(page, "見出し") or old.get("heading", ""),
            "description": text(page, "本文") or text(page, "日本語") or old.get("description", ""),
            "buttonLabel": text(page, "ボタン文言") or old.get("buttonLabel", ""),
            "linkUrl": url_value(page, "リンク先") or old.get("linkUrl", ""),
            "image": resolve_image(page, ["画像"], "homepage", page_id, old.get("image", "")),
            "themeId": text(page, "テーマID") or old.get("themeId", ""),
            "anchor": old.get("anchor") or slugify(title, page_id.replace("-", "")),
            "order": int(number(page, "表示順", old.get("order", 9999)) or 9999),
            "notionPageId": page_id,
        })
    if not incoming:
        print("SKIP homepage: no public Notion rows; existing data preserved")
        return False
    merged = merge_items(current.get("items", []), incoming, lambda x: str(x.get("title", "")))
    merged.sort(key=lambda x: (int(x.get("order", 9999)), str(x.get("title", ""))))
    return backup_and_write("homepage.json", {**current, "source": "notion+repository-fallback", "items": merged})


def valid_hex(value: str, fallback: str) -> str:
    value = value.strip()
    return value.lower() if re.fullmatch(r"#[0-9a-fA-F]{6}", value) else fallback


def sync_site_theme(pages: list[dict[str, Any]]) -> bool:
    active = [page for page in pages if checkbox(page, "有効")]
    if not active:
        print("SKIP siteTheme: no active Notion row; existing data preserved")
        return False
    page = active[0]
    current = load_json("site-theme.json")
    old = current.get("theme", {})
    main = valid_hex(text(page, "メインカラー"), old.get("primary", "#8f7cff"))
    sub = valid_hex(text(page, "サブカラー"), old.get("secondary", "#ff71b8"))
    accent = valid_hex(text(page, "アクセントカラー"), old.get("accent", "#58e0d1"))
    theme = {
        **old,
        "name": text(page, "テーマ名") or old.get("name", "NSWER"),
        "background": valid_hex(text(page, "ダーク背景"), old.get("background", "#080b16")),
        "background2": valid_hex(text(page, "グラデーション開始"), old.get("background2", "#10162a")),
        "card": valid_hex(text(page, "カード背景色"), old.get("card", "#151c33")),
        "card2": valid_hex(text(page, "グラデーション終了"), old.get("card2", "#1d2542")),
        "primary": main,
        "primarySoft": sub,
        "secondary": sub,
        "accent": accent,
        "blue": main,
        "text": valid_hex(text(page, "ダーク文字色"), old.get("text", "#f8f9ff")),
        "lightBackground": valid_hex(text(page, "背景色"), old.get("lightBackground", "#f6f7ff")),
        "lightCard": valid_hex(text(page, "カード背景色"), old.get("lightCard", "#ffffff")),
        "lightText": valid_hex(text(page, "文字色"), old.get("lightText", "#171a2b")),
        "notionThemeId": text(page, "テーマID"),
    }
    return backup_and_write("site-theme.json", {**current, "source": "notion", "theme": theme})


def sync_comeback_themes(pages: list[dict[str, Any]]) -> bool:
    current = load_json("comeback-themes.json")
    old_by_key = {item.get("key", ""): item for item in current.get("themes", [])}
    incoming = []
    active_candidates = []
    for page in pages:
        title = text(page, "カムバック名")
        key = text(page, "テーマID") or slugify(title, page.get("id", "").replace("-", ""))
        if not title:
            continue
        old = old_by_key.get(key, {})
        start, _ = date_value(page, "開始日")
        end, _ = date_value(page, "終了日")
        colors = {
            **old.get("colors", {}),
            "background": valid_hex(text(page, "背景色"), old.get("colors", {}).get("background", "#080b16")),
            "background2": valid_hex(text(page, "グラデーション開始"), old.get("colors", {}).get("background2", "#10162a")),
            "card": valid_hex(text(page, "グラデーション終了"), old.get("colors", {}).get("card", "#151c33")),
            "primary": valid_hex(text(page, "メインカラー"), old.get("colors", {}).get("primary", "#8f7cff")),
            "secondary": valid_hex(text(page, "サブカラー"), old.get("colors", {}).get("secondary", "#ff71b8")),
            "accent": valid_hex(text(page, "アクセントカラー"), old.get("colors", {}).get("accent", "#58e0d1")),
            "text": valid_hex(text(page, "文字色"), old.get("colors", {}).get("text", "#f8f9ff")),
        }
        page_id = str(page.get("id", ""))
        item = {
            **old,
            "key": key,
            "name": title,
            "release": title,
            "startDate": start[:10],
            "endDate": end[:10],
            "colors": colors,
            "heroDesktop": resolve_image(page, ["PC背景画像"], "comeback", f"{key}-desktop", old.get("heroDesktop", "")),
            "heroMobile": resolve_image(page, ["スマホ背景画像"], "comeback", f"{key}-mobile", old.get("heroMobile", "")),
            "logo": resolve_image(page, ["ロゴ画像"], "comeback", f"{key}-logo", old.get("logo", "")),
            "cover": resolve_image(page, ["ジャケット画像"], "comeback", f"{key}-cover", old.get("cover", "")),
            "notionPageId": page_id,
        }
        incoming.append(item)
        if checkbox(page, "有効"):
            active_candidates.append((start or "", key))
    if not incoming:
        print("SKIP comebackThemes: no Notion rows; existing data preserved")
        return False
    merged = merge_items(current.get("themes", []), incoming, lambda x: str(x.get("key", "")))
    active_key = sorted(active_candidates)[-1][1] if active_candidates else current.get("activeTheme", "default")
    return backup_and_write("comeback-themes.json", {**current, "source": "notion+repository-fallback", "activeTheme": active_key, "themes": merged})


SYNC_JOBS: list[tuple[str, Callable[[list[dict[str, Any]]], bool]]] = [
    ("news", sync_news),
    ("schedule", sync_schedule),
    ("members", sync_members),
    ("discography", sync_discography),
    ("musicShowWins", sync_wins),
    ("charts", sync_charts),
    ("guides", sync_guides),
    ("officialLinks", sync_official_links),
    ("homepage", sync_homepage),
    ("siteTheme", sync_site_theme),
    ("comebackThemes", sync_comeback_themes),
]


def main() -> int:
    ASSETS.mkdir(parents=True, exist_ok=True)
    changed_sources: list[str] = []
    failures: list[str] = []
    successful_queries = 0
    for name, handler in SYNC_JOBS:
        try:
            pages = query_pages(name)
            successful_queries += 1
            print(f"Notion {name}: {len(pages)} rows fetched")
            if handler(pages):
                changed_sources.append(name)
        except Exception as error:
            failures.append(f"{name}: {error}")
            print(f"ERROR {name}: {error}\nExisting repository data was preserved.", file=sys.stderr)
    status = {
        "generatedAt": now_iso(),
        "workspace": CONFIG.get("workspace", "NMIXX Fanbase JP"),
        "source": "notion",
        "successfulQueries": successful_queries,
        "changedSources": changed_sources,
        "failures": failures,
        "safety": "A failed or empty source never replaces existing repository JSON.",
    }
    backup_and_write("notion-sync-status.json", status)
    print(f"Notion sync complete: changed={changed_sources or 'none'}, failures={len(failures)}")
    if successful_queries == 0:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
