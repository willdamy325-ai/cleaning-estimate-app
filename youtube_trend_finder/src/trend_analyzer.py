"""再生速度・登録者比・反応率から Trend Score を作る。"""

from __future__ import annotations

import math
from datetime import datetime

import config
from src.utils import (
    clamp,
    hours_between,
    jp_char_ratio,
    median,
    normalize_weights,
    parse_datetime,
    parse_duration_seconds,
    recency_raw,
    robust_scale,
    safe_div,
    to_int,
)


def prepare_video(video: dict, now: datetime) -> dict:
    row = dict(video)
    row["views"] = to_int(row.get("views")) or 0
    row["likes"] = to_int(row.get("likes"))
    row["comments"] = to_int(row.get("comments"))
    row["subscriber_count"] = to_int(row.get("subscriber_count"))
    row["channel_total_views"] = to_int(row.get("channel_total_views"))
    row["channel_video_count"] = to_int(row.get("channel_video_count"))
    row["duration_seconds"] = parse_duration_seconds(row.get("duration_seconds"))
    published = parse_datetime(row.get("published_at"))
    row["_published"] = published
    if published is not None:
        hours = hours_between(now, published)
        row["hours_since_publish"] = round(hours, 3)
        row["days_since_publish"] = round(hours / 24.0, 3)
        velocity_hours = max(hours, config.MIN_HOURS_FOR_VELOCITY)
        row["velocity_hours_used"] = round(velocity_hours, 3)
        row["views_per_hour"] = row["views"] / velocity_hours
        row["views_per_day"] = row["views"] / max(hours / 24.0, config.MIN_HOURS_FOR_VELOCITY / 24.0)
    else:
        row["hours_since_publish"] = None
        row["days_since_publish"] = None
        row["velocity_hours_used"] = None
        row["views_per_hour"] = None
        row["views_per_day"] = None
    row["views_per_subscriber"] = safe_div(row["views"], row["subscriber_count"])
    views_for_rate = row["views"] if row["views"] >= config.MIN_VIEWS_FOR_RATE else None
    row["likes_per_view"] = safe_div(row["likes"], views_for_rate)
    row["comments_per_view"] = safe_div(row["comments"], views_for_rate)
    row["in_24h"] = _within(row.get("hours_since_publish"), config.COMPARE_WINDOWS_HOURS["24h"])
    row["in_3d"] = _within(row.get("hours_since_publish"), config.COMPARE_WINDOWS_HOURS["3d"])
    row["in_7d"] = _within(row.get("hours_since_publish"), config.COMPARE_WINDOWS_HOURS["7d"])
    row["jp_ratio"] = jp_char_ratio(str(row.get("title") or ""))
    _mark_shorts(row)
    row["excluded"] = bool(row.get("excluded"))
    row["exclude_reason"] = row.get("exclude_reason") or ""
    row["penalty_notes"] = row.get("penalty_notes") or ""
    if not row.get("video_url") and row.get("video_id"):
        from src.utils import video_url

        row["video_url"] = video_url(str(row["video_id"]), shorts=bool(row.get("is_shorts")))
    return row


def _within(hours: float | None, limit: float) -> bool:
    return hours is not None and hours <= limit


def _mark_shorts(row: dict) -> None:
    title = str(row.get("title") or "")
    description = str(row.get("description") or "")
    blob = f"{title}\n{description}".lower()
    has_tag = "#shorts" in blob or "#short" in blob
    duration = row.get("duration_seconds")
    if duration is None:
        row["is_shorts"] = has_tag or bool(row.get("from_short_search", False))
        row["shorts_band"] = "unknown"
        if not row["is_shorts"]:
            row["exclude_reason"] = row.get("exclude_reason") or "尺が不明でShortsと判断できない"
            row["is_shorts"] = False
        return
    if duration <= config.SHORTS_MAX_SECONDS:
        row["is_shorts"] = True
        row["shorts_band"] = "preferred" if duration <= config.PREFERRED_SHORTS_SECONDS else "standard"
        return
    row["is_shorts"] = False
    row["shorts_band"] = "long"
    row["exclude_reason"] = "180秒を超えるためShorts候補から外した"


def mark_exclusions(row: dict, exclude_keywords: list[str]) -> dict:
    if row.get("exclude_reason") and not row.get("is_shorts", True):
        row["excluded"] = True
        return row
    blob = f"{row.get('title') or ''}\n{row.get('description') or ''}".lower()
    for keyword in exclude_keywords:
        if keyword.lower() in blob:
            row["excluded"] = True
            row["exclude_reason"] = f"除外キーワード: {keyword}"
            return row
    # 速報だけで、企画カテゴリが乗っていないものはニュース扱いにする。
    title = str(row.get("title") or "")
    categories = set(row.get("categories") or [])
    themes = {c for c in categories if c not in {"その他", "ランキング", "TOP3", "TOP5"}}
    if "速報" in title and not themes:
        row["excluded"] = True
        row["exclude_reason"] = "ニュース速報のみ"
        return row
    if not str(row.get("title") or "").strip():
        row["excluded"] = True
        row["exclude_reason"] = "タイトルが空"
        return row
    row["excluded"] = False
    return row


def score_trends(videos: list[dict]) -> list[dict]:
    targets = [video for video in videos if video.get("is_shorts") and not video.get("excluded")]
    if not targets:
        for video in videos:
            video["trend_score"] = 0.0
        return videos

    weights = normalize_weights(config.TREND_WEIGHTS)
    velocity = robust_scale([video.get("views_per_hour") or 0.0 for video in targets])
    vps_values = [video.get("views_per_subscriber") for video in targets]
    known_vps = [value for value in vps_values if value is not None]
    vps_median = median(known_vps)
    filled_vps = [value if value is not None else (vps_median if vps_median is not None else 0.0) for value in vps_values]
    vps_scaled = robust_scale(filled_vps)
    comments = robust_scale([video.get("comments_per_view") or 0.0 for video in targets])
    likes = robust_scale([video.get("likes_per_view") or 0.0 for video in targets])
    recency = [clamp(recency_raw(video.get("hours_since_publish"))) for video in targets]

    comment_rates = [video.get("comments_per_view") or 0.0 for video in targets]
    bonus_cut = _percentile(comment_rates, 90)

    vps_known_median = vps_median if vps_median is not None else 0.0
    for index, video in enumerate(targets):
        velocity_score = velocity[index]
        subs = video.get("subscriber_count")
        vps = video.get("views_per_subscriber")
        if subs is not None and subs >= config.MEGA_CHANNEL_SUBS and (vps or 0) < vps_known_median:
            velocity_score *= config.MEGA_LOW_VPS_VELOCITY_FACTOR
            video["penalty_notes"] = _join_note(video.get("penalty_notes"), "大手で登録者比が低いため再生速度を抑制")
        vps_score = vps_scaled[index]
        if vps is None:
            vps_score *= config.UNKNOWN_SUBS_FACTOR
        score = (
            weights["velocity"] * velocity_score
            + weights["subscriber_ratio"] * vps_score
            + weights["comments"] * comments[index]
            + weights["likes"] * likes[index]
            + weights["recency"] * recency[index]
        )
        if (video.get("comments_per_view") or 0) >= bonus_cut and bonus_cut > 0:
            score += config.COMMENT_TOP_DECILE_BONUS
        factor = config.DURATION_SCORE_FACTOR.get(video.get("shorts_band") or "unknown", 0.9)
        score *= factor
        if (video.get("jp_ratio") or 0) < config.MIN_JP_CHAR_RATIO:
            score *= config.LOW_JP_FACTOR
            video["penalty_notes"] = _join_note(video.get("penalty_notes"), "日本語タイトルが少ない")
        blob = f"{video.get('title') or ''} {video.get('description') or ''}"
        for keyword in config.SOFT_DOWNRANK_KEYWORDS:
            if keyword.lower() in blob.lower():
                score *= config.SOFT_DOWNRANK_FACTOR
                video["penalty_notes"] = _join_note(video.get("penalty_notes"), f"弱めに減点: {keyword}")
                break
        video["trend_velocity"] = round(velocity_score, 2)
        video["trend_vps"] = round(vps_score, 2)
        video["trend_comments"] = round(comments[index], 2)
        video["trend_likes"] = round(likes[index], 2)
        video["trend_recency"] = round(recency[index], 2)
        video["trend_score"] = round(clamp(score), 2)

    for video in videos:
        if "trend_score" not in video:
            video["trend_score"] = 0.0
    return videos


def apply_channel_diversity(videos: list[dict]) -> list[dict]:
    ranked = [video for video in videos if video.get("is_shorts") and not video.get("excluded")]
    ranked.sort(key=lambda video: video.get("opportunity_score") or 0, reverse=True)
    counts: dict[str, int] = {}
    for video in ranked:
        key = video.get("channel_id") or video.get("channel_name") or video.get("video_id")
        counts[key] = counts.get(key, 0) + 1
        if counts[key] > config.MAX_VIDEOS_PER_CHANNEL:
            video["opportunity_score"] = round((video.get("opportunity_score") or 0) * config.EXTRA_VIDEO_FACTOR, 2)
            video["penalty_notes"] = _join_note(video.get("penalty_notes"), "同一チャンネルの重複を抑制")
    return videos


def _percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    rank = (len(ordered) - 1) * (pct / 100.0)
    low = math.floor(rank)
    high = math.ceil(rank)
    if low == high:
        return ordered[low]
    weight = rank - low
    return ordered[low] * (1 - weight) + ordered[high] * weight


def _join_note(current: str | None, extra: str) -> str:
    if not current:
        return extra
    if extra in current:
        return current
    return f"{current}; {extra}"
