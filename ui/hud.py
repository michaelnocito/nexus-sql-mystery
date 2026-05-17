# ui/hud.py
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QFrame, QPushButton
from PySide6.QtCore import Qt

BG          = "#ffffff"
BORDER      = "#d0d7de"
ACCENT      = "#0969da"
TEXT_MAIN   = "#1f2328"
TEXT_DIM    = "#57606a"
SUCCESS     = "#1a7f37"
SCENE_TITLE = "#6639ba"


class HUDBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(48)
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

        # Button style (reusable)
        btn_qss = f"""
            QPushButton {{
                background: transparent;
                color: {ACCENT};
                border: 1px solid {ACCENT};
                border-radius: 5px;
                padding: 4px 14px;
                font-size: 13px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background: {ACCENT};
                color: white;
            }}
        """

        # Field Guide button
        self.docs_btn = QPushButton("📄  Field Guide")
        self.docs_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.docs_btn.setStyleSheet(btn_qss)
        layout.addWidget(self.docs_btn)

        layout.addSpacing(8)

        # Codex button
        self.codex_btn = QPushButton("📖  Codex")
        self.codex_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.codex_btn.setStyleSheet(btn_qss)
        layout.addWidget(self.codex_btn)

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

    def _vsep(self):
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setFixedWidth(1)
        sep.setFixedHeight(22)
        sep.setStyleSheet(f"background: {BORDER}; border: none;")
        return sep
