"""YouTube Data API v3。検索はまとめ、動画とチャンネルは一括で取る。"""

from __future__ import annotations

import hashlib
import re
import time
from datetime import datetime, timedelta
from typing import Any

import requests

import config
from src.utils import (
    APIKeyError,
    NetworkError,
    QuotaExceededError,
    isoformat_utc,
    log,
    parse_duration_seconds,
    read_json,
    to_int,
    today_stamp,
    video_url,
    write_json,
)


class YouTubeClient:
    def __init__(self, api_key: str, cache_path=None, session: requests.Session | None = None, now: datetime | None = None):
        self.api_key = (api_key or "").strip()
        self.cache_path = cache_path or config.cache_dir()
        self.cache_path.mkdir(parents=True, exist_ok=True)
        self.session = session or requests.Session()
        self.now = now or datetime.now(tz=__import__("src.utils", fromlist=["TOKYO"]).TOKYO)
        self.day = today_stamp(self.now)
        self.api_calls = {"search": 0, "videos": 0, "channels": 0}
        self.cache_hits = {"search": 0, "videos": 0, "channels": 0}
        self.quota_used = 0
        self._video_cache = read_json(self.cache_path / "videos.json", {})
        self._channel_cache = read_json(self.cache_path / "channels.json", {})
        ledger = read_json(self.cache_path / f"quota_{self.day}.json", {})
        self.quota_already = int(ledger.get("used") or 0)

    @property
    def quota_total_today(self) -> int:
        return self.quota_already + self.quota_used

    def remaining_budget(self) -> int:
        return config.DAILY_QUOTA_BUDGET - self.quota_total_today

    def _save_ledger(self) -> None:
        write_json(
            self.cache_path / f"quota_{self.day}.json",
            {
                "date": self.day,
                "used": self.quota_total_today,
                "calls": self.api_calls,
                "cache_hits": self.cache_hits,
            },
        )

    def _spend(self, kind: str, cost: int) -> None:
        if self.remaining_budget() < cost:
            raise QuotaExceededError(
                "YouTube APIの1日の利用枠が、このツールの予算に達しました。"
                "太平洋時間で日付が変わると枠が戻ります（日本時間ではおおむね16時か17時）。"
                "取得済みのデータでレポートを作ります。"
            )
        self.api_calls[kind] += 1
        self.quota_used += cost
        self._save_ledger()

    def _get(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        if not self.api_key:
            raise APIKeyError(
                "YouTube APIキーが未設定です。.env に YOUTUBE_API_KEY を記入してから再実行してください。"
            )
        url = f"{config.YOUTUBE_API_BASE}/{path}"
        last_error: Exception | None = None
        for attempt in range(1, config.API_RETRY_COUNT + 1):
            try:
                response = self.session.get(
                    url,
                    params={**params, "key": self.api_key},
                    timeout=config.API_TIMEOUT_SECONDS,
                )
            except requests.RequestException as exc:
                last_error = exc
                time.sleep(min(2 ** attempt, 8))
                continue
            payload: dict[str, Any] = {}
            try:
                payload = response.json()
            except ValueError:
                payload = {}
            if response.status_code == 200:
                return payload
            reason = _error_reason(payload)
            if reason in {"quotaExceeded", "dailyLimitExceeded", "rateLimitExceeded"}:
                raise QuotaExceededError(
                    "YouTube APIの1日の利用上限に達しました。"
                    "太平洋時間の日付が変わるまで待って、翌日もう一度 python main.py を実行してください。"
                    "取得できた分だけでレポートを作ります。"
                )
            message = _error_message(payload)
            if reason in {"keyInvalid", "accessNotConfigured"} or "API key" in message:
                raise APIKeyError(
                    "YouTube APIキーが無効か、YouTube Data API v3 が有効になっていません。"
                    ".env の YOUTUBE_API_KEY と、Google CloudのAPI設定を確認してください。"
                )
            if response.status_code in {429, 500, 503}:
                last_error = NetworkError(f"YouTube APIが一時的に応答しませんでした（HTTP {response.status_code}）。")
                time.sleep(min(2 ** attempt, 8))
                continue
            message = _error_message(payload) or f"HTTP {response.status_code}"
            raise NetworkError(f"YouTube APIからエラーが返ってきました: {message}")
        raise NetworkError(
            "インターネット接続かYouTube APIへの通信に失敗しました。キャッシュがあればそれを使います。"
        ) from last_error

    def search_video_ids(self, keyword: str, published_after: datetime, window: str, max_results: int) -> list[str]:
        cache_file = self.cache_path / f"search_{self.day}_{window}_{_hash(keyword)}.json"
        cached = read_json(cache_file, None)
        if isinstance(cached, dict) and "video_ids" in cached:
            self.cache_hits["search"] += 1
            return list(cached["video_ids"])
        self._spend("search", config.SEARCH_QUOTA_COST)
        payload = self._get(
            "search",
            {
                "part": "snippet",
                "q": keyword,
                "type": "video",
                "order": "viewCount",
                "publishedAfter": isoformat_utc(published_after),
                "maxResults": max(1, min(50, max_results)),
                "regionCode": config.REGION_CODE,
                "relevanceLanguage": config.RELEVANCE_LANGUAGE,
                "videoDuration": "short",
                "safeSearch": "none",
            },
        )
        ids: list[str] = []
        for item in payload.get("items") or []:
            video_id = (item.get("id") or {}).get("videoId")
            if video_id and video_id not in ids:
                ids.append(video_id)
        write_json(cache_file, {"keyword": keyword, "window": window, "video_ids": ids})
        return ids

    def get_videos(self, video_ids: list[str]) -> list[dict[str, Any]]:
        fresh, missing = self._split_cache(self._video_cache, video_ids, "videos")
        collected = list(fresh)
        for batch in _chunks(missing, 50):
            self._spend("videos", config.VIDEOS_QUOTA_COST)
            payload = self._get("videos", {"part": "snippet,statistics,contentDetails", "id": ",".join(batch)})
            found_ids = set()
            for item in payload.get("items") or []:
                parsed = _parse_video(item)
                if not parsed:
                    continue
                found_ids.add(parsed["video_id"])
                self._video_cache[parsed["video_id"]] = {"fetched_at": isoformat_utc(self.now), "data": parsed}
                collected.append(parsed)
            for video_id in batch:
                if video_id not in found_ids:
                    self._video_cache[video_id] = {
                        "fetched_at": isoformat_utc(self.now),
                        "data": None,
                    }
        write_json(self.cache_path / "videos.json", self._video_cache)
        return [row for row in collected if row]

    def get_channels(self, channel_ids: list[str]) -> dict[str, dict[str, Any]]:
        fresh, missing = self._split_cache(self._channel_cache, channel_ids, "channels")
        result = {row["channel_id"]: row for row in fresh if row}
        for batch in _chunks(missing, 50):
            self._spend("channels", config.CHANNELS_QUOTA_COST)
            payload = self._get("channels", {"part": "snippet,statistics", "id": ",".join(batch)})
            found = set()
            for item in payload.get("items") or []:
                parsed = _parse_channel(item)
                if not parsed:
                    continue
                found.add(parsed["channel_id"])
                self._channel_cache[parsed["channel_id"]] = {
                    "fetched_at": isoformat_utc(self.now),
                    "data": parsed,
                }
                result[parsed["channel_id"]] = parsed
            for channel_id in batch:
                if channel_id not in found:
                    self._channel_cache[channel_id] = {"fetched_at": isoformat_utc(self.now), "data": None}
        write_json(self.cache_path / "channels.json", self._channel_cache)
        return result

    def _split_cache(self, bucket: dict, ids: list[str], kind: str) -> tuple[list[dict], list[str]]:
        fresh: list[dict] = []
        missing: list[str] = []
        for item_id in ids:
            entry = bucket.get(item_id)
            if entry and _cache_fresh(entry.get("fetched_at"), self.now):
                self.cache_hits[kind] += 1
                if entry.get("data"):
                    fresh.append(entry["data"])
                continue
            missing.append(item_id)
        return fresh, missing


def collect_videos(client: YouTubeClient, keywords: list[str], now: datetime) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """キーワード検索 → videoIdをまとめる → videos.list と channels.list。"""
    ordered_ids: list[str] = []
    seen: set[str] = set()
    skipped: list[str] = []
    for window in config.SEARCH_WINDOWS:
        published_after = now - timedelta(hours=window["hours"])
        for keyword in keywords:
            cache_file = client.cache_path / f"search_{client.day}_{window['name']}_{_hash(keyword)}.json"
            cached = cache_file.exists()
            if not cached and client.remaining_budget() < config.SEARCH_QUOTA_COST:
                skipped.append(f"{keyword}（{window['name']}）")
                continue
            try:
                ids = client.search_video_ids(keyword, published_after, window["name"], window["max_results"])
            except QuotaExceededError:
                skipped.append(f"{keyword}（{window['name']}）")
                log("クォータ予算に達したため、残りの検索を止めます。")
                break
            for video_id in ids:
                if video_id not in seen:
                    seen.add(video_id)
                    ordered_ids.append(video_id)
        else:
            continue
        break

    log(f"検索で集まった動画ID: {len(ordered_ids)}件（重複は除いています）")
    videos = client.get_videos(ordered_ids) if ordered_ids else []
    channel_ids = []
    for video in videos:
        if video.get("channel_id") and video["channel_id"] not in channel_ids:
            channel_ids.append(video["channel_id"])
    try:
        channels = client.get_channels(channel_ids) if channel_ids else {}
    except QuotaExceededError:
        log("チャンネル情報の取得前にクォータ予算へ達しました。登録者数は空欄のまま進めます。")
        channels = {}
    for video in videos:
        channel = channels.get(video.get("channel_id")) or {}
        video["subscriber_count"] = channel.get("subscriber_count")
        video["channel_total_views"] = channel.get("channel_total_views")
        video["channel_video_count"] = channel.get("channel_video_count")
        if channel.get("channel_name") and not video.get("channel_name"):
            video["channel_name"] = channel["channel_name"]
        video["video_url"] = video_url(video["video_id"], shorts=True)
    meta = {
        "quota_used_this_run": client.quota_used,
        "quota_used_today": client.quota_total_today,
        "api_calls": dict(client.api_calls),
        "cache_hits": dict(client.cache_hits),
        "skipped_searches": skipped,
        "video_ids": len(ordered_ids),
    }
    return videos, meta


def _hash(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:12]


def _chunks(items: list[str], size: int) -> list[list[str]]:
    return [items[index : index + size] for index in range(0, len(items), size)]


def _cache_fresh(fetched_at: str | None, now: datetime) -> bool:
    if not fetched_at:
        return False
    from src.utils import parse_datetime, hours_between

    parsed = parse_datetime(fetched_at)
    if parsed is None:
        return False
    return hours_between(now, parsed) <= config.CACHE_TTL_HOURS


def _error_reason(payload: dict[str, Any]) -> str:
    error = payload.get("error") or {}
    errors = error.get("errors") or []
    if errors:
        return str(errors[0].get("reason") or "")
    return ""


def _error_message(payload: dict[str, Any]) -> str:
    error = payload.get("error") or {}
    message = str(error.get("message") or "")
    message = re.sub(r"AIza[\w\-]+", "[KEY]", message)
    return message[:180]


def _thumb(snippet: dict[str, Any]) -> str:
    thumbs = snippet.get("thumbnails") or {}
    for key in ("maxres", "standard", "high", "medium", "default"):
        url = (thumbs.get(key) or {}).get("url")
        if url:
            return url
    return ""


def _parse_video(item: dict[str, Any]) -> dict[str, Any] | None:
    video_id = item.get("id")
    snippet = item.get("snippet") or {}
    if not video_id or not snippet:
        return None
    if snippet.get("liveBroadcastContent") in {"live", "upcoming"}:
        return None
    stats = item.get("statistics") or {}
    details = item.get("contentDetails") or {}
    return {
        "video_id": video_id,
        "title": snippet.get("title") or "",
        "channel_id": snippet.get("channelId") or "",
        "channel_name": snippet.get("channelTitle") or "",
        "published_at": snippet.get("publishedAt") or "",
        "duration_seconds": parse_duration_seconds(details.get("duration")),
        "views": to_int(stats.get("viewCount")),
        "likes": to_int(stats.get("likeCount")),
        "comments": to_int(stats.get("commentCount")),
        "subscriber_count": None,
        "channel_total_views": None,
        "channel_video_count": None,
        "description": snippet.get("description") or "",
        "thumbnail_url": _thumb(snippet),
        "video_url": video_url(video_id, shorts=True),
        "from_short_search": True,
    }


def _parse_channel(item: dict[str, Any]) -> dict[str, Any] | None:
    channel_id = item.get("id")
    if not channel_id:
        return None
    stats = item.get("statistics") or {}
    snippet = item.get("snippet") or {}
    hidden = bool(stats.get("hiddenSubscriberCount"))
    return {
        "channel_id": channel_id,
        "channel_name": snippet.get("title") or "",
        "subscriber_count": None if hidden else to_int(stats.get("subscriberCount")),
        "channel_total_views": to_int(stats.get("viewCount")),
        "channel_video_count": to_int(stats.get("videoCount")),
    }
