"""Tests for services/youtube_client.py. No network: _get_json is monkeypatched."""

import io
import urllib.error
import urllib.request

import pytest

from services import youtube_client
from services.youtube_client import YouTubeAPIError


def test_parse_duration():
    parse = youtube_client._parse_duration
    assert parse("PT1H2M3S") == 3723
    assert parse("PT15M") == 900
    assert parse("PT45S") == 45
    assert parse("P1DT2H") == 93600  # never emitted by the API, parsed anyway
    assert parse("banana") == 0  # malformed -> 0, documented
    assert parse("") == 0
    assert parse("PT") == 0


def test_parse_uploads_playlist():
    resp = {"items": [{"contentDetails": {"relatedPlaylists": {"uploads": "UUabc"}}}]}
    assert youtube_client.parse_uploads_playlist(resp) == "UUabc"
    with pytest.raises(YouTubeAPIError):
        youtube_client.parse_uploads_playlist({"items": []})


def test_parse_video_ids():
    resp = {
        "items": [{"contentDetails": {"videoId": "a"}}],
        "nextPageToken": "T2",
    }
    assert youtube_client.parse_video_ids(resp) == (["a"], "T2")
    assert youtube_client.parse_video_ids({"items": []}) == ([], None)


def test_normalize_video_missing_like_count():
    item = {
        "id": "v1",
        "snippet": {"title": "T", "publishedAt": "2026-01-01T00:00:00Z"},
        "statistics": {"viewCount": "100", "commentCount": "2"},
        "contentDetails": {"duration": "PT1M30S"},
    }
    video = youtube_client.normalize_video(item)
    assert video["likes"] == 0  # likes disabled -> likeCount absent
    assert video["views"] == 100
    assert video["duration_s"] == 90


def _fake_pages(monkeypatch):
    pages = {
        None: {
            "items": [
                {"contentDetails": {"videoId": "a"}},
                {"contentDetails": {"videoId": "b"}},
            ],
            "nextPageToken": "T2",
        },
        "T2": {"items": [{"contentDetails": {"videoId": "c"}}]},
    }

    def fake_get_json(url, timeout=20):
        return pages["T2" if "pageToken=T2" in url else None]

    monkeypatch.setattr(youtube_client, "_get_json", fake_get_json)


def test_playlist_pagination_order_and_max(monkeypatch):
    _fake_pages(monkeypatch)
    assert youtube_client.fetch_playlist_video_ids("KEY", "PL", 10) == ["a", "b", "c"]
    assert youtube_client.fetch_playlist_video_ids("KEY", "PL", 2) == ["a", "b"]


def test_fetch_channel_videos_never_calls_search(monkeypatch):
    seen = []

    def fake_get_json(url, timeout=20):
        seen.append(url)
        if "playlistItems" in url:
            return {
                "items": [
                    {"contentDetails": {"videoId": "v1"}},
                    {"contentDetails": {"videoId": "v2"}},
                ]
            }
        if url.split("?")[0].endswith("/videos"):
            return {
                "items": [
                    {
                        "id": "v1",
                        "snippet": {"title": "T1", "publishedAt": "2026-01-01T00:00:00Z"},
                        "statistics": {"viewCount": "100"},
                        "contentDetails": {"duration": "PT1M"},
                    },
                    {
                        "id": "v2",
                        "snippet": {"title": "T2", "publishedAt": "2026-01-02T00:00:00Z"},
                        "statistics": {"viewCount": "200"},
                        "contentDetails": {"duration": "PT2M"},
                    },
                ]
            }
        return {"items": [{"contentDetails": {"relatedPlaylists": {"uploads": "UU1"}}}]}

    monkeypatch.setattr(youtube_client, "_get_json", fake_get_json)
    videos = youtube_client.fetch_channel_videos("KEY", "UC1234567890", max_videos=10)
    assert [v["id"] for v in videos] == ["v1", "v2"]  # playlist order kept
    assert videos[0]["likes"] == 0
    assert seen, "expected HTTP calls"
    assert all("search.list" not in url for url in seen), "search.list costs 100 units"


def test_get_json_error_carries_api_message_not_key(monkeypatch):
    def fake_urlopen(request, timeout=20):
        raise urllib.error.HTTPError(
            request.full_url,
            403,
            "Forbidden",
            {},
            io.BytesIO(b'{"error": {"message": "Quota exceeded."}}'),
        )

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    with pytest.raises(YouTubeAPIError) as exc_info:
        youtube_client._get_json("https://example.com/x?key=SECRETKEY")
    assert "Quota exceeded" in str(exc_info.value)
    assert "SECRETKEY" not in str(exc_info.value)
