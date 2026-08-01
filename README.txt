NMIXX YouTube 3-category final correction

Overwrite these exact repository paths:
.github/workflows/sync-youtube.yml
scripts/sync-youtube-channels.mjs
scripts/test-youtube-sync.py
scripts/validate-site.py
data/youtube-channels.json
youtube.html

Then run Sync YouTube with full_history=true.
The validator verifies the exact NMIXX channel ID and per-video channel ID/category,
instead of rejecting legitimate public video titles that mention another artist.
