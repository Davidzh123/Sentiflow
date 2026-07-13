"""
Génération des PDF SentiFlow.

Le module conserve fpdf2 pour rester léger, mais produit de vrais rapports :
- identité visuelle cohérente ;
- couverture et métadonnées ;
- cartes KPI ;
- graphiques vectoriels ;
- tableaux comparatifs ;
- tweets lisibles ;
- pagination et pied de page ;
- police Unicode lorsque DejaVu Sans est disponible.
"""
from __future__ import annotations

import logging
import math
import os
import re
import unicodedata
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

logger = logging.getLogger("sentiflow.pdf")

try:
    from fpdf import FPDF

    FPDF_AVAILABLE = True
except ImportError:
    FPDF_AVAILABLE = False


# ---------------------------------------------------------------------------
# Design tokens
# ---------------------------------------------------------------------------
BRAND = (82, 113, 255)          # #5271ff
BRAND_DARK = (51, 74, 188)
INK = (15, 23, 42)              # slate-900
TEXT = (51, 65, 85)             # slate-700
MUTED = (100, 116, 139)         # slate-500
BORDER = (226, 232, 240)        # slate-200
SURFACE = (248, 250, 252)       # slate-50
BRAND_SURFACE = (241, 244, 255)
WHITE = (255, 255, 255)
SUCCESS = (34, 197, 94)
DANGER = (239, 68, 68)
WARNING = (245, 158, 11)

_SENTIMENT_RGB: Dict[str, Tuple[int, int, int]] = {
    "joie": (34, 197, 94),
    "amour": (236, 72, 153),
    "colere": (239, 68, 68),
    "tristesse": (59, 130, 246),
    "peur": (168, 85, 247),
    "surprise": (245, 158, 11),
    "neutre": (148, 163, 184),
    "incertain": (148, 163, 184),
    "inconnu": (148, 163, 184),
}
_SENTIMENT_LABEL = {
    "joie": "Joie",
    "amour": "Amour",
    "colere": "Colère",
    "tristesse": "Tristesse",
    "peur": "Peur",
    "surprise": "Surprise",
    "neutre": "Neutre",
    "incertain": "Incertain",
    "inconnu": "Non classé",
}
_TARGET_LINE_COLORS = [
    BRAND,
    (236, 72, 153),
    (34, 197, 94),
    (245, 158, 11),
    (168, 85, 247),
    (14, 165, 233),
]

_FONT_CANDIDATES = {
    "regular": [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    ],
    "bold": [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
    ],
    "italic": [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Italic.ttf",
    ],
}


def _first_existing(paths: Iterable[str]) -> Optional[str]:
    for path in paths:
        if os.path.exists(path):
            return path
    return None


def _safe_text(value: Any) -> str:
    """Fallback propre lorsque seules les polices PDF de base sont disponibles."""
    text = "" if value is None else str(value)
    replacements = {
        "’": "'",
        "‘": "'",
        "“": '"',
        "”": '"',
        "–": "-",
        "—": "-",
        "…": "...",
        "•": "-",
        "€": "EUR",
        "→": "->",
        "←": "<-",
        "✅": "OK",
        "❌": "X",
    }
    for source, target in replacements.items():
        text = text.replace(source, target)
    # Conserver autant que possible les accents latin-1, supprimer les emojis restants.
    return text.encode("latin-1", "replace").decode("latin-1")


def _clean_markdown(value: Any) -> str:
    text = "" if value is None else str(value)
    text = re.sub(r"```(?:\w+)?", "", text)
    text = text.replace("```", "")
    text = re.sub(r"\[(.*?)\]\((.*?)\)", r"\1", text)
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    text = re.sub(r"__(.*?)__", r"\1", text)
    text = re.sub(r"(?m)^#{1,6}\s*", "", text)
    text = re.sub(r"(?m)^\s*[-*+]\s+", "• ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _normalize_sentiment(value: Any) -> str:
    text = str(value or "inconnu").strip().lower()
    text = unicodedata.normalize("NFD", text)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    return text if text in _SENTIMENT_RGB else "inconnu"


def _pct(value: float) -> str:
    return f"{round(float(value or 0) * 100)} %"


def _format_number(value: Any) -> str:
    try:
        return f"{int(value):,}".replace(",", " ")
    except (TypeError, ValueError):
        return "0"


def _parse_datetime(value: Any) -> Optional[datetime]:
    if isinstance(value, datetime):
        return value
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None


def _format_datetime(value: Any, include_time: bool = True) -> str:
    dt = _parse_datetime(value)
    if not dt:
        return "Non renseigné"
    return dt.strftime("%d/%m/%Y à %H:%M" if include_time else "%d/%m/%Y")


def _format_period(start: Any, end: Any) -> str:
    start_dt = _parse_datetime(start)
    end_dt = _parse_datetime(end)
    if start_dt and end_dt:
        if start_dt.date() == end_dt.date():
            return f"{start_dt.strftime('%d/%m/%Y')}"
        return f"Du {start_dt.strftime('%d/%m/%Y')} au {end_dt.strftime('%d/%m/%Y')}"
    return "Période disponible en base"


def _net_label(score: float) -> str:
    score = float(score or 0)
    if score >= 0.4:
        return "Très positive"
    if score >= 0.1:
        return "Plutôt positive"
    if score > -0.1:
        return "Partagée"
    if score > -0.4:
        return "Plutôt négative"
    return "Très négative"


def _score_display(score: float) -> str:
    score = float(score or 0)
    return f"{score:+.2f}"


def _score_color(score: float) -> Tuple[int, int, int]:
    score = float(score or 0)
    if score > 0.08:
        return SUCCESS
    if score < -0.08:
        return DANGER
    return MUTED


class SentiFlowPDF(FPDF):
    """FPDF enrichi de composants de mise en page réutilisables."""

    def __init__(self, report_title: str = "Rapport d'analyse") -> None:
        super().__init__(orientation="P", unit="mm", format="A4")
        self.report_title = report_title
        self.set_margins(14, 15, 14)
        self.set_auto_page_break(auto=True, margin=16)
        self.alias_nb_pages()
        self.font_family = "Helvetica"
        self.unicode_enabled = False
        self._register_fonts()
        self.set_title(report_title)
        self.set_author("SentiFlow")
        self.set_creator("SentiFlow")
        self.set_subject("Rapport d'analyse de sentiments")

    def _register_fonts(self) -> None:
        regular = _first_existing(_FONT_CANDIDATES["regular"])
        bold = _first_existing(_FONT_CANDIDATES["bold"])
        italic = _first_existing(_FONT_CANDIDATES["italic"])
        if not (regular and bold):
            return
        try:
            self.add_font("SentiFlow", "", regular)
            self.add_font("SentiFlow", "B", bold)
            if italic:
                self.add_font("SentiFlow", "I", italic)
            self.font_family = "SentiFlow"
            self.unicode_enabled = True
        except Exception as exc:  # pragma: no cover - dépend de l'environnement système
            logger.info("[PDF] Police Unicode indisponible: %s", exc)

    def text_value(self, value: Any) -> str:
        text = "" if value is None else str(value)
        return text if self.unicode_enabled else _safe_text(text)

    def header(self) -> None:
        if self.page_no() <= 1:
            return
        self.set_fill_color(*WHITE)
        self.set_draw_color(*BORDER)
        self.set_line_width(0.25)
        self.line(14, 12, 196, 12)
        self.set_xy(14, 5.4)
        self.set_font(self.font_family, "B", 9)
        self.set_text_color(*BRAND)
        self.cell(30, 5, "SentiFlow")
        self.set_font(self.font_family, "", 8)
        self.set_text_color(*MUTED)
        self.set_xy(45, 5.4)
        self.cell(151, 5, self.text_value(self.report_title[:80]), align="R")
        self.set_y(16)

    def footer(self) -> None:
        self.set_y(-11)
        self.set_draw_color(*BORDER)
        self.line(14, self.get_y(), 196, self.get_y())
        self.set_y(-9)
        self.set_font(self.font_family, "", 7.5)
        self.set_text_color(*MUTED)
        self.cell(90, 5, self.text_value("SentiFlow - Rapport généré automatiquement"))
        self.cell(92, 5, self.text_value(f"Page {self.page_no()}/{{nb}}"), align="R")

    def ensure_space(self, required_height: float) -> None:
        if self.get_y() + required_height > self.h - 18:
            self.add_page()

    def brand_mark(self, x: float, y: float, scale: float = 1.0) -> None:
        self.set_fill_color(*BRAND)
        self.ellipse(x, y, 7 * scale, 7 * scale, style="F")
        self.set_fill_color(*WHITE)
        self.ellipse(x + 1.8 * scale, y + 1.8 * scale, 1.2 * scale, 1.2 * scale, style="F")
        self.ellipse(x + 4.0 * scale, y + 1.8 * scale, 1.2 * scale, 1.2 * scale, style="F")
        self.ellipse(x + 2.9 * scale, y + 4.0 * scale, 1.2 * scale, 1.2 * scale, style="F")

    def hero(self, title: str, subtitle: str, metadata: Sequence[Tuple[str, str]]) -> None:
        self.add_page()
        self.set_fill_color(*BRAND)
        self.rect(0, 0, 210, 70, style="F")
        self.set_fill_color(*BRAND_DARK)
        self.ellipse(158, -32, 86, 86, style="F")
        self.set_fill_color(107, 133, 255)
        self.ellipse(178, 24, 55, 55, style="F")

        self.brand_mark(15, 13, 1.25)
        self.set_xy(26, 12)
        self.set_font(self.font_family, "B", 14)
        self.set_text_color(*WHITE)
        self.cell(90, 8, "SentiFlow")

        self.set_xy(15, 28)
        self.set_font(self.font_family, "B", 21)
        self.multi_cell(155, 10, self.text_value(title[:120]))
        self.set_x(15)
        self.set_font(self.font_family, "", 10)
        self.set_text_color(230, 235, 255)
        self.multi_cell(155, 5.5, self.text_value(subtitle[:180]))

        self.set_y(78)
        if metadata:
            card_gap = 3
            card_w = (182 - card_gap * (len(metadata) - 1)) / max(len(metadata), 1)
            x = 14
            for label, value in metadata:
                self.set_fill_color(*SURFACE)
                self.set_draw_color(*BORDER)
                self.rect(x, 78, card_w, 21, style="DF")
                self.set_xy(x + 3, 82)
                self.set_font(self.font_family, "B", 7.5)
                self.set_text_color(*MUTED)
                self.cell(card_w - 6, 4, self.text_value(label.upper()))
                self.set_xy(x + 3, 88)
                self.set_font(self.font_family, "B", 9.3)
                self.set_text_color(*INK)
                self.multi_cell(card_w - 6, 4.2, self.text_value(value[:55]))
                x += card_w + card_gap
        self.set_y(106)

    def section_title(self, title: str, subtitle: Optional[str] = None) -> None:
        self.ensure_space(16 if subtitle else 11)
        self.set_fill_color(*BRAND)
        self.rect(14, self.get_y() + 1, 2.2, 8, style="F")
        self.set_x(19)
        self.set_font(self.font_family, "B", 12.5)
        self.set_text_color(*INK)
        self.cell(0, 6, self.text_value(title), ln=True)
        if subtitle:
            self.set_x(19)
            self.set_font(self.font_family, "", 8.5)
            self.set_text_color(*MUTED)
            self.multi_cell(175, 4.3, self.text_value(subtitle))
        self.ln(2)

    def callout(self, text: str, accent: Tuple[int, int, int] = BRAND) -> None:
        text = self.text_value(_clean_markdown(text))
        lines = self._wrapped_lines(text, 168, 9)
        height = max(18, 9 + 4.5 * len(lines))
        self.ensure_space(height + 3)
        y = self.get_y()
        self.set_fill_color(*BRAND_SURFACE)
        self.set_draw_color(*BORDER)
        self.rect(14, y, 182, height, style="DF")
        self.set_fill_color(*accent)
        self.rect(14, y, 3, height, style="F")
        self.set_xy(21, y + 5)
        self.set_font(self.font_family, "", 9.2)
        self.set_text_color(*TEXT)
        self.multi_cell(168, 4.6, text)
        self.set_y(y + height + 4)

    def metric_cards(self, cards: Sequence[Tuple[str, str, Optional[str], Tuple[int, int, int]]]) -> None:
        if not cards:
            return
        self.ensure_space(27)
        gap = 3
        count = min(len(cards), 4)
        card_w = (182 - gap * (count - 1)) / count
        y = self.get_y()
        x = 14
        for label, value, hint, color in cards[:4]:
            self.set_fill_color(*WHITE)
            self.set_draw_color(*BORDER)
            self.rect(x, y, card_w, 24, style="DF")
            self.set_fill_color(*color)
            self.rect(x, y, card_w, 2.2, style="F")
            self.set_xy(x + 3.5, y + 5)
            self.set_font(self.font_family, "B", 15)
            self.set_text_color(*INK)
            self.cell(card_w - 7, 7, self.text_value(value))
            self.set_xy(x + 3.5, y + 13)
            self.set_font(self.font_family, "B", 7.2)
            self.set_text_color(*MUTED)
            self.cell(card_w - 7, 4, self.text_value(label.upper()))
            if hint:
                self.set_xy(x + 3.5, y + 17.5)
                self.set_font(self.font_family, "", 6.8)
                self.set_text_color(*color)
                self.cell(card_w - 7, 3.5, self.text_value(hint[:35]))
            x += card_w + gap
        self.set_y(y + 29)

    def stacked_bar(self, distribution: Dict[str, float], width: float = 182) -> None:
        items = [
            (_normalize_sentiment(sentiment), float(ratio or 0))
            for sentiment, ratio in distribution.items()
            if float(ratio or 0) > 0
        ]
        items.sort(key=lambda item: item[1], reverse=True)
        if not items:
            self.callout("Aucune distribution de sentiment n'est disponible.", MUTED)
            return
        total = sum(value for _, value in items) or 1
        x = 14
        y = self.get_y()
        self.ensure_space(23)
        self.set_fill_color(*SURFACE)
        self.rect(x, y, width, 8, style="F")
        cursor = x
        for sentiment, value in items:
            segment_w = width * value / total
            self.set_fill_color(*_SENTIMENT_RGB[sentiment])
            self.rect(cursor, y, segment_w, 8, style="F")
            cursor += segment_w
        self.set_y(y + 11)
        legend_x = 14
        row_y = self.get_y()
        for sentiment, value in items:
            label = f"{_SENTIMENT_LABEL[sentiment]} {_pct(value / total)}"
            label_w = min(46, self.get_string_width(self.text_value(label)) + 9)
            if legend_x + label_w > 196:
                legend_x = 14
                row_y += 6
            self.set_fill_color(*_SENTIMENT_RGB[sentiment])
            self.ellipse(legend_x, row_y + 1.3, 2.3, 2.3, style="F")
            self.set_xy(legend_x + 4, row_y)
            self.set_font(self.font_family, "", 7.4)
            self.set_text_color(*TEXT)
            self.cell(label_w - 4, 5, self.text_value(label))
            legend_x += label_w
        self.set_y(row_y + 8)

    def target_comparison_table(self, targets: Sequence[Dict[str, Any]]) -> None:
        if not targets:
            return
        self.ensure_space(14 + 8 * min(len(targets), 5))
        x = 14
        widths = [48, 25, 36, 31, 42]
        headers = ["Cible", "Tweets", "Dominant", "Confiance", "Score net"]
        self.set_fill_color(*INK)
        self.set_text_color(*WHITE)
        self.set_font(self.font_family, "B", 7.8)
        for width, header in zip(widths, headers):
            self.cell(width, 7, self.text_value(header), border=0, fill=True, align="C")
        self.ln()
        for index, target in enumerate(targets):
            fill = SURFACE if index % 2 == 0 else WHITE
            self.set_fill_color(*fill)
            self.set_draw_color(*BORDER)
            name = str(target.get("name", "?"))
            total = _format_number(target.get("total", 0))
            dominant = _SENTIMENT_LABEL.get(
                _normalize_sentiment(target.get("dominant_sentiment")), "Non classé"
            )
            avg_conf = _pct(float(target.get("average_confidence", 0) or 0))
            score = float(target.get("net_sentiment_score", 0) or 0)
            values = [name[:26], total, dominant, avg_conf, f"{_score_display(score)} · {_net_label(score)}"]
            aligns = ["L", "C", "C", "C", "C"]
            self.set_x(x)
            self.set_font(self.font_family, "", 7.5)
            for col, (width, value, align) in enumerate(zip(widths, values, aligns)):
                if col == 4:
                    self.set_text_color(*_score_color(score))
                    self.set_font(self.font_family, "B", 7.3)
                else:
                    self.set_text_color(*TEXT)
                    self.set_font(self.font_family, "", 7.5)
                self.cell(width, 7.5, self.text_value(value), border="B", fill=True, align=align)
            self.ln()
        self.ln(3)

    def target_distribution(self, target: Dict[str, Any]) -> None:
        distribution = target.get("distribution", {}) or {}
        items = [
            (_normalize_sentiment(key), float(value or 0))
            for key, value in distribution.items()
            if float(value or 0) > 0
        ]
        items.sort(key=lambda item: item[1], reverse=True)
        if not items:
            return
        block_height = 12 + 6 * len(items)
        self.ensure_space(block_height)
        self.set_font(self.font_family, "B", 9.5)
        self.set_text_color(*INK)
        self.cell(0, 6, self.text_value(f"{target.get('name', '?')} · {_format_number(target.get('total', 0))} tweets"), ln=True)
        max_w = 112
        for sentiment, ratio in items:
            y = self.get_y()
            self.set_font(self.font_family, "", 7.6)
            self.set_text_color(*TEXT)
            self.set_x(17)
            self.cell(28, 5, self.text_value(_SENTIMENT_LABEL[sentiment]))
            self.set_fill_color(*SURFACE)
            self.rect(48, y + 1.1, max_w, 3.2, style="F")
            self.set_fill_color(*_SENTIMENT_RGB[sentiment])
            self.rect(48, y + 1.1, max(1.2, max_w * min(ratio, 1)), 3.2, style="F")
            self.set_xy(164, y)
            self.set_font(self.font_family, "B", 7.4)
            self.set_text_color(*_SENTIMENT_RGB[sentiment])
            self.cell(30, 5, _pct(ratio), align="R", ln=True)
        self.ln(2)

    def timeline_chart(self, targets: Sequence[Dict[str, Any]]) -> None:
        series = []
        all_dates = set()
        for target in targets:
            timeline = target.get("timeline", []) or []
            if len(timeline) < 2:
                continue
            by_date = {str(point.get("date")): float(point.get("net_sentiment_score", 0) or 0) for point in timeline}
            all_dates.update(by_date)
            series.append((str(target.get("name", "?")), by_date))
        dates = sorted(all_dates)
        if not series or len(dates) < 2:
            self.callout(
                "L'évolution temporelle nécessite des tweets analysés sur au moins deux dates distinctes.",
                MUTED,
            )
            return

        self.ensure_space(72)
        chart_x, chart_y, chart_w, chart_h = 25, self.get_y() + 4, 166, 48
        self.set_draw_color(*BORDER)
        self.set_line_width(0.25)
        for score in [-1, -0.5, 0, 0.5, 1]:
            y = chart_y + (1 - (score + 1) / 2) * chart_h
            self.line(chart_x, y, chart_x + chart_w, y)
            self.set_xy(14, y - 2)
            self.set_font(self.font_family, "", 6.5)
            self.set_text_color(*MUTED)
            self.cell(9, 4, f"{score:+.1f}", align="R")

        x_step = chart_w / max(len(dates) - 1, 1)
        for index, (name, by_date) in enumerate(series):
            color = _TARGET_LINE_COLORS[index % len(_TARGET_LINE_COLORS)]
            points = []
            for date_index, date in enumerate(dates):
                if date not in by_date:
                    continue
                score = max(-1, min(1, by_date[date]))
                x = chart_x + date_index * x_step
                y = chart_y + (1 - (score + 1) / 2) * chart_h
                points.append((x, y))
            self.set_draw_color(*color)
            self.set_fill_color(*color)
            self.set_line_width(0.65)
            for first, second in zip(points, points[1:]):
                self.line(first[0], first[1], second[0], second[1])
            for x, y in points:
                self.ellipse(x - 0.9, y - 0.9, 1.8, 1.8, style="F")

        label_indexes = sorted(set([0, len(dates) // 2, len(dates) - 1]))
        self.set_font(self.font_family, "", 6.5)
        self.set_text_color(*MUTED)
        for index in label_indexes:
            x = chart_x + index * x_step
            label = dates[index][5:] if len(dates[index]) >= 10 else dates[index]
            self.set_xy(x - 10, chart_y + chart_h + 2)
            self.cell(20, 4, self.text_value(label), align="C")

        legend_y = chart_y + chart_h + 9
        legend_x = 25
        for index, (name, _) in enumerate(series):
            color = _TARGET_LINE_COLORS[index % len(_TARGET_LINE_COLORS)]
            self.set_fill_color(*color)
            self.ellipse(legend_x, legend_y + 1.2, 2.4, 2.4, style="F")
            self.set_xy(legend_x + 4, legend_y)
            self.set_font(self.font_family, "", 7)
            self.set_text_color(*TEXT)
            width = min(52, self.get_string_width(self.text_value(name)) + 8)
            self.cell(width, 5, self.text_value(name[:25]))
            legend_x += width + 2
            if legend_x > 170:
                legend_x = 25
                legend_y += 5
        self.set_y(legend_y + 8)

    def keyword_cloud(self, targets: Sequence[Dict[str, Any]]) -> None:
        keywords: Dict[str, int] = {}
        for target in targets:
            for row in target.get("keywords", []) or []:
                term = str(row.get("term", "")).strip()
                if not term:
                    continue
                keywords[term] = keywords.get(term, 0) + int(row.get("count", 0) or 0)
        rows = sorted(keywords.items(), key=lambda item: item[1], reverse=True)[:18]
        if not rows:
            self.callout("Aucun mot-clé suffisamment récurrent n'a été identifié.", MUTED)
            return

        self.ensure_space(28)
        x, y = 14, self.get_y()
        max_x = 196
        for index, (term, count) in enumerate(rows):
            label = f"{term}  {count}"
            font_size = 7.2 + min(2.2, math.log(max(count, 1), 3) * 0.45)
            self.set_font(self.font_family, "B", font_size)
            pill_w = self.get_string_width(self.text_value(label)) + 8
            pill_h = 7
            if x + pill_w > max_x:
                x = 14
                y += pill_h + 2
                self.ensure_space(pill_h + 3)
            self.set_fill_color(*(BRAND_SURFACE if index % 2 == 0 else SURFACE))
            self.set_draw_color(*BORDER)
            self.rect(x, y, pill_w, pill_h, style="DF")
            self.set_xy(x + 4, y + 1.2)
            self.set_text_color(*(BRAND_DARK if index < 6 else TEXT))
            self.cell(pill_w - 8, 4.5, self.text_value(label), align="C")
            x += pill_w + 2
        self.set_y(y + 11)

    def tweet_card(self, tweet: Dict[str, Any], index: int) -> None:
        sentiment = _normalize_sentiment(tweet.get("sentiment"))
        color = _SENTIMENT_RGB[sentiment]
        author = str(tweet.get("author") or "Utilisateur inconnu")
        target = str(tweet.get("target") or tweet.get("target_name") or "")
        confidence = float(tweet.get("confidence", 0) or 0)
        date = _format_datetime(tweet.get("date") or tweet.get("tweet_created_at"), include_time=False)
        text = self.text_value(str(tweet.get("text") or "").strip())
        lines = self._wrapped_lines(text, 166, 8.4)
        # Évite qu'un tweet très long monopolise une page.
        if len(lines) > 8:
            lines = lines[:8]
            lines[-1] = lines[-1].rstrip() + "..."
        height = 17 + len(lines) * 4.2
        self.ensure_space(height + 3)
        y = self.get_y()
        self.set_fill_color(*WHITE)
        self.set_draw_color(*BORDER)
        self.rect(14, y, 182, height, style="DF")
        self.set_fill_color(*color)
        self.rect(14, y, 3, height, style="F")

        self.set_xy(21, y + 4)
        self.set_font(self.font_family, "B", 8.7)
        self.set_text_color(*INK)
        self.cell(78, 5, self.text_value(f"{index}. @{author}"))
        self.set_font(self.font_family, "B", 7.2)
        self.set_text_color(*color)
        self.cell(42, 5, self.text_value(_SENTIMENT_LABEL[sentiment]), align="R")
        self.set_font(self.font_family, "", 7.1)
        self.set_text_color(*MUTED)
        self.cell(48, 5, self.text_value(f"Confiance {_pct(confidence)}"), align="R")

        meta = " · ".join(part for part in [target, date] if part and part != "Non renseigné")
        self.set_xy(21, y + 9)
        self.set_font(self.font_family, "", 7)
        self.set_text_color(*MUTED)
        self.cell(168, 4, self.text_value(meta))

        self.set_xy(21, y + 14)
        self.set_font(self.font_family, "", 8.4)
        self.set_text_color(*TEXT)
        self.multi_cell(166, 4.2, "\n".join(lines))
        self.set_y(y + height + 3)

    def prose(self, text: str, max_chars: Optional[int] = None) -> None:
        cleaned = _clean_markdown(text)
        if max_chars and len(cleaned) > max_chars:
            cleaned = cleaned[: max_chars - 3].rstrip() + "..."
        paragraphs = [part.strip() for part in cleaned.split("\n") if part.strip()]
        self.set_font(self.font_family, "", 9)
        self.set_text_color(*TEXT)
        for paragraph in paragraphs:
            bullet = paragraph.startswith("• ")
            self.ensure_space(8)
            if bullet:
                self.set_x(18)
                self.set_text_color(*BRAND)
                self.cell(4, 4.8, "•")
                self.set_text_color(*TEXT)
                self.multi_cell(168, 4.8, self.text_value(paragraph[2:]))
            else:
                self.set_x(14)
                self.multi_cell(182, 4.8, self.text_value(paragraph))
            self.ln(1)

    def methodology_box(self, text: str, title: str = "À propos de cette analyse") -> None:
        self.ensure_space(25)
        y = self.get_y()
        cleaned = self.text_value(_clean_markdown(text))
        lines = self._wrapped_lines(cleaned, 168, 7.6)
        height = max(20, 10 + len(lines) * 4)
        self.set_fill_color(*SURFACE)
        self.set_draw_color(*BORDER)
        self.rect(14, y, 182, height, style="DF")
        self.set_xy(20, y + 4)
        self.set_font(self.font_family, "B", 8)
        self.set_text_color(*INK)
        self.cell(0, 4, self.text_value(title), ln=True)
        self.set_x(20)
        self.set_font(self.font_family, "", 7.4)
        self.set_text_color(*MUTED)
        self.multi_cell(168, 4, cleaned)
        self.set_y(y + height + 3)

    def _wrapped_lines(self, text: str, width: float, font_size: float) -> List[str]:
        previous_family = getattr(self, "font_family", self.font_family)
        previous_style = getattr(self, "font_style", "")
        previous_size = getattr(self, "font_size_pt", font_size)
        self.set_font(self.font_family, "", font_size)
        lines: List[str] = []
        for paragraph in str(text).splitlines() or [""]:
            words = paragraph.split()
            if not words:
                lines.append("")
                continue
            current = words[0]
            for word in words[1:]:
                candidate = f"{current} {word}"
                if self.get_string_width(candidate) <= width:
                    current = candidate
                else:
                    lines.append(current)
                    current = word
            lines.append(current)
        try:
            self.set_font(previous_family, previous_style, previous_size)
        except Exception:
            pass
        return lines


# ---------------------------------------------------------------------------
# Helpers de données
# ---------------------------------------------------------------------------
def _overall_distribution(targets: Sequence[Dict[str, Any]]) -> Dict[str, float]:
    counts: Dict[str, float] = {}
    total = 0.0
    for target in targets:
        target_total = float(target.get("total", 0) or 0)
        distribution = target.get("distribution", {}) or {}
        for sentiment, ratio in distribution.items():
            normalized = _normalize_sentiment(sentiment)
            count = float(ratio or 0) * target_total
            counts[normalized] = counts.get(normalized, 0) + count
            total += count
    return {sentiment: value / total for sentiment, value in counts.items()} if total else {}


def _aggregate_report_kpis(targets: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    total = sum(int(target.get("total", 0) or 0) for target in targets)
    positive = sum(int(target.get("positive", 0) or 0) for target in targets)
    negative = sum(int(target.get("negative", 0) or 0) for target in targets)
    weighted_confidence = sum(
        float(target.get("average_confidence", 0) or 0) * int(target.get("total", 0) or 0)
        for target in targets
    )
    avg_confidence = weighted_confidence / total if total else 0
    net = (positive - negative) / total if total else 0
    return {
        "total": total,
        "positive_ratio": positive / total if total else 0,
        "negative_ratio": negative / total if total else 0,
        "average_confidence": avg_confidence,
        "net_sentiment_score": net,
    }


def _dominant_from_distribution(distribution: Dict[str, Any]) -> str:
    if not distribution:
        return "inconnu"
    return _normalize_sentiment(max(distribution.items(), key=lambda item: float(item[1] or 0))[0])


def _normalise_target_rows(targets: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for target in targets:
        row = dict(target)
        distribution = row.get("distribution", {}) or {}
        row.setdefault("dominant_sentiment", _dominant_from_distribution(distribution))
        total = int(row.get("total", 0) or 0)
        if "net_sentiment_score" not in row:
            pos = int(row.get("positive", 0) or 0)
            neg = int(row.get("negative", 0) or 0)
            row["net_sentiment_score"] = (pos - neg) / total if total else 0
        row.setdefault("average_confidence", 0)
        rows.append(row)
    return rows


# ---------------------------------------------------------------------------
# Rapports
# ---------------------------------------------------------------------------
def generate_dashboard_pdf(
    title: str,
    question: str,
    answer: str,
    sources: List[Dict[str, Any]],
    metrics: Optional[Dict[str, Any]] = None,
    sentiment_stats: Optional[Dict[str, Any]] = None,
) -> Optional[bytes]:
    """Rapport exporté directement depuis l'assistant."""
    if not FPDF_AVAILABLE:
        logger.warning("[PDF] fpdf2 non installé. pip install fpdf2")
        return None

    normalized_sources: List[Dict[str, Any]] = []
    sentiment_counts: Dict[str, int] = {}
    confidences: List[float] = []
    for source in sources or []:
        sentiment = _normalize_sentiment(source.get("sentiment"))
        confidence = float(source.get("confidence", 0) or 0)
        confidences.append(confidence)
        sentiment_counts[sentiment] = sentiment_counts.get(sentiment, 0) + 1
        normalized_sources.append(
            {
                "author": source.get("author") or source.get("author_username") or "?",
                "sentiment": sentiment,
                "confidence": confidence,
                "text": source.get("text", ""),
                "target": source.get("target_name") or source.get("target") or "",
                "date": source.get("tweet_created_at") or source.get("display_date"),
            }
        )

    if sentiment_stats and not sentiment_counts:
        sentiment_counts = {
            _normalize_sentiment(key): int(value or 0) for key, value in sentiment_stats.items()
        }
    total = sum(sentiment_counts.values()) or len(normalized_sources)
    distribution = {
        key: value / total for key, value in sentiment_counts.items()
    } if total else {}
    positive = sum(sentiment_counts.get(key, 0) for key in ("joie", "amour"))
    negative = sum(sentiment_counts.get(key, 0) for key in ("colere", "tristesse", "peur"))
    net = (positive - negative) / total if total else 0
    avg_conf = sum(confidences) / len(confidences) if confidences else 0

    pdf = SentiFlowPDF(title or "Rapport SentiFlow")
    pdf.hero(
        title=title or "Rapport d'analyse SentiFlow",
        subtitle="Synthèse de la réponse de l'assistant et des tweets utilisés comme sources.",
        metadata=[
            ("Généré le", datetime.utcnow().strftime("%d/%m/%Y à %H:%M")),
            ("Tweets sources", _format_number(total)),
            ("Confiance moyenne", _pct(avg_conf)),
        ],
    )

    pdf.section_title("Question analysée")
    pdf.callout(question or "Question non renseignée")

    pdf.section_title("Lecture rapide", "Les indicateurs ci-dessous portent sur les sources incluses dans la réponse.")
    pdf.metric_cards(
        [
            ("Tweets sources", _format_number(total), None, BRAND),
            ("Sentiments positifs", _pct(positive / total if total else 0), None, SUCCESS),
            ("Sentiments négatifs", _pct(negative / total if total else 0), None, DANGER),
            ("Score net", _score_display(net), _net_label(net), _score_color(net)),
        ]
    )
    pdf.stacked_bar(distribution)

    pdf.section_title("Réponse de l'assistant")
    pdf.prose(answer or "Aucune réponse n'a été enregistrée.", max_chars=6500)

    if normalized_sources:
        pdf.section_title(
            "Tweets utilisés comme sources",
            f"Sélection de {min(len(normalized_sources), 16)} tweets parmi les éléments transmis à l'assistant.",
        )
        for index, source in enumerate(normalized_sources[:16], 1):
            pdf.tweet_card(source, index)

    if metrics:
        retrieval = metrics.get("retrieval", {}) or {}
        timing = metrics.get("timing", {}) or {}
        pdf.section_title("Qualité technique de la réponse")
        pdf.metric_cards(
            [
                ("Pertinence", f"{float(retrieval.get('relevance', 0) or 0):.2f}", None, BRAND),
                ("Cohérence", f"{float(retrieval.get('coherence', 0) or 0):.2f}", None, SUCCESS),
                ("MRR", f"{float(retrieval.get('mrr', 0) or 0):.2f}", None, WARNING),
                ("Temps total", f"{float(timing.get('total', 0) or 0):.2f} s", None, MUTED),
            ]
        )

    pdf.methodology_box(
        "Les sentiments sont produits automatiquement par le modèle SentiFlow. "
        "Ils représentent une estimation statistique et peuvent contenir des erreurs, notamment en présence "
        "d'ironie, de contexte implicite ou de messages très courts."
    )
    return bytes(pdf.output())


def generate_report_pdf(
    title: str,
    question: str,
    created_at: Optional[str],
    targets: List[Dict[str, Any]],
    tweets: List[Dict[str, Any]],
    synthesis: Optional[str] = None,
    period_start: Optional[Any] = None,
    period_end: Optional[Any] = None,
    collection_note: Optional[str] = None,
) -> Optional[bytes]:
    """Rapport analytique complet associé à un dashboard généré."""
    if not FPDF_AVAILABLE:
        logger.warning("[PDF] fpdf2 non installé. pip install fpdf2")
        return None

    target_rows = _normalise_target_rows(targets or [])
    kpis = _aggregate_report_kpis(target_rows)
    overall_distribution = _overall_distribution(target_rows)
    targets_label = ", ".join(str(row.get("name", "?")) for row in target_rows[:4])
    if len(target_rows) > 4:
        targets_label += f" +{len(target_rows) - 4}"

    pdf = SentiFlowPDF(title or "Rapport d'analyse des tweets")
    pdf.hero(
        title=title or "Rapport d'analyse des tweets",
        subtitle=question or "Analyse de sentiments réalisée à partir des tweets collectés.",
        metadata=[
            ("Période analysée", _format_period(period_start, period_end)),
            ("Cibles", targets_label or "Aucune cible"),
            ("Rapport créé", _format_datetime(created_at)),
        ],
    )

    if collection_note:
        pdf.callout(collection_note, WARNING)

    pdf.section_title(
        "Synthèse exécutive",
        "Une vue rapide pour comprendre le volume, la tonalité globale et la fiabilité des classifications.",
    )
    pdf.metric_cards(
        [
            ("Tweets analysés", _format_number(kpis["total"]), f"{len(target_rows)} cible(s)", BRAND),
            ("Positifs", _pct(kpis["positive_ratio"]), "Joie + amour", SUCCESS),
            ("Négatifs", _pct(kpis["negative_ratio"]), "Colère + tristesse + peur", DANGER),
            (
                "Score net",
                _score_display(kpis["net_sentiment_score"]),
                _net_label(kpis["net_sentiment_score"]),
                _score_color(kpis["net_sentiment_score"]),
            ),
        ]
    )
    pdf.stacked_bar(overall_distribution)

    if synthesis:
        pdf.section_title("Analyse rédigée par l'assistant")
        pdf.prose(synthesis, max_chars=7000)

    if target_rows:
        pdf.section_title(
            "Comparaison des cibles",
            "Le score net varie de -1 (tonalité négative) à +1 (tonalité positive).",
        )
        pdf.target_comparison_table(target_rows)

        pdf.ensure_space(46)
        pdf.section_title("Répartition détaillée des sentiments")
        for target in target_rows:
            pdf.target_distribution(target)

        pdf.section_title(
            "Évolution temporelle",
            "Évolution quotidienne du score net pour chaque cible.",
        )
        pdf.timeline_chart(target_rows)

        pdf.section_title("Sujets et mots récurrents")
        pdf.keyword_cloud(target_rows)
    else:
        pdf.callout(
            "Aucun tweet analysé n'était disponible pour les cibles et la période associées à ce dashboard.",
            WARNING,
        )

    if tweets:
        pdf.ensure_space(38)
        pdf.section_title(
            "Tweets représentatifs",
            f"Sélection de {min(len(tweets), 16)} tweets à forte confiance, répartis entre les cibles.",
        )
        for index, tweet in enumerate(tweets[:16], 1):
            pdf.tweet_card(tweet, index)

    pdf.ensure_space(38)
    pdf.section_title("Méthodologie et limites")
    pdf.methodology_box(
        "La distribution est calculée à partir des tweets analysés enregistrés pour la période du rapport. "
        "Le score net correspond à (tweets positifs - tweets négatifs) / tweets analysés. "
        "La classification automatique peut être moins fiable pour l'ironie, les citations, le sarcasme, "
        "les contenus multilingues et les messages sans contexte. Les tweets affichés sont une sélection "
        "représentative et non l'intégralité du corpus."
    )
    return bytes(pdf.output())


def generate_invoice_pdf(
    number: str,
    username: str,
    email: str,
    plan: str,
    amount: float,
    period: str,
    created_at: str,
) -> Optional[bytes]:
    """Facture SentiFlow avec une présentation cohérente avec les rapports."""
    if not FPDF_AVAILABLE:
        return None

    pdf = SentiFlowPDF("Facture SentiFlow")
    pdf.add_page()
    pdf.set_fill_color(*BRAND)
    pdf.rect(0, 0, 210, 42, style="F")
    pdf.brand_mark(15, 12, 1.25)
    pdf.set_xy(26, 10)
    pdf.set_font(pdf.font_family, "B", 16)
    pdf.set_text_color(*WHITE)
    pdf.cell(80, 10, "SentiFlow")
    pdf.set_xy(120, 11)
    pdf.set_font(pdf.font_family, "B", 18)
    pdf.cell(76, 10, pdf.text_value("FACTURE"), align="R")

    pdf.set_y(51)
    pdf.set_font(pdf.font_family, "B", 11)
    pdf.set_text_color(*INK)
    pdf.cell(100, 7, pdf.text_value(f"Facture n° {number}"))
    pdf.set_font(pdf.font_family, "", 9)
    pdf.set_text_color(*MUTED)
    pdf.cell(82, 7, pdf.text_value(f"Émise le {_format_datetime(created_at, False)}"), align="R", ln=True)
    pdf.ln(5)

    y = pdf.get_y()
    pdf.set_fill_color(*SURFACE)
    pdf.set_draw_color(*BORDER)
    pdf.rect(14, y, 86, 33, style="DF")
    pdf.rect(110, y, 86, 33, style="DF")
    pdf.set_xy(19, y + 5)
    pdf.set_font(pdf.font_family, "B", 8)
    pdf.set_text_color(*MUTED)
    pdf.cell(70, 5, pdf.text_value("CLIENT"), ln=True)
    pdf.set_x(19)
    pdf.set_font(pdf.font_family, "B", 10)
    pdf.set_text_color(*INK)
    pdf.cell(70, 6, pdf.text_value(username), ln=True)
    pdf.set_x(19)
    pdf.set_font(pdf.font_family, "", 8.5)
    pdf.set_text_color(*TEXT)
    pdf.cell(70, 5, pdf.text_value(email))

    pdf.set_xy(115, y + 5)
    pdf.set_font(pdf.font_family, "B", 8)
    pdf.set_text_color(*MUTED)
    pdf.cell(70, 5, pdf.text_value("DÉTAIL DU PAIEMENT"), ln=True)
    pdf.set_x(115)
    pdf.set_font(pdf.font_family, "B", 10)
    pdf.set_text_color(*INK)
    pdf.cell(70, 6, pdf.text_value(f"Abonnement {plan}"), ln=True)
    pdf.set_x(115)
    pdf.set_font(pdf.font_family, "", 8.5)
    pdf.set_text_color(*TEXT)
    pdf.cell(70, 5, pdf.text_value(period))

    pdf.set_y(y + 42)
    widths = [118, 32, 32]
    headers = ["Description", "Période", "Montant"]
    pdf.set_fill_color(*INK)
    pdf.set_text_color(*WHITE)
    pdf.set_font(pdf.font_family, "B", 8.5)
    for width, header in zip(widths, headers):
        pdf.cell(width, 9, pdf.text_value(header), fill=True, align="C")
    pdf.ln()
    pdf.set_fill_color(*WHITE)
    pdf.set_text_color(*TEXT)
    pdf.set_font(pdf.font_family, "", 9)
    values = [f"Abonnement SentiFlow {plan}", period, f"{amount:.2f} EUR"]
    aligns = ["L", "C", "R"]
    for width, value, align in zip(widths, values, aligns):
        pdf.cell(width, 11, pdf.text_value(value), border="B", align=align)
    pdf.ln(18)

    pdf.set_x(110)
    pdf.set_fill_color(*BRAND_SURFACE)
    pdf.set_draw_color(*BRAND)
    pdf.set_font(pdf.font_family, "B", 11)
    pdf.set_text_color(*INK)
    pdf.cell(48, 12, pdf.text_value("TOTAL PAYÉ"), border=1, fill=True)
    pdf.set_text_color(*BRAND_DARK)
    pdf.cell(38, 12, pdf.text_value(f"{amount:.2f} EUR"), border=1, fill=True, align="R", ln=True)

    pdf.ln(14)
    pdf.methodology_box(
        "Paiement simulé dans l'environnement de démonstration SentiFlow. "
        "Ce document atteste de l'opération enregistrée sur la plateforme.",
        title="À propos de cette facture",
    )
    return bytes(pdf.output())
