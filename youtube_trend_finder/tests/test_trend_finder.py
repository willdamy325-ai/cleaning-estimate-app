"""スコア、分類、クラスタ、企画、API失敗時の動きを確認する。"""

from __future__ import annotations

import csv
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import config
from src.pipeline import analyze
from src.title_analyzer import analyze_title
from src.utils import load_table, parse_duration_seconds, robust_scale
from src.youtube_api import YouTubeClient
from src.utils import TOKYO, isoformat_utc


NOW = datetime(2026, 11, 1, 18, 0, tzinfo=TOKYO)


def _video(video_id, title, channel, subs, views, hours, likes=100, comments=10, duration=40):
    return {
        "video_id": video_id,
        "title": title,
        "channel_id": channel,
        "channel_name": channel,
        "published_at": isoformat_utc(NOW - timedelta(hours=hours)),
        "duration_seconds": duration,
        "views": views,
        "likes": likes,
        "comments": comments,
        "subscriber_count": subs,
        "description": "#shorts",
        "from_short_search": True,
    }


def test_duration_parser():
    assert parse_duration_seconds("PT45S") == 45
    assert parse_duration_seconds("PT1M30S") == 90
    assert parse_duration_seconds("PT1H2M3S") == 3723
    assert parse_duration_seconds("1:02") == 62
    assert parse_duration_seconds("45秒") == 45
    assert parse_duration_seconds(None) is None


def test_title_ps2_ranking():
    analysis = analyze_title("PS2で死ぬほど遊んだ神ゲーTOP5")
    assert "神ゲー" in analysis.categories
    assert "ランキング" in analysis.categories
    assert "TOP5" in analysis.categories
    assert "PS2" in analysis.hardware
    assert "2000年代" in analysis.eras


def test_title_does_not_treat_hours_as_n64():
    analysis = analyze_title("PS2で64時間遊んだ神ゲー")
    assert "N64" not in analysis.hardware
    assert "PS2" in analysis.hardware


def test_velocity_floor_and_mega_channel_does_not_own_the_board():
    videos = [
        _video("mega", "有名チャンネルの普通のゲーム紹介", "big", 2_000_000, 500_000, 48, 1000, 50),
        _video("small", "PS2の隠れた神ゲー7選", "small", 10_000, 200_000, 48, 8000, 900),
        _video("mid1", "ドラクエの伏線TOP5", "mid", 20_000, 80_000, 40, 3000, 400),
        _video("mid2", "鬱ゲーを5本だけ紹介", "mid2", 15_000, 70_000, 36, 2500, 500),
        _video("mid3", "Switchの隠れた名作", "mid3", 18_000, 60_000, 30, 2000, 200),
    ]
    result = analyze(videos, [], [], NOW, ["マイクラ"])
    by_id = {row["video_id"]: row for row in result["raw"]}
    assert by_id["small"]["views_per_hour"] == pytest.approx(200_000 / 48)
    fresh = _video("fresh", "公開直後の神ゲー", "x", 10_000, 30_000, 1, 100, 10)
    prepared = analyze([fresh], [], [], NOW, [])
    assert prepared["raw"][0]["velocity_hours_used"] == config.MIN_HOURS_FOR_VELOCITY
    assert by_id["small"]["opportunity_score"] > by_id["mega"]["opportunity_score"]


def test_ps2_titles_cluster_across_channels():
    videos = [
        _video("a", "PS2の隠れた神ゲーTOP5", "A", 12000, 180000, 20, 9000, 1000),
        _video("b", "今やっても面白いPS2神ゲー7選", "B", 30000, 220000, 30, 8000, 900),
        _video("c", "PS2で500時間遊んだゲーム", "C", 8000, 150000, 26, 7000, 800),
        _video("d", "子供向けなのに鬱すぎたゲーム7選", "D", 15000, 160000, 18, 7000, 1200),
    ]
    result = analyze(videos, [], [], NOW, [])
    by_id = {row["video_id"]: row for row in result["raw"]}
    assert by_id["a"]["cluster_id"] == by_id["b"]["cluster_id"]
    assert by_id["c"]["cluster_id"] == by_id["a"]["cluster_id"]
    assert "PS2" in by_id["a"]["theme_cluster"]
    assert by_id["d"]["cluster_id"] != by_id["a"]["cluster_id"]


def test_exclude_minecraft_and_keep_in_raw():
    videos = [
        _video("ok", "スーファミの神ゲー5選", "A", 10000, 50000, 20, 2000, 200),
        _video("ng", "マイクラ建築がすごい切り抜き", "B", 10000, 900000, 10, 2000, 200),
    ]
    result = analyze(videos, [], [], NOW, ["マイクラ", "切り抜き"])
    ranked_ids = {row["video_id"] for row in result["ranked"]}
    assert "ok" in ranked_ids
    assert "ng" not in ranked_ids
    raw = {row["video_id"]: row for row in result["raw"]}
    assert raw["ng"]["excluded"] is True


def test_column_alias_and_channel_fit_uses_history(tmp_path: Path):
    path = tmp_path / "kuro_youtube_40.csv"
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["動画のタイトル", "再生回数", "公開日"])
        writer.writeheader()
        writer.writerow({"動画のタイトル": "PS2の神ゲー7選", "再生回数": "300,000", "公開日": "2024-01-01"})
        writer.writerow({"動画のタイトル": "PS2ランキング", "再生回数": "250000", "公開日": "2024-02-01"})
        writer.writerow({"動画のタイトル": "雑学だけ", "再生回数": "1000", "公開日": "2024-03-01"})
        writer.writerow({"動画のタイトル": "今日の雑談", "再生回数": "800", "公開日": "2024-04-01"})
    rows = load_table(path)
    assert rows[0]["title"] == "PS2の神ゲー7選"
    assert rows[0]["views"] == "300,000"
    videos = [
        _video("fit", "今さら語るPS2神ゲー5選", "Z", 10000, 100000, 20, 4000, 300),
        _video("off", "ただの雑学5選", "Y", 10000, 100000, 20, 4000, 300),
    ]
    result = analyze(videos, rows, [], NOW, [])
    by_id = {row["video_id"]: row for row in result["raw"]}
    assert by_id["fit"]["channel_fit_score"] > by_id["off"]["channel_fit_score"]


def test_ideas_are_original_and_ten_from_demo():
    from src.demo_data import demo_collected, demo_competitor, demo_own

    result = analyze(demo_collected(NOW), demo_own(NOW), demo_competitor(NOW), NOW, ["マイクラ", "切り抜き", "フォートナイト", "VTuber", "事前登録", "今すぐダウンロード"])
    assert len(result["ideas"]) == 10
    references = []
    for video in result["raw"]:
        references.append(video["title"])
    for idea in result["ideas"]:
        assert config.TITLE_MIN_CHARS <= len(idea.title) <= config.TITLE_MAX_CHARS
        assert idea.priority in {"S", "A", "B"}
        assert idea.title not in references
        assert "0.0〜1.0秒" in idea.structure
        for ref in references:
            from src.utils import similarity

            assert similarity(idea.title, ref) < 0.72


def test_scores_stay_in_range():
    values = robust_scale([1, 10, 100, 10_000_000])
    assert all(0 <= value <= 100 for value in values)
    assert values[-1] == pytest.approx(100)


def test_subscriber_hidden_is_empty_not_crash():
    videos = [
        _video("a", "レトロゲームの神ゲー7選", "A", None, 50000, 20, 2000, 300),
        _video("b", "PSPの神ゲー5選", "B", 8000, 40000, 24, 1500, 200),
    ]
    result = analyze(videos, [], [], NOW, [])
    hidden = next(row for row in result["raw"] if row["video_id"] == "a")
    assert hidden["subscriber_count"] is None
    assert hidden["views_per_subscriber"] is None
    assert 0 <= hidden["trend_score"] <= 100


def test_missing_api_key_message(tmp_path: Path):
    client = YouTubeClient("", cache_path=tmp_path, now=NOW)
    with pytest.raises(Exception) as caught:
        client.search_video_ids("PS2", NOW - timedelta(days=7), "7d", 5)
    assert "APIキー" in str(caught.value)


class _Response:
    def __init__(self, payload, status=200):
        self._payload = payload
        self.status_code = status
        self.content = b"{}"

    def json(self):
        return self._payload


class _Session:
    def __init__(self, payload):
        self.payload = payload
        self.calls = 0

    def get(self, url, params, timeout):
        self.calls += 1
        assert "key" in params
        assert params["key"] == "test-key"
        return _Response(self.payload)


def test_search_is_cached_and_quota_counted_once(tmp_path: Path):
    session = _Session({"items": [{"id": {"videoId": "abc123"}}]})
    client = YouTubeClient("test-key", cache_path=tmp_path, session=session, now=NOW)
    first = client.search_video_ids("PS2", NOW - timedelta(days=7), "7d", 5)
    second = client.search_video_ids("PS2", NOW - timedelta(days=7), "7d", 5)
    assert first == ["abc123"]
    assert second == ["abc123"]
    assert session.calls == 1
    assert client.api_calls["search"] == 1
    assert client.quota_used == config.SEARCH_QUOTA_COST
    assert client.cache_hits["search"] == 1


def test_quota_error_is_japanese(tmp_path: Path):
    class Bad(_Session):
        def get(self, url, params, timeout):
            self.calls += 1
            return _Response(
                {"error": {"errors": [{"reason": "quotaExceeded"}], "message": "quota"}},
                status=403,
            )

    client = YouTubeClient("test-key", cache_path=tmp_path, session=Bad({"x": 1}), now=NOW)
    from src.utils import QuotaExceededError

    with pytest.raises(QuotaExceededError) as caught:
        client.search_video_ids("神ゲー", NOW - timedelta(days=1), "1d", 5)
    assert "上限" in str(caught.value)


def test_long_video_is_not_a_short():
    videos = [_video("long", "PS2神ゲーを全部語る", "A", 10000, 10000, 10, duration=600)]
    result = analyze(videos, [], [], NOW, [])
    assert result["ranked"] == []
    assert result["raw"][0]["is_shorts"] is False
