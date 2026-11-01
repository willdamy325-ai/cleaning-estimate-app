"""取得済みの動画を、スコア・クラスタ・企画まで通す。"""

from __future__ import annotations

from datetime import datetime

import config
from src.channel_fit import load_profiles, score_fit
from src.cluster_analyzer import assign_multi_channel_scores, cluster_videos, summarize_clusters
from src.idea_generator import generate_ideas
from src.title_analyzer import apply_title_fields
from src.trend_analyzer import apply_channel_diversity, mark_exclusions, prepare_video, score_trends
from src.utils import clamp, normalize_weights


RAW_COLUMNS = [
    "video_id",
    "title",
    "channel_id",
    "channel_name",
    "published_at",
    "duration_seconds",
    "views",
    "likes",
    "comments",
    "subscriber_count",
    "channel_total_views",
    "channel_video_count",
    "description",
    "thumbnail_url",
    "video_url",
    "hours_since_publish",
    "days_since_publish",
    "views_per_hour",
    "views_per_day",
    "views_per_subscriber",
    "likes_per_view",
    "comments_per_view",
    "in_24h",
    "in_3d",
    "in_7d",
    "is_shorts",
    "shorts_band",
    "category",
    "game_title",
    "hardware",
    "series",
    "era",
    "theme_cluster",
    "trend_score",
    "channel_fit_score",
    "competitor_score",
    "multi_channel_score",
    "opportunity_score",
    "excluded",
    "exclude_reason",
    "penalty_notes",
]

RANKED_COLUMNS = [
    "rank",
    "title",
    "channel_name",
    "views",
    "subscriber_count",
    "views_per_hour",
    "views_per_subscriber",
    "trend_score",
    "category",
    "game_title",
    "hardware",
    "theme_cluster",
    "channel_fit_score",
    "opportunity_score",
    "video_url",
]


def analyze(
    videos: list[dict],
    own_rows: list[dict],
    competitor_rows: list[dict],
    now: datetime,
    exclude_keywords: list[str] | None = None,
) -> dict:
    exclude_keywords = exclude_keywords if exclude_keywords is not None else []
    prepared = [prepare_video(video, now) for video in videos]
    for row in prepared:
        apply_title_fields(row)
        mark_exclusions(row, exclude_keywords)
    score_trends(prepared)
    cluster_videos(prepared)
    assign_multi_channel_scores(prepared)

    own_profile, competitor_profile, profile_stats = load_profiles(own_rows, competitor_rows)
    score_fit(prepared, own_profile, "channel_fit_score")
    score_fit(prepared, competitor_profile, "competitor_score")
    _opportunity(prepared)
    apply_channel_diversity(prepared)

    ranked = [row for row in prepared if row.get("is_shorts") and not row.get("excluded")]
    ranked.sort(key=lambda row: (row.get("opportunity_score") or 0, row.get("trend_score") or 0), reverse=True)
    for index, row in enumerate(ranked, start=1):
        row["rank"] = index

    clusters = summarize_clusters(prepared)
    ideas = generate_ideas(clusters, prepared, own_profile)
    return {
        "raw": prepared,
        "ranked": ranked,
        "clusters": clusters,
        "ideas": ideas,
        "profile_stats": profile_stats,
        "own_profile": own_profile,
    }


def _opportunity(videos: list[dict]) -> None:
    weights = normalize_weights(config.OPPORTUNITY_WEIGHTS)
    for video in videos:
        if not video.get("is_shorts") or video.get("excluded"):
            video["opportunity_score"] = 0.0
            continue
        score = (
            weights["trend"] * float(video.get("trend_score") or 0)
            + weights["channel_fit"] * float(video.get("channel_fit_score") or 0)
            + weights["competitor"] * float(video.get("competitor_score") or 0)
            + weights["multi_channel"] * float(video.get("multi_channel_score") or 0)
        )
        video["opportunity_score"] = round(clamp(score), 2)
