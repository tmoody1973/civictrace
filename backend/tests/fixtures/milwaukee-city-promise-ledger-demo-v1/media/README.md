# Media fixtures (Slice 6, MOO-715)

The raw meeting video is **not committed** (2.9 GB; see repo `.gitignore`). The manifest
entry in `docs/sources/corpus-manifest.yaml` carries its canonical URLs, sha256, and
segment provenance; the immutable copy lives in the GCS vault.

## Re-fetch (must run from a residential IP — Granicus 403s datacenter IPs)

```bash
UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"
# 1. Resolve the archive MP4 from the official player page (clip 5262 = Legistar EventMedia for event 13443)
MP4=$(curl -sL -A "$UA" "https://milwaukee.granicus.com/MediaPlayer.php?clip_id=5262" \
  | grep -oE 'archive-video\.granicus\.com/[^"'\'' <>\\]+\.mp4' | head -1)
# 2. Download and verify against the manifest hash
curl -s -A "$UA" -o znd-committee-2026-07-28.mp4 "https://$MP4"
shasum -a 256 znd-committee-2026-07-28.mp4   # must match content_hash in the manifest
```

TID 121 (file 260433) discussion: **5287s → 5990s** (Legistar `EventItemVideoIndex`
values, agenda item 493916; see `../provenance/znd-event-13443-items-2026-08-20.json`).
