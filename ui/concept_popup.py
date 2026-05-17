# ui/concept_popup.py
# ConceptPopup — the "concept card" that slides in after an objective is met.
# Teaches the SQL/Python concept the player just used.
# Dismissed by pressing Enter, clicking the button, or pressing Escape.

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QSizePolicy, QScrollArea, QWidget,
)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QRect, QSize
from PySide6.QtGui import QFont, QColor, QPalette, QKeySequence, QShortcut


DARK_BG    = "#f6f8fa"
PANEL_BG   = "#ffffff"
BORDER     = "#d0d7de"
ACCENT     = "#0969da"
TEXT_MAIN  = "#1f2328"
TEXT_DIM   = "#57606a"
SUCCESS    = "#1a7f37"
WARNING    = "#9a6700"
CODE_BG    = "#eaeef2"


POPUP_QSS = f"""
QDialog {{
    background: {PANEL_BG};
    border: 1px solid {BORDER};
    border-radius: 10px;
}}

QLabel#header {{
    color: {ACCENT};
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 2px;
}}

QLabel#title {{
    color: {TEXT_MAIN};
    font-size: 17px;
    font-weight: 700;
}}

QLabel#section_label {{
    color: {TEXT_DIM};
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 1px;
    text-transform: uppercase;
}}

QLabel#body_text {{
    color: {TEXT_MAIN};
    font-size: 13px;
    line-height: 1.5;
}}

QLabel#code_text {{
    background: {CODE_BG};
    color: {ACCENT};
    font-family: 'Consolas', 'Courier New', monospace;
    font-size: 12px;
    padding: 10px 14px;
    border-radius: 6px;
    border: 1px solid {BORDER};
}}

QFrame#analogy_box {{
    background: #fff8e6;
    border: 1px solid #f0c060;
    border-radius: 6px;
    padding: 0px;
}}

QLabel#analogy_text {{
    color: #7a4f00;
    font-size: 13px;
    font-style: italic;
    padding: 8px 12px;
}}

QLabel#gotcha_text {{
    color: #cf222e;
    font-size: 12px;
}}

QPushButton#dismiss_btn {{
    background: {ACCENT};
    color: #0d1117;
    border: none;
    border-radius: 6px;
    padding: 8px 24px;
    font-size: 13px;
    font-weight: 600;
    min-width: 120px;
}}

QPushButton#dismiss_btn:hover {{
    background: #79b8ff;
}}

QPushButton#dismiss_btn:pressed {{
    background: #4393e6;
}}
"""


class ConceptPopup(QDialog):
    """
    A floating concept card.
    Call load_concept(dict) then show_centered(parent_window) to display it.
    """

    def __init__(self, parent=None):
        super().__init__(parent, Qt.WindowType.FramelessWindowHint |
                                  Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet(POPUP_QSS)
        self.setModal(True)
        self.setFixedWidth(520)
        self.setMaximumHeight(680)

        self._build_ui()

        # Escape closes too
        esc = QShortcut(QKeySequence("Escape"), self)
        esc.activated.connect(self.accept)

        # Enter/Return also dismisses
        enter = QShortcut(QKeySequence("Return"), self)
        enter.activated.connect(self.accept)

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        # Card frame (gives us rounded corners with border)
        card = QFrame()
        card.setObjectName("card")
        card.setStyleSheet(f"""
            QFrame#card {{
                background: {PANEL_BG};
                border: 1px solid {BORDER};
                border-radius: 10px;
            }}
        """)
        outer.addWidget(card)

        # Use a scroll area INSIDE the card so tall content scrolls
        card_outer = QVBoxLayout(card)
        card_outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet(f"""
            QScrollArea {{ background: {PANEL_BG}; border: none; }}
            QScrollBar:vertical {{ width: 6px; background: {PANEL_BG}; }}
            QScrollBar::handle:vertical {{ background: {BORDER}; border-radius: 3px; min-height: 20px; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
        """)
        card_outer.addWidget(scroll)

        inner = QWidget()
        inner.setStyleSheet(f"background: {PANEL_BG};")
        scroll.setWidget(inner)

        layout = QVBoxLayout(inner)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(14)

        # ── Header row: chip + close X ───────────────────────────────────────
        header_row = QHBoxLayout()
        self._header = QLabel("CONCEPT UNLOCKED")
        self._header.setObjectName("header")
        header_row.addWidget(self._header)
        header_row.addStretch()

        close_x = QPushButton("✕")
        close_x.setFixedSize(28, 28)
        close_x.setCursor(Qt.CursorShape.PointingHandCursor)
        close_x.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {TEXT_DIM};
                border: none;
                font-size: 16px;
                font-weight: 700;
                border-radius: 14px;
            }}
            QPushButton:hover {{
                background: {BORDER};
                color: {TEXT_MAIN};
            }}
        """)
        close_x.clicked.connect(self.accept)
        header_row.addWidget(close_x)
        layout.addLayout(header_row)

        # ── STORY SO FAR — bright, unmissable recap ─────────────────────────
        self._story_box = QFrame()
        self._story_box.setStyleSheet(f"""
            QFrame {{
                background: #eff6ff;
                border: 2px solid #3b82f6;
                border-radius: 8px;
            }}
        """)
        story_layout = QVBoxLayout(self._story_box)
        story_layout.setContentsMargins(14, 10, 14, 10)
        story_layout.setSpacing(6)

        story_header = QLabel("📖  STORY SO FAR")
        story_header.setStyleSheet(f"""
            color: #1d4ed8;
            font-size: 12px;
            font-weight: 700;
            letter-spacing: 2px;
            background: transparent;
            border: none;
        """)
        story_layout.addWidget(story_header)

        self._story_text = QLabel()
        self._story_text.setWordWrap(True)
        self._story_text.setStyleSheet(f"""
            color: {TEXT_MAIN};
            font-size: 13px;
            line-height: 1.4;
            background: transparent;
            border: none;
        """)
        story_layout.addWidget(self._story_text)

        self._story_box.hide()  # hidden until populated
        layout.addWidget(self._story_box)

        # ── Title ────────────────────────────────────────────────────────────
        self._title = QLabel()
        self._title.setObjectName("title")
        self._title.setWordWrap(True)
        layout.addWidget(self._title)

        # Divider
        layout.addWidget(self._make_hsep())

        # ── WHAT ─────────────────────────────────────────────────────────────
        self._what_label = self._section("WHAT IS IT?")
        layout.addWidget(self._what_label)
        self._what = QLabel()
        self._what.setObjectName("body_text")
        self._what.setWordWrap(True)
        layout.addWidget(self._what)

        # ── WHY ──────────────────────────────────────────────────────────────
        self._why_label = self._section("WHY IT MATTERS")
        layout.addWidget(self._why_label)
        self._why = QLabel()
        self._why.setObjectName("body_text")
        self._why.setWordWrap(True)
        layout.addWidget(self._why)

        # ── SYNTAX ───────────────────────────────────────────────────────────
        self._syntax_label = self._section("SYNTAX")
        layout.addWidget(self._syntax_label)
        self._syntax = QLabel()
        self._syntax.setObjectName("code_text")
        self._syntax.setWordWrap(True)
        self._syntax.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        layout.addWidget(self._syntax)

        # ── ANALOGY ──────────────────────────────────────────────────────────
        self._analogy_label = self._section("💡  REAL-WORLD ANALOGY")
        layout.addWidget(self._analogy_label)

        analogy_box = QFrame()
        analogy_box.setObjectName("analogy_box")
        analogy_box_layout = QVBoxLayout(analogy_box)
        analogy_box_layout.setContentsMargins(0, 0, 0, 0)
        self._analogy = QLabel()
        self._analogy.setObjectName("analogy_text")
        self._analogy.setWordWrap(True)
        analogy_box_layout.addWidget(self._analogy)
        layout.addWidget(analogy_box)

        # ── GOTCHA ───────────────────────────────────────────────────────────
        self._gotcha_label = self._section("⚠  COMMON MISTAKE")
        layout.addWidget(self._gotcha_label)
        self._gotcha = QLabel()
        self._gotcha.setObjectName("gotcha_text")
        self._gotcha.setWordWrap(True)
        layout.addWidget(self._gotcha)

        layout.addSpacing(6)

        # ── Dismiss button ───────────────────────────────────────────────────
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self._btn = QPushButton("Got it — keep going")
        self._btn.setObjectName("dismiss_btn")
        self._btn.clicked.connect(self.accept)
        self._btn.setDefault(True)
        btn_row.addWidget(self._btn)
        layout.addLayout(btn_row)

    def load_concept(self, concept: dict, **kwargs) -> None:
        """Populate the card with a concept from core/codex.py.
        Optional kwargs: story_so_far (str) — narrative recap shown at top.
        """
        # Story recap — bright blue box at the top
        story = kwargs.get("story_so_far", "")
        if story:
            self._story_text.setText(story)
            self._story_box.show()
        else:
            self._story_box.hide()

        self._title.setText(concept.get("title", ""))
        self._what.setText(concept.get("what", ""))
        self._why.setText(concept.get("why", ""))
        self._syntax.setText(concept.get("syntax", ""))
        self._analogy.setText(concept.get("analogy", ""))
        self._gotcha.setText(concept.get("gotcha", ""))
        self.adjustSize()

    def show_centered(self, parent: "QWidget") -> None:
        """Center over the parent window, clamped to stay on screen."""
        self.adjustSize()

        # Center in parent
        pg = parent.geometry()
        x = pg.x() + (pg.width()  - self.width())  // 2
        y = pg.y() + (pg.height() - self.height()) // 2

        # Clamp to screen bounds so it never goes off the bottom/right
        from PySide6.QtWidgets import QApplication
        screen = QApplication.primaryScreen()
        if screen:
            avail = screen.availableGeometry()  # excludes taskbar
            # Keep at least 40px from screen edges
            x = max(avail.x() + 20, min(x, avail.right() - self.width() - 20))
            y = max(avail.y() + 20, min(y, avail.bottom() - self.height() - 20))

        self.move(x, y)

        # Slide in from slightly above
        start_y = y - 20
        anim = QPropertyAnimation(self, b"pos", self)
        anim.setDuration(180)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        from PySide6.QtCore import QPoint
        anim.setStartValue(QPoint(x, start_y))
        anim.setEndValue(QPoint(x, y))
        anim.start()
        self._anim = anim  # keep reference

        self.exec()

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _section(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setObjectName("section_label")
        return lbl

    def _make_hsep(self) -> QFrame:
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background: {BORDER}; border: none;")
        return sep
