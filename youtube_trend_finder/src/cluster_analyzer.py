"""似たタイトルをまとめ、複数チャンネルで起きているテーマを見つける。"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field

import config
from src.title_analyzer import FORMAT_CATEGORIES
from src.utils import jaccard, median

POSITIVE_THEMES = {"神ゲー", "隠れた名作", "懐かしい", "おすすめ", "神BGM", "ストーリー"}
CONFLICT = {
    "神ゲー": {"クソゲー", "鬱", "トラウマ"},
    "隠れた名作": {"クソゲー"},
    "クソゲー": {"神ゲー", "隠れた名作"},
    "鬱": {"神ゲー"},
    "トラウマ": {"神ゲー"},
}

THEME_PRIORITY = [
    "伏線",
    "衝撃展開",
    "トラウマ",
    "鬱",
    "神BGM",
    "隠れた名作",
    "神ゲー",
    "クソゲー",
    "懐かしい",
    "知らないと損",
    "高難易度",
    "エンディング",
    "裏技",
    "バグ",
    "炎上",
    "あるある",
    "雑学",
    "小ネタ",
    "ストーリー",
    "キャラクター",
]


@dataclass
class ClusterSummary:
    cluster_id: str
    label: str
    video_ids: list[str] = field(default_factory=list)
    channel_count: int = 0
    video_count: int = 0
    avg_views_per_hour: float = 0.0
    median_views_per_subscriber: float | None = None
    avg_comments_per_view: float = 0.0
    avg_trend_score: float = 0.0
    avg_channel_fit: float = 0.0
    avg_opportunity: float = 0.0
    multi_channel_score: float = 0.0
    periods: dict = field(default_factory=dict)
    why: str = ""
    hardware: str = ""
    series: str = ""
    theme: str = ""


def cluster_videos(videos: list[dict]) -> list[dict]:
    targets = [video for video in videos if video.get("is_shorts") and not video.get("excluded")]
    for video in videos:
        video.setdefault("theme_cluster", "")
        video.setdefault("cluster_id", "")
    if not targets:
        return videos

    titles = [str(video.get("title") or "") for video in targets]
    similarity = _cosine_matrix(titles)
    token_sets = [_token_set(video) for video in targets]
    parent = list(range(len(targets)))

    def find(index: int) -> int:
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    def union(left: int, right: int) -> None:
        root_left, root_right = find(left), find(right)
        if root_left != root_right:
            parent[root_right] = root_left

    for i in range(len(targets)):
        for j in range(i + 1, len(targets)):
            if _pair_similarity(i, j, similarity, token_sets) >= config.CLUSTER_SIM_THRESHOLD:
                union(i, j)

    groups: dict[int, list[int]] = defaultdict(list)
    for index in range(len(targets)):
        groups[find(index)].append(index)

    _attach_loose_titles(targets, groups, token_sets, similarity)

    label_counts: dict[str, int] = defaultdict(int)
    for indexes in groups.values():
        if not indexes:
            continue
        label = _label([targets[index] for index in indexes])
        label_counts[label] += 1
        suffix = "" if label_counts[label] == 1 else f" #{label_counts[label]}"
        cluster_id = f"{label}{suffix}"
        for index in indexes:
            targets[index]["theme_cluster"] = label
            targets[index]["cluster_id"] = cluster_id
    return videos


def _attach_loose_titles(targets, groups, token_sets, similarity) -> None:
    """『PS2で500時間遊んだ』のように語が足りない動画を、同じハードの簇へ寄せる。"""
    members = {index: root for root, indexes in groups.items() for index in indexes}
    for index, video in enumerate(targets):
        root = members[index]
        if len(groups[root]) > 1:
            continue
        themes = set(_themes(video))
        if themes & set(CONFLICT) and themes - POSITIVE_THEMES:
            continue
        hardware = _hardware(video)
        if not hardware:
            continue
        title = str(video.get("title") or "")
        time_sink = any(word in title for word in ("時間", "沼", "やみつき", "中毒", "死ぬほど", "ハマ", "面白い"))
        # テーマ語が無く、長時間プレイの言い回しも無い動画は、同じハードというだけで簇に入れない。
        if not themes and not time_sink:
            continue
        best_root = None
        best_score = 0.0
        for other_root, indexes in groups.items():
            if other_root == root or len(indexes) < 2:
                continue
            other_videos = [targets[i] for i in indexes]
            other_hw = Counter(hw for item in other_videos for hw in _hardware(item))
            if not other_hw or other_hw.most_common(1)[0][0] not in hardware:
                continue
            other_themes = Counter(theme for item in other_videos for theme in _themes(item))
            # 別テーマの簇には寄せない。テーマ語が無い動画（「500時間遊んだ」など）だけ寄せる。
            if themes and other_themes and not (themes & set(other_themes)):
                continue
            if other_themes and set(other_themes) & set(CONFLICT):
                dominant = other_themes.most_common(1)[0][0]
                if dominant in CONFLICT and themes & CONFLICT[dominant]:
                    continue
            score = max(float(similarity[index][i]) for i in indexes)
            shared_hw = 0.15 if hardware & set(other_hw) else 0.0
            score += shared_hw
            if time_sink:
                score += 0.12
            if score > best_score:
                best_score = score
                best_root = other_root
        if best_root is not None and best_score >= 0.28:
            groups[best_root].append(index)
            groups[root].remove(index)
            members[index] = best_root


def assign_multi_channel_scores(videos: list[dict]) -> list[dict]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for video in videos:
        if video.get("cluster_id"):
            grouped[video["cluster_id"]].append(video)
    for members in grouped.values():
        score = _multi_channel_score(members)
        for video in members:
            video["multi_channel_score"] = round(score, 2)
    for video in videos:
        video.setdefault("multi_channel_score", 0.0)
    return videos


def summarize_clusters(videos: list[dict]) -> list[ClusterSummary]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for video in videos:
        if video.get("is_shorts") and not video.get("excluded") and video.get("cluster_id"):
            grouped[video["cluster_id"]].append(video)
    summaries: list[ClusterSummary] = []
    global_vph = median([video.get("views_per_hour") or 0 for video in videos if video.get("is_shorts") and not video.get("excluded")]) or 0
    global_vps = median(
        [
            video["views_per_subscriber"]
            for video in videos
            if video.get("is_shorts") and not video.get("excluded") and video.get("views_per_subscriber") is not None
        ]
    )
    global_comments = median(
        [
            video.get("comments_per_view") or 0
            for video in videos
            if video.get("is_shorts") and not video.get("excluded") and (video.get("views") or 0) >= config.MIN_VIEWS_FOR_RATE
        ]
    ) or 0

    for cluster_id, members in grouped.items():
        channels = {video.get("channel_id") or video.get("channel_name") for video in members}
        channels.discard("")
        vps_values = [video["views_per_subscriber"] for video in members if video.get("views_per_subscriber") is not None]
        summary = ClusterSummary(
            cluster_id=cluster_id,
            label=members[0].get("theme_cluster") or cluster_id,
            video_ids=[video.get("video_id") or "" for video in members],
            channel_count=len(channels),
            video_count=len(members),
            avg_views_per_hour=_avg([video.get("views_per_hour") or 0 for video in members]),
            median_views_per_subscriber=median(vps_values),
            avg_comments_per_view=_avg([video.get("comments_per_view") or 0 for video in members]),
            avg_trend_score=_avg([video.get("trend_score") or 0 for video in members]),
            avg_channel_fit=_avg([video.get("channel_fit_score") or 0 for video in members]),
            avg_opportunity=_avg([video.get("opportunity_score") or 0 for video in members]),
            multi_channel_score=_multi_channel_score(members),
            hardware=_mode([video.get("hardware") or "" for video in members]),
            series=_mode([video.get("series") or "" for video in members]),
            theme=_mode_theme(members),
        )
        summary.periods = {
            "24h": _period_stats(members, "in_24h"),
            "3d": _period_stats(members, "in_3d"),
            "7d": _period_stats(members, "in_7d"),
        }
        summary.why = _why(summary, global_vph, global_vps, global_comments)
        summaries.append(summary)
    summaries.sort(
        key=lambda item: (
            item.channel_count >= 2,
            item.avg_opportunity + min(item.channel_count, 4) * 2,
            item.channel_count,
        ),
        reverse=True,
    )
    return summaries


def _cosine_matrix(titles: list[str]):
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
    except ImportError:
        size = len(titles)
        return [[1.0 if i == j else 0.0 for j in range(size)] for i in range(size)]
    if len(titles) == 1:
        return [[1.0]]
    matrix = TfidfVectorizer(analyzer="char", ngram_range=(2, 4)).fit_transform(titles)
    return cosine_similarity(matrix)


def _token_set(video: dict) -> set[str]:
    tokens = set(video.get("theme_tokens") or [])
    return {token for token in tokens if token.startswith(("hw:", "sr:", "th:", "fmt:"))}


def _pair_similarity(i: int, j: int, cosine, tokens: list[set[str]]) -> float:
    left, right = tokens[i], tokens[j]
    shared_core = {token for token in left & right if token.startswith(("hw:", "sr:", "th:"))}
    if not shared_core:
        return 0.0
    left_themes = {token[3:] for token in left if token.startswith("th:")}
    right_themes = {token[3:] for token in right if token.startswith("th:")}
    for theme, blocked in CONFLICT.items():
        if theme in left_themes and right_themes & blocked:
            return 0.0
        if theme in right_themes and left_themes & blocked:
            return 0.0
    token_score = jaccard(left, right)
    text_score = float(cosine[i][j])
    score = config.CLUSTER_TFIDF_WEIGHT * text_score + config.CLUSTER_TOKEN_WEIGHT * token_score
    # 日本語の短いタイトルは文字n-gramのcosが低く出る。
    # 同じハード（またはシリーズ）かつ同じテーマなら、企画として同じ簇にする。
    shared_theme = {token for token in shared_core if token.startswith("th:")}
    shared_place = {token for token in shared_core if token.startswith(("hw:", "sr:"))}
    if shared_theme and shared_place:
        score = max(score, 0.74)
    elif shared_theme and not any(token.startswith(("hw:", "sr:")) for token in left | right):
        # ハードが付いていない同じテーマ同士。「鬱ゲー」同士をまとめる。
        # ハード付きの神ゲーとは繋がない。繋がるとPS2とスーファミが一つに溶ける。
        score = max(score, 0.72)
    return score


def _label(members: list[dict]) -> str:
    hardware = Counter(hw for video in members for hw in _split(video.get("hardware")))
    series = Counter(item for video in members for item in _split(video.get("series")))
    themes = Counter(theme for video in members for theme in _themes(video))
    hw = hardware.most_common(1)[0][0] if hardware else ""
    sr = series.most_common(1)[0][0] if series and series.most_common(1)[0][1] >= max(1, len(members) / 2) else ""
    theme = _best_theme(themes)
    if sr and theme:
        return f"{sr} {theme}"
    if hw and theme:
        return f"{hw} {theme}"
    if hw and sr:
        return f"{hw} {sr}"
    return theme or hw or sr or "その他"


def _best_theme(counter: Counter) -> str:
    if not counter:
        return ""
    best_count = counter.most_common(1)[0][1]
    tied = [name for name, count in counter.items() if count == best_count]
    priority = {name: index for index, name in enumerate(THEME_PRIORITY)}
    tied.sort(key=lambda name: priority.get(name, 99))
    return tied[0]


def _themes(video: dict) -> list[str]:
    categories = video.get("categories") or []
    if isinstance(categories, str):
        categories = [part.strip() for part in categories.split("/") if part.strip()]
    return [cat for cat in categories if cat not in FORMAT_CATEGORIES and cat != "その他"]


def _hardware(video: dict) -> set[str]:
    return set(_split(video.get("hardware")))


def _split(value: object) -> list[str]:
    if not value:
        return []
    return [part.strip() for part in str(value).split("/") if part.strip()]


def _mode(values: list[str]) -> str:
    cleaned = [value for value in values if value]
    if not cleaned:
        return ""
    return Counter(cleaned).most_common(1)[0][0]


def _mode_theme(members: list[dict]) -> str:
    counter = Counter(theme for video in members for theme in _themes(video))
    return _best_theme(counter)


def _avg(values: list[float]) -> float:
    if not values:
        return 0.0
    return float(sum(values) / len(values))


def _period_stats(members: list[dict], flag: str) -> dict:
    picked = [video for video in members if video.get(flag)]
    return {
        "count": len(picked),
        "avg_views_per_hour": _avg([video.get("views_per_hour") or 0 for video in picked]) if picked else 0.0,
    }


def _multi_channel_score(members: list[dict]) -> float:
    strong = [video for video in members if (video.get("trend_score") or 0) >= 45]
    pool = strong or members
    channels = {video.get("channel_id") or video.get("channel_name") for video in pool}
    channels.discard("")
    count = len(channels)
    if not strong:
        return min(40.0, 18.0 + count * 8)
    if count <= 1:
        return 22.0
    if count == 2:
        return 60.0
    if count == 3:
        return 78.0
    return min(100.0, 86.0 + (count - 4) * 4)


def _why(summary: ClusterSummary, global_vph: float, global_vps: float | None, global_comments: float) -> str:
    reasons: list[str] = []
    if summary.channel_count >= 3:
        reasons.append(f"{summary.channel_count}つの別チャンネルで、近いテーマのShortsが同時に伸びています。")
    elif summary.channel_count == 2:
        reasons.append("2チャンネルで同テーマが伸びており、1本だけの偶然より再現性があります。")
    else:
        reasons.append("まだ1チャンネルが中心なので、波及するかは次の日も見た方がよいです。")
    if global_vph and summary.avg_views_per_hour >= global_vph * 1.4:
        ratio = summary.avg_views_per_hour / global_vph
        reasons.append(f"平均の再生速度は、今回のShorts全体の中央値の約{ratio:.1f}倍です。")
    if summary.median_views_per_subscriber and (
        summary.median_views_per_subscriber >= 3
        or (global_vps and summary.median_views_per_subscriber >= global_vps * 1.5)
    ):
        reasons.append(
            f"登録者比の中央値は{summary.median_views_per_subscriber:.1f}倍で、"
            "チャンネルの大きさだけでは説明しにくいです。"
        )
    if global_comments and summary.avg_comments_per_view >= global_comments * 1.4:
        reasons.append("コメント率が高く、自分の体験を書きたくなるテーマです。")
    day = summary.periods.get("24h") or {}
    week = summary.periods.get("7d") or {}
    if day.get("count") and week.get("avg_views_per_hour") and day["avg_views_per_hour"] > week["avg_views_per_hour"] * 1.15:
        reasons.append("過去7日より直近24時間の再生速度が上で、今伸びている途中です。")
    elif day.get("count"):
        reasons.append("直近24時間にも新しい動画があり、話題が途切れていません。")
    return "".join(reasons)
