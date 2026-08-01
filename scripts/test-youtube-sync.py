#!/usr/bin/env python3
"""Offline regression tests for the NMIXX YouTube tab synchronizer."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "sync-youtube-channels.mjs"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_sync(work: Path, mode: str, *, fail_tabs: str = "", dataset: str = "full") -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.update(
        {
            "PATH": f"{work / 'bin'}:{env.get('PATH', '')}",
            "YOUTUBE_SYNC_MODE": mode,
            "YOUTUBE_TAB_RETRIES": "1",
            "YOUTUBE_TAB_TIMEOUT_MS": "10000",
            "FAKE_FAIL_TABS": fail_tabs,
            "FAKE_DATASET": dataset,
            "FAKE_LOG": str(work / "yt-dlp-args.jsonl"),
        }
    )
    return subprocess.run(
        ["node", str(SCRIPT), "data/youtube-channels.json"],
        cwd=work,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="nswer-youtube-test-") as temporary:
        work = Path(temporary)
        (work / "data").mkdir()
        (work / "bin").mkdir()
        seed = {
            "generatedAt": "2026-01-01T00:00:00.000Z",
            "historyComplete": False,
            "channels": [
                {
                    "key": "nmixx",
                    "channelId": "UCnUAyD4t2LkvW68YrDh7fDg",
                    "videos": [
                        {
                            "videoId": "OLDSEED0001",
                            "title": "Seed",
                            "url": "https://www.youtube.com/watch?v=OLDSEED0001",
                            "thumbnail": "",
                            "publishedAt": "2022-01-01T00:00:00.000Z",
                            "videoType": "video",
                            "sourceTypes": ["video"],
                            "channelKey": "nmixx",
                            "channelId": "UCnUAyD4t2LkvW68YrDh7fDg",
                        }
                    ],
                }
            ],
        }
        data_path = work / "data" / "youtube-channels.json"
        data_path.write_text(json.dumps(seed), encoding="utf-8")

        fake = work / "bin" / "yt-dlp"
        fake.write_text(
            r'''#!/usr/bin/env python3
import json, os, sys
args=sys.argv[1:]
url=args[-1]
tab=url.rstrip('/').split('/')[-1]
with open(os.environ['FAKE_LOG'],'a',encoding='utf-8') as f:
    f.write(json.dumps({'tab':tab,'args':args},ensure_ascii=False)+'\n')
failed=set(filter(None,os.environ.get('FAKE_FAIL_TABS','').split(',')))
if tab in failed or 'all' in failed:
    print(f'forced failure: {tab}',file=sys.stderr)
    raise SystemExit(1)
dataset=os.environ.get('FAKE_DATASET','full')
base={
 'videos':[{'id':'VIDEO000001','title':'Regular 30 second video','timestamp':1700000000,'duration':30,'thumbnails':[]},
           {'id':'DUPLICATE01','title':'Stream archive','timestamp':1700000100,'duration':300,'thumbnails':[]}],
 'shorts':[{'id':'SHORT000001','title':'Short','timestamp':1700000200,'duration':90,'thumbnails':[]}],
 'streams':[{'id':'LIVE0000001','title':'Live','timestamp':1700000300,'duration':3600,'live_status':'was_live','thumbnails':[]},
            {'id':'DUPLICATE01','title':'Stream archive','timestamp':1700000100,'duration':300,'live_status':'was_live','thumbnails':[]}],
}
if dataset=='recent':
    base['videos'].append({'id':'NEWVIDEO001','title':'New upload','timestamp':1800000000,'duration':200,'thumbnails':[]})
print(json.dumps({'playlist_count':len(base[tab]),'entries':base[tab]},ensure_ascii=False))
''',
            encoding="utf-8",
        )
        fake.chmod(0o755)

        # Even when "recent" is requested, an incomplete seed must force an unlimited full sync.
        first = run_sync(work, "recent")
        assert first.returncode == 0, first.stderr
        payload = json.loads(data_path.read_text(encoding="utf-8"))
        videos = payload["channels"][0]["videos"]
        by_id = {item["videoId"]: item for item in videos}
        assert payload["historyComplete"] is True
        assert payload["effectiveSyncMode"] == "full"
        assert "OLDSEED0001" not in by_id
        assert set(by_id) == {"VIDEO000001", "DUPLICATE01", "SHORT000001", "LIVE0000001"}
        assert by_id["VIDEO000001"]["videoType"] == "video"  # duration alone must not make it a Short
        assert by_id["SHORT000001"]["videoType"] == "short"  # source tab is authoritative
        assert by_id["DUPLICATE01"]["videoType"] == "live"   # live has the highest precedence
        assert set(by_id["DUPLICATE01"]["sourceTypes"]) == {"video", "live"}
        assert payload["channels"][0]["typeCounts"] == {"video": 1, "short": 1, "live": 2}
        logs = [json.loads(line) for line in (work / "yt-dlp-args.jsonl").read_text(encoding="utf-8").splitlines()]
        assert {row["tab"] for row in logs} == {"videos", "shorts", "streams"}
        assert all("--playlist-end" not in row["args"] for row in logs)

        # After a complete archive exists, recent mode must merge new entries without losing history.
        (work / "yt-dlp-args.jsonl").write_text("", encoding="utf-8")
        recent = run_sync(work, "recent", dataset="recent")
        assert recent.returncode == 0, recent.stderr
        payload = json.loads(data_path.read_text(encoding="utf-8"))
        ids = {item["videoId"] for item in payload["channels"][0]["videos"]}
        assert "NEWVIDEO001" in ids
        assert "SHORT000001" in ids and "LIVE0000001" in ids
        logs = [json.loads(line) for line in (work / "yt-dlp-args.jsonl").read_text(encoding="utf-8").splitlines()]
        assert all("--playlist-end" in row["args"] for row in logs)

        # A partial full-sync failure must preserve the last complete archive.
        partial = run_sync(work, "full", fail_tabs="shorts")
        assert partial.returncode == 0, partial.stderr
        payload = json.loads(data_path.read_text(encoding="utf-8"))
        ids = {item["videoId"] for item in payload["channels"][0]["videos"]}
        assert "SHORT000001" in ids
        assert payload["historyComplete"] is True
        assert payload["partialFailures"]

        # Total failure must leave the JSON byte-for-byte unchanged.
        before = digest(data_path)
        failed = run_sync(work, "full", fail_tabs="all")
        assert failed.returncode == 2
        assert digest(data_path) == before

    print("YouTube 3タブ全履歴同期のオフライン検査に合格しました。")


if __name__ == "__main__":
    main()
