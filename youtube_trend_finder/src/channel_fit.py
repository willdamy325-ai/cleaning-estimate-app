"""過去動画から、自チャンネルと競合で成績が良かったテーマを数値にする。"""

from __future__ import annotations

from collections import defaultdict

import config
from src.title_analyzer import apply_title_fields
from src.utils import log, robust_scale, to_int


def prepare_history(rows: list[dict], source: str) -> list[dict]:
    prepared: list[dict] = []
    for row in rows:
        title = str(row.get("title") or "").strip()
        views = to_int(row.get("views"))
        if not title or views is None:
            continue
        item = dict(row)
        item["title"] = title
        item["views"] = views
        item["source"] = source
        apply_title_fields(item)
        prepared.append(item)
    if not prepared:
        return []
    scores = robust_scale([item["views"] for item in prepared])
    for item, score in zip(prepared, scores):
        item["performance"] = score
    return prepared


def build_profile(rows: list[dict]) -> dict[str, float]:
    """トークンごとの相対成績。本数が少ないトークンは50点へ寄せる。"""
    if not rows:
        return {}
    grouped: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        performance = float(row.get("performance") or 50)
        for token in _fit_tokens(row):
            grouped[token].append(performance)
    prior_strength = 2.0 if len(rows) >= 3 else 8.0
    profile: dict[str, float] = {}
    for token, scores in grouped.items():
        mean = sum(scores) / len(scores)
        profile[token] = (mean * len(scores) + 50.0 * prior_strength) / (len(scores) + prior_strength)
    return profile


def score_fit(videos: list[dict], profile: dict[str, float], field: str) -> None:
    neutral = config.NEUTRAL_FIT_SCORE if not profile else config.UNSEEN_THEME_FIT
    for video in videos:
        if not video.get("is_shorts"):
            video[field] = 0.0
            continue
        tokens = _fit_tokens(video)
        weighted = 0.0
        weight_sum = 0.0
        for token in tokens:
            if token not in profile:
                continue
            weight = _token_weight(token)
            weighted += profile[token] * weight
            weight_sum += weight
        if weight_sum == 0:
            video[field] = round(neutral, 2)
        else:
            video[field] = round(weighted / weight_sum, 2)


def describe_fit(video: dict, profile: dict[str, float]) -> str:
    if not profile:
        return (
            "過去動画のCSVが見つからないため、相性は中立の50点です。"
            "kuro_youtube_40.csv を置くと、過去に伸びたテーマへ寄るようになります。"
        )
    matched = []
    for token in _fit_tokens(video):
        if token in profile:
            matched.append((profile[token], token))
    if not matched:
        return "過去動画には近いテーマが少なく、相性は中立より少し下です。導入の一言をチャンネルの語り口に寄せると扱いやすいです。"
    matched.sort(reverse=True)
    strong = [ _token_label(token) for score, token in matched if score >= 60][:3]
    score = video.get("channel_fit_score") or 0
    if score >= 75 and strong:
        return f"過去動画では{'・'.join(strong)}の成績が良く、今回の企画とかなり重なります。"
    if score >= 60 and strong:
        return f"過去動画の{'・'.join(strong)}と重なり、いつもの視聴者に届きやすいテーマです。"
    if score >= 48:
        return "過去の当たりテーマと一部が重なります。ランキングの型に乗せれば、チャンネルの流れを崩さずに出せます。"
    weak = _token_label(matched[-1][1])
    return f"過去動画では{weak}の成績は控えめです。フックの一言を、伸びたテーマの語り口に寄せた方が安全です。"


def _fit_tokens(row: dict) -> list[str]:
    tokens = list(row.get("theme_tokens") or [])
    if not tokens and row.get("category"):
        apply_title_fields(row)
        tokens = list(row.get("theme_tokens") or [])
    return [token for token in tokens if token.startswith(("th:", "hw:", "sr:", "fmt:"))]


def _token_weight(token: str) -> float:
    if token.startswith("th:"):
        return 1.35
    if token.startswith("hw:"):
        return 1.2
    if token.startswith("sr:"):
        return 1.2
    if token.startswith("fmt:"):
        return 1.15
    return 1.0


def _token_label(token: str) -> str:
    return token.split(":", 1)[-1]


def load_profiles(own_rows: list[dict], competitor_rows: list[dict]) -> tuple[dict[str, float], dict[str, float], dict]:
    own = prepare_history(own_rows, "own")
    competitor = prepare_history(competitor_rows, "competitor")
    if own_rows and not own:
        log("自チャンネルCSVは見つかりましたが、タイトルと再生回数を読めませんでした。列名を確認してください。")
    if competitor_rows and not competitor:
        log("競合CSVは見つかりましたが、タイトルと再生回数を読めませんでした。")
    stats = {
        "own_videos": len(own),
        "competitor_videos": len(competitor),
        "own_top_tokens": _top_tokens(build_profile(own)),
        "competitor_top_tokens": _top_tokens(build_profile(competitor)),
    }
    return build_profile(own), build_profile(competitor), stats


def _top_tokens(profile: dict[str, float], limit: int = 8) -> list[dict]:
    ranked = sorted(profile.items(), key=lambda item: item[1], reverse=True)
    return [{"token": _token_label(token), "score": round(score, 1)} for token, score in ranked[:limit]]
