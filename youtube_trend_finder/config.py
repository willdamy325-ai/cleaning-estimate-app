"""変更しやすい設定。重みや期間はここを編集する。"""

from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def project_root() -> Path:
    override = os.environ.get("TREND_FINDER_HOME")
    if override:
        return Path(override)
    return ROOT


def data_dir() -> Path:
    return project_root() / "data"


def cache_dir() -> Path:
    return data_dir() / "cache"


def daily_dir() -> Path:
    return data_dir() / "daily"


def reports_dir() -> Path:
    return project_root() / "reports"


def keywords_path() -> Path:
    return project_root() / "config" / "search_keywords.txt"


def exclude_path() -> Path:
    return project_root() / "config" / "exclude_keywords.txt"


# 検索ウィンドウ。3日は7日検索の結果を公開時刻で切り分ける（search.listを増やさない）。
SEARCH_WINDOWS = [
    {"name": "7d", "hours": 24 * 7, "max_results": 15},
    {"name": "1d", "hours": 24, "max_results": 10},
]
COMPARE_WINDOWS_HOURS = {"24h": 24, "3d": 24 * 3, "7d": 24 * 7}

REGION_CODE = "JP"
RELEVANCE_LANGUAGE = "ja"

SHORTS_MAX_SECONDS = 180
PREFERRED_SHORTS_SECONDS = 60
# 60秒以内を基準にし、61〜180秒はわずかに下げる。
DURATION_SCORE_FACTOR = {"preferred": 1.0, "standard": 0.92, "unknown": 0.9}

# 公開直後の再生速度が暴れないように、分母は最低この時間にする。
MIN_HOURS_FOR_VELOCITY = 3.0

# 再生数が少ない動画のいいね率・コメント率は信用しない。
MIN_VIEWS_FOR_RATE = 1000

# Trend Score の内訳。合計が1でなくても実行時に比率へ直す。
TREND_WEIGHTS = {
    "velocity": 0.35,
    "subscriber_ratio": 0.30,
    "comments": 0.15,
    "likes": 0.10,
    "recency": 0.10,
}

# 登録者非公開の動画は、登録者比を「分かっている動画の中央値」にしてから少し下げる。
UNKNOWN_SUBS_FACTOR = 0.85

# 登録者が多く、登録者比が中央値未満の動画は再生速度の効きを弱める。
MEGA_CHANNEL_SUBS = 500_000
MEGA_LOW_VPS_VELOCITY_FACTOR = 0.65

# コメント率が上位10%なら、少しだけ加点する。
COMMENT_TOP_DECILE_BONUS = 3.0

# 日本語がほとんど無いタイトルは下げる（日本のゲームShortsが対象）。
MIN_JP_CHAR_RATIO = 0.2
LOW_JP_FACTOR = 0.55

# 実況・速報などは除外リストには入れず、スコアだけ下げる。
SOFT_DOWNRANK_KEYWORDS = ["実況", "リアクション", "ガチャ", "速報"]
SOFT_DOWNRANK_FACTOR = 0.4

# Opportunity Score の内訳。
OPPORTUNITY_WEIGHTS = {
    "trend": 0.45,
    "channel_fit": 0.25,
    "competitor": 0.15,
    "multi_channel": 0.15,
}

# 過去データが無いときの中立点。
NEUTRAL_FIT_SCORE = 50.0
# 過去にそのテーマが無いときの適合。実績があるテーマより少し下。
UNSEEN_THEME_FIT = 46.0

# 同じチャンネルの動画がランキングを埋めないように、3本目以降を下げる。
MAX_VIDEOS_PER_CHANNEL = 2
EXTRA_VIDEO_FACTOR = 0.55

# クラスタリング
CLUSTER_SIM_THRESHOLD = 0.40
CLUSTER_TFIDF_WEIGHT = 0.55
CLUSTER_TOKEN_WEIGHT = 0.45

# 企画の優先度
PRIORITY_S_OPPORTUNITY = 70
PRIORITY_S_CHANNELS = 3
PRIORITY_S_FIT = 58
PRIORITY_A_OPPORTUNITY = 60

# API
DAILY_QUOTA_BUDGET = 6500
SEARCH_QUOTA_COST = 100
VIDEOS_QUOTA_COST = 1
CHANNELS_QUOTA_COST = 1
CACHE_TTL_HOURS = 12
API_TIMEOUT_SECONDS = 20
API_RETRY_COUNT = 3

YOUTUBE_API_BASE = "https://www.googleapis.com/youtube/v3"

# フォールバック。config/search_keywords.txt が空のときだけ使う。
DEFAULT_KEYWORDS = [
    "PS2",
    "神ゲー",
    "レトロゲーム",
    "ドラクエ",
    "鬱ゲー",
    "ゲーム ランキング",
]

IDEA_COUNT = 10
THEME_TOP_N = 10

# 企画タイトルの文字数。Shortsの読み上げに乗る長さ。
TITLE_MIN_CHARS = 20
TITLE_MAX_CHARS = 35
