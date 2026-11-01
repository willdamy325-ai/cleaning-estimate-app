"""入出力、日付、正規化、壊れにくい数値処理。"""

from __future__ import annotations

import csv
import json
import math
import os
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

TOKYO = ZoneInfo("Asia/Tokyo")

COLUMN_ALIASES: dict[str, list[str]] = {
    "video_id": [
        "video_id",
        "videoid",
        "id",
        "動画id",
        "動画のid",
        "video id",
    ],
    "title": ["title", "タイトル", "動画タイトル", "動画のタイトル", "name", "video title"],
    "channel_id": ["channel_id", "channelid", "チャンネルid", "channel id"],
    "channel_name": [
        "channel_name",
        "channel",
        "channel_title",
        "チャンネル名",
        "チャンネル",
        "channel title",
        "チャンネルタイトル",
    ],
    "published_at": [
        "published_at",
        "published",
        "publish_date",
        "publishedat",
        "公開日",
        "公開日時",
        "投稿日",
        "日付",
        "upload_date",
    ],
    "duration_seconds": [
        "duration_seconds",
        "duration",
        "長さ",
        "秒数",
        "動画の長さ",
        "video_duration",
        "length",
    ],
    "views": [
        "views",
        "view_count",
        "viewcount",
        "再生回数",
        "視聴回数",
        "再生数",
        "views_count",
    ],
    "likes": ["likes", "like_count", "likecount", "高評価", "高評価数", "いいね", "いいね数"],
    "comments": [
        "comments",
        "comment_count",
        "commentcount",
        "コメント",
        "コメント数",
    ],
    "subscriber_count": [
        "subscriber_count",
        "subscribers",
        "subscribercount",
        "登録者",
        "登録者数",
        "チャンネル登録者数",
    ],
    "channel_total_views": [
        "channel_total_views",
        "channel_views",
        "チャンネル総再生数",
        "総再生回数",
    ],
    "channel_video_count": [
        "channel_video_count",
        "video_count",
        "チャンネル動画数",
        "動画本数",
    ],
    "description": ["description", "説明", "概要", "説明欄", "概要欄", "video_description"],
    "thumbnail_url": ["thumbnail_url", "thumbnail", "サムネイル", "サムネイルurl", "thumbnails"],
    "url": ["url", "video_url", "動画url", "リンク", "watch_url"],
    "category": ["category", "カテゴリ", "分類"],
    "game_title": ["game_title", "ゲームタイトル", "ゲーム名"],
    "hardware": ["hardware", "ハード", "機種"],
}


class APIKeyError(Exception):
    """APIキーが無い、または無効。"""


class QuotaExceededError(Exception):
    """YouTube Data APIの1日の上限。"""


class NetworkError(Exception):
    """通信失敗。"""


def log(message: str) -> None:
    print(message, flush=True)


def now_tokyo() -> datetime:
    return datetime.now(TOKYO)


def today_stamp(now: datetime | None = None) -> str:
    current = now or now_tokyo()
    if current.tzinfo is None:
        current = current.replace(tzinfo=TOKYO)
    return current.astimezone(TOKYO).strftime("%Y-%m-%d")


def load_env_file(path: Path) -> None:
    """python-dotenv が無くても .env を読む。"""
    if path.exists():
        try:
            from dotenv import load_dotenv

            load_dotenv(path)
            return
        except ImportError:
            pass
        for line in path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in stripped:
                continue
            key, value = stripped.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value


def read_list_file(path: Path) -> list[str]:
    if not path.exists():
        log(f"設定ファイルが見つかりません: {path}")
        return []
    items: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        text = line.strip()
        if not text:
            continue
        # 「# メモ」はコメント。「#広告」のようにタグそのものはキーワードとして残す。
        if text.startswith("#") and (len(text) == 1 or text[1].isspace()):
            continue
        items.append(text)
    return items


def _fold(name: str) -> str:
    text = unicodedata.normalize("NFKC", str(name)).strip().lower()
    text = text.replace(" ", "").replace("_", "").replace("-", "")
    return text


def normalize_columns(fieldnames: list[str] | None) -> dict[str, str]:
    """CSVの実際の列名 → 内部名。"""
    if not fieldnames:
        return {}
    folded = {_fold(name): name for name in fieldnames}
    mapping: dict[str, str] = {}
    used: set[str] = set()
    for internal, aliases in COLUMN_ALIASES.items():
        for alias in aliases:
            key = _fold(alias)
            if key in folded and folded[key] not in used:
                mapping[internal] = folded[key]
                used.add(folded[key])
                break
    return mapping


def _is_blank(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, float) and math.isnan(value):
        return True
    text = str(value).strip()
    return text == "" or text.lower() in {"null", "none", "nan", "非公開", "n/a", "-"}


def to_int(value: Any) -> int | None:
    if _is_blank(value):
        return None
    if isinstance(value, bool):
        return None
    text = str(value).strip().replace(",", "").replace("，", "")
    text = text.replace("回", "").replace("人", "").replace("本", "")
    try:
        return int(float(text))
    except ValueError:
        return None


def to_float(value: Any) -> float | None:
    if _is_blank(value):
        return None
    try:
        return float(str(value).replace(",", ""))
    except ValueError:
        return None


def parse_duration_seconds(value: Any) -> int | None:
    if _is_blank(value):
        return None
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if isinstance(value, float) and math.isnan(value):
            return None
        return max(0, int(value))
    text = unicodedata.normalize("NFKC", str(value).strip())
    iso = re.fullmatch(
        r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?",
        text,
        flags=re.IGNORECASE,
    )
    if iso and text.upper().startswith("PT"):
        hours = int(iso.group(1) or 0)
        minutes = int(iso.group(2) or 0)
        seconds = int(iso.group(3) or 0)
        return hours * 3600 + minutes * 60 + seconds
    if text.endswith("秒"):
        return to_int(text[:-1])
    if re.fullmatch(r"\d+(\.\d+)?", text):
        return int(float(text))
    parts = text.split(":")
    if len(parts) in {2, 3} and all(re.fullmatch(r"\d+", part) for part in parts):
        numbers = [int(part) for part in parts]
        if len(numbers) == 2:
            return numbers[0] * 60 + numbers[1]
        return numbers[0] * 3600 + numbers[1] * 60 + numbers[2]
    return None


def parse_datetime(value: Any) -> datetime | None:
    """タイムゾーンが無い日時は日本時間として扱う。"""
    if _is_blank(value):
        return None
    if isinstance(value, datetime):
        dt = value
    else:
        text = unicodedata.normalize("NFKC", str(value).strip())
        text = text.replace("Z", "+00:00")
        text = text.replace("/", "-")
        dt = None
        try:
            dt = datetime.fromisoformat(text)
        except ValueError:
            for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d", "%Y%m%d"):
                try:
                    dt = datetime.strptime(text, fmt)
                    break
                except ValueError:
                    continue
        if dt is None:
            return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=TOKYO)
    return dt.astimezone(timezone.utc)


def isoformat_utc(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=TOKYO)
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def hours_between(later: datetime, earlier: datetime) -> float:
    later_utc = later if later.tzinfo else later.replace(tzinfo=TOKYO)
    earlier_utc = earlier if earlier.tzinfo else earlier.replace(tzinfo=TOKYO)
    seconds = (later_utc - earlier_utc).total_seconds()
    return max(0.0, seconds / 3600.0)


def safe_div(numerator: float | None, denominator: float | None) -> float | None:
    if numerator is None or denominator is None:
        return None
    if denominator == 0:
        return None
    return numerator / denominator


def jp_char_ratio(text: str) -> float:
    if not text:
        return 0.0
    chars = [ch for ch in text if not ch.isspace()]
    if not chars:
        return 0.0
    jp = 0
    for ch in chars:
        code = ord(ch)
        if (
            0x3040 <= code <= 0x30FF
            or 0x4E00 <= code <= 0x9FFF
            or 0x3400 <= code <= 0x4DBF
        ):
            jp += 1
    return jp / len(chars)


def robust_scale(values: list[float | None]) -> list[float]:
    """log変換 → 上下5%を丸める → 0〜100。外れ値1本で潰れにくい。"""
    import numpy as np

    if not values:
        return []
    clean = [0.0 if v is None or (isinstance(v, float) and math.isnan(v)) else float(v) for v in values]
    arr = np.log1p(np.clip(np.array(clean, dtype=float), 0, None))
    if len(arr) == 1:
        return [50.0]
    lo = float(np.percentile(arr, 5))
    hi = float(np.percentile(arr, 95))
    if hi - lo < 1e-9:
        return [50.0] * len(values)
    clipped = np.clip(arr, lo, hi)
    scaled = (clipped - lo) / (hi - lo) * 100.0
    return [float(x) for x in scaled]


def median(values: list[float]) -> float | None:
    nums = sorted(v for v in values if v is not None and not math.isnan(v))
    if not nums:
        return None
    mid = len(nums) // 2
    if len(nums) % 2:
        return float(nums[mid])
    return float((nums[mid - 1] + nums[mid]) / 2)


def normalize_weights(weights: dict[str, float]) -> dict[str, float]:
    total = sum(max(0.0, float(v)) for v in weights.values())
    if total <= 0:
        raise ValueError("スコアの重みがすべて0です。config.py を確認してください。")
    return {key: max(0.0, float(value)) / total for key, value in weights.items()}


def clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        log(f"キャッシュを読めなかったので無視します: {path.name}")
        return default


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def load_table(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        mapping = normalize_columns(reader.fieldnames)
        rows: list[dict[str, Any]] = []
        for raw in reader:
            item: dict[str, Any] = {}
            for internal, original in mapping.items():
                item[internal] = raw.get(original)
            if not any(not _is_blank(v) for v in item.values()):
                continue
            rows.append(item)
        return rows


def write_table(path: Path, rows: list[dict[str, Any]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            out: dict[str, Any] = {}
            for column in columns:
                value = row.get(column)
                if value is None or (isinstance(value, float) and math.isnan(value)):
                    out[column] = ""
                elif isinstance(value, float):
                    out[column] = round(value, 4)
                elif isinstance(value, bool):
                    out[column] = "1" if value else "0"
                else:
                    out[column] = value
            writer.writerow(out)


def discover_csv(exact_names: list[str], patterns: list[str]) -> Path | None:
    """ルート直下や data/existing を探し、日次出力は使わない。"""
    import config

    roots = [
        Path.cwd(),
        Path.cwd() / "data" / "existing",
        config.project_root(),
        config.project_root() / "data" / "existing",
        config.project_root().parent,
        config.project_root().parent / "data" / "existing",
    ]
    seen: set[Path] = set()
    ordered_roots: list[Path] = []
    for root in roots:
        resolved = root.resolve()
        if resolved in seen or not resolved.exists():
            continue
        seen.add(resolved)
        ordered_roots.append(resolved)

    for root in ordered_roots:
        for name in exact_names:
            candidate = root / name
            if candidate.is_file():
                return candidate

    matches: list[Path] = []
    for root in ordered_roots:
        for pattern in patterns:
            for candidate in root.glob(pattern):
                if not candidate.is_file():
                    continue
                if "data/daily" in candidate.as_posix() or "data\\daily" in str(candidate):
                    continue
                if candidate.name.startswith("trend_"):
                    continue
                matches.append(candidate)
    if not matches:
        return None
    matches.sort(key=lambda path: (len(path.name), str(path)))
    return matches[0]


def video_url(video_id: str, shorts: bool = True) -> str:
    if not video_id:
        return ""
    if shorts:
        return f"https://www.youtube.com/shorts/{video_id}"
    return f"https://www.youtube.com/watch?v={video_id}"


def format_int(value: Any) -> str:
    number = to_int(value)
    if number is None:
        return "非公開"
    return f"{number:,}"


def format_float(value: Any, digits: int = 1) -> str:
    number = to_float(value)
    if number is None:
        return "—"
    return f"{number:,.{digits}f}"


def recency_raw(hours: float | None) -> float:
    """3時間未満は不安定なので頭打ちにし、その後は緩やかに下がる。"""
    if hours is None:
        return 40.0
    if hours < 3:
        return 42.0
    # 3時間時点を100とし、おおよそ4日で半減する。
    return 100.0 * math.exp(-(hours - 3.0) / 96.0)


def jaccard(left: set[str], right: set[str]) -> float:
    if not left and not right:
        return 0.0
    union = left | right
    if not union:
        return 0.0
    return len(left & right) / len(union)


def similarity(left: str, right: str) -> float:
    from difflib import SequenceMatcher

    a = re.sub(r"\s+", "", left).lower()
    b = re.sub(r"\s+", "", right).lower()
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a, b).ratio()
