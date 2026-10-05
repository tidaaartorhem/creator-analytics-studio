"""YouTube Data API v3 client (stdlib only, urllib).

Quota-cheap read pattern:
  1. channels.list?part=contentDetails&id=...            (cost: 1 unit)
  2. playlistItems.list?part=contentDetails&pageToken=.. (cost: 1 unit per page)
  3. videos.list?part=statistics,snippet,contentDetails
     with up to 50 comma-joined ids per call            (cost: 1 unit per call)

We NEVER call search.list: it costs 100 quota units per call, which would
burn a default 10,000-unit daily quota in about 100 calls. Walking the
uploads playlist gives the full catalog at 1 unit per page instead.

Structure is test-first: `_get_json` is the single HTTP seam (monkeypatch it
in tests), and every response shape has a pure parsing function.
"""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.parse
import urllib.request

from . import API_TIMEOUT_S

BASE_URL = "https://www.googleapis.com/youtube/v3"
USER_AGENT = "creator-analytics-studio/1.0"
PAGE_SIZE = 50
IDS_PER_CALL = 50

# ISO-8601 durations as the Data API emits them (PT#H#M#S). A day component
# never appears in practice, but we parse it anyway for robustness.
_DURATION_RE = re.compile(
    r"^P(?:(?P<days>\d+)D)?T?(?:(?P<hours>\d+)H)?(?:(?P<minutes>\d+)M)?(?:(?P<seconds>\d+)S)?$"
)


class YouTubeAPIError(RuntimeError):
    """Raised for any YouTube API failure. Never contains the API key."""


def _api_error_message(exc: urllib.error.HTTPError) -> str:
    """Extract the API's own error message. The URL (and key) is excluded."""
    try:
        payload = json.loads(exc.read().decode("utf-8", "replace"))
        message = payload.get("error", {}).get("message")
        if message:
            return f"YouTube API error (HTTP {exc.code}): {message}"
    except Exception:
        pass
    return f"YouTube API error (HTTP {exc.code})"


def _get_json(url: str, timeout: int = API_TIMEOUT_S) -> dict:
    """Single HTTP seam: GET a URL and return the decoded JSON body.

    Non-200 responses raise YouTubeAPIError carrying the API's error message.
    Network failures raise YouTubeAPIError with no URL (and no key) attached.
    """
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        raise YouTubeAPIError(_api_error_message(exc)) from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise YouTubeAPIError(f"network error contacting YouTube API: {exc}") from exc
    try:
        return json.loads(body)
    except json.JSONDecodeError as exc:
        raise YouTubeAPIError(f"invalid JSON from YouTube API: {exc}") from exc


def _parse_duration(value: str) -> int:
    """Parse an ISO-8601 duration (PT1H2M3S) into seconds.

    Returns 0 for anything that does not look like a duration rather than
    raising: a missing/odd duration must not kill a whole catalog pull.
    """
    if not value:
        return 0
    match = _DURATION_RE.match(value.strip())
    if not match:
        return 0
    parts = match.groupdict()
    if not any(parts.values()):
        return 0
    days = int(parts["days"] or 0)
    hours = int(parts["hours"] or 0)
    minutes = int(parts["minutes"] or 0)
    seconds = int(parts["seconds"] or 0)
    return days * 86400 + hours * 3600 + minutes * 60 + seconds


def _to_int(value) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def parse_uploads_playlist(response: dict) -> str:
    """Extract the uploads playlist id from a channels.list response."""
    items = response.get("items") or []
    if not items:
        raise YouTubeAPIError("channels.list returned no items for this channel id")
    try:
        return items[0]["contentDetails"]["relatedPlaylists"]["uploads"]
    except (KeyError, TypeError) as exc:
        raise YouTubeAPIError("channels.list response missing uploads playlist") from exc


def parse_video_ids(response: dict) -> tuple[list, str | None]:
    """Extract (video ids in page order, next page token or None)."""
    ids = []
    for item in response.get("items") or []:
        video_id = (item.get("contentDetails") or {}).get("videoId")
        if video_id:
            ids.append(video_id)
    return ids, response.get("nextPageToken")


def normalize_video(item: dict) -> dict:
    """Normalize one videos.list item to the pipeline's video dict.

    Missing statistics (e.g. likeCount when likes are disabled) become 0.
    """
    snippet = item.get("snippet") or {}
    stats = item.get("statistics") or {}
    content = item.get("contentDetails") or {}
    return {
        "id": item.get("id", ""),
        "title": snippet.get("title", ""),
        "published_at": snippet.get("publishedAt", ""),
        "duration_s": _parse_duration(content.get("duration", "")),
        "views": _to_int(stats.get("viewCount")),
        "likes": _to_int(stats.get("likeCount")),
        "comments": _to_int(stats.get("commentCount")),
    }


def parse_channel_meta(response: dict) -> dict:
    """Extract channel-level metadata from a channels.list response."""
    items = response.get("items") or []
    if not items:
        raise YouTubeAPIError("channels.list returned no items for this channel id")
    item = items[0]
    snippet = item.get("snippet") or {}
    stats = item.get("statistics") or {}
    return {
        "id": item.get("id", ""),
        "title": snippet.get("title", ""),
        "description": snippet.get("description", ""),
        "subscriberCount": _to_int(stats.get("subscriberCount")),
        "videoCount": _to_int(stats.get("videoCount")),
        "viewCount": _to_int(stats.get("viewCount")),
        "publishedAt": snippet.get("publishedAt", ""),
    }


def _url(path: str, params: dict) -> str:
    return f"{BASE_URL}/{path}?{urllib.parse.urlencode(params)}"


def fetch_uploads_playlist_id(api_key: str, channel_id: str) -> str:
    """channels.list (1 quota unit) -> uploads playlist id."""
    response = _get_json(
        _url("channels", {"part": "contentDetails", "id": channel_id, "key": api_key})
    )
    return parse_uploads_playlist(response)


def fetch_channel_meta(api_key: str, channel_id: str) -> dict:
    """channels.list (1 quota unit) -> normalized channel metadata."""
    response = _get_json(
        _url(
            "channels",
            {"part": "snippet,statistics", "id": channel_id, "key": api_key},
        )
    )
    return parse_channel_meta(response)


def fetch_playlist_video_ids(
    api_key: str, playlist_id: str, max_videos: int
) -> list:
    """Walk playlistItems pages (1 quota unit per page) in playlist order."""
    ids: list = []
    page_token = None
    while len(ids) < max_videos:
        params = {
            "part": "contentDetails",
            "playlistId": playlist_id,
            "maxResults": min(PAGE_SIZE, max_videos - len(ids)),
            "key": api_key,
        }
        if page_token:
            params["pageToken"] = page_token
        page_ids, page_token = parse_video_ids(_get_json(_url("playlistItems", params)))
        ids.extend(page_ids)
        if not page_token:
            break
    return ids[:max_videos]


def fetch_video_details(api_key: str, video_ids: list) -> list:
    """videos.list in batches of 50 (1 quota unit per call), playlist order kept."""
    by_id: dict = {}
    for start in range(0, len(video_ids), IDS_PER_CALL):
        batch = video_ids[start : start + IDS_PER_CALL]
        response = _get_json(
            _url(
                "videos",
                {
                    "part": "statistics,snippet,contentDetails",
                    "id": ",".join(batch),
                    "key": api_key,
                },
            )
        )
        for item in response.get("items") or []:
            normalized = normalize_video(item)
            by_id[normalized["id"]] = normalized
    # Preserve playlist order; drop ids the API did not return.
    return [by_id[video_id] for video_id in video_ids if video_id in by_id]


def fetch_channel_videos(
    api_key: str, channel_id: str, max_videos: int = 200
) -> list:
    """Full quota-cheap pull: playlist id -> video ids -> normalized details."""
    playlist_id = fetch_uploads_playlist_id(api_key, channel_id)
    video_ids = fetch_playlist_video_ids(api_key, playlist_id, max_videos)
    return fetch_video_details(api_key, video_ids)
