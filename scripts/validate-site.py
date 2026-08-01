#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
TEXT_EXT = {
    '.html', '.js', '.mjs', '.py', '.json', '.md', '.txt', '.css',
    '.xml', '.webmanifest', '.yml', '.yaml', '.sh', '.csv', '.ics'
}
FORBIDDEN = [
    r'(?i)rescene', r'リセンヌ', r'리센느', r'(?i)plus\s*chat',
    r'(?i)the\s+show', r'(?i)bigc', r'\bWONI\b', r'\bLIV\b',
    r'\bMINAMI\b', r'\bMAY\b', r'\bZENA\b', r'(?i)scenedrome',
    r'(?i)love\s+attack', r'(?i)pretty\s+girl', r'(?i)lip\s+bomb',
    r'(?i)busy\s+boy', r'(?i)glow\s+up', r'(?i)pinball',
    r'(?i)remember\s+a\s+scene', r'(?i)scent\s*·\s*scene',
    r'香りと記憶', r'香りを通じて', r'(?i)artist/nswer/',
    r'(?i)nswer-fb\.jp', r'(?i)x\.com/nswer_japan',
    r'(?i)instagram\.com/nswer_japan',
    r'(?i)tiktok\.com/@?nswer[._]japan'
]
IGNORE_DIRS = {'.git', 'node_modules'}
YOUTUBE_DATA = Path('data/youtube-channels.json')
EXPECTED_YOUTUBE = {
    'key': 'nmixx',
    'handle': '@NMIXXOfficial',
    'channelId': 'UCnUAyD4t2LkvW68YrDh7fDg',
    'url': 'https://www.youtube.com/@NMIXXOfficial',
}
ALLOWED_VIDEO_TYPES = {'video', 'short', 'live'}
TYPE_PRIORITY = {'video': 1, 'short': 2, 'live': 3}

errors: list[str] = []
SELF = Path(__file__).resolve()


def relative(path: Path) -> Path:
    return path.resolve().relative_to(ROOT.resolve())


def validate_youtube_data(path: Path) -> None:
    """Validate source identity and three-category integrity.

    Video titles are public content from the verified NMIXX channel. They are not
    subjected to the site's legacy-word blacklist because a legitimate upload can
    mention another artist. Instead, every entry must carry the exact NMIXX channel
    identity and a valid source-tab category.
    """
    try:
        payload = json.loads(path.read_text(encoding='utf-8'))
    except Exception as exc:
        errors.append(f'JSON error {YOUTUBE_DATA}: {exc}')
        return

    channels = payload.get('channels')
    if not isinstance(channels, list) or len(channels) != 1:
        errors.append(f'YouTube data must contain exactly one NMIXX channel: {YOUTUBE_DATA}')
        return

    channel = channels[0]
    if not isinstance(channel, dict):
        errors.append(f'Invalid YouTube channel object: {YOUTUBE_DATA}')
        return

    for field, expected in EXPECTED_YOUTUBE.items():
        actual = channel.get(field)
        if actual != expected:
            errors.append(
                f'Unexpected YouTube {field}: expected {expected!r}, got {actual!r}'
            )

    videos = channel.get('videos')
    if not isinstance(videos, list):
        errors.append(f'YouTube videos must be an array: {YOUTUBE_DATA}')
        return

    seen_ids: set[str] = set()
    computed_counts = {'video': 0, 'short': 0, 'live': 0}

    for index, video in enumerate(videos):
        label = f'{YOUTUBE_DATA} videos[{index}]'
        if not isinstance(video, dict):
            errors.append(f'Invalid YouTube video object: {label}')
            continue

        video_id = str(video.get('videoId') or '').strip()
        if not video_id:
            errors.append(f'Missing videoId: {label}')
        elif video_id in seen_ids:
            errors.append(f'Duplicate YouTube videoId {video_id}: {label}')
        else:
            seen_ids.add(video_id)

        if video.get('channelKey') != EXPECTED_YOUTUBE['key']:
            errors.append(f'Unexpected channelKey: {label}')
        if video.get('channelId') != EXPECTED_YOUTUBE['channelId']:
            errors.append(f'Unexpected channelId: {label}')

        video_type = video.get('videoType')
        if video_type not in ALLOWED_VIDEO_TYPES:
            errors.append(f'Invalid videoType {video_type!r}: {label}')
            continue
        computed_counts[video_type] += 1

        source_types = video.get('sourceTypes', [video_type])
        if not isinstance(source_types, list) or not source_types:
            errors.append(f'Invalid sourceTypes: {label}')
            continue
        invalid_types = [item for item in source_types if item not in ALLOWED_VIDEO_TYPES]
        if invalid_types:
            errors.append(f'Invalid sourceTypes {invalid_types!r}: {label}')
            continue
        expected_type = max(source_types, key=lambda item: TYPE_PRIORITY[item])
        if video_type != expected_type:
            errors.append(
                f'Category precedence mismatch: {label} expected {expected_type!r}, got {video_type!r}'
            )

    if channel.get('totalVideos') != len(videos):
        errors.append(
            f'YouTube totalVideos mismatch: expected {len(videos)}, got {channel.get("totalVideos")!r}'
        )

    declared_counts = channel.get('typeCounts')
    if declared_counts != computed_counts:
        errors.append(
            f'YouTube typeCounts mismatch: expected {computed_counts!r}, got {declared_counts!r}'
        )

    if payload.get('historyComplete') is True:
        tabs = set(payload.get('successfulTabs') or [])
        if tabs != {'videos', 'shorts', 'streams'}:
            errors.append(
                'Complete YouTube history must have successful videos/shorts/streams tabs'
            )
        if payload.get('partialFailures'):
            errors.append('Complete YouTube history cannot contain partialFailures')


for path in ROOT.rglob('*'):
    if (
        not path.is_file()
        or path.resolve() == SELF
        or any(part in IGNORE_DIRS for part in path.parts)
    ):
        continue

    rel = relative(path)

    if path.suffix.lower() == '.json':
        try:
            json.loads(path.read_text(encoding='utf-8'))
        except Exception as exc:
            errors.append(f'JSON error {rel}: {exc}')

    if path.suffix.lower() in TEXT_EXT:
        # YouTube is machine-generated public channel data. Validate its exact
        # channel identity and categories below instead of scanning video titles.
        if rel == YOUTUBE_DATA:
            continue
        text = path.read_text(encoding='utf-8', errors='ignore')
        for pattern in FORBIDDEN:
            if re.search(pattern, text):
                errors.append(f'Forbidden text {pattern}: {rel}')


youtube_path = ROOT / YOUTUBE_DATA
if youtube_path.exists():
    validate_youtube_data(youtube_path)
else:
    errors.append(f'Missing required data: {YOUTUBE_DATA}')

for path in ROOT.rglob('*.html'):
    if any(part in IGNORE_DIRS for part in path.parts):
        continue
    text = path.read_text(encoding='utf-8', errors='ignore')
    for _, url in re.findall(r'\b(src|href)=["\']([^"\']+)["\']', text, re.I):
        if (
            not url
            or '${' in url
            or '{{' in url
            or url.startswith((
                '#', 'mailto:', 'tel:', 'javascript:', 'data:', 'webcal:',
                'http://', 'https://', '//'
            ))
        ):
            continue
        clean = unquote(urlsplit(url).path)
        if not clean:
            continue
        target = (
            (ROOT / clean.lstrip('/'))
            if clean.startswith('/')
            else (path.parent / clean)
        ).resolve()
        try:
            target.relative_to(ROOT.resolve())
        except ValueError:
            errors.append(f'Path escapes root: {relative(path)} -> {url}')
            continue
        if not target.exists():
            errors.append(f'Missing local target: {relative(path)} -> {url}')

required_data = [
    'data/members.json', 'data/news.json', 'data/schedule.json',
    'data/discography.json', 'data/records.json', 'data/streaming-guide.json',
    'data/voting-guide.json', 'data/chants.json', 'data/official-links.json',
    'data/homepage.json', 'data/site-theme.json', 'data/comeback-themes.json',
    str(YOUTUBE_DATA),
]
for rel in required_data:
    if not (ROOT / rel).exists():
        errors.append(f'Missing required data: {rel}')

if errors:
    print(f'検査エラー {len(errors)}件')
    for error in errors[:200]:
        print('-', error)
    sys.exit(1)

print('サイト検査に合格しました。')
