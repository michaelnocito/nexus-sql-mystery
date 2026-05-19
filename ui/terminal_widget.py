# ui/terminal_widget.py
# TerminalWidget — cartoon cel-shaded monitor that IS the SQL terminal.
#
# Visual language: same as NPC portraits — bold ink outlines, angular
# flat cel-shading, one hard shadow plane, strong silhouette.
# The screen itself is a live QTextEdit (green prompt, white output).
#
# Changes vs v1:
#   - Screen now fills ~84 % of the widget height (was 67 %)
#   - Stand is slimmer; desk decorations (post-it, mug) removed
#   - play_unlock_animation() — Matrix rain → CONCEPT UNLOCKED reveal

import random

from PySide6.QtWidgets import QWidget, QTextEdit
from PySide6.QtCore import Qt, QTimer, QRect, QRectF
from PySide6.QtGui import (
    QPainter, QColor, QPen, QBrush, QPainterPath,
    QFont, QLinearGradient, QRadialGradient,
    QTextCharFormat, QTextCursor,
)

# ── Palette ───────────────────────────────────────────────────────────────────

C_BEZEL      = QColor("#1e2d4a")
C_BEZEL_HI   = QColor("#253561")   # highlight face
C_BEZEL_SH   = QColor("#111e30")   # shadow face
C_SCREEN     = QColor("#0d1117")
C_BORDER     = QColor("#0d1117")
C_INK        = QColor("#080e1a")
C_DESK       = QColor("#1a2438")
C_DESK_EDGE  = QColor("#0f1724")
C_STAND      = QColor("#182035")
C_LED_ON     = QColor("#22c55e")
C_LED_GLOW   = QColor(34, 197, 94, 55)

PROMPT_COL   = "#3fb950"
CMD_COL      = "#e6edf3"
OUT_COL      = "#c9d1d9"
ERR_COL      = "#ff7b72"
DIM_COL      = "#8b949e"
UNLOCK_COL   = "#58a6ff"

# Characters for Matrix rain
_MATRIX_CHARS = list(
    "01アイウエオカキクケコサシスセソタチツテト"
    "{}[]<>ABCDEFabcdef0123456789#$%@!?/|\\"
)


class TerminalWidget(QWidget):
    """
    Cartoon monitor illustration containing a live terminal.
    The painted monitor is decorative; the real interaction happens
    in the embedded QTextEdit child widget that sits inside the
    painted screen rect.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, False)

        # ── Screen content (live terminal) ───────────────────────────────────
        self._text = QTextEdit(self)
        self._text.setReadOnly(True)
        self._text.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        self._text.setFrameShape(QTextEdit.Shape.NoFrame)
        self._text.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._text.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._text.setStyleSheet("""
            QTextEdit {
                background: #0d1117;
                color: #c9d1d9;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 13px;
                border: none;
                padding: 10px 14px;
                selection-background-color: #264f78;
            }
            QScrollBar:vertical   { background:#161b22; width:8px; }
            QScrollBar::handle:vertical   { background:#30363d; border-radius:4px; min-height:20px; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height:0; }
            QScrollBar:horizontal { background:#161b22; height:8px; }
            QScrollBar::handle:horizontal { background:#30363d; border-radius:4px; min-width:20px; }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width:0; }
        """)

        # ── Idle / blinking cursor ────────────────────────────────────────────
        self._has_content   = False
        self._cursor_on     = True
        self._cursor_anchor = 0   # char position where the block cursor sits
        self._animating     = False

        self._idle_timer = QTimer(self)
        self._idle_timer.timeout.connect(self._blink)
        self._idle_timer.start(530)

        self._init_idle()

    # ── Layout (keep text inside painted screen) ──────────────────────────────

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._place_screen()

    def _screen_rect(self) -> QRect:
        """The pixel rect of the painted screen area — must match _draw() exactly."""
        w, h = self.width(), self.height()
        bx = max(8, int(w * 0.025))
        by = max(6, int(h * 0.025))
        bw = w - 2 * bx
        bh = int(h * 0.84)           # ← taller: was 0.67
        sm = max(5, int(w * 0.032))  # inner side margin (slimmer)
        sf_x = bx + sm
        sf_y = by + max(26, int(h * 0.068))   # below title bar
        sf_w = bw - 2 * sm
        sf_h = bh - (sf_y - by) - max(4, int(h * 0.010))
        return QRect(sf_x + 2, sf_y + 2, sf_w - 4, sf_h - 4)

    def _place_screen(self):
        r = self._screen_rect()
        self._text.setGeometry(r)

    # ── Painting ──────────────────────────────────────────────────────────────

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        self._draw(p, w, h)
        p.end()

    def _draw(self, p: QPainter, w: int, h: int):
        ink_w = max(2.0, w * 0.006)
        ink = QPen(C_INK, ink_w)
        ink.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        ink.setCapStyle(Qt.PenCapStyle.RoundCap)

        bx = max(8, int(w * 0.025))
        by = max(6, int(h * 0.025))
        bw = w - 2 * bx
        bh = int(h * 0.84)            # ← taller bezel
        sm = max(5, int(w * 0.032))

        # ── 1. Monitor body (bezel) ───────────────────────────────────────────
        # Shadow face (right + bottom edges)
        sh_path = QPainterPath()
        r8 = 14
        sh_path.moveTo(bx + bw - r8, by + r8)
        sh_path.lineTo(bx + bw,      by + r8)
        sh_path.lineTo(bx + bw,      by + bh - r8)
        sh_path.lineTo(bx + bw - r8, by + bh)
        sh_path.lineTo(bx + r8,      by + bh)
        sh_path.lineTo(bx + r8,      by + bh - r8)
        sh_path.closeSubpath()
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(C_BEZEL_SH))
        p.drawPath(sh_path)

        # Main bezel fill
        p.setPen(ink)
        p.setBrush(QBrush(C_BEZEL))
        p.drawRoundedRect(bx, by, bw, bh, 14, 14)

        # Highlight plane (top-left) — cel-shade signature
        hi_path = QPainterPath()
        hi_path.moveTo(bx + 14,           by)
        hi_path.lineTo(bx + int(bw * 0.46), by)
        hi_path.lineTo(bx + int(bw * 0.40), by + int(bh * 0.14))
        hi_path.lineTo(bx + int(bw * 0.08), by + int(bh * 0.14))
        hi_path.lineTo(bx,                  by + int(bh * 0.08))
        hi_path.lineTo(bx,                  by + 14)
        hi_path.closeSubpath()
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(QColor(255, 255, 255, 24)))
        p.drawPath(hi_path)

        # ── 2. Screen recess ──────────────────────────────────────────────────
        sf_x = bx + sm
        sf_y = by + max(26, int(h * 0.068))
        sf_w = bw - 2 * sm
        sf_h = bh - (sf_y - by) - max(4, int(h * 0.010))

        # Inset shadow
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(C_INK))
        p.drawRoundedRect(sf_x - 3, sf_y - 3, sf_w + 6, sf_h + 6, 8, 8)

        # Screen fill
        p.setPen(ink)
        p.setBrush(QBrush(C_SCREEN))
        p.drawRoundedRect(sf_x, sf_y, sf_w, sf_h, 5, 5)

        # Scanline gradient
        scan = QLinearGradient(sf_x, sf_y, sf_x, sf_y + sf_h)
        scan.setColorAt(0.0, QColor(255, 255, 255, 6))
        scan.setColorAt(0.5, QColor(0, 0, 0, 0))
        scan.setColorAt(1.0, QColor(0, 0, 0, 14))
        p.setPen(Qt.PenStyle.NoPen)
        p.fillRect(sf_x, sf_y, sf_w, sf_h, scan)

        # Screen glow
        glow = QRadialGradient(sf_x + sf_w // 2, sf_y + sf_h // 2, sf_w * 0.65)
        glow.setColorAt(0, QColor(34, 197, 94, 18))
        glow.setColorAt(1, QColor(0, 0, 0, 0))
        p.fillRect(sf_x, sf_y, sf_w, sf_h, glow)

        # ── 3. Title bar — traffic lights + label ─────────────────────────────
        bar_y = by + 8
        bar_h = sf_y - by - 10

        dot_y = bar_y + bar_h // 2 - 5
        for i, dc in enumerate(("#ff5f57", "#ffbd2e", "#28c840")):
            dx = bx + 16 + i * 21
            p.setPen(QPen(C_INK, 1.2))
            p.setBrush(QBrush(QColor(dc)))
            p.drawEllipse(dx, dot_y, 11, 11)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(QColor(255, 255, 255, 55)))
            p.drawEllipse(dx + 2, dot_y + 1, 4, 4)

        label_x = bx + 16 + 3 * 21 + 10
        p.setPen(QPen(QColor("#8b949e")))
        p.setFont(QFont("Consolas", max(8, int(min(w, 800) * 0.016)), QFont.Weight.Normal))
        p.drawText(label_x, bar_y + bar_h - 3, "nexus-db  ─  SQL Terminal")

        # ── 4. LED indicator (power light) ────────────────────────────────────
        led_x = bx + bw - 20
        led_y = by + bh - 17
        led_glow = QRadialGradient(led_x + 5, led_y + 5, 16)
        led_glow.setColorAt(0, C_LED_GLOW)
        led_glow.setColorAt(1, QColor(0, 0, 0, 0))
        p.setPen(Qt.PenStyle.NoPen)
        p.fillRect(led_x - 10, led_y - 10, 30, 30, led_glow)
        p.setPen(QPen(C_INK, 1.5))
        p.setBrush(QBrush(C_LED_ON))
        p.drawEllipse(led_x, led_y, 10, 10)

        # ── 5. Slim stand (neck + base only, no desk clutter) ─────────────────
        stand_cx  = w // 2
        neck_top  = by + bh
        neck_w    = max(12, int(w * 0.065))
        neck_h    = max(8,  int(h * 0.032))   # slimmer: was 0.07

        neck = QPainterPath()
        neck.moveTo(stand_cx - neck_w // 3, neck_top)
        neck.lineTo(stand_cx + neck_w // 3, neck_top)
        neck.lineTo(stand_cx + neck_w // 2, neck_top + neck_h)
        neck.lineTo(stand_cx - neck_w // 2, neck_top + neck_h)
        neck.closeSubpath()
        p.setPen(ink)
        p.setBrush(QBrush(C_STAND))
        p.drawPath(neck)

        base_y = neck_top + neck_h
        base_w = max(50, int(w * 0.22))       # narrower: was 0.30
        base_h = max(7,  int(h * 0.022))      # slimmer:  was 0.048
        p.drawRoundedRect(stand_cx - base_w // 2, base_y, base_w, base_h, 5, 5)

        # ── 6. Desk — thin dark strip (grounds the monitor, no decorations) ───
        desk_y = base_y + base_h
        desk_h = max(0, h - desk_y)
        if desk_h > 0:
            desk_grad = QLinearGradient(0, desk_y, 0, h)
            desk_grad.setColorAt(0.0, QColor("#1a2438"))
            desk_grad.setColorAt(1.0, QColor("#0f1724"))
            p.setPen(QPen(QColor("#243050"), 1))
            p.setBrush(QBrush(desk_grad))
            p.drawRect(0, desk_y, w, desk_h)

    # ── Idle blinking cursor ───────────────────────────────────────────────────

    def _init_idle(self):
        """Write the idle prompt with a blinking block cursor."""
        self._write_raw("nexus@analytics:~$ ", PROMPT_COL, bold=True)
        self._cursor_anchor = self._text.textCursor().position()
        self._write_raw("█", PROMPT_COL)

    def _blink(self):
        if self._has_content or self._animating:
            return
        self._cursor_on = not self._cursor_on
        doc = self._text.document()  # noqa: F841
        cursor = self._text.textCursor()
        cursor.setPosition(self._cursor_anchor)
        cursor.movePosition(QTextCursor.MoveOperation.End,
                            QTextCursor.MoveMode.KeepAnchor)
        cursor.removeSelectedText()
        if self._cursor_on:
            fmt = QTextCharFormat()
            fmt.setForeground(QColor(PROMPT_COL))
            cursor.insertText("█", fmt)
        self._text.setTextCursor(cursor)

    # ── Public write API ──────────────────────────────────────────────────────

    def write_command(self, cmd: str) -> None:
        """Write the green prompt + user command."""
        if not self._has_content:
            cursor = self._text.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.Start)
            cursor.movePosition(QTextCursor.MoveOperation.End,
                                QTextCursor.MoveMode.KeepAnchor)
            cursor.removeSelectedText()
            self._has_content = True
        self._write_raw("\nnexus@analytics:~$ ", PROMPT_COL, bold=True)
        self._write_raw(cmd.strip() + "\n", CMD_COL)

    def write_output(self, text: str) -> None:
        """Write query results / output."""
        self._has_content = True
        clean = text.rstrip("\n")
        if clean:
            self._write_raw(clean + "\n", OUT_COL)

    def write_error(self, text: str) -> None:
        """Write an error line in red."""
        self._has_content = True
        self._write_raw(text.rstrip("\n") + "\n", ERR_COL)

    def write_dim(self, text: str) -> None:
        """Write a muted/dim line (grey)."""
        self._has_content = True
        self._write_raw(text.rstrip("\n") + "\n", DIM_COL)

    # ── Matrix unlock animation ───────────────────────────────────────────────

    # Rotating Morpheus-style messages — mysterious figure behind the scenes
    _MORPHEUS_MSGS = [
        [
            "  Good.",
            "  You're starting to see it.",
            "",
            "  The data doesn't lie.",
            "  People do.",
            "",
            "  Keep pulling the thread.",
            "",
            "                              — M",
        ],
        [
            "  Pattern recognized.",
            "",
            "  They've been hiding in plain sight —",
            "  in numbers they hoped you'd ignore.",
            "",
            "  You're asking the right questions.",
            "  That makes you dangerous.",
            "",
            "                              — M",
        ],
        [
            "  You found it.",
            "",
            "  The database remembers everything.",
            "  Every transaction. Every approval.",
            "  Every number they hoped you'd miss.",
            "",
            "  They underestimated you.",
            "  That's their mistake.",
            "",
            "                              — M",
        ],
        [
            "  There it is.",
            "",
            "  Most analysts never look this closely.",
            "  They see the surface.",
            "  You see what's underneath.",
            "",
            "  We chose well.",
            "",
            "                              — M",
        ],
        [
            "  Exactly.",
            "",
            "  The truth is in the query.",
            "  It was always there —",
            "  waiting for someone who knew how to ask.",
            "",
            "  You're ready for what comes next.",
            "",
            "                              — M",
        ],
    ]

    def play_unlock_animation(self, title: str = "") -> None:
        """
        Three-phase animation on concept unlock:
          Phase 1 — Matrix rain (fast random chars, ~1 s)
          Phase 2 — Resolve: message chars lock in progressively (10 frames)
          Phase 3 — Clean Morpheus message displayed 4 s, then back to prompt
        """
        if self._animating:
            return
        self._animating = True
        self._idle_timer.stop()
        self._has_content = True
        self._text.clear()

        msg_lines = random.choice(self._MORPHEUS_MSGS)
        # Prepend the concept title if provided
        if title:
            header = [f"  [ {title} ]", ""]
            msg_lines = header + list(msg_lines)

        RAIN_FRAMES    = 20
        RESOLVE_FRAMES = 12
        state = {"phase": "rain", "frame": 0}

        def _tick():
            phase = state["phase"]
            f     = state["frame"]

            if phase == "rain":
                line = "".join(random.choice(_MATRIX_CHARS) for _ in range(46))
                col  = PROMPT_COL if f % 3 != 2 else DIM_COL
                self._write_raw("  " + line + "\n", col)
                state["frame"] += 1
                if f >= RAIN_FRAMES - 1:
                    # Switch to resolve phase
                    state["phase"] = "resolve"
                    state["frame"] = 0
                    self._text.clear()
                    QTimer.singleShot(60, _tick)
                else:
                    delay = 40 + f * 3   # 40 ms → 97 ms, fast rain feel
                    QTimer.singleShot(delay, _tick)

            elif phase == "resolve":
                # Each frame: lock in more of the real message chars
                progress = (f + 1) / RESOLVE_FRAMES  # 0.08 → 1.0
                self._text.clear()
                for line in msg_lines:
                    if not line.strip():
                        self._write_raw("\n", OUT_COL)
                        continue
                    # Each char: real or random depending on progress
                    resolved = ""
                    for ch in line:
                        if ch == " " or random.random() < progress:
                            resolved += ch
                        else:
                            resolved += random.choice(_MATRIX_CHARS)
                    # Colour shifts from green → white as it resolves
                    col = PROMPT_COL if progress < 0.55 else CMD_COL
                    self._write_raw(resolved + "\n", col)

                state["frame"] += 1
                if f >= RESOLVE_FRAMES - 1:
                    # Final clean render after tiny pause
                    QTimer.singleShot(120, _show_final)
                else:
                    delay = 70 + f * 18   # 70 ms → 268 ms, slowing to a stop
                    QTimer.singleShot(delay, _tick)

        def _show_final():
            """Render the clean Morpheus message, hold 4.5 s, then restore."""
            morpheus = random.choice(self._MORPHEUS_MSGS)
            self._text.clear()
            self._write_raw("\n", OUT_COL)
            self._write_raw("  " + "─" * 44 + "\n", PROMPT_COL)
            self._write_raw("\n", OUT_COL)
            if title:
                self._write_raw(f"  [ {title} ]\n", UNLOCK_COL)
                self._write_raw("\n", OUT_COL)
            for line in morpheus:
                if not line.strip():
                    self._write_raw("\n", OUT_COL)
                elif "— M" in line:
                    self._write_raw(line + "\n", DIM_COL)
                else:
                    self._write_raw(line + "\n", CMD_COL)
            self._write_raw("\n", OUT_COL)
            self._write_raw("  " + "─" * 44 + "\n", PROMPT_COL)
            self._write_raw("\n", OUT_COL)
            self._write_raw("  ◆ Concept unlocked — open the Concepts panel for details.\n", UNLOCK_COL)
            self._write_raw("\n", OUT_COL)
            QTimer.singleShot(4500, self._end_animation)

        QTimer.singleShot(0, _tick)

    def _end_animation(self) -> None:
        """Restore normal prompt after the unlock animation."""
        self._animating = False
        self._write_raw("nexus@analytics:~$ ", PROMPT_COL, bold=True)
        self._cursor_anchor = self._text.textCursor().position()
        self._write_raw("█", PROMPT_COL)
        self._has_content = False   # re-enable idle blink
        self._idle_timer.start(530)

    def _write_raw(self, text: str, color: str, bold: bool = False) -> None:
        cursor = self._text.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(color))
        if bold:
            fmt.setFontWeight(QFont.Weight.Bold)
        cursor.insertText(text, fmt)
        self._text.setTextCursor(cursor)
        self._text.ensureCursorVisible()
