"""タイトルをルールで分類し、ハード・年代・シリーズを抜く。"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

from src.game_dictionary import ordered_games, ordered_series

CATEGORY_ORDER = [
    "ランキング",
    "TOP3",
    "TOP5",
    "神ゲー",
    "クソゲー",
    "隠れた名作",
    "懐かしい",
    "鬱",
    "トラウマ",
    "衝撃展開",
    "伏線",
    "神BGM",
    "知らないと損",
    "あるある",
    "比較",
    "おすすめ",
    "炎上",
    "バグ",
    "小ネタ",
    "雑学",
    "ストーリー",
    "キャラクター",
    "裏技",
    "高難易度",
    "エンディング",
    "その他",
]

FORMAT_CATEGORIES = {"ランキング", "TOP3", "TOP5", "おすすめ", "比較"}

HARDWARE_RULES: list[tuple[str, str]] = [
    ("PS Vita", r"(ps\s?vita|ヴィータ|psvita)"),
    ("PSP", r"(?<![a-z])psp(?![a-z])"),
    ("PS1", r"(ps\s?1|psone|プレステ1|初代プレステ|プレイステーション1)"),
    ("PS2", r"(ps\s?2|プレステ2|プレイステーション2)"),
    ("PS3", r"(ps\s?3|プレステ3|プレイステーション3)"),
    ("PS4", r"(ps\s?4|プレステ4|プレイステーション4)"),
    ("PS5", r"(ps\s?5|プレステ5|プレイステーション5)"),
    ("Wii U", r"wii\s?u"),
    ("Wii", r"(?<![a-z])wii(?![a-z])|ウィー"),
    ("3DS", r"3ds|スリーディーエス"),
    ("DS", r"(ニンテンドー?ds|(?<![a-z0-9])ds(?![a-z0-9]))"),
    ("Switch", r"(switch|スイッチ)"),
    ("スーパーファミコン", r"(スーパーファミコン|スーファミ|(?<![a-z])sfc(?![a-z]))"),
    ("ファミコン", r"(ファミコン|famicom)"),
    ("N64", r"(n64|ニンテンドー?64|ロクヨン|(?<![0-9])64(?![0-9時間分秒選本])(?:で|の|版|時代|ソフト)?)"),
    ("ゲームキューブ", r"(ゲームキューブ|(?<![a-z])gc(?![a-z]))"),
    ("ゲームボーイ", r"(ゲームボーイ|(?<![a-z])gba(?![a-z]))"),
    ("メガドライブ", r"メガドライブ"),
    ("ドリームキャスト", r"ドリームキャスト"),
    ("セガサターン", r"(セガサターン|サターン)"),
    ("Xbox", r"(xbox|エックスボックス)"),
]

HARDWARE_ERA = {
    "ファミコン": "1980年代",
    "スーパーファミコン": "1990年代",
    "ゲームボーイ": "1990年代",
    "メガドライブ": "1990年代",
    "セガサターン": "1990年代",
    "PS1": "1990年代",
    "N64": "1990年代",
    "ドリームキャスト": "1990年代",
    "PS2": "2000年代",
    "ゲームキューブ": "2000年代",
    "PSP": "2000年代",
    "DS": "2000年代",
    "Wii": "2000年代",
    "PS3": "2000年代",
    "Xbox": "2000年代",
    "3DS": "2010年代",
    "PS Vita": "2010年代",
    "Wii U": "2010年代",
    "PS4": "2010年代",
    "Switch": "2010年代以降",
    "PS5": "2020年代",
}

_DIGIT_TRANS = str.maketrans("０１２３４５６７８９", "0123456789")
_GAMES = ordered_games()
_SERIES = ordered_series()


@dataclass
class TitleAnalysis:
    categories: list[str] = field(default_factory=list)
    game_titles: list[str] = field(default_factory=list)
    hardware: list[str] = field(default_factory=list)
    series: list[str] = field(default_factory=list)
    eras: list[str] = field(default_factory=list)

    @property
    def category_label(self) -> str:
        return " / ".join(self.categories) if self.categories else "その他"

    @property
    def game_label(self) -> str:
        return " / ".join(self.game_titles)

    @property
    def hardware_label(self) -> str:
        return " / ".join(self.hardware)

    @property
    def series_label(self) -> str:
        return " / ".join(self.series)

    @property
    def era_label(self) -> str:
        return " / ".join(self.eras)

    def theme_categories(self) -> list[str]:
        return [c for c in self.categories if c not in FORMAT_CATEGORIES and c != "その他"]

    def tokens(self) -> set[str]:
        tokens: set[str] = set()
        for hw in self.hardware:
            tokens.add(f"hw:{hw}")
        for series in self.series:
            tokens.add(f"sr:{series}")
        for cat in self.theme_categories():
            tokens.add(f"th:{cat}")
        if any(cat in {"ランキング", "TOP3", "TOP5"} for cat in self.categories):
            tokens.add("fmt:ランキング")
        for game in self.game_titles:
            tokens.add(f"gm:{game}")
        return tokens


def _normalize(text: str) -> str:
    folded = unicodedata.normalize("NFKC", text or "").lower().translate(_DIGIT_TRANS)
    return folded


def _add_unique(bucket: list[str], value: str) -> None:
    if value and value not in bucket:
        bucket.append(value)


def _categories(text: str) -> list[str]:
    found: list[str] = []

    def has(pattern: str) -> bool:
        return re.search(pattern, text) is not None

    if has(r"(ランキング|top\s?\d+|ベスト|\d+選)"):
        found.append("ランキング")
    if has(r"(top\s?3|(?<!\d)3選)"):
        found.append("TOP3")
    if has(r"(top\s?5|(?<!\d)5選)"):
        found.append("TOP5")
    if has(r"(隠れた名作|隠れた神|埋もれた名作|埋もれた傑作|知られざる名作|誰も知らない名作)"):
        found.append("隠れた名作")
    if has(r"(神ゲー|神ゲ|最高傑作)"):
        found.append("神ゲー")
    elif has(r"名作") and "隠れた名作" not in found:
        found.append("神ゲー")
    if has(r"(クソゲー|ゴミゲー|駄作)"):
        found.append("クソゲー")
    if has(r"(懐かしい|あの頃|当時の)"):
        found.append("懐かしい")
    if has(r"(鬱|うつゲー|後味が悪|後味が重|しんどい)"):
        found.append("鬱")
    if has(r"(トラウマ|怖すぎ|夜眠れ|ホラー)"):
        found.append("トラウマ")
    if has(r"(衝撃展開|どんでん返し|まさかの展開|衝撃の展開|衝撃)"):
        found.append("衝撃展開")
    if has(r"(伏線|フラグ回収|回収がすごい)"):
        found.append("伏線")
    if has(r"(神bgm|bgm|サントラ|神曲|音楽が良)"):
        found.append("神BGM")
    if has(r"(知らないと損|知るべき|やっちゃダメ|やる前に)"):
        found.append("知らないと損")
    if has(r"あるある"):
        found.append("あるある")
    if has(r"(比較|どっち|対して| vs )"):
        found.append("比較")
    if has(r"(おすすめ|オススメ|推したい|やるべき)"):
        found.append("おすすめ")
    if has(r"(炎上|賛否|物議)"):
        found.append("炎上")
    if has(r"(バグ|グリッチ|裏仕様)"):
        found.append("バグ")
    if has(r"(小ネタ|豆知識)"):
        found.append("小ネタ")
    if has(r"雑学"):
        found.append("雑学")
    if has(r"(ストーリー|物語|シナリオ)"):
        found.append("ストーリー")
    if has(r"(キャラ|登場人物)"):
        found.append("キャラクター")
    if has(r"(裏技|小技|テクニック)"):
        found.append("裏技")
    if has(r"(高難易度|死にゲー|鬼畜|難しすぎ)"):
        found.append("高難易度")
    if has(r"(エンディング|ラスト|クリア後|結末|エンデ)"):
        found.append("エンディング")

    if not found:
        found.append("その他")
    order = {name: index for index, name in enumerate(CATEGORY_ORDER)}
    return sorted(set(found), key=lambda name: order.get(name, 99))


def _hardware(text: str) -> list[str]:
    found: list[str] = []
    for name, pattern in HARDWARE_RULES:
        if re.search(pattern, text):
            _add_unique(found, name)
    if "3DS" in found and "DS" in found:
        found = [name for name in found if name != "DS"]
    if "Wii U" in found and "Wii" in found:
        found = [name for name in found if name != "Wii"]
    if "スーパーファミコン" in found and "ファミコン" in found:
        # 「スーパーファミコン」はファミコンも含む文字列なので、スーファミだけ残す。
        # ただし「ファミコンからスーファミ」のように両方ある場合は残す。
        if "ファミコンから" not in text and "ファミコンと" not in text and "fc" not in text:
            bare = re.sub(r"スーパーファミコン|スーファミ", "", text)
            if not re.search(r"ファミコン|famicom", bare):
                found = [name for name in found if name != "ファミコン"]
    return found


def _era(text: str, hardware: list[str]) -> list[str]:
    eras: list[str] = []
    for hw in hardware:
        era = HARDWARE_ERA.get(hw)
        if era:
            _add_unique(eras, era)
    for match in re.findall(r"(19[7-9]\d|20[0-2]\d)", text):
        year = int(match)
        if year < 1990:
            _add_unique(eras, "1980年代")
        elif year < 2000:
            _add_unique(eras, "1990年代")
        elif year < 2010:
            _add_unique(eras, "2000年代")
        elif year < 2020:
            _add_unique(eras, "2010年代")
        else:
            _add_unique(eras, "2020年代")
    if re.search(r"90年代", text):
        _add_unique(eras, "1990年代")
    if re.search(r"00年代|2000年代", text):
        _add_unique(eras, "2000年代")
    return eras


def _games_and_series(text: str) -> tuple[list[str], list[str]]:
    games: list[str] = []
    series: list[str] = []
    for alias, name, series_name in _GAMES:
        if alias and alias in text:
            _add_unique(games, name)
            if series_name:
                _add_unique(series, series_name)
            if len(games) >= 3:
                break
    for alias, name in _SERIES:
        if len(alias) < 2:
            continue
        if alias in text:
            _add_unique(series, name)
    # FFは「off」などに当たらないよう、英字の境界で見る。
    if re.search(r"(?<![a-z])ff\s?\d{0,2}(?![a-z])", text):
        _add_unique(series, "ファイナルファンタジー")
    quoted = re.findall(r"[「『](.{2,18}?)[」』]", text)
    for piece in quoted:
        if piece not in games and not any(word in piece for word in ("神ゲー", "ランキング", "選")):
            _add_unique(games, piece)
    return games[:3], series[:3]


def analyze_title(title: str, description: str = "") -> TitleAnalysis:
    text = _normalize(f"{title or ''} {description or ''}")
    hardware = _hardware(text)
    games, series = _games_and_series(text)
    return TitleAnalysis(
        categories=_categories(text),
        game_titles=games,
        hardware=hardware,
        series=series,
        eras=_era(text, hardware),
    )


def apply_title_fields(video: dict) -> dict:
    analysis = analyze_title(str(video.get("title") or ""), str(video.get("description") or ""))
    video["category"] = analysis.category_label
    video["categories"] = analysis.categories
    video["game_title"] = analysis.game_label
    video["hardware"] = analysis.hardware_label
    video["series"] = analysis.series_label
    video["era"] = analysis.era_label
    video["theme_tokens"] = sorted(analysis.tokens())
    video["_analysis"] = analysis
    return video
