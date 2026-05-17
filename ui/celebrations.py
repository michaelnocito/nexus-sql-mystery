# ui/celebrations.py
# Micro-celebration effects — toast banners, screen flash, and system beep.
# Keeps the dopamine loop tight without being obnoxious.
#
# Mobile games use: brief color flash + banner slide + sound.
# We do the same but tasteful.

from PySide6.QtWidgets import QLabel, QWidget, QGraphicsOpacityEffect
from PySide6.QtCore import (
    Qt, QTimer, QPropertyAnimation, QEasingCurve,
    QPoint, QSequentialAnimationGroup, QParallelAnimationGroup,
    Property,
)
from PySide6.QtGui import QFont, QColor, QPainter, QBrush, QPen
import random


# ── Colors ────────────────────────────────────────────────────────────────────

SUCCESS_BG   = "#dcfce7"   # light green
SUCCESS_BORDER = "#16a34a"
SUCCESS_TEXT = "#15803d"
GOLD_BG      = "#fef9c3"   # gold for big milestones
GOLD_BORDER  = "#ca8a04"
GOLD_TEXT    = "#854d0e"


# ── Toast Banner ──────────────────────────────────────────────────────────────

class ToastBanner(QLabel):
    """
    A brief banner that slides down from the top of the parent, holds, then fades.
    Mobile-game style "Achievement Unlocked!" micro-reward.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setWordWrap(True)
        self.hide()

        self._opacity = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self._opacity)
        self._opacity.setOpacity(0.0)

    def show_toast(self, text: str, style: str = "success", duration: int = 2800):
        """Animate a toast banner. style: 'success' or 'gold'."""
        if style == "gold":
            bg, border, fg = GOLD_BG, GOLD_BORDER, GOLD_TEXT
        else:
            bg, border, fg = SUCCESS_BG, SUCCESS_BORDER, SUCCESS_TEXT

        self.setText(text)
        self.setStyleSheet(f"""
            background: {bg};
            color: {fg};
            border: 2px solid {border};
            border-radius: 8px;
            font-size: 15px;
            font-weight: 700;
            padding: 12px 24px;
        """)

        # Size and position — centered at top of parent
        pw = self.parent().width()
        self.setFixedWidth(min(480, pw - 40))
        self.adjustSize()
        self.setFixedHeight(max(self.height(), 48))

        start_x = (pw - self.width()) // 2
        start_y = -self.height()
        end_y = 16

        self.move(start_x, start_y)
        self.show()
        self.raise_()

        # ── Animation group: slide in → hold → fade out ──────────────────
        group = QSequentialAnimationGroup(self)

        # 1. Slide in + fade in (parallel)
        enter = QParallelAnimationGroup()

        slide_in = QPropertyAnimation(self, b"pos")
        slide_in.setDuration(300)
        slide_in.setEasingCurve(QEasingCurve.Type.OutBack)  # slight overshoot bounce
        slide_in.setStartValue(QPoint(start_x, start_y))
        slide_in.setEndValue(QPoint(start_x, end_y))
        enter.addAnimation(slide_in)

        fade_in = QPropertyAnimation(self._opacity, b"opacity")
        fade_in.setDuration(200)
        fade_in.setStartValue(0.0)
        fade_in.setEndValue(1.0)
        enter.addAnimation(fade_in)

        group.addAnimation(enter)

        # 2. Hold
        hold = QPropertyAnimation(self._opacity, b"opacity")
        hold.setDuration(duration)
        hold.setStartValue(1.0)
        hold.setEndValue(1.0)
        group.addAnimation(hold)

        # 3. Fade out
        fade_out = QPropertyAnimation(self._opacity, b"opacity")
        fade_out.setDuration(400)
        fade_out.setStartValue(1.0)
        fade_out.setEndValue(0.0)
        group.addAnimation(fade_out)

        group.finished.connect(self.hide)
        group.start()
        self._anim_group = group  # prevent GC


# ── Screen Flash ──────────────────────────────────────────────────────────────

class ScreenFlash(QWidget):
    """
    A full-parent overlay that flashes a color and fades out.
    Used on objective completion — brief green pulse.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._color = QColor(22, 163, 74, 0)  # transparent green
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.hide()

    def flash(self, hex_color: str = "#16a34a", peak_alpha: int = 40, duration: int = 500):
        """Brief color wash over the parent widget."""
        self._color = QColor(hex_color)
        self._color.setAlpha(peak_alpha)

        self.setGeometry(0, 0, self.parent().width(), self.parent().height())
        self.show()
        self.raise_()

        # Fade: peak → 0
        self._alpha = peak_alpha
        self._target = 0
        self._step = max(1, peak_alpha // (duration // 30))
        self._timer = QTimer(self)
        self._timer.setInterval(30)
        self._timer.timeout.connect(self._tick)
        self._timer.start()

    def _tick(self):
        self._alpha = max(0, self._alpha - self._step)
        self._color.setAlpha(self._alpha)
        self.update()
        if self._alpha <= 0:
            self._timer.stop()
            self.hide()

    def paintEvent(self, event):
        p = QPainter(self)
        p.fillRect(self.rect(), self._color)
        p.end()


# ── System beep (cross-platform) ─────────────────────────────────────────────

def play_chime():
    """Play a brief system notification sound. Non-blocking."""
    try:
        import winsound
        # 800Hz for 80ms — short, pleasant, not annoying
        winsound.Beep(800, 80)
    except Exception:
        pass  # silently skip on non-Windows or if sound fails


def play_victory_chime():
    """Play a longer celebratory chime sequence for major milestones."""
    try:
        import winsound
        import threading
        def _play():
            for freq, ms in [(523, 80), (659, 80), (784, 80), (1047, 200)]:
                winsound.Beep(freq, ms)
        threading.Thread(target=_play, daemon=True).start()
    except Exception:
        pass
