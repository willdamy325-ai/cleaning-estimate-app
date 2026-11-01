"""クラスタから、クロのゲーム情報局向けの企画を10本にする。"""

from __future__ import annotations

import re
from dataclasses import dataclass

import config
from src.channel_fit import describe_fit
from src.cluster_analyzer import ClusterSummary
from src.utils import similarity


@dataclass
class Idea:
    rank: int
    plan: str
    title: str
    theme: str
    references: list[dict]
    evidence: str
    fit_text: str
    audience: str
    structure: str
    priority: str
    opportunity: float
    cluster_id: str


def generate_ideas(
    clusters: list[ClusterSummary],
    videos: list[dict],
    own_profile: dict[str, float],
    limit: int | None = None,
) -> list[Idea]:
    limit = limit or config.IDEA_COUNT
    by_id = {video.get("video_id"): video for video in videos}
    usable = [cluster for cluster in clusters if cluster.video_count >= 1 and cluster.label != "その他"]
    usable.sort(key=lambda cluster: (cluster.channel_count >= 2, cluster.avg_opportunity, cluster.channel_count), reverse=True)
    ideas: list[Idea] = []
    used_titles: list[str] = []
    for cluster in usable:
        if len(ideas) >= limit:
            break
        members = [by_id[video_id] for video_id in cluster.video_ids if video_id in by_id]
        members.sort(key=lambda video: video.get("opportunity_score") or 0, reverse=True)
        if not members:
            continue
        reference_titles = [str(video.get("title") or "") for video in members]
        title = _title_for(cluster, members, reference_titles + used_titles, variant=0)
        if not title:
            continue
        used_titles.append(title)
        ideas.append(_build_idea(len(ideas) + 1, cluster, members, title, own_profile, variant=0))

    # テーマが10個に満たないときは、強いクラスタの別角度で埋める。
    cursor = 0
    while len(ideas) < limit and usable:
        cluster = usable[cursor % len(usable)]
        cursor += 1
        if cursor > limit * 4:
            break
        members = [by_id[video_id] for video_id in cluster.video_ids if video_id in by_id]
        members.sort(key=lambda video: video.get("opportunity_score") or 0, reverse=True)
        title = _title_for(cluster, members, [item.title for item in ideas] + [str(v.get("title") or "") for v in members], variant=cursor)
        if not title:
            continue
        idea = _build_idea(len(ideas) + 1, cluster, members, title, own_profile, variant=cursor)
        if idea.priority == "S":
            idea.priority = "A"
        elif idea.priority == "A":
            idea.priority = "B"
        idea.plan = "同じテーマの別角度。" + idea.plan
        ideas.append(idea)
    for index, idea in enumerate(ideas, start=1):
        idea.rank = index
    return ideas[:limit]


def _build_idea(rank, cluster: ClusterSummary, members: list[dict], title: str, own_profile: dict, variant: int) -> Idea:
    lead = members[0]
    games = []
    for video in members:
        for name in str(video.get("game_title") or "").split("/"):
            name = name.strip()
            if name and name not in games:
                games.append(name)
    if games:
        game_hint = "、".join(games[:4])
    else:
        anchor = cluster.hardware or cluster.series or "レトロ"
        game_hint = f"{anchor}でコメントが割れやすい具体タイトル"
    theme = cluster.label
    plan = (
        f"「{theme}」を、ゲーム映像の一言フックから{ _count_in_title(title) }本のランキングShortsにする。"
        f"各順位は作品名のあと、コメントで実際に起きそうな反応を2つ置く。"
    )
    if variant:
        plan = f"切り口を変えて、{theme}の中でも議論が割れやすい順にする。" + plan
    evidence = cluster.why or "複数の指標で、いま反応が付いているテーマです。"
    fit_text = describe_fit(lead, own_profile)
    audience = _audience(cluster)
    structure = _structure(title, theme, game_hint)
    priority = _priority(cluster, lead, bool(own_profile))
    references = []
    for video in members[:3]:
        references.append(
            {
                "title": video.get("title") or "",
                "channel_name": video.get("channel_name") or "",
                "url": video.get("video_url") or "",
                "views": video.get("views") or 0,
            }
        )
    return Idea(
        rank=rank,
        plan=plan,
        title=title,
        theme=theme,
        references=references,
        evidence=evidence,
        fit_text=fit_text,
        audience=audience,
        structure=structure,
        priority=priority,
        opportunity=round(cluster.avg_opportunity, 1),
        cluster_id=cluster.cluster_id,
    )


def _priority(cluster: ClusterSummary, lead: dict, has_history: bool) -> str:
    fit = lead.get("channel_fit_score") or 0
    opportunity = cluster.avg_opportunity
    if (
        has_history
        and opportunity >= config.PRIORITY_S_OPPORTUNITY
        and cluster.channel_count >= config.PRIORITY_S_CHANNELS
        and fit >= config.PRIORITY_S_FIT
    ):
        return "S"
    if opportunity >= config.PRIORITY_A_OPPORTUNITY and cluster.channel_count >= 2:
        return "A"
    if opportunity >= 68 and fit >= 70 and cluster.channel_count >= 2:
        return "A"
    return "B"


def _audience(cluster: ClusterSummary) -> str:
    bits = ["20代後半〜50代で、昔のゲームを自分の体験として語りたい人"]
    if cluster.hardware:
        bits.append(f"{cluster.hardware}を実際に触っていた層")
    if cluster.series:
        bits.append(f"{cluster.series}の話ならコメントしたくなる人")
    if cluster.theme in {"鬱", "トラウマ", "衝撃展開", "伏線"}:
        bits.append("ネタバレと感想でコメント欄が動きやすい人")
    return "。".join(bits) + "。"


def _structure(title: str, theme: str, game_hint: str) -> str:
    hook = _hook(theme)
    return (
        f"0.0〜1.0秒: ゲーム映像＋「{hook}」\n"
        f"1.0〜1.5秒: 短いタイトル「{title}」\n"
        "1.5秒〜: 下の順位から即ランキング（1本あたり約5秒）\n"
        f"  順位 → ゲームタイトル（候補: {game_hint}）\n"
        "  → コメント反応を2つ（「これ入ってる」「自分の1位は別」）\n"
        "最後: 「あなたは何位派？」でコメント誘導\n"
        "想定尺: 45〜50秒。本数は5〜7個。"
    )


def _hook(theme: str) -> str:
    table = {
        "神ゲー": "これ、今やっても神",
        "クソゲー": "買った自分を殴りたい",
        "隠れた名作": "知らないのは損",
        "鬱": "子供には早すぎた",
        "トラウマ": "夜、急に思い出す",
        "衝撃展開": "最後で全部変わる",
        "伏線": "一周目は気づけない",
        "神BGM": "音だけで泣ける",
        "懐かしい": "あの頃に戻りたい",
        "知らないと損": "始める前に知りたい",
        "高難易度": "理不尽なのに好き",
        "エンディング": "クリア後に意味が変わる",
    }
    for key, line in table.items():
        if key in theme:
            return line
    return "これは語りたくなる"


def _count_in_title(title: str) -> int:
    for number in ("7", "5", "3"):
        if f"{number}選" in title:
            return int(number)
    return 7


def _title_for(cluster: ClusterSummary, members: list[dict], banned: list[str], variant: int) -> str:
    subject = _subject(cluster)
    theme_word = _theme_word(cluster)
    candidates = _candidates(subject, theme_word, variant)
    for candidate in candidates:
        if not (config.TITLE_MIN_CHARS <= len(candidate) <= config.TITLE_MAX_CHARS):
            continue
        if any(similarity(candidate, other) >= 0.72 for other in banned if other):
            continue
        if any(_too_close(candidate, str(video.get("title") or "")) for video in members):
            continue
        return candidate
    # 長さだけ合わせて、参考タイトルとは別の文にする。
    for candidate in candidates:
        fitted = _fit_length(candidate)
        if any(similarity(fitted, other) >= 0.72 for other in banned if other):
            continue
        if config.TITLE_MIN_CHARS <= len(fitted) <= config.TITLE_MAX_CHARS:
            return fitted
    return ""


def _too_close(candidate: str, reference: str) -> bool:
    if not reference:
        return False
    if candidate.replace(" ", "") == reference.replace(" ", ""):
        return True
    return similarity(candidate, reference) >= 0.72


def _subject(cluster: ClusterSummary) -> str:
    series = (cluster.series or "").split("/")[0].strip()
    hardware = (cluster.hardware or "").split("/")[0].strip()
    if series in {"ファイナルファンタジー"}:
        series = "FF"
    if series in {"ポケットモンスター"}:
        series = "ポケモン"
    if series in {"ゼルダの伝説"}:
        series = "ゼルダ"
    if series and hardware and series not in hardware:
        if len(series) <= 8:
            return series
    return hardware or series or "ゲーム"


def _theme_word(cluster: ClusterSummary) -> str:
    theme = cluster.theme or ""
    if theme in {"その他", ""}:
        for key in ("神ゲー", "クソゲー", "鬱", "トラウマ", "伏線", "神BGM", "隠れた名作"):
            if key in cluster.label:
                return key
        return "神ゲー"
    if theme == "神BGM":
        return "神BGM"
    return theme


def _candidates(subject: str, theme: str, variant: int) -> list[str]:
    """参考動画の文は使わない。20〜35文字に入るものだけ返す。"""
    number = (7, 5, 3, 7)[variant % 4]
    raw = [
        f"今遊んでも評価が落ちない{subject}の{theme}{number}選",
        f"コメント欄が割れそうな{subject}の{theme}{number}選",
        f"大人になって順位が変わる{subject}の{theme}{number}選",
        f"今夜だれかに話したくなる{subject}の{theme}{number}選",
    ]
    themed = {
        "鬱": [
            f"エンディングのあと部屋が静かになる{subject}鬱ゲー{number}選",
            f"子供のころは笑えていたのに鬱な{subject}{number}選",
            f"クリアした夜に余韻だけが残る鬱な{subject}{number}選",
        ],
        "トラウマ": [
            f"音を聞いただけで手が止まる恐怖{subject}{number}選",
            f"今でも夜にタイトルが浮かぶ{subject}{number}選",
            f"子供のころ再生ボタンを止めた{subject}{number}選",
        ],
        "伏線": [
            f"二周目になってから鳥肌が立つ{subject}の伏線{number}選",
            f"冒頭の1時間で張られていた{subject}伏線{number}選",
            f"回収した瞬間に意味が反転する{subject}伏線{number}選",
        ],
        "衝撃展開": [
            f"終盤でいきなり景色が反転する{subject}の展開{number}選",
            f"ネタバレなしでは語れない{subject}の衝撃{number}選",
            f"クリア後に話したくなる{subject}の展開{number}選",
        ],
        "神BGM": [
            f"戦闘前に音量を上げたくなる{subject}の神曲{number}選",
            f"曲名を今も口ずさんでいる{subject}神BGM{number}選",
            f"音を聴いただけでその場に戻る{subject}{number}選",
        ],
        "隠れた名作": [
            f"売上の数字だけでは語られない{subject}の隠れた名作{number}選",
            f"友達がだれも持っていなかった{subject}名作{number}選",
            f"今から触ってもまったく遅くない{subject}名作{number}選",
        ],
        "クソゲー": [
            f"期待して買って黙り込んだ{subject}クソゲー{number}選",
            f"怒りながら最後まで見た{subject}のクソゲー{number}選",
            f"面白さの方向がすっかりズレた{subject}{number}選",
        ],
        "懐かしい": [
            f"名前を出しただけで顔が緩んでしまう{subject}{number}選",
            f"授業中にふと思い出していた{subject}{number}選",
            f"起動音を聞いただけで景色が戻る{subject}{number}選",
        ],
        "神ゲー": [
            f"今遊んでも評価が落ちない{subject}の神ゲー{number}選",
            f"一晩で時間を溶かしたままの{subject}神ゲー{number}選",
            f"友達に黙って貸したくなる{subject}の神ゲー{number}選",
        ],
    }
    if subject == "ゲーム" and theme == "神ゲー":
        themed["神ゲー"] = [
            "一晩で時間を溶かしてしまう神ゲーだけ7選",
            "今遊んでも評価が落ちない神ゲーだけ7選",
            "友達に黙って貸したくなる神ゲー7選",
        ]
    raw = themed.get(theme, []) + raw
    shift = variant % len(raw)
    ordered = raw[shift:] + raw[:shift]
    polished: list[str] = []
    for title in ordered:
        polished.extend(_polish(title))
    return polished


def _fix_glue(title: str) -> str:
    """『PS27選』『FF7選』のように、機種名と本数がくっつくのを防ぐ。"""
    return re.sub(r"([A-Za-z0-9])(\d選)", r"\1の\2", title)


def _avoid_double(title: str) -> str:
    for source, target in (
        ("ゲーム鬱ゲー", "鬱ゲー"),
        ("ゲーム神ゲー", "神ゲー"),
        ("ゲームクソゲー", "クソゲー"),
    ):
        replaced = title.replace(source, target)
        if config.TITLE_MIN_CHARS <= len(replaced) <= config.TITLE_MAX_CHARS:
            title = replaced
    return title


def _polish(title: str) -> list[str]:
    """短い案は末尾を足す。文頭を同じ言葉で揃えない。"""
    title = _avoid_double(_fix_glue(title.strip()))
    options = [title]
    if len(title) < config.TITLE_MIN_CHARS and title.endswith("選"):
        options.append(_fix_glue(title[:-1] + "本だけ"))
        options.append(_fix_glue(title + "、今出す"))
    elif len(title) < config.TITLE_MIN_CHARS:
        options.append(title + "を今出す")
    unique: list[str] = []
    for option in options:
        if config.TITLE_MIN_CHARS <= len(option) <= config.TITLE_MAX_CHARS and option not in unique:
            unique.append(option)
    return unique


def _fit_length(title: str) -> str:
    title = title.strip()
    if len(title) > config.TITLE_MAX_CHARS:
        title = title[: config.TITLE_MAX_CHARS]
    if len(title) < config.TITLE_MIN_CHARS:
        prefix = "今さら語りたい"
        title = prefix + title
    if len(title) > config.TITLE_MAX_CHARS:
        title = title[: config.TITLE_MAX_CHARS]
    return title
