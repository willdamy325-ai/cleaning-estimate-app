"""ゲーム系Shortsの収集から企画TOP10までを1コマンドで実行する。"""

from __future__ import annotations

import argparse
import os
import sys
import traceback
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import config
from src.demo_data import demo_collected, demo_competitor, demo_own
from src.pipeline import RANKED_COLUMNS, RAW_COLUMNS, analyze
from src.report_generator import render_report, save_report
from src.utils import (
    APIKeyError,
    NetworkError,
    QuotaExceededError,
    discover_csv,
    load_env_file,
    load_table,
    log,
    now_tokyo,
    read_json,
    read_list_file,
    today_stamp,
    write_json,
    write_table,
)
from src.youtube_api import YouTubeClient, collect_videos


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="ゲーム系YouTube Shortsのトレンドから企画TOP10を作ります。")
    parser.add_argument("--demo", action="store_true", help="APIを使わず、サンプルデータでレポートの形を確認します。")
    parser.add_argument("--skip-api", action="store_true", help="APIを呼ばず、キャッシュと既存CSVだけで集計します。")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    load_env_file(config.project_root() / ".env")
    now = now_tokyo()
    stamp = today_stamp(now)
    log("クロのゲーム情報局向けに、ゲームShortsのトレンドを調べます。")
    log(f"調査日: {stamp}（日本時間）")

    keywords = read_list_file(config.keywords_path()) or list(config.DEFAULT_KEYWORDS)
    exclude_keywords = read_list_file(config.exclude_path())
    if not keywords:
        log("検索キーワードが空です。config.py の初期キーワードで続けます。")
        keywords = list(config.DEFAULT_KEYWORDS)

    own_path, comp_path, own_rows, comp_rows = _load_history(demo=args.demo, now=now)
    videos, meta, notice = _collect(args, keywords, now)

    try:
        result = analyze(videos, own_rows, comp_rows, now, exclude_keywords)
    except Exception as exc:  # noqa: BLE001
        log("分析の途中で問題が起きました。空の結果でレポートだけ残します。")
        log(f"詳細: {exc}")
        result = {"raw": [], "ranked": [], "clusters": [], "ideas": [], "profile_stats": {}}

    file_stamp = f"demo_{stamp}" if args.demo else stamp
    raw_path = config.daily_dir() / f"trend_raw_{file_stamp}.csv"
    ranked_path = config.daily_dir() / f"trend_ranked_{file_stamp}.csv"
    report_path = config.reports_dir() / (f"demo_report_{stamp}.md" if args.demo else f"daily_report_{stamp}.md")
    try:
        write_table(raw_path, result["raw"], RAW_COLUMNS)
        ranked_out = []
        for row in result["ranked"]:
            item = dict(row)
            if item.get("subscriber_count") is None:
                item["subscriber_count"] = ""
            ranked_out.append(item)
        write_table(ranked_path, ranked_out, RANKED_COLUMNS)
    except OSError as exc:
        log(f"CSVを保存できませんでした: {exc}")

    stats = _stats(result, meta, notice, own_path, comp_path, args.demo, len(videos))
    report = render_report(now, result["raw"], result["ranked"], result["clusters"], result["ideas"], stats)
    try:
        save_report(report_path, report)
    except OSError as exc:
        log(f"レポートを保存できませんでした: {exc}")
        return 1

    _print_summary(result, stats, raw_path, ranked_path, report_path)
    if notice and not videos and not args.demo:
        log("新規の動画は取れていません。上のメッセージを直してから、もう一度 python main.py を実行してください。")
    return 0


def _load_history(demo: bool, now: datetime):
    if demo:
        log("デモモードです。YouTube APIは呼びません。数字はサンプルです。")
        return None, None, demo_own(now), demo_competitor(now)
    own_path = discover_csv(
        ["kuro_youtube_40.csv", "kuro_youtube.csv"],
        ["kuro_youtube*.csv", "*kuro*youtube*.csv"],
    )
    comp_path = discover_csv(
        ["other_channels_youtube_75.csv", "other_channels_youtube.csv"],
        ["other_channels_youtube*.csv", "*other_channels*youtube*.csv"],
    )
    own_rows: list[dict] = []
    comp_rows: list[dict] = []
    if own_path is None:
        log("自チャンネルCSVが見つかりません（kuro_youtube_40.csv）。Channel Fitは中立スコアになります。")
    else:
        log(f"自チャンネルCSVを使います: {own_path}")
        own_rows = load_table(own_path)
        if not own_rows:
            log("自チャンネルCSVはありましたが、行を読めませんでした。文字コードがUTF-8か確認してください。")
    if comp_path is None:
        log("競合CSVが見つかりません（other_channels_youtube_75.csv）。競合実績は中立スコアになります。")
    else:
        log(f"競合CSVを使います: {comp_path}")
        comp_rows = load_table(comp_path)
        if not comp_rows:
            log("競合CSVはありましたが、行を読めませんでした。")
    return own_path, comp_path, own_rows, comp_rows


def _collect(args, keywords: list[str], now: datetime):
    cache_file = config.cache_dir() / "last_collected.json"
    if args.demo:
        videos = demo_collected(now)
        meta = {
            "quota_used_this_run": 0,
            "quota_used_today": 0,
            "api_calls": {"search": 0, "videos": 0, "channels": 0},
            "cache_hits": {"search": 0, "videos": 0, "channels": 0},
            "skipped_searches": [],
        }
        return videos, meta, ""

    if args.skip_api:
        log("APIは呼ばず、前回のキャッシュだけで進めます。")
        cached = _load_cached_videos(cache_file)
        return cached, _empty_meta(), "APIをスキップしました。"

    api_key = os.environ.get("YOUTUBE_API_KEY", "").strip()
    if not api_key:
        log("YouTube APIキーが未設定です。.env に YOUTUBE_API_KEY= を書いてください。")
        log("取得はスキップし、キャッシュと手元のCSVだけで続行します。")
        cached = _load_cached_videos(cache_file)
        notice = "APIキーが未設定のため、新しい動画は取れていません。"
        if not cached:
            notice += " data/cache にも前回の取得がありません。"
        return cached, _empty_meta(), notice

    client = YouTubeClient(api_key, cache_path=config.cache_dir(), now=now)
    log(
        f"検索キーワードは{len(keywords)}語です。"
        f"7日分と24時間分を各1回ずつ検索すると、最大およそ{len(keywords) * 2 * config.SEARCH_QUOTA_COST}ユニットです。"
    )
    log(f"今日すでに記録している使用量: {client.quota_already} / 予算 {config.DAILY_QUOTA_BUDGET}")
    try:
        videos, meta = collect_videos(client, keywords, now)
        write_json(cache_file, {"saved_at": today_stamp(now), "videos": videos})
        return videos, meta, ""
    except APIKeyError as exc:
        log(str(exc))
        return _load_cached_videos(cache_file), _empty_meta(), str(exc)
    except QuotaExceededError as exc:
        log(str(exc))
        cached = _load_cached_videos(cache_file)
        return cached, _empty_meta(), str(exc)
    except NetworkError as exc:
        log(str(exc))
        return _load_cached_videos(cache_file), _empty_meta(), str(exc)
    except Exception as exc:  # noqa: BLE001
        log("動画の取得で予期しない問題が起きました。キャッシュがあればそれを使います。")
        log(f"詳細: {exc}")
        traceback.print_exc()
        return _load_cached_videos(cache_file), _empty_meta(), "取得中に予期しないエラーが起きました。"


def _load_cached_videos(path: Path) -> list[dict]:
    payload = read_json(path, {})
    videos = payload.get("videos") if isinstance(payload, dict) else None
    if not videos:
        log("前回取得した動画キャッシュがありません。")
        return []
    log(f"前回の取得キャッシュを使います: {len(videos)}件")
    return videos


def _empty_meta() -> dict:
    return {
        "quota_used_this_run": 0,
        "quota_used_today": 0,
        "api_calls": {"search": 0, "videos": 0, "channels": 0},
        "cache_hits": {"search": 0, "videos": 0, "channels": 0},
        "skipped_searches": [],
    }


def _stats(result: dict, meta: dict, notice: str, own_path, comp_path, demo: bool, fetched: int) -> dict:
    calls = meta.get("api_calls") or {}
    search_units = calls.get("search", 0) * config.SEARCH_QUOTA_COST
    video_units = calls.get("videos", 0) * config.VIDEOS_QUOTA_COST
    channel_units = calls.get("channels", 0) * config.CHANNELS_QUOTA_COST
    this_run = meta.get("quota_used_this_run", search_units + video_units + channel_units)
    quota_text = (
        f"今回 {this_run} ユニット"
        f"（search.list {calls.get('search', 0)}回×100、"
        f"videos.list {calls.get('videos', 0)}回×1、"
        f"channels.list {calls.get('channels', 0)}回×1）。"
        f"キャッシュ利用 search {meta.get('cache_hits', {}).get('search', 0)} / "
        f"videos {meta.get('cache_hits', {}).get('videos', 0)} / "
        f"channels {meta.get('cache_hits', {}).get('channels', 0)}。"
        f"今日の累計概算 {meta.get('quota_used_today', this_run)} / 予算 {config.DAILY_QUOTA_BUDGET}。"
    )
    profile = result.get("profile_stats") or {}
    if demo:
        own_label = "デモ用の過去動画（実在のCSVではありません）"
        comp_label = "デモ用の競合動画（実在のCSVではありません）"
    else:
        own_label = str(own_path) if own_path else ""
        comp_label = str(comp_path) if comp_path else ""
    return {
        "demo": demo,
        "fetched": fetched,
        "notice": notice,
        "quota_text": quota_text,
        "own_csv": own_label,
        "competitor_csv": comp_label,
        "own_videos": profile.get("own_videos", 0),
        "competitor_videos": profile.get("competitor_videos", 0),
        "own_top_tokens": profile.get("own_top_tokens") or [],
        "competitor_top_tokens": profile.get("competitor_top_tokens") or [],
    }


def _print_summary(result: dict, stats: dict, raw_path: Path, ranked_path: Path, report_path: Path) -> None:
    raw = result["raw"]
    excluded = [row for row in raw if row.get("excluded") or not row.get("is_shorts")]
    analyzed = [row for row in raw if row.get("is_shorts") and not row.get("excluded")]
    log("")
    log("=== 結果 ===")
    log(f"取得できた動画数: {stats['fetched']}")
    log(f"除外された動画数: {len(excluded)}")
    log(f"分析対象数: {len(analyzed)}")
    log("TOPテーマ:")
    clusters = result["clusters"][:10]
    if not clusters:
        log("  （なし）")
    for index, cluster in enumerate(clusters, start=1):
        log(f"  {index}. {cluster.label} / チャンネル{cluster.channel_count} / 機会スコア{cluster.avg_opportunity:.1f}")
    log("企画TOP10:")
    if not result["ideas"]:
        log("  （なし）")
    for idea in result["ideas"]:
        log(f"  {idea.rank}位 [{idea.priority}] {idea.title}")
    log(f"API使用量の概算: {stats['quota_text']}")
    log(f"生データ: {raw_path}")
    log(f"ランキング: {ranked_path}")
    log(f"レポート: {report_path}")


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        log("中断しました。")
        raise SystemExit(1)
