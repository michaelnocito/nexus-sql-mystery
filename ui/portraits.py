# ui/portraits.py
# NPC portrait system — 90s-X-Men-animated style.
#
# Hand-drawn QPainter busts (no image assets, consistent with scene_view).
# Style rules: bold black ink outline, ANGULAR features (sharp jaw, not
# round), flat cel-shaded colour with ONE hard-edged shadow plane,
# strong geometric hair silhouette, slightly heroic proportions.
#
# Each speaking NPC gets a distinct silhouette + a signature accent
# colour used by the dialogue speech box. A neutral fallback covers any
# unattributed / minor speaker so rendering never crashes.

from PySide6.QtCore import Qt, QRect, QPointF
from PySide6.QtGui import (
    QPixmap, QPainter, QColor, QPen, QBrush, QPainterPath, QFont,
)

# ── Per-NPC signature accent colours (speech-box border / name tag) ──────────

NPC_COLORS = {
    "Sam":     "#5b7a99",   # spirit guide — ghost slate-blue
    "Diana":   "#0d7d8c",   # manager      — teal, sharp
    "Rachel":  "#7d4fc7",   # COO          — authoritative violet
    "Vanessa": "#b5527a",   # HR           — warm rose
    "_":       "#57606a",   # fallback     — neutral grey
}

# Name aliases → canonical key (content uses first names / variants)
_ALIASES = {
    "sam": "Sam",
    "diana": "Diana", "diana reeves": "Diana", "d.r.": "Diana", "d. r.": "Diana",
    "narrator": "Diana",  # Diana narrates the story — she leaves the desk note
    "narration": "Diana",
    "rachel": "Rachel", "rachel kim": "Rachel", "kim": "Rachel",
    "vanessa": "Vanessa", "vanessa cole": "Vanessa",
}

_INK   = QColor("#15171c")   # bold outline
_WHITE = QColor("#f6f8fa")


def canonical(name: str) -> str:
    """Map any speaker string to a known NPC key, or '_' fallback."""
    if not name:
        return "_"
    key = _ALIASES.get(name.strip().lower())
    if key:
        return key
    # bare first word match (e.g. "Diana walks by")
    first = name.strip().split()[0].lower()
    return _ALIASES.get(first, "_")


def npc_color(name: str) -> str:
    return NPC_COLORS.get(canonical(name), NPC_COLORS["_"])


# ── Drawing helpers ─────────────────────────────────────────────────────────

def _shade(hex_color: str, factor: float) -> QColor:
    c = QColor(hex_color)
    return QColor(
        max(0, min(255, int(c.red()   * factor))),
        max(0, min(255, int(c.green() * factor))),
        max(0, min(255, int(c.blue()  * factor))),
    )


def _bust_base(p: QPainter, s: int, accent: str):
    """Tinted rounded background + shoulders. Shared by all NPCs."""
    bg = QColor(accent)
    bg.setAlpha(38)
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(bg))
    p.drawRoundedRect(0, 0, s, s, s * 0.16, s * 0.16)
    # Shoulders (angular blazer wedge)
    sh = QPainterPath()
    sh.moveTo(s * 0.10, s)
    sh.lineTo(s * 0.22, s * 0.74)
    sh.lineTo(s * 0.78, s * 0.74)
    sh.lineTo(s * 0.90, s)
    sh.closeSubpath()
    p.setBrush(QBrush(QColor(accent)))
    p.setPen(QPen(_INK, max(1.5, s * 0.035)))
    p.drawPath(sh)


def _cel_face(p: QPainter, s: int, skin: str, jaw: str = "sharp"):
    """Angular cel-shaded head + one hard shadow plane. Returns face rect."""
    skin_c = QColor(skin)
    shadow = _shade(skin, 0.78)

    face = QPainterPath()
    if jaw == "sharp":
        face.moveTo(s * 0.30, s * 0.26)
        face.lineTo(s * 0.70, s * 0.26)
        face.lineTo(s * 0.74, s * 0.50)
        face.lineTo(s * 0.58, s * 0.70)   # angular chin
        face.lineTo(s * 0.42, s * 0.70)
        face.lineTo(s * 0.26, s * 0.50)
        face.closeSubpath()
    else:  # softer (still angular, rounder chin) — Vanessa
        face.moveTo(s * 0.31, s * 0.27)
        face.lineTo(s * 0.69, s * 0.27)
        face.lineTo(s * 0.73, s * 0.52)
        face.lineTo(s * 0.50, s * 0.72)
        face.lineTo(s * 0.27, s * 0.52)
        face.closeSubpath()

    p.setPen(QPen(_INK, max(1.6, s * 0.04)))
    p.setBrush(QBrush(skin_c))
    p.drawPath(face)

    # Hard-edged shadow plane on the left third (cel-shade signature)
    p.save()
    p.setClipPath(face)
    shade_poly = QPainterPath()
    shade_poly.moveTo(s * 0.20, s * 0.20)
    shade_poly.lineTo(s * 0.46, s * 0.20)
    shade_poly.lineTo(s * 0.40, s * 0.80)
    shade_poly.lineTo(s * 0.20, s * 0.80)
    shade_poly.closeSubpath()
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(shadow))
    p.drawPath(shade_poly)
    p.restore()
    return face


def _eyes(p: QPainter, s: int, sharp: bool = True):
    p.setPen(QPen(_INK, max(1.4, s * 0.03)))
    p.setBrush(QBrush(_INK))
    ey = s * 0.46
    for ex in (s * 0.42, s * 0.58):
        if sharp:
            br = QPainterPath()
            br.moveTo(ex - s * 0.06, ey - s * 0.02)
            br.lineTo(ex + s * 0.06, ey - s * 0.05)
            p.drawPath(br)  # angled brow
        p.drawEllipse(QPointF(ex, ey + s * 0.04), s * 0.022, s * 0.030)


# ── Per-NPC heads ───────────────────────────────────────────────────────────

def _draw_sam(p: QPainter, s: int):
    """Spirit guide — ethereal, translucent, glowing eyes, wispy."""
    accent = NPC_COLORS["Sam"]
    _bust_base(p, s, accent)
    p.setOpacity(0.55)
    face = _cel_face(p, s, "#cfe0ef", "sharp")
    p.setOpacity(1.0)
    # Wispy hooded shroud
    hood = QPainterPath()
    hood.moveTo(s * 0.22, s * 0.50)
    hood.lineTo(s * 0.28, s * 0.16)
    hood.lineTo(s * 0.50, s * 0.08)
    hood.lineTo(s * 0.72, s * 0.16)
    hood.lineTo(s * 0.78, s * 0.50)
    hood.lineTo(s * 0.66, s * 0.30)
    hood.lineTo(s * 0.50, s * 0.22)
    hood.lineTo(s * 0.34, s * 0.30)
    hood.closeSubpath()
    sc = QColor(accent); sc.setAlpha(170)
    p.setPen(QPen(_INK, max(1.3, s * 0.03)))
    p.setBrush(QBrush(sc))
    p.drawPath(hood)
    # Glowing eyes
    glow = QColor("#9fe6ff")
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(glow))
    for ex in (s * 0.42, s * 0.58):
        p.drawEllipse(QPointF(ex, s * 0.50), s * 0.030, s * 0.034)


def _draw_diana(p: QPainter, s: int):
    """Manager — sharp asymmetric bob, confident, teal blazer."""
    accent = NPC_COLORS["Diana"]
    _bust_base(p, s, accent)
    face = _cel_face(p, s, "#e8c4a0", "sharp")
    # Sharp angular bob (geometric)
    hair = QPainterPath()
    hair.moveTo(s * 0.24, s * 0.56)
    hair.lineTo(s * 0.24, s * 0.24)
    hair.lineTo(s * 0.40, s * 0.12)
    hair.lineTo(s * 0.66, s * 0.12)
    hair.lineTo(s * 0.78, s * 0.26)
    hair.lineTo(s * 0.78, s * 0.60)
    hair.lineTo(s * 0.70, s * 0.40)
    hair.lineTo(s * 0.70, s * 0.24)
    hair.lineTo(s * 0.40, s * 0.22)
    hair.lineTo(s * 0.34, s * 0.34)
    hair.lineTo(s * 0.34, s * 0.58)
    hair.closeSubpath()
    p.setPen(QPen(_INK, max(1.6, s * 0.04)))
    p.setBrush(QBrush(QColor("#3a2c22")))
    p.drawPath(hair)
    _eyes(p, s, sharp=True)


def _draw_rachel(p: QPainter, s: int):
    """COO — sleek straight hair, strong jaw, composed authority."""
    accent = NPC_COLORS["Rachel"]
    _bust_base(p, s, accent)
    face = _cel_face(p, s, "#e3b88f", "sharp")
    # Sleek straight long hair framing
    hair = QPainterPath()
    hair.moveTo(s * 0.22, s * 0.70)
    hair.lineTo(s * 0.26, s * 0.20)
    hair.lineTo(s * 0.50, s * 0.08)
    hair.lineTo(s * 0.74, s * 0.20)
    hair.lineTo(s * 0.78, s * 0.70)
    hair.lineTo(s * 0.70, s * 0.52)
    hair.lineTo(s * 0.70, s * 0.26)
    hair.lineTo(s * 0.50, s * 0.20)
    hair.lineTo(s * 0.30, s * 0.26)
    hair.lineTo(s * 0.30, s * 0.52)
    hair.closeSubpath()
    p.setPen(QPen(_INK, max(1.6, s * 0.04)))
    p.setBrush(QBrush(QColor("#1c1620")))
    p.drawPath(hair)
    _eyes(p, s, sharp=True)


def _draw_vanessa(p: QPainter, s: int):
    """HR — softer rounder face, warm, wavy hair."""
    accent = NPC_COLORS["Vanessa"]
    _bust_base(p, s, accent)
    face = _cel_face(p, s, "#f0cdb0", "soft")
    # Wavy fuller hair
    hair = QPainterPath()
    hair.moveTo(s * 0.22, s * 0.60)
    hair.cubicTo(s * 0.16, s * 0.30, s * 0.34, s * 0.06, s * 0.50, s * 0.08)
    hair.cubicTo(s * 0.66, s * 0.06, s * 0.84, s * 0.30, s * 0.78, s * 0.60)
    hair.lineTo(s * 0.70, s * 0.46)
    hair.cubicTo(s * 0.70, s * 0.24, s * 0.50, s * 0.20, s * 0.50, s * 0.20)
    hair.cubicTo(s * 0.50, s * 0.20, s * 0.30, s * 0.24, s * 0.30, s * 0.46)
    hair.closeSubpath()
    p.setPen(QPen(_INK, max(1.6, s * 0.04)))
    p.setBrush(QBrush(QColor("#5a3520")))
    p.drawPath(hair)
    _eyes(p, s, sharp=False)


def _draw_fallback(p: QPainter, s: int):
    """Neutral silhouette — unattributed / minor speaker."""
    accent = NPC_COLORS["_"]
    _bust_base(p, s, accent)
    p.setPen(QPen(_INK, max(1.6, s * 0.04)))
    p.setBrush(QBrush(QColor("#9aa4b0")))
    p.drawEllipse(QPointF(s * 0.50, s * 0.46), s * 0.20, s * 0.22)
    # question-mark to signal "unknown speaker"
    p.setPen(QPen(_WHITE))
    f = QFont("Segoe UI", int(s * 0.26), QFont.Weight.Bold)
    p.setFont(f)
    p.drawText(QRect(0, int(s * 0.30), s, int(s * 0.34)),
               Qt.AlignmentFlag.AlignCenter, "?")


_DRAW = {
    "Sam":     _draw_sam,
    "Diana":   _draw_diana,
    "Rachel":  _draw_rachel,
    "Vanessa": _draw_vanessa,
    "_":       _draw_fallback,
}

_CACHE: dict[tuple[str, int], QPixmap] = {}


def npc_portrait(name: str, size: int = 52) -> QPixmap:
    """Return a cached QPixmap bust for the given speaker (any string)."""
    key = canonical(name)
    ck = (key, size)
    if ck in _CACHE:
        return _CACHE[ck]
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    _DRAW.get(key, _draw_fallback)(p, size)
    p.end()
    _CACHE[ck] = pm
    return pm
