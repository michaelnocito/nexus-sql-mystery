# ui/celebrations.py
# Celebration effects — toast banners, screen flash, particles, and system beep.
# Keeps the dopamine loop tight without being obnoxious.
#
# Toast: center-screen, large, 10s persist with close button.
# Particles: burst of rising sparkle dots on milestone.
# Flash: brief full-screen color wash.

from PySide6.QtWidgets import QLabel, QWidget, QGraphicsOpacityEffect, QPushButton, QVBoxLayout, QHBoxLayout
from PySide6.QtCore import (
    Qt, QTimer, QPropertyAnimation, QEasingCurve,
    QPoint, QSequentialAnimationGroup, QParallelAnimationGroup,
    QPointF, QRectF,
    Property,
)
from PySide6.QtGui import QFont, QColor, QPainter, QBrush, QPen, QRadialGradient
import random
import math


# ── Colors ────────────────────────────────────────────────────────────────────

SUCCESS_BG     = "#dcfce7"
SUCCESS_BORDER = "#16a34a"
SUCCESS_TEXT   = "#15803d"
GOLD_BG        = "#fef9c3"
GOLD_BORDER    = "#ca8a04"
GOLD_TEXT      = "#854d0e"
PANEL_BG       = "#ffffff"
ACCENT         = "#0969da"


# ── Motivational messages ────────────────────────────────────────────────────

CAREER_MESSAGES = [
    "You're building real skills. This is how analysts think.",
    "That query? Senior devs write that exact pattern every day.",
    "You just did something most people never learn. Keep going.",
    "LinkedIn can wait. You're actually learning something useful.",
    "Somewhere, a spreadsheet just shed a tear of joy.",
    "Fun fact: you now know more SQL than 90% of MBA graduates.",
    "Your future self is going to thank you for this.",
    "That wasn't luck. That was understanding.",
    "You're not just playing a game. You're building a career.",
    "Data analyst energy: confirmed.",
]

MILESTONE_MESSAGES = [
    "Okay, you're officially dangerous with a database now.",
    "Three clues deep. The CFO should be worried.",
    "You're on a roll. The data doesn't stand a chance.",
    "At this rate, HR is going to offer you a raise before lunch.",
    "You're finding clues faster than Marcus can hide them.",
    "Half the analysts I know couldn't do that. Seriously.",
]

FINAL_MESSAGES = [
    "You just solved a $1.87M fraud case. With SQL. On your first day.",
    "Rachel Kim is going to remember your name.",
]


# ── Particle Effect ──────────────────────────────────────────────────────────

class ParticleOverlay(QWidget):
    """
    Burst of rising sparkle particles on milestone achievements.
    Feels like career growth confetti — upward-rising dots that
    fade and spread, like ideas taking flight.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self._particles = []
        self._timer = QTimer(self)
        self._timer.setInterval(30)
        self._timer.timeout.connect(self._tick)
        self.hide()

    def burst(self, style: str = "success"):
        """Launch a burst of particles from the center of the parent."""
        pw = self.parent().width()
        ph = self.parent().height()
        self.setGeometry(0, 0, pw, ph)

        # Color palette based on style
        if style == "gold":
            colors = [
                QColor("#fbbf24"), QColor("#f59e0b"), QColor("#d97706"),
                QColor("#92400e"), QColor("#fef08a"), QColor("#fcd34d"),
            ]
        elif style == "final":
            colors = [
                QColor("#22c55e"), QColor("#16a34a"), QColor("#fbbf24"),
                QColor("#3b82f6"), QColor("#8b5cf6"), QColor("#ef4444"),
                QColor("#ec4899"), QColor("#f97316"),
            ]
        else:
            colors = [
                QColor("#22c55e"), QColor("#16a34a"), QColor("#4ade80"),
                QColor("#86efac"), QColor("#15803d"),
            ]

        # Spawn particles from center-bottom area
        cx = pw // 2
        cy = int(ph * 0.55)
        count = 35 if style == "final" else 20

        self._particles = []
        for _ in range(count):
            angle = random.uniform(-math.pi * 0.8, -math.pi * 0.2)  # mostly upward
            speed = random.uniform(3, 9)
            self._particles.append({
                "x": cx + random.randint(-80, 80),
                "y": cy + random.randint(-20, 20),
                "vx": math.cos(angle) * speed,
                "vy": math.sin(angle) * speed - random.uniform(1, 4),
                "size": random.uniform(4, 10),
                "color": random.choice(colors),
                "alpha": 255,
                "decay": random.uniform(3, 7),
                "gravity": random.uniform(0.02, 0.08),
            })

        self.show()
        self.raise_()
        self._timer.start()

    def _tick(self):
        alive = False
        for p in self._particles:
            p["x"] += p["vx"]
            p["vy"] += p["gravity"]
            p["y"] += p["vy"]
            p["alpha"] = max(0, p["alpha"] - p["decay"])
            p["size"] = max(0, p["size"] - 0.05)
            if p["alpha"] > 0:
                alive = True
        self.update()
        if not alive:
            self._timer.stop()
            self.hide()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        for pt in self._particles:
            if pt["alpha"] <= 0:
                continue
            c = QColor(pt["color"])
            c.setAlpha(int(pt["alpha"]))
            # Glow effect: draw a larger faded circle behind
            glow = QColor(c)
            glow.setAlpha(int(pt["alpha"] * 0.3))
            p.setBrush(QBrush(glow))
            p.setPen(Qt.PenStyle.NoPen)
            gs = pt["size"] * 2.5
            p.drawEllipse(QPointF(pt["x"], pt["y"]), gs, gs)
            # Core dot
            p.setBrush(QBrush(c))
            p.drawEllipse(QPointF(pt["x"], pt["y"]), pt["size"], pt["size"])
        p.end()


# ── Toast Banner ─────────────────────────────────────────────────────────────

class ToastBanner(QWidget):
    """
    Center-screen celebration banner with close button.
    Large, bold, eye-level. Persists for 10 seconds with manual dismiss option.
    Career growth messaging and fun jokes.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(520)
        self.hide()

        self._opacity = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self._opacity)
        self._opacity.setOpacity(0.0)

        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Main label (achievement text)
        self._label = QLabel()
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label.setWordWrap(True)
        layout.addWidget(self._label)

        # Motivational subtext
        self._subtext = QLabel()
        self._subtext.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._subtext.setWordWrap(True)
        layout.addWidget(self._subtext)

        # Close button row
        btn_row = QHBoxLayout()
        btn_row.setContentsMargins(0, 8, 0, 0)
        btn_row.addStretch()
        self._close_btn = QPushButton("Keep going  ➜")
        self._close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._close_btn.clicked.connect(self._dismiss)
        btn_row.addWidget(self._close_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

    def show_toast(self, text: str, style: str = "success", duration: int = 10000,
                   subtext: str = ""):
        """Show a center-screen celebration banner."""
        if style == "gold":
            bg, border, fg = GOLD_BG, GOLD_BORDER, GOLD_TEXT
            sub_color = "#92400e"
            if not subtext:
                subtext = random.choice(MILESTONE_MESSAGES)
        elif style == "final":
            bg, border, fg = "#f0fdf4", "#16a34a", "#15803d"
            sub_color = "#166534"
            if not subtext:
                subtext = random.choice(FINAL_MESSAGES)
            duration = 15000
        else:
            bg, border, fg = SUCCESS_BG, SUCCESS_BORDER, SUCCESS_TEXT
            sub_color = "#166534"
            if not subtext:
                subtext = random.choice(CAREER_MESSAGES)

        self._label.setText(text)
        self._label.setStyleSheet(f"""
            color: {fg};
            font-size: 18px;
            font-weight: 800;
            padding: 8px 16px 4px 16px;
            background: transparent;
        """)

        self._subtext.setText(subtext)
        self._subtext.setStyleSheet(f"""
            color: {sub_color};
            font-size: 13px;
            font-style: italic;
            padding: 2px 16px 4px 16px;
            background: transparent;
        """)

        self._close_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {fg};
                border: 1px solid {border};
                border-radius: 5px;
                padding: 5px 18px;
                font-size: 12px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background: {fg};
                color: {bg};
            }}
        """)

        self.setStyleSheet(f"""
            QWidget {{
                background: {bg};
                border: 2px solid {border};
                border-radius: 12px;
            }}
        """)

        # Position: center of parent, vertically at eye level (~45% from top)
        pw = self.parent().width()
        ph = self.parent().height()
        self.setFixedWidth(min(520, pw - 60))
        self.adjustSize()

        x = (pw - self.width()) // 2
        y = int(ph * 0.38) - self.height() // 2

        self.move(x, y + 30)  # start slightly below final position
        self.show()
        self.raise_()

        # ── Animation: scale up from below + fade in ─────────────────────
        group = QParallelAnimationGroup(self)

        # Slide up
        slide = QPropertyAnimation(self, b"pos")
        slide.setDuration(400)
        slide.setEasingCurve(QEasingCurve.Type.OutBack)
        slide.setStartValue(QPoint(x, y + 30))
        slide.setEndValue(QPoint(x, y))
        group.addAnimation(slide)

        # Fade in
        fade_in = QPropertyAnimation(self._opacity, b"opacity")
        fade_in.setDuration(300)
        fade_in.setStartValue(0.0)
        fade_in.setEndValue(1.0)
        group.addAnimation(fade_in)

        group.start()
        self._enter_anim = group

        # Auto-dismiss after duration
        self._auto_dismiss = QTimer(self)
        self._auto_dismiss.setSingleShot(True)
        self._auto_dismiss.setInterval(duration)
        self._auto_dismiss.timeout.connect(self._dismiss)
        self._auto_dismiss.start()

    def _dismiss(self):
        """Fade out and hide."""
        if self._auto_dismiss.isActive():
            self._auto_dismiss.stop()

        fade_out = QPropertyAnimation(self._opacity, b"opacity")
        fade_out.setDuration(300)
        fade_out.setStartValue(1.0)
        fade_out.setEndValue(0.0)
        fade_out.finished.connect(self.hide)
        fade_out.start()
        self._fade_anim = fade_out


# ── Screen Flash ─────────────────────────────────────────────────────────────

class ScreenFlash(QWidget):
    """
    A full-parent overlay that flashes a color and fades out.
    Used on objective completion — brief green pulse.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._color = QColor(22, 163, 74, 0)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.hide()

    def flash(self, hex_color: str = "#16a34a", peak_alpha: int = 40, duration: int = 500):
        """Brief color wash over the parent widget."""
        self._color = QColor(hex_color)
        self._color.setAlpha(peak_alpha)

        self.setGeometry(0, 0, self.parent().width(), self.parent().height())
        self.show()
        self.raise_()

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


# ── System beep (cross-platform) ────────────────────────────────────────────

def play_chime():
    """Play a brief system notification sound. Non-blocking."""
    try:
        import winsound
        winsound.Beep(800, 80)
    except Exception:
        pass


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
