"""毎日のMarkdownレポート。"""

from __future__ import annotations

from datetime import datetime

import config
from src.idea_generator import Idea
from src.utils import format_float, format_int, today_stamp


def render_report(
    now: datetime,
    raw_rows: list[dict],
    ranked_rows: list[dict],
    clusters: list,
    ideas: list[Idea],
    stats: dict,
) -> str:
    analyzed = [row for row in raw_rows if row.get("is_shorts") and not row.get("excluded")]
    excluded = [row for row in raw_rows if row.get("excluded") or not row.get("is_shorts")]
    lines: list[str] = []
    demo = "【デモデータ】" if stats.get("demo") else ""
    lines.append(f"# 今日のゲームShortsトレンド{demo}")
    lines.append("")
    lines.append(f"- 調査日: {today_stamp(now)}（日本時間）")
    lines.append("- 対象: 日本語のゲーム系Shorts。過去24時間・過去3日・過去7日を比べています。")
    lines.append(f"- 取得できた動画数: {stats.get('fetched', len(raw_rows))}")
    lines.append(f"- 除外された動画数: {len(excluded)}")
    lines.append(f"- 分析対象数: {len(analyzed)}")
    lines.append(f"- API使用量の概算: {stats.get('quota_text', '0ユニット（API未使用）')}")
    if stats.get("own_csv"):
        lines.append(f"- 自チャンネルCSV: {stats['own_csv']}（読めた動画 {stats.get('own_videos', 0)}本）")
    else:
        lines.append("- 自チャンネルCSV: 見つかりません。相性スコアは中立です。")
    if stats.get("competitor_csv"):
        lines.append(f"- 競合CSV: {stats['competitor_csv']}（読めた動画 {stats.get('competitor_videos', 0)}本）")
    else:
        lines.append("- 競合CSV: 見つかりません。競合実績は中立です。")
    if stats.get("notice"):
        lines.append(f"- 注意: {stats['notice']}")
    lines.append("")
    lines.append("## 今伸びているテーマTOP10")
    lines.append("")
    if not clusters:
        lines.append("今日はテーマを作れる動画がありません。APIキー、ネット、検索キーワードを確認してください。")
        lines.append("")
    for index, cluster in enumerate(clusters[: config.THEME_TOP_N], start=1):
        lines.append(f"### {index}. {cluster.label}")
        lines.append("")
        lines.append(f"- テーマ名: {cluster.label}")
        lines.append("- 根拠となる動画:")
        members = _members(cluster, analyzed)
        if not members:
            lines.append("  - （動画データを表示できません）")
        for video in members[:3]:
            views = format_int(video.get("views"))
            speed = format_float(video.get("views_per_hour"), 0)
            channel = video.get("channel_name") or "チャンネル名不明"
            url = video.get("video_url") or ""
            title = video.get("title") or ""
            lines.append(f"  - [{title}]({url}) / {channel} / 再生 {views} / 速度 {speed}回/時")
        lines.append(f"- チャンネル数: {cluster.channel_count}")
        lines.append(f"- 平均再生速度: {format_float(cluster.avg_views_per_hour, 0)}回/時")
        if cluster.median_views_per_subscriber is None:
            lines.append("- 登録者比: 登録者数が非公開の動画だけです")
        else:
            lines.append(f"- 登録者比: 中央値 {cluster.median_views_per_subscriber:.2f}倍（再生÷登録者）")
        p24 = cluster.periods.get("24h") or {}
        p3 = cluster.periods.get("3d") or {}
        p7 = cluster.periods.get("7d") or {}
        lines.append(
            "- 期間比較: "
            f"24時間 {p24.get('count', 0)}本（平均 {format_float(p24.get('avg_views_per_hour'), 0)}回/時） / "
            f"3日 {p3.get('count', 0)}本（平均 {format_float(p3.get('avg_views_per_hour'), 0)}回/時） / "
            f"7日 {p7.get('count', 0)}本（平均 {format_float(p7.get('avg_views_per_hour'), 0)}回/時）"
        )
        lines.append(f"- なぜ伸びていると判断したか: {cluster.why}")
        lines.append("")

    lines.append("## 今作るべき動画企画TOP10")
    lines.append("")
    lines.append("クロのゲーム情報局向けです。0〜1秒でフック、すぐランキング、1本につき反応を2つ、45〜50秒に収まる企画を優先しています。")
    lines.append("参考動画のタイトルは真似せず、テーマだけを借りて別の言い方にしています。")
    lines.append("")
    if not ideas:
        lines.append("企画を作れるテーマがありません。")
        lines.append("")
    for idea in ideas:
        lines.extend(_idea_block(idea))

    lines.append("## 自チャンネルで相性が良かったテーマ")
    lines.append("")
    tokens = stats.get("own_top_tokens") or []
    if not tokens:
        lines.append("過去動画が無いため、まだ算出していません。")
    else:
        for token in tokens:
            lines.append(f"- {token['token']}: 相対スコア {token['score']}")
    lines.append("")
    lines.append("## 競合の過去動画で強かったテーマ")
    lines.append("")
    comp_tokens = stats.get("competitor_top_tokens") or []
    if not comp_tokens:
        lines.append("競合の過去動画が無いため、まだ算出していません。")
    else:
        for token in comp_tokens:
            lines.append(f"- {token['token']}: 相対スコア {token['score']}")
    lines.append("")
    lines.append("## スコアの見方")
    lines.append("")
    lines.append("- Trend Score: 再生速度、登録者比、コメント率、いいね率、新しさ。0〜100。")
    lines.append("- Channel Fit: 自チャンネルの過去動画で、相対的に再生が良かったテーマとの近さ。")
    lines.append("- Opportunity Score: Trend、Channel Fit、競合の過去実績、複数チャンネルで同時発生、の合計。")
    lines.append("- 公開から3時間未満の再生速度は、分母を3時間にして跳ねすぎを抑えています。")
    lines.append("- 登録者が多いだけで登録者比が低い動画は、再生速度の効きを弱めています。")
    lines.append("")
    if excluded:
        lines.append("## 除外・見送り")
        lines.append("")
        for video in excluded[:12]:
            reason = video.get("exclude_reason") or ("Shortsではない" if not video.get("is_shorts") else "優先度を下げた")
            lines.append(f"- {video.get('title') or '（無題）'}: {reason}")
        if len(excluded) > 12:
            lines.append(f"- ほか {len(excluded) - 12}件はCSVの excluded 列を見てください。")
        lines.append("")
    lines.append("順位の全体は `data/daily/` の trend_ranked を見てください。")
    lines.append("")
    return "\n".join(lines)


def _members(cluster, analyzed: list[dict]) -> list[dict]:
    wanted = set(cluster.video_ids)
    rows = [video for video in analyzed if video.get("video_id") in wanted]
    rows.sort(key=lambda video: video.get("opportunity_score") or 0, reverse=True)
    return rows


def _idea_block(idea: Idea) -> list[str]:
    refs = []
    for ref in idea.references:
        refs.append(f"{ref['title']}（{ref['channel_name']} / {ref['url']}）")
    reference_text = " / ".join(refs) if refs else "—"
    return [
        f"### {idea.rank}位",
        "",
        f"企画：{idea.plan}",
        "",
        f"タイトル案：{idea.title}",
        "",
        f"テーマ：{idea.theme}",
        "",
        f"参考動画：{reference_text}",
        "",
        f"伸びている根拠：{idea.evidence}",
        "",
        f"自チャンネルとの相性：{idea.fit_text}",
        "",
        f"狙う視聴者：{idea.audience}",
        "",
        "おすすめ構成：",
        "",
        idea.structure,
        "",
        f"優先度：{idea.priority}",
        "",
    ]


def save_report(path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
