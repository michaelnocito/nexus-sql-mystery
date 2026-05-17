# ui/codex_panel.py
# CodexPanel — a browsable list of unlocked SQL concepts.
# Opens as a sidebar dialog. Each card is clickable to view the full concept popup.

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QScrollArea, QWidget, QFrame,
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont, QColor, QCursor

BG        = "#f6f8fa"
PANEL_BG  = "#ffffff"
BORDER    = "#d0d7de"
ACCENT    = "#0969da"
TEXT_MAIN = "#1f2328"
TEXT_DIM  = "#57606a"
SUCCESS   = "#1a7f37"
CODE_BG   = "#eaeef2"
LOCKED    = "#d0d7de"

PANEL_QSS = f"""
QDialog {{
    background: {BG};
}}

QScrollArea {{
    background: {BG};
    border: none;
}}

QWidget#scroll_contents {{
    background: {BG};
}}

QFrame#concept_card {{
    background: {PANEL_BG};
    border: 1px solid {BORDER};
    border-radius: 8px;
}}
QFrame#concept_card:hover {{
    border-color: {ACCENT};
    background: #f0f6ff;
}}

QFrame#locked_card {{
    background: {BG};
    border: 1px dashed {LOCKED};
    border-radius: 8px;
}}

QLabel#card_title {{
    color: {TEXT_MAIN};
    font-size: 14px;
    font-weight: 700;
}}

QLabel#card_preview {{
    color: {TEXT_DIM};
    font-size: 12px;
}}

QLabel#card_tag {{
    background: {CODE_BG};
    color: {ACCENT};
    font-family: 'Consolas', monospace;
    font-size: 11px;
    padding: 2px 7px;
    border-radius: 4px;
}}

QLabel#locked_label {{
    color: {LOCKED};
    font-size: 13px;
    font-style: italic;
}}

QPushButton#close_btn {{
    background: {PANEL_BG};
    color: {TEXT_DIM};
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 6px 20px;
    font-size: 13px;
}}
QPushButton#close_btn:hover {{
    border-color: {ACCENT};
    color: {ACCENT};
}}

QLabel#header_title {{
    color: {TEXT_MAIN};
    font-size: 18px;
    font-weight: 700;
}}

QLabel#header_sub {{
    color: {TEXT_DIM};
    font-size: 13px;
}}
"""


class CodexPanel(QDialog):
    """
    Floating codex browser.
    Shows all concepts as cards — unlocked ones are clickable, locked ones are greyed out.
    """

    def __init__(self, game, all_concepts, show_concept_fn, parent=None):
        super().__init__(parent, Qt.WindowType.Dialog)
        self.setWindowTitle("Codex — SQL Concepts")
        self.setMinimumSize(QSize(540, 620))
        self.resize(560, 680)
        self.setStyleSheet(PANEL_QSS)

        self._game = game
        self._all_concepts = all_concepts      # list of dicts from codex.py
        self._show_concept = show_concept_fn   # callable(concept_dict)

        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Header ───────────────────────────────────────────────────────────
        header = QWidget()
        header.setStyleSheet(f"background: {PANEL_BG}; border-bottom: 1px solid {BORDER};")
        hl = QVBoxLayout(header)
        hl.setContentsMargins(24, 18, 24, 14)
        hl.setSpacing(2)

        title = QLabel("📖  Codex")
        title.setObjectName("header_title")
        hl.addWidget(title)

        self._sub = QLabel("0 concepts unlocked")
        self._sub.setObjectName("header_sub")
        hl.addWidget(self._sub)

        layout.addWidget(header)

        # ── Scrollable card list ──────────────────────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        contents = QWidget()
        contents.setObjectName("scroll_contents")
        self._cards_layout = QVBoxLayout(contents)
        self._cards_layout.setContentsMargins(20, 16, 20, 16)
        self._cards_layout.setSpacing(10)
        self._cards_layout.addStretch()

        scroll.setWidget(contents)
        layout.addWidget(scroll, stretch=1)

        # ── Footer ───────────────────────────────────────────────────────────
        footer = QWidget()
        footer.setStyleSheet(f"background: {PANEL_BG}; border-top: 1px solid {BORDER};")
        fl = QHBoxLayout(footer)
        fl.setContentsMargins(20, 12, 20, 12)
        fl.addStretch()
        close_btn = QPushButton("Close")
        close_btn.setObjectName("close_btn")
        close_btn.clicked.connect(self.accept)
        fl.addWidget(close_btn)
        layout.addWidget(footer)

    def refresh(self):
        """Rebuild the card list from current game state."""
        unlocked = set(self._game.completed)
        # Count unlocked concepts
        unlocked_concepts = [c for c in self._all_concepts
                             if c["id"] in {o.get("concept") for o in
                                            self._get_completed_objectives()}]
        self._sub.setText(f"{len(unlocked_concepts)} of {len(self._all_concepts)} concepts unlocked")

        # Clear existing cards (keep the stretch at end)
        while self._cards_layout.count() > 1:
            item = self._cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Completed objective → concept mapping
        completed_concepts = {
            obj.get("concept")
            for obj in self._get_completed_objectives()
        }

        # Build cards
        for concept in self._all_concepts:
            is_unlocked = concept["id"] in completed_concepts
            card = self._make_card(concept, is_unlocked)
            self._cards_layout.insertWidget(self._cards_layout.count() - 1, card)

    def _get_completed_objectives(self):
        from core.game import OBJECTIVES_BY_ID
        from core.season2_game import S2_OBJECTIVES_BY_ID
        combined = {**OBJECTIVES_BY_ID, **S2_OBJECTIVES_BY_ID}
        return [combined[oid] for oid in self._game.completed
                if oid in OBJECTIVES_BY_ID]

    def _make_card(self, concept: dict, unlocked: bool) -> QFrame:
        card = QFrame()
        card.setObjectName("concept_card" if unlocked else "locked_card")
        card.setFixedHeight(82)

        layout = QHBoxLayout(card)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)

        left = QVBoxLayout()
        left.setSpacing(4)

        if unlocked:
            title = QLabel(concept["title"])
            title.setObjectName("card_title")
            left.addWidget(title)

            preview = QLabel(concept["what"][:70] + ("…" if len(concept["what"]) > 70 else ""))
            preview.setObjectName("card_preview")
            preview.setWordWrap(True)
            left.addWidget(preview)
        else:
            lbl = QLabel("🔒  Not yet unlocked")
            lbl.setObjectName("locked_label")
            left.addWidget(lbl)
            hint = QLabel("Keep investigating to discover this concept.")
            hint.setObjectName("card_preview")
            left.addWidget(hint)

        layout.addLayout(left, stretch=1)

        if unlocked:
            # SQL tag chip
            right = QVBoxLayout()
            right.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)
            tag = QLabel("SQL")
            tag.setObjectName("card_tag")
            tag.setAlignment(Qt.AlignmentFlag.AlignCenter)
            right.addWidget(tag)
            layout.addLayout(right)

            # Make whole card clickable
            card.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            card.mousePressEvent = lambda e, c=concept: self._on_card_click(c)

        return card

    def _on_card_click(self, concept: dict):
        self._show_concept(concept)

    def showEvent(self, event):
        self.refresh()
        super().showEvent(event)
