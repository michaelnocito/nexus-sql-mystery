# ui/collectibles_panel.py
# CollectiblesPanel — "The Analyst's Field Guide" browsable document viewer.
#
# Styled like a parchment journal. Each scene completion unlocks a new page.
# Locked pages show as silhouettes to motivate progression.

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QScrollArea, QWidget, QPushButton,
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont, QColor


# ── Palette ──────────────────────────────────────────────────────────────────

PARCHMENT   = "#faf6ee"
PARCH_DARK  = "#e8dcc8"
INK         = "#2c1810"
INK_DIM     = "#6b5b4b"
ACCENT      = "#8b4513"    # saddle brown
ACCENT_LT   = "#cd853f"    # peru
BORDER      = "#c4b39c"
LOCKED_BG   = "#eee9df"
LOCKED_FG   = "#b8ad9c"
PANEL_BG    = "#ffffff"
TEXT_MAIN   = "#1f2328"
BLUE        = "#0969da"


PANEL_QSS = f"""
QDialog {{
    background: {PANEL_BG};
}}
QScrollArea {{
    border: none;
    background: {PANEL_BG};
}}
"""


class CollectiblesPanel(QDialog):
    """
    Modal dialog showing The Analyst's Field Guide.
    Each page is a parchment-styled card.
    """

    def __init__(self, game, all_pages, parent=None):
        super().__init__(parent)
        self._game = game
        self._all_pages = all_pages

        self.setWindowTitle("The Analyst's Field Guide")

    def set_pages(self, pages: list) -> None:
        """Swap to a different season's collectible pages."""
        self._all_pages = pages
        self.setWindowTitle("The Python Codex")
        self.setMinimumSize(QSize(560, 500))
        self.setMaximumSize(QSize(700, 800))
        self.setStyleSheet(PANEL_QSS)

        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        # Header
        header = QLabel("📄  The Analyst's Field Guide")
        header.setFont(QFont("Georgia", 18, QFont.Weight.Bold))
        header.setStyleSheet(f"color: {ACCENT}; padding-bottom: 4px;")
        layout.addWidget(header)

        subtitle = QLabel("Season 1: The Audit — Collected documents from your investigation")
        subtitle.setFont(QFont("Segoe UI", 11))
        subtitle.setStyleSheet(f"color: {INK_DIM};")
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background: {BORDER};")
        layout.addWidget(sep)

        # Scrollable page list
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self._page_container = QWidget()
        self._page_layout = QVBoxLayout(self._page_container)
        self._page_layout.setContentsMargins(0, 0, 0, 0)
        self._page_layout.setSpacing(16)

        scroll.setWidget(self._page_container)
        layout.addWidget(scroll, stretch=1)

        # Close button
        close_btn = QPushButton("Close")
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setFixedWidth(100)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background: {BLUE};
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 16px;
                font-size: 13px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background: #0550ae;
            }}
        """)
        close_btn.clicked.connect(self.close)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_row.addWidget(close_btn)
        layout.addLayout(btn_row)

    def refresh(self):
        """Rebuild the page cards based on current game state."""
        # Clear existing cards
        while self._page_layout.count():
            item = self._page_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Determine which scenes are complete
        completed_scenes = []
        for page in self._all_pages:
            if self._game.scene_complete(page["scene"]):
                completed_scenes.append(page["scene"])

        # Count stats
        unlocked = len(completed_scenes)
        total = len(self._all_pages)

        # Progress indicator
        progress = QLabel(f"📖  {unlocked} of {total} pages collected")
        progress.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        progress.setStyleSheet(f"color: {ACCENT}; padding: 4px 0;")
        self._page_layout.addWidget(progress)

        # Render each page
        for page in self._all_pages:
            is_unlocked = page["scene"] in completed_scenes
            card = self._make_page_card(page, is_unlocked)
            self._page_layout.addWidget(card)

        self._page_layout.addStretch()

    def _make_page_card(self, page: dict, unlocked: bool) -> QFrame:
        """Create a single page card — parchment style if unlocked, greyed if locked."""
        card = QFrame()
        card.setFrameShape(QFrame.Shape.StyledPanel)

        if unlocked:
            card.setStyleSheet(f"""
                QFrame {{
                    background: {PARCHMENT};
                    border: 1px solid {BORDER};
                    border-radius: 8px;
                    padding: 0;
                }}
            """)
        else:
            card.setStyleSheet(f"""
                QFrame {{
                    background: {LOCKED_BG};
                    border: 1px solid {BORDER};
                    border-radius: 8px;
                    padding: 0;
                }}
            """)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(8)

        if unlocked:
            # Title
            title = QLabel(page["title"])
            title.setFont(QFont("Georgia", 14, QFont.Weight.Bold))
            title.setStyleSheet(f"color: {ACCENT}; border: none;")
            layout.addWidget(title)

            # Subtitle
            sub = QLabel(page["subtitle"])
            sub.setFont(QFont("Georgia", 11, QFont.Weight.Normal, True))
            sub.setStyleSheet(f"color: {INK_DIM}; border: none;")
            layout.addWidget(sub)

            # Body text
            body = QLabel(page["body"])
            body.setFont(QFont("Georgia", 11))
            body.setStyleSheet(f"color: {INK}; border: none; line-height: 1.5;")
            body.setWordWrap(True)
            layout.addWidget(body)

            # Skill summary bar
            skill_bar = QFrame()
            skill_bar.setStyleSheet(f"""
                QFrame {{
                    background: {PARCH_DARK};
                    border: none;
                    border-radius: 4px;
                    padding: 0;
                }}
            """)
            sb_layout = QHBoxLayout(skill_bar)
            sb_layout.setContentsMargins(12, 8, 12, 8)

            skill_icon = QLabel("🔧")
            skill_icon.setFont(QFont("Segoe UI", 12))
            skill_icon.setStyleSheet("border: none;")
            sb_layout.addWidget(skill_icon)

            skill_text = QLabel(page["skill_summary"])
            skill_text.setFont(QFont("Consolas", 10))
            skill_text.setStyleSheet(f"color: {ACCENT}; border: none; font-weight: 600;")
            sb_layout.addWidget(skill_text)
            sb_layout.addStretch()

            layout.addWidget(skill_bar)
        else:
            # Locked page
            lock_icon = QLabel("🔒")
            lock_icon.setFont(QFont("Segoe UI", 24))
            lock_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lock_icon.setStyleSheet("border: none;")
            layout.addWidget(lock_icon)

            lock_title = QLabel(page["title"])
            lock_title.setFont(QFont("Georgia", 13, QFont.Weight.Bold))
            lock_title.setStyleSheet(f"color: {LOCKED_FG}; border: none;")
            lock_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(lock_title)

            lock_hint = QLabel("Complete this scene to unlock")
            lock_hint.setFont(QFont("Segoe UI", 10))
            lock_hint.setStyleSheet(f"color: {LOCKED_FG}; border: none;")
            lock_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(lock_hint)

        return card
