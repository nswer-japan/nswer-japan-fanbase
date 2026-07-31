#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import re
import shutil
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JST = timezone(timedelta(hours=9))
CONFIG = {
    "news": ("data/csv/news.csv", "data/news.json", "news"),
    "schedule": ("data/csv/schedule.csv", "data/schedule.json", "events"),
    "wins": ("data/csv/music-show-wins.csv", "data/records.json", "musicShowWins"),
    "discography": ("data/csv/discography.csv", "data/discography.json", "releases"),
    "links": ("data/csv/official-links.csv", "data/official-links.json", "links"),
    "updates": ("data/csv/site-updates.csv", "data/site-updates.json", "items"),
}
PLACEHOLDERS = {"example-news", "example-event", "Example Song", "タイトル", "予定タイトル", "Example Release", "Example Link", "Example Update"}


def fail(message: str) -> None:
    raise SystemExit(f"CSV取込を中止しました: {message}")


def clean_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            fail(f"{path} に見出し行がありません。")
        rows = []
        for raw in reader:
            row = {str(k).strip(): (v.strip() if isinstance(v, str) else "") for k, v in raw.items() if k is not None}
            if any(row.values()):
                rows.append(row)
    if not rows:
        fail(f"{path} にデータ行がありません。既存JSONは変更していません。")
    if any(value in PLACEHOLDERS for row in rows for value in row.values()):
        fail("テンプレート用の例示文字が残っています。実データへ置き換えてください。")
    return rows


def require(row: dict[str, str], fields: tuple[str, ...], row_number: int) -> None:
    missing = [field for field in fields if not row.get(field)]
    if missing:
        fail(f"{row_number}行目の必須項目が不足しています: {', '.join(missing)}")


def normalize_news(rows: list[dict[str, str]]) -> list[dict]:
    result = []
    for index, row in enumerate(rows, start=2):
        require(row, ("slug", "date", "title"), index)
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", row["slug"]):
            fail(f"{index}行目のslugは半角英小文字・数字・ハイフンで入力してください。")
        if not re.fullmatch(r"\d{4}\.\d{2}\.\d{2}", row["date"]):
            fail(f"{index}行目のdateはYYYY.MM.DD形式で入力してください。")
        result.append({
            "slug": row["slug"], "date": row["date"], "category": row.get("category") or "notice",
            "label": row.get("label") or "NEWS", "title": row["title"], "text": row.get("text", ""),
            "image": row.get("image", ""), "sourceLink": row.get("sourceLink", ""),
            "sourceLabel": row.get("sourceLabel") or "詳細を見る",
        })
    return result


def iso_time(date: str, value: str) -> str:
    if not value:
        return ""
    if "T" in value:
        return value
    if re.fullmatch(r"\d{2}:\d{2}", value):
        return f"{date}T{value}:00+09:00"
    fail(f"時刻「{value}」はHH:MMまたはISO 8601形式で入力してください。")
    return ""


def normalize_schedule(rows: list[dict[str, str]]) -> list[dict]:
    result = []
    for index, row in enumerate(rows, start=2):
        require(row, ("id", "title", "date"), index)
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]*", row["id"]):
            fail(f"{index}行目のidは半角英数字・ハイフン・アンダーバーで入力してください。")
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", row["date"]):
            fail(f"{index}行目のdateはYYYY-MM-DD形式で入力してください。")
        start = iso_time(row["date"], row.get("start", ""))
        end = iso_time(row["date"], row.get("end", ""))
        result.append({
            "id": row["id"], "title": row["title"], "date": row["date"], "start": start, "end": end,
            "category": row.get("category") or "event", "type": row.get("type") or "EVENT",
            "description": row.get("description", ""), "link": row.get("link", ""),
            "linkLabel": row.get("linkLabel", ""), "image": row.get("image", ""),
            "source": row.get("source") or "repository-csv",
        })
    return result


def normalize_wins(rows: list[dict[str, str]]) -> list[dict]:
    result = []
    for index, row in enumerate(rows, start=2):
        require(row, ("song", "date", "program"), index)
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", row["date"]):
            fail(f"{index}行目のdateはYYYY-MM-DD形式で入力してください。")
        order_text = row.get("order", "")
        score_text = row.get("score", "")
        if order_text and not order_text.isdigit():
            fail(f"{index}行目のorderは整数で入力してください。")
        if score_text and not score_text.isdigit():
            fail(f"{index}行目のscoreは整数で入力してください。")
        result.append({
            "title": row.get("title") or f'{row["song"]} - {row["program"]}',
            "song": row["song"], "date": row["date"], "program": row["program"],
            "description": row.get("description", ""), "videoUrl": row.get("videoUrl", ""),
            "image": row.get("image", ""), "order": int(order_text) if order_text else len(result) + 1,
            "videoLabel": row.get("videoLabel") or "アンコール・受賞映像を見る",
            "score": int(score_text) if score_text else 0,
        })
    return result



def split_pipe(value: str) -> list[str]:
    return [item.strip() for item in value.split("|") if item.strip()]


def as_bool(value: str, default: bool = True) -> bool:
    if not value:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on", "公開"}


def normalize_discography(rows: list[dict[str, str]]) -> list[dict]:
    result = []
    for index, row in enumerate(rows, start=2):
        require(row, ("slug", "title", "releaseDate"), index)
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", row["slug"]):
            fail(f"{index}行目のslugは半角英小文字・数字・ハイフンで入力してください。")
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", row["releaseDate"]):
            fail(f"{index}行目のreleaseDateはYYYY-MM-DD形式で入力してください。")
        order_text = row.get("order", "")
        if order_text and not order_text.isdigit():
            fail(f"{index}行目のorderは整数で入力してください。")
        result.append({
            "anchor": row.get("anchor") or row["slug"], "slug": row["slug"], "title": row["title"],
            "releaseDate": row["releaseDate"], "category": row.get("category") or "digital",
            "categoryName": row.get("categoryName", ""), "mark": row.get("mark", ""),
            "badge": row.get("badge", ""), "type": row.get("type", ""),
            "description": row.get("description", ""), "tracks": split_pipe(row.get("tracks", "")),
            "appleMusic": row.get("appleMusic", ""), "spotify": row.get("spotify", ""),
            "youtubeMusic": row.get("youtubeMusic", ""), "lineMusic": row.get("lineMusic", ""),
            "youtube": row.get("youtube", ""), "officialLink": row.get("officialLink", ""),
            "purchase": row.get("purchase", ""), "cover": row.get("cover", ""),
            "order": int(order_text) if order_text else len(result) + 1,
            "published": as_bool(row.get("published", ""), True),
        })
    return result


def normalize_links(rows: list[dict[str, str]]) -> list[dict]:
    result = []
    for index, row in enumerate(rows, start=2):
        require(row, ("title", "url"), index)
        category_order = row.get("categoryOrder", "")
        order = row.get("order", "")
        if category_order and not category_order.isdigit():
            fail(f"{index}行目のcategoryOrderは整数で入力してください。")
        if order and not order.isdigit():
            fail(f"{index}行目のorderは整数で入力してください。")
        result.append({
            "title": row["title"], "category": row.get("category") or "公式リンク",
            "categoryOrder": int(category_order) if category_order else 100,
            "order": int(order) if order else len(result) + 1, "url": row["url"],
            "subtitle": row.get("subtitle", ""), "description": row.get("description", ""),
            "label": row.get("label", ""), "icon": row.get("icon", ""),
            "iconText": row.get("iconText", ""), "anchor": row.get("anchor", ""),
        })
    return result


def normalize_updates(rows: list[dict[str, str]]) -> list[dict]:
    result = []
    for index, row in enumerate(rows, start=2):
        require(row, ("date", "title", "description"), index)
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", row["date"]):
            fail(f"{index}行目のdateはYYYY-MM-DD形式で入力してください。")
        result.append({
            "date": row["date"], "title": row["title"], "description": row["description"],
            "commit": row.get("commit", ""), "files": split_pipe(row.get("files", "")),
        })
    return result

def atomic_write(path: Path, obj: dict) -> Path:
    backup_dir = ROOT / "data/backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(JST).strftime("%Y%m%d-%H%M%S")
    backup = backup_dir / f"{path.stem}-{stamp}.json"
    shutil.copy2(path, backup)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)
    return backup


def main() -> None:
    if len(sys.argv) < 2 or sys.argv[1] not in CONFIG:
        raise SystemExit("使い方: python scripts/import-csv.py news|schedule|wins|discography|links|updates")
    kind = sys.argv[1]
    csv_rel, json_rel, array_key = CONFIG[kind]
    rows = clean_rows(ROOT / csv_rel)
    normalized = {"news": normalize_news, "schedule": normalize_schedule, "wins": normalize_wins, "discography": normalize_discography, "links": normalize_links, "updates": normalize_updates}[kind](rows)
    target = ROOT / json_rel
    obj = json.loads(target.read_text(encoding="utf-8"))
    obj[array_key] = normalized
    obj["generatedAt"] = datetime.now(JST).isoformat(timespec="seconds")
    obj["source"] = "repository-csv"
    backup = atomic_write(target, obj)
    print(f"{len(normalized)}件を {json_rel} へ反映しました。バックアップ: {backup.relative_to(ROOT)}")
    print("続けて python scripts/build-content.py を実行してください。")


if __name__ == "__main__":
    main()
