# ui/hud.py
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QFrame, QPushButton
from PySide6.QtCore import Qt, QTimer

BG          = "#ffffff"
BORDER      = "#d0d7de"
ACCENT      = "#0969da"
TEXT_MAIN   = "#1f2328"
TEXT_DIM    = "#57606a"
SUCCESS     = "#1a7f37"
SCENE_TITLE = "#6639ba"

_CONCEPTS_NORMAL = """
    QPushButton {
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 #60a5fa, stop:1 #3b82f6);
        color: #ffffff;
        border: 2px solid #2563eb;
        border-bottom: 3px solid #1d4ed8;
        border-radius: 8px;
        padding: 6px 18px;
        font-size: 14px;
        font-weight: 700;
        min-width: 110px;
    }
    QPushButton:hover {
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 #93c5fd, stop:1 #60a5fa);
        border-color: #3b82f6;
    }
    QPushButton:pressed {
        background: #2563eb;
        border-bottom: 2px solid #1d4ed8;
        padding-top: 7px;
    }
"""

_CONCEPTS_FLASH = """
    QPushButton {
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 #22c55e, stop:1 #16a34a);
        color: #ffffff;
        border: 2px solid #15803d;
        border-bottom: 3px solid #166534;
        border-radius: 8px;
        padding: 6px 18px;
        font-size: 14px;
        font-weight: 700;
        min-width: 110px;
    }
"""


class HUDBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(56)
        self.setStyleSheet(f"""
            HUDBar {{
                background: {BG};
                border-bottom: 1px solid {BORDER};
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 0, 20, 0)
        layout.setSpacing(0)

        # Logo
        self._logo = QLabel("NEXUS")
        self._logo.setStyleSheet(f"""
            color: {ACCENT};
            font-size: 16px;
            font-weight: 800;
            letter-spacing: 4px;
        """)
        layout.addWidget(self._logo)

        layout.addSpacing(20)
        layout.addWidget(self._vsep())
        layout.addSpacing(20)

        # Scene name
        self._scene_label = QLabel("Your Desk — Analytics Department")
        self._scene_label.setStyleSheet(f"""
            color: {SCENE_TITLE};
            font-size: 15px;
            font-weight: 600;
        """)
        layout.addWidget(self._scene_label)

        layout.addStretch()

        # Clue count
        self._clue_label = QLabel("🔍  0 clues found")
        self._clue_label.setStyleSheet(f"color: {TEXT_DIM}; font-size: 13px;")
        layout.addWidget(self._clue_label)

        layout.addSpacing(20)
        layout.addWidget(self._vsep())
        layout.addSpacing(20)

        # Progress
        self._progress_label = QLabel("0% complete")
        self._progress_label.setStyleSheet(f"color: {TEXT_DIM}; font-size: 13px;")
        layout.addWidget(self._progress_label)

        layout.addSpacing(20)
        layout.addWidget(self._vsep())
        layout.addSpacing(16)

        guide_qss = """
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #fbbf24, stop:1 #f59e0b);
                color: #78350f;
                border: 2px solid #d97706;
                border-bottom: 3px solid #b45309;
                border-radius: 8px;
                padding: 6px 18px;
                font-size: 14px;
                font-weight: 700;
                min-width: 120px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #fcd34d, stop:1 #fbbf24);
                border-color: #f59e0b;
            }
            QPushButton:pressed {
                background: #d97706;
                border-bottom: 2px solid #b45309;
                padding-top: 7px;
            }
        """

        # Field Guide button
        self.docs_btn = QPushButton("📄  Field Guide")
        self.docs_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.docs_btn.setStyleSheet(guide_qss)
        layout.addWidget(self.docs_btn)

        layout.addSpacing(10)

        # Concepts button (was Codex)
        self.codex_btn = QPushButton("◆  Concepts")   # keep attribute name for compat
        self.codex_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.codex_btn.setStyleSheet(_CONCEPTS_NORMAL)
        layout.addWidget(self.codex_btn)

        # Flash state
        self._flash_count = 0
        self._flash_timer = QTimer(self)
        self._flash_timer.timeout.connect(self._do_flash)

    def set_scene(self, title):
        self._scene_label.setText(title)

    def set_clues(self, count):
        noun = "clue" if count == 1 else "clues"
        self._clue_label.setText(f"🔍  {count} {noun} found")
        color = SUCCESS if count > 0 else TEXT_DIM
        weight = "700" if count > 0 else "400"
        self._clue_label.setStyleSheet(f"color: {color}; font-size: 13px; font-weight: {weight};")

    def set_progress(self, pct):
        self._progress_label.setText(f"{pct}% complete")
        if pct == 100:
            self._progress_label.setStyleSheet(f"color: {SUCCESS}; font-size: 13px; font-weight: 700;")

    def flash_concept_btn(self) -> None:
        """Flash the Concepts button green several times to signal a new unlock."""
        self._flash_count = 0
        if not self._flash_timer.isActive():
            self._flash_timer.start(180)

    def _do_flash(self):
        MAX = 10   # 5 on/off cycles
        if self._flash_count >= MAX:
            self._flash_timer.stop()
            self.codex_btn.setStyleSheet(_CONCEPTS_NORMAL)
            return
        if self._flash_count % 2 == 0:
            self.codex_btn.setStyleSheet(_CONCEPTS_FLASH)
        else:
            self.codex_btn.setStyleSheet(_CONCEPTS_NORMAL)
        self._flash_count += 1

    def _vsep(self):
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setFixedWidth(1)
        sep.setFixedHeight(22)
        sep.setStyleSheet(f"background: {BORDER}; border: none;")
        return sep
