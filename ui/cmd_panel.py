# ui/cmd_panel.py
# CmdPanel — narrative output + focus box + input bar.
#
# Key design principle: story text uses a readable sans-serif (Segoe UI 15px).
# Code output (SQL results, echoed commands) uses monospace with a tinted bg.
# Clues and objectives are visually bold and distinct — never lost in the wall of text.

import sys
import io
import traceback

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit,
    QLabel, QFrame, QPushButton, QScrollArea, QSizePolicy,
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import (
    QFont, QTextCursor, QColor, QTextCharFormat,
    QTextBlockFormat, QPixmap,
)
from ui.sql_editor import SQLEditor
from ui.portraits import npc_portrait, npc_color, canonical
from ui.terminal_widget import TerminalWidget

# ── Palette (light) ───────────────────────────────────────────────────────────

BG          = "#f6f8fa"
PANEL_BG    = "#ffffff"
BORDER      = "#d0d7de"
ACCENT      = "#0969da"
TEXT_MAIN   = "#1f2328"
TEXT_DIM    = "#57606a"
SUCCESS     = "#1a7f37"
ERROR_COL   = "#cf222e"
WARNING     = "#9a6700"
SCENE_COL   = "#6639ba"
GUIDANCE    = "#0550ae"
CODE_BG     = "#eaeef2"
INPUT_BG    = "#ffffff"
CLUE_COL    = "#1a7f37"
PANEL_QSS = f"""
QTextEdit#narrative {{
    background: {PANEL_BG};
    color: {TEXT_MAIN};
    border: none;
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 15px;
    padding: 20px 24px;
    selection-background-color: #b6d4fb;
}}

QFrame#focus_frame {{
    background: {CODE_BG};
    border-top: 1px solid {BORDER};
    border-bottom: 1px solid {BORDER};
}}

QLabel#focus_label {{
    color: {TEXT_DIM};
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 2px;
}}

QLabel#focus_cmd {{
    background: {PANEL_BG};
    color: {ACCENT};
    font-family: 'Consolas', 'Courier New', monospace;
    font-size: 14px;
    font-weight: 600;
    padding: 6px 10px;
    border: 1px solid {BORDER};
    border-radius: 5px;
}}

QPushButton#reveal_btn {{
    background: transparent;
    color: {ACCENT};
    border: 1px solid {ACCENT};
    border-radius: 5px;
    padding: 3px 12px;
    font-size: 12px;
    font-weight: 600;
}}
QPushButton#reveal_btn:hover {{
    background: {ACCENT};
    color: {PANEL_BG};
}}

QPushButton#copy_btn {{
    background: {PANEL_BG};
    color: {TEXT_DIM};
    border: 1px solid {BORDER};
    border-radius: 5px;
    padding: 3px 10px;
    font-size: 12px;
}}
QPushButton#copy_btn:hover {{
    color: {ACCENT};
    border-color: {ACCENT};
}}

QFrame#input_frame {{
    background: {INPUT_BG};
    border-top: 2px solid {ACCENT};
}}

QLabel#prompt_label {{
    color: {ACCENT};
    font-family: 'Consolas', 'Courier New', monospace;
    font-size: 14px;
    font-weight: 700;
}}

QPushButton#hint_btn {{
    background: transparent;
    color: {TEXT_DIM};
    border: 1px solid {BORDER};
    border-radius: 5px;
    padding: 5px 14px;
    font-size: 12px;
    margin-right: 10px;
}}
QPushButton#hint_btn:hover {{
    color: {WARNING};
    border-color: {WARNING};
    background: #fff8e6;
}}
"""


# Message rendering is now widget-based (see _make_text / _make_dialogue).
# The old QTextCharFormat STYLES map was removed with the QTextEdit flow.


class CmdPanel(QWidget):

    def __init__(self, game, db, parent=None):
        super().__init__(parent)
        self._game = game
        self._db   = db
        self.setStyleSheet(PANEL_QSS)

        self._pending_reset: bool = False
        self._exec_ns = self._build_namespace()
        self._current_concept: dict = {}  # Track the persistent concept card

        # Right panel persistent data
        self._investigation_log = []
        self._your_move = ""
        self._progress_pct = 0
        self._goal = ""

        self._build_ui()

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ── TOP SECTION: Three-column split (left: story/narrative/focus, center: results, right: concept) ────
        top_split = QHBoxLayout()
        top_split.setContentsMargins(0, 0, 0, 0)
        top_split.setSpacing(0)

        # ── LEFT SIDE: Unified conversation thread (narrator + Sam + activity) ──
        left_section = QVBoxLayout()
        left_section.setContentsMargins(0, 0, 0, 0)
        left_section.setSpacing(0)

        # ── Hidden story state (kept for set_story() compatibility) ───────────
        self._story_why    = QLabel()
        self._story_beat   = QLabel()
        self._story_recall = QLabel()
        self._story_recall.hide()
        self._beat_scroll  = QScrollArea()  # stub for scroll-reset calls
        self._narrator_text = QLabel()      # stub kept for set_narrator() compat

        # ── Conversation scroll — ONE unified thread ─────────────────────────
        # Narrator (Diana), Sam, command echoes, success/hint messages all live
        # here in chronological order, like a messaging thread.
        self._scroll = QScrollArea()
        self._scroll.setObjectName("msg_scroll")
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._scroll.setStyleSheet(
            f"QScrollArea#msg_scroll {{ background: {BG}; border: none; border-right: 1px solid {BORDER}; }}"
            f"QWidget#msg_container {{ background: {BG}; }}"
        )

        self._msg_container = QWidget()
        self._msg_container.setObjectName("msg_container")
        self._msg_layout = QVBoxLayout(self._msg_container)
        self._msg_layout.setContentsMargins(14, 16, 14, 16)
        self._msg_layout.setSpacing(10)
        self._msg_layout.addStretch(1)   # messages stack from top

        self._scroll.setWidget(self._msg_container)
        left_section.addWidget(self._scroll, stretch=1)

        # Max width for dialogue bubbles
        self._msg_max_w = 420

        # ── Focus command box (at bottom of left column) ──────────────────────
        self._focus_frame = QFrame()
        self._focus_frame.setObjectName("focus_frame")
        fl = QVBoxLayout(self._focus_frame)
        fl.setContentsMargins(14, 10, 14, 10)
        fl.setSpacing(6)

        top_row = QHBoxLayout()
        top_row.setSpacing(8)

        self._focus_label = QLabel("TRY THIS FIRST:")
        self._focus_label.setObjectName("focus_label")
        top_row.addWidget(self._focus_label)
        top_row.addStretch()

        self._reveal_btn = QPushButton("show solution →")
        self._reveal_btn.setObjectName("reveal_btn")
        self._reveal_btn.setFixedHeight(24)
        self._reveal_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._reveal_btn.clicked.connect(self._toggle_reveal)
        top_row.addWidget(self._reveal_btn)

        self._copy_btn = QPushButton("copy")
        self._copy_btn.setObjectName("copy_btn")
        self._copy_btn.setFixedHeight(24)
        self._copy_btn.clicked.connect(self._copy_focus)
        self._copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._copy_btn.hide()
        top_row.addWidget(self._copy_btn)
        fl.addLayout(top_row)

        self._focus_cmd = QLabel("")
        self._focus_cmd.setObjectName("focus_cmd")
        self._focus_cmd.setWordWrap(True)
        self._focus_cmd.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self._focus_cmd.hide()
        fl.addWidget(self._focus_cmd)

        self._solution_revealed = False
        self._focus_frame.adjustSize()
        left_section.addWidget(self._focus_frame)

        # Left column — equal width to right, conversation thread
        top_split.addLayout(left_section, stretch=2)

        # ── CENTER COLUMN: Cartoon terminal monitor (the centerpiece) ────────────
        self._results_frame = TerminalWidget()
        self._results_frame.setMinimumWidth(320)
        # Alias for write methods
        self._terminal = self._results_frame
        # Keep stub for legacy _results_label references
        self._results_label = QLabel()

        # Show from the start — idle screen with blinking cursor
        top_split.addWidget(self._results_frame, stretch=4)

        # ── RIGHT SIDE: Persistent tracking panel (Investigation Log, Your Move, Progress, Goal, Concept) ────
        self._right_frame = QFrame()
        self._right_frame.setObjectName("right_frame")
        self._right_frame.setStyleSheet(f"""
            QFrame#right_frame {{
                background: {PANEL_BG};
                border-left: 1px solid {BORDER};
            }}
        """)
        self._right_frame.setMinimumWidth(240)

        right_layout = QVBoxLayout(self._right_frame)
        right_layout.setContentsMargins(12, 12, 12, 12)
        right_layout.setSpacing(8)

        # ── Investigation Log ─────────────────────────────────────────────────
        inv_header = QLabel("INVESTIGATION LOG")
        inv_header.setStyleSheet(f"""
            color: {TEXT_DIM};
            font-size: 10px;
            font-weight: 700;
            letter-spacing: 1px;
        """)
        right_layout.addWidget(inv_header)

        self._inv_log = QLabel("")
        self._inv_log.setWordWrap(True)
        self._inv_log.setStyleSheet(f"""
            color: {SUCCESS};
            font-size: 13px;
            font-weight: 600;
        """)
        right_layout.addWidget(self._inv_log)

        # ── Your Move ─────────────────────────────────────────────────────────
        move_header = QLabel("YOUR MOVE")
        move_header.setStyleSheet(f"""
            color: {TEXT_DIM};
            font-size: 10px;
            font-weight: 700;
            letter-spacing: 1px;
            margin-top: 8px;
        """)
        right_layout.addWidget(move_header)

        self._your_move_label = QLabel("")
        self._your_move_label.setWordWrap(True)
        self._your_move_label.setStyleSheet(f"""
            color: {TEXT_MAIN};
            font-size: 13px;
            font-weight: 600;
        """)
        right_layout.addWidget(self._your_move_label)

        # ── Progress Bar ──────────────────────────────────────────────────────
        self._progress_bar = QFrame()
        self._progress_bar.setStyleSheet(f"""
            QFrame {{
                background: {CODE_BG};
                border: 1px solid {BORDER};
                border-radius: 3px;
            }}
        """)
        self._progress_bar.setFixedHeight(8)
        right_layout.addWidget(self._progress_bar)

        self._progress_label = QLabel("0%")
        self._progress_label.setStyleSheet(f"""
            color: {TEXT_DIM};
            font-size: 10px;
        """)
        right_layout.addWidget(self._progress_label)

        # ── Goal ──────────────────────────────────────────────────────────────
        goal_header = QLabel("GOAL")
        goal_header.setStyleSheet(f"""
            color: {TEXT_DIM};
            font-size: 10px;
            font-weight: 700;
            letter-spacing: 1px;
            margin-top: 8px;
        """)
        right_layout.addWidget(goal_header)

        self._goal_label = QLabel("")
        self._goal_label.setWordWrap(True)
        self._goal_label.setStyleSheet(f"""
            color: {TEXT_MAIN};
            font-size: 13px;
            font-weight: 600;
        """)
        right_layout.addWidget(self._goal_label)

        # Stretch to fill remaining right panel space
        right_layout.addStretch(1)

        # Hidden stub so append_concept() doesn't crash
        self._concept_label = QLabel()
        self._concept_label.hide()

        top_split.addWidget(self._right_frame, stretch=2)  # equal to left column

        # Add top split to main layout
        main_layout.addLayout(top_split, stretch=1)

        # ── SQL Editor input (full width, at bottom) ──────────────────────────
        input_frame = QFrame()
        input_frame.setObjectName("input_frame")
        input_layout = QVBoxLayout(input_frame)
        input_layout.setContentsMargins(0, 0, 0, 0)
        input_layout.setSpacing(0)

        # Top bar: prompt label + shortcut hints + hint button
        bar = QHBoxLayout()
        bar.setContentsMargins(12, 6, 12, 2)
        bar.setSpacing(8)

        prompt = QLabel(">>>  SQL Editor")
        prompt.setObjectName("prompt_label")
        bar.addWidget(prompt)
        bar.addStretch()

        shortcuts_label = QLabel("Ctrl+Enter run  ·  Ctrl+H hint  ·  Ctrl+S solution  ·  Ctrl+D copy")
        shortcuts_label.setStyleSheet(f"color: {TEXT_DIM}; font-size: 10px; font-style: italic;")
        bar.addWidget(shortcuts_label)

        self._hint_btn = QPushButton("💡  Hint")
        self._hint_btn.setObjectName("hint_btn")
        self._hint_btn.setFixedHeight(32)
        self._hint_btn.setMinimumWidth(90)
        self._hint_btn.setStyleSheet(f"""
            QPushButton#hint_btn {{
                background: #fff8e6;
                color: {WARNING};
                border: 2px solid {WARNING};
                border-radius: 7px;
                padding: 4px 16px;
                font-size: 13px;
                font-weight: 700;
            }}
            QPushButton#hint_btn:hover {{
                background: {WARNING};
                color: #ffffff;
            }}
        """)
        self._hint_btn.clicked.connect(self._on_hint)
        self._hint_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        bar.addWidget(self._hint_btn)
        input_layout.addLayout(bar)

        # The actual editor
        self._editor = SQLEditor()
        self._editor.setMinimumHeight(100)
        self._editor.setMaximumHeight(200)
        self._editor.execute_requested.connect(self._on_execute)
        input_layout.addWidget(self._editor)

        main_layout.addWidget(input_frame)

        # ── Keyboard shortcuts ───────────────────────────────────────────────
        from PySide6.QtGui import QShortcut, QKeySequence
        hint_shortcut = QShortcut(QKeySequence("Ctrl+H"), self)
        hint_shortcut.activated.connect(self._on_hint)

        reveal_shortcut = QShortcut(QKeySequence("Ctrl+S"), self)
        reveal_shortcut.activated.connect(self._toggle_reveal)

        copy_shortcut = QShortcut(QKeySequence("Ctrl+D"), self)
        copy_shortcut.activated.connect(self._copy_focus)

        QTimer.singleShot(0, self._editor.setFocus)

    # ── Right Panel Persistence (Investigation Log, Your Move, Progress, Goal) ─

    def set_investigation_log(self, items: list) -> None:
        """Update the Investigation Log with completed actions."""
        self._investigation_log = items
        log_text = "\n".join(f"✓ {item}" for item in items) if items else ""
        self._inv_log.setText(log_text)

    def set_your_move(self, text: str) -> None:
        """Set the current 'Your Move' objective."""
        self._your_move = text
        self._your_move_label.setText(text)

    def set_progress(self, percent: int) -> None:
        """Update the progress bar (0-100)."""
        self._progress_pct = max(0, min(100, percent))
        self._progress_label.setText(f"{self._progress_pct}%")

        # Visually fill the progress bar
        filled_width = int(330 * self._progress_pct / 100)  # Approximate bar width
        self._progress_bar.setStyleSheet(f"""
            QFrame {{
                background: linear-gradient(to right, #1a7f37 {self._progress_pct}%, #eaeef2 {self._progress_pct}%);
                border: 1px solid {BORDER};
                border-radius: 3px;
            }}
        """)

    def set_goal(self, text: str) -> None:
        """Set the scene goal text."""
        self._goal = text
        self._goal_label.setText(text)

    def set_narrator(self, text: str) -> None:
        """Set the narrator dialogue (Day One narrative)."""
        self._narrator_text.setText(text)

    # ── Focus ─────────────────────────────────────────────────────────────────

    def set_focus(self, label, command):
        self._focus_label.setText(label.upper() if label else "TRY THIS:")
        self._focus_cmd.setText(command)
        self._focus_frame.setVisible(bool(command))
        # Reset toggle state when focus changes (new objective)
        self._solution_revealed = False
        self._focus_cmd.hide()
        self._copy_btn.hide()
        self._reveal_btn.setText("show solution →")
        self._reveal_btn.show()

    def _toggle_reveal(self):
        if not self._focus_frame.isVisible():
            return
        self._solution_revealed = not self._solution_revealed
        if self._solution_revealed:
            self._focus_cmd.show()
            self._copy_btn.show()
            self._reveal_btn.setText("← hide solution")
        else:
            self._focus_cmd.hide()
            self._copy_btn.hide()
            self._reveal_btn.setText("show solution →")

    def _copy_focus(self):
        from PySide6.QtWidgets import QApplication
        cmd = self._focus_cmd.text()
        if cmd:
            QApplication.clipboard().setText(cmd)
            self._copy_btn.setText("copied!")
            QTimer.singleShot(1500, lambda: self._copy_btn.setText("copy"))

    # ── Output ────────────────────────────────────────────────────────────────

    # Map legacy on_output styles → message channel
    _STYLE_KIND = {
        "scene":    "narration",
        "normal":   "narration",
        "dim":      "muted",
        "guidance": "tutorial",
        "warning":  "hint",
        "success":  "success",
        "error":    "failure",
        "spirit":   "dialogue",   # Sam — auto-routes to a dialogue bubble
        "input":    "echo",
        "output":   "query_output",
    }

    def append_output(self, text: str, style: str = "normal") -> None:
        """Back-compat entry point. Routes every legacy style to a typed widget."""
        kind = self._STYLE_KIND.get(style, "narration")

        # ── query_output and echo go straight to the terminal center ────
        if kind == "query_output":
            self._show_results(text)
            return
        if kind == "echo":
            # Already handled by _echo_input() before exec — skip left scroll
            return

        if kind == "dialogue":
            # Sam speaking via the old spirit channel — strip any "Sam whispers:" prefix
            body = text.strip()
            for pre in ("👻  Sam whispers:", "Sam whispers:", "Sam pings you:", "👻"):
                if body.startswith(pre):
                    body = body[len(pre):].strip()
            body = body.strip().strip("'\"").strip()
            self.append_dialogue("Sam", body)
            return

        # ── SQL/game errors → terminal, never the left conversation panel ──
        if kind == "failure":
            self._terminal.write_error(text.strip())
            return

        if kind in ("narration", "muted"):
            for chunk in self._chunk(text):
                self._add_widget(self._make_text(chunk, kind))
            self._autoscroll()
            return

        self._add_widget(self._make_text(text.strip(), kind))
        self._autoscroll()

    def append_dialogue(self, speaker: str, text: str) -> None:
        """Render an NPC line as a portrait + name-tag + tinted speech box."""
        if not text:
            return
        self._add_widget(self._make_dialogue(speaker, text.strip()))
        self._autoscroll()

    # ── STORY panel API (separate from the mechanical console feed) ─────────

    def set_story(self, kind: str, text: str) -> None:
        """Route story beats into the conversation thread as Diana (Narrator) bubbles."""
        if not text:
            return
        if kind in ("why", "beat"):
            # Both 'why' (premise) and 'beat' (current moment) go into the
            # conversation thread as Diana speaking — same style as Sam.
            self.append_dialogue("Diana", text)
        elif kind == "recall":
            # Recall is a reminder of what was already found — show as muted note
            self.append_output("🔁  " + text, style="dim")

    def append_concept(self, concept: dict, story: str = "") -> None:
        """
        Display the concept card PERSISTENTLY in the right panel.
        This replaces the inline concept card approach with a persistent
        right-side display that always shows the current unlocked concept.
        """
        self._current_concept = concept

        # Trigger the Matrix-rain → unlock animation on the terminal
        title = concept.get("title", "")
        if title:
            self._terminal.play_unlock_animation(title)

    def append_cliffhanger(self, card: dict) -> None:
        """
        Show a dramatic end-of-scene card in the conversation thread.
        card keys: eyebrow, headline, teaser, cta
        """
        w = QFrame()
        w.setObjectName("cliff_card")
        w.setStyleSheet(f"""
            QFrame#cliff_card {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1e1b4b, stop:1 #0f172a);
                border: 1px solid #4f46e5;
                border-radius: 10px;
            }}
        """)
        lay = QVBoxLayout(w)
        lay.setContentsMargins(24, 20, 24, 20)
        lay.setSpacing(8)

        # Eyebrow
        eyebrow = QLabel(card.get("eyebrow", "NEXT").upper())
        eyebrow.setStyleSheet(
            "color: #818cf8; font-size: 11px; font-weight: 800; "
            "letter-spacing: 3px; background: transparent; border: none;"
        )
        lay.addWidget(eyebrow)

        # Headline
        headline = QLabel(card.get("headline", ""))
        headline.setStyleSheet(
            "color: #e2e8f0; font-size: 20px; font-weight: 800; "
            "background: transparent; border: none;"
        )
        lay.addWidget(headline)

        # Divider
        div = QFrame()
        div.setFixedHeight(1)
        div.setStyleSheet("background: #4f46e5; border: none;")
        lay.addWidget(div)

        # Teaser body
        teaser_text = card.get("teaser", "")
        teaser = QLabel(teaser_text)
        teaser.setWordWrap(True)
        teaser.setStyleSheet(
            "color: #94a3b8; font-size: 14px; line-height: 1.6; "
            "background: transparent; border: none; margin-top: 4px;"
        )
        lay.addWidget(teaser)

        # CTA line
        cta_text = card.get("cta", "")
        if cta_text:
            cta = QLabel(cta_text)
            cta.setStyleSheet(
                "color: #818cf8; font-size: 13px; font-weight: 700; "
                "background: transparent; border: none; margin-top: 4px;"
            )
            lay.addWidget(cta)

        self._add_widget(w)
        self._autoscroll()

    def _concept_to_html(self, concept: dict, story: str = "") -> str:
        """Convert a concept dict to formatted HTML for display in right panel."""
        parts = []
        parts.append(f'<div style="color:{ACCENT}; font-size:11px; font-weight:800; letter-spacing:2px;">◆  CONCEPT UNLOCKED</div>')
        parts.append('<div style="height:8px;"></div>')

        if story:
            parts.append(f'<div style="background:#eff6ff; border:1px solid #bcd5f5; border-radius:6px; padding:10px; margin-bottom:10px;">')
            parts.append(f'<div style="color:#1d4ed8; font-size:11px; font-weight:700; letter-spacing:1px;">📖  STORY SO FAR</div>')
            parts.append(f'<div style="color:{TEXT_MAIN}; font-size:13px; margin-top:4px;">{story}</div>')
            parts.append('</div>')

        title = concept.get("title", "")
        if title:
            parts.append(f'<div style="color:{TEXT_MAIN}; font-size:16px; font-weight:800; margin:10px 0 8px 0;">{title}</div>')

        if concept.get("what"):
            parts.append(f'<div style="color:{TEXT_DIM}; font-size:10px; font-weight:700; letter-spacing:1px;">WHAT IS IT?</div>')
            parts.append(f'<div style="color:{TEXT_MAIN}; font-size:13px; margin-bottom:8px;">{concept["what"]}</div>')

        if concept.get("why"):
            parts.append(f'<div style="color:{TEXT_DIM}; font-size:10px; font-weight:700; letter-spacing:1px;">WHY IT MATTERS</div>')
            parts.append(f'<div style="color:{TEXT_MAIN}; font-size:13px; margin-bottom:8px;">{concept["why"]}</div>')

        if concept.get("syntax"):
            parts.append(f'<div style="color:{TEXT_DIM}; font-size:10px; font-weight:700; letter-spacing:1px;">SYNTAX</div>')
            parts.append(f'<div style="color:{ACCENT}; font-family:Consolas,monospace; font-size:12px; background:{CODE_BG}; border:1px solid {BORDER}; border-radius:5px; padding:8px; margin-bottom:8px; word-wrap:break-word;">{concept["syntax"]}</div>')

        if concept.get("analogy"):
            parts.append(f'<div style="color:{TEXT_DIM}; font-size:10px; font-weight:700; letter-spacing:1px;">💡  REAL-WORLD ANALOGY</div>')
            parts.append(f'<div style="color:#7a4f00; font-size:12px; font-style:italic; background:#fff8e6; border:1px solid #f0c060; border-radius:5px; padding:8px; margin-bottom:8px;">{concept["analogy"]}</div>')

        if concept.get("gotcha"):
            parts.append(f'<div style="color:{TEXT_DIM}; font-size:10px; font-weight:700; letter-spacing:1px;">⚠  COMMON MISTAKE</div>')
            parts.append(f'<div style="color:{ERROR_COL}; font-size:12px;">{concept["gotcha"]}</div>')

        return "".join(parts)

    # ── Chunking (research-backed: ≤3 sentences, collapse manual line breaks) ─

    @staticmethod
    def _chunk(text: str) -> list[str]:
        import re as _re
        out: list[str] = []
        # Respect explicit paragraph breaks; collapse single \n to spaces so
        # lines wrap naturally at the column cap instead of awkward short lines.
        for para in text.split("\n\n"):
            para = " ".join(para.split())
            if not para:
                continue
            sentences = _re.findall(r'[^.!?]+[.!?]+|\S+$|[^.!?]+$', para)
            buf: list[str] = []
            for s in sentences:
                buf.append(s.strip())
                if len(buf) >= 3:                      # ≤3-sentence blocks
                    out.append(" ".join(buf)); buf = []
            if buf:
                out.append(" ".join(buf))
        return out or [text.strip()]

    # ── Message-widget factory ───────────────────────────────────────────────

    def _add_widget(self, w: QWidget) -> None:
        # insert before the trailing stretch
        self._msg_layout.insertWidget(self._msg_layout.count() - 1, w)

    def _autoscroll(self) -> None:
        def _go():
            bar = self._scroll.verticalScrollBar()
            bar.setValue(bar.maximum())
        QTimer.singleShot(0, _go)

    def _label(self, text: str, css: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setWordWrap(True)
        lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        lbl.setMaximumWidth(self._msg_max_w)
        lbl.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        lbl.setStyleSheet(css)
        return lbl

    def _make_text(self, text: str, kind: str) -> QWidget:
        if kind == "narration":
            return self._label(text,
                f"color:{TEXT_MAIN}; font-family:'Segoe UI',sans-serif; "
                f"font-size:15px; padding:2px 0;")
        if kind == "muted":
            return self._label(text,
                f"color:{TEXT_DIM}; font-style:italic; font-size:13px; padding:1px 0;")
        if kind == "success":
            return self._label("✔   " + text,
                f"color:{SUCCESS}; font-weight:700; font-size:15px; "
                f"background:#eaf6ec; border-left:3px solid {SUCCESS}; "
                f"border-radius:5px; padding:8px 12px;")
        if kind == "failure":
            return self._label("✖   " + text,
                f"color:{ERROR_COL}; font-weight:700; font-size:14px; "
                f"background:#fdeceb; border-left:3px solid {ERROR_COL}; "
                f"border-radius:5px; padding:8px 12px;")
        if kind == "hint":
            return self._label("💡  " + text,
                f"color:{WARNING}; font-size:14px; background:#fff8e6; "
                f"border-left:3px solid {WARNING}; border-radius:5px; padding:8px 12px;")
        if kind == "tutorial":
            return self._label(text,
                f"color:{GUIDANCE}; font-size:15px; background:#eef4fd; "
                f"border-left:3px solid {ACCENT}; border-radius:5px; padding:10px 14px;")
        if kind == "echo":
            return self._label(text.strip(),
                f"color:{ACCENT}; font-family:'Consolas',monospace; "
                f"font-size:13px; font-weight:700; padding:6px 0 2px 0;")
        if kind == "query_output":
            lbl = self._label(text.rstrip("\n"),
                f"color:{TEXT_MAIN}; font-family:'Consolas',monospace; "
                f"font-size:13px; background:{CODE_BG}; border:1px solid {BORDER}; "
                f"border-radius:6px; padding:10px 12px;")
            lbl.setMaximumWidth(self._msg_max_w + 80)   # tables need a bit more room
            return lbl
        return self._label(text, f"color:{TEXT_MAIN}; font-size:15px;")

    def _make_dialogue(self, speaker: str, text: str) -> QWidget:
        accent = npc_color(speaker)
        key = canonical(speaker)
        display = speaker if key != "_" else (speaker or "Unknown")

        frame = QFrame()
        frame.setMaximumWidth(self._msg_max_w + 40)
        frame.setStyleSheet(
            f"QFrame {{ background:{self._tint(accent, 0.10)}; "
            f"border:1px solid {self._tint(accent, 0.45)}; "
            f"border-left:4px solid {accent}; border-radius:8px; }}"
        )
        row = QHBoxLayout(frame)
        row.setContentsMargins(10, 10, 12, 10)
        row.setSpacing(10)

        pic = QLabel()
        pic.setPixmap(npc_portrait(speaker, 52))
        pic.setFixedSize(52, 52)
        pic.setAlignment(Qt.AlignmentFlag.AlignTop)
        row.addWidget(pic, 0, Qt.AlignmentFlag.AlignTop)

        col = QVBoxLayout()
        col.setSpacing(3)
        name = QLabel(display.upper())
        name.setStyleSheet(
            f"color:{accent}; font-family:'Segoe UI',sans-serif; "
            f"font-size:11px; font-weight:800; letter-spacing:1.5px; border:none;")
        body = QLabel(text)
        body.setWordWrap(True)
        body.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        body.setMaximumWidth(self._msg_max_w - 70)
        body.setStyleSheet(
            f"color:{TEXT_MAIN}; font-family:'Segoe UI',sans-serif; "
            f"font-size:15px; border:none; background:transparent;")
        col.addWidget(name)
        col.addWidget(body)
        row.addLayout(col, 1)
        return frame

    def _make_concept(self, concept: dict, story: str = "") -> QWidget:
        """Inline concept card — same content as the old modal, in the stream."""
        frame = QFrame()
        frame.setMaximumWidth(self._msg_max_w + 60)
        frame.setStyleSheet(
            f"QFrame#cc {{ background:#ffffff; border:1px solid {BORDER}; "
            f"border-left:4px solid {ACCENT}; border-radius:8px; }}"
        )
        frame.setObjectName("cc")
        v = QVBoxLayout(frame)
        v.setContentsMargins(18, 16, 18, 16)
        v.setSpacing(10)

        def lab(text, css):
            l = QLabel(text)
            l.setWordWrap(True)
            l.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            l.setStyleSheet(css + "border:none; background:transparent;")
            return l

        def section(label, body, body_css):
            v.addWidget(lab(label, f"color:{TEXT_DIM}; font-size:10px; "
                                   f"font-weight:700; letter-spacing:1px;"))
            v.addWidget(lab(body, body_css))

        v.addWidget(lab("◆  CONCEPT UNLOCKED",
            f"color:{ACCENT}; font-size:11px; font-weight:800; letter-spacing:2px;"))

        if story:
            box = QFrame()
            box.setStyleSheet("QFrame{background:#eff6ff; border:1px solid #bcd5f5; "
                              "border-radius:6px;}")
            bl = QVBoxLayout(box); bl.setContentsMargins(12, 9, 12, 9); bl.setSpacing(4)
            bl.addWidget(lab("📖  STORY SO FAR",
                "color:#1d4ed8; font-size:11px; font-weight:700; letter-spacing:1px;"))
            bl.addWidget(lab(story, f"color:{TEXT_MAIN}; font-size:13px;"))
            v.addWidget(box)

        v.addWidget(lab(concept.get("title", ""),
            f"color:{TEXT_MAIN}; font-size:17px; font-weight:800;"))

        if concept.get("what"):
            section("WHAT IS IT?", concept["what"], f"color:{TEXT_MAIN}; font-size:14px;")
        if concept.get("why"):
            section("WHY IT MATTERS", concept["why"], f"color:{TEXT_MAIN}; font-size:14px;")
        if concept.get("syntax"):
            section("SYNTAX", concept["syntax"],
                f"color:{ACCENT}; font-family:'Consolas',monospace; font-size:13px; "
                f"background:{CODE_BG}; border:1px solid {BORDER}; border-radius:6px; "
                f"padding:10px 12px;")
        if concept.get("analogy"):
            section("💡  REAL-WORLD ANALOGY", concept["analogy"],
                "color:#7a4f00; font-size:13px; font-style:italic; "
                "background:#fff8e6; border:1px solid #f0c060; border-radius:6px; "
                "padding:8px 12px;")
        if concept.get("gotcha"):
            section("⚠  COMMON MISTAKE", concept["gotcha"],
                f"color:{ERROR_COL}; font-size:13px;")

        for w in frame.findChildren(QLabel):
            w.setMaximumWidth(self._msg_max_w + 20)
        return frame

    @staticmethod
    def _tint(hex_color: str, alpha: float) -> str:
        c = QColor(hex_color)
        return f"rgba({c.red()},{c.green()},{c.blue()},{alpha:.2f})"

    def _echo_input(self, text: str) -> None:
        """Write a command prompt + command into the cartoon terminal."""
        self._terminal.write_command(text.strip())

    def _show_results(self, text: str) -> None:
        """Write query output into the cartoon terminal."""
        self._terminal.write_output(text)

    # ── Command execution ─────────────────────────────────────────────────────

    def _on_execute(self, raw: str):
        """Called when player presses Ctrl+Enter in the SQL editor."""
        raw = raw.strip()
        if not raw:
            return

        self._echo_input(raw)

        # Handle reset confirmation
        if self._pending_reset:
            self._pending_reset = False
            if raw.lower() in ("yes", "y"):
                self._do_reset()
            else:
                self.append_output("  Reset cancelled.\n", style="dim")
            return

        if raw == "db":
            self.append_output(repr(self._db) + "\n", style="dim")
            self.append_output("Try: db.tables()  to list tables, then write SQL directly.\n", style="guidance")
            return
        if raw in ("help", "?"):
            self._show_help()
            return
        if raw in ("hint", "?hint"):
            self._on_hint()
            return
        if raw == "clues":
            self._show_clues()
            return
        if raw in ("reset", "restart", "new game"):
            self._on_reset()
            return

        # ── Recall gate: validate against the typed SQL text, skip execution ──
        # Recall questions use hypothetical tables (orders, users, sales, etc.)
        # that don't exist in the game DB.  Running them would fail every time.
        # Instead, validate keywords in the raw text and advance on success.
        if self._game._recall_pending is not None:
            self._game._handle_recall(raw)
            return   # never execute the fake-table SQL

        # ── Auto-wrap raw SQL ────────────────────────────────────────────
        # If the player types plain SQL (SELECT, INSERT, etc.), wrap it in
        # db.query("...") so they never need to learn the Python wrapper.
        # This keeps the game focused on teaching SQL, not Python syntax.
        sql_keywords = (
            "SELECT ", "INSERT ", "UPDATE ", "DELETE ", "CREATE ",
            "DROP ", "ALTER ", "PRAGMA ", "WITH ",
            "select ", "insert ", "update ", "delete ", "create ",
            "drop ", "alter ", "pragma ", "with ",
        )
        if raw.startswith(sql_keywords):
            # Escape any quotes in the SQL and wrap it
            escaped = raw.replace('\\', '\\\\').replace('"', '\\"')
            raw = f'db.query("{escaped}")'

        self._exec_command(raw)

    def _exec_command(self, code):
        stdout_cap = io.StringIO()
        old_out = sys.stdout
        sys.stdout = stdout_cap

        result_value = None
        try:
            try:
                compiled = compile(code, "<nexus>", "eval")
                result_value = eval(compiled, self._exec_ns)
            except SyntaxError:
                compiled = compile(code, "<nexus>", "exec")
                exec(compiled, self._exec_ns)
        except Exception as e:
            tb = traceback.format_exc()
            lines = [l for l in tb.strip().splitlines() if l.strip()]
            friendly = lines[-1] if lines else str(e)
            # Errors go straight into the terminal (center) — not the left panel
            self._terminal.write_error(f"\n  ✖  {friendly}")
            self._terminal.write_dim("  Type 'hint' if you're stuck.")
        finally:
            sys.stdout = old_out

        out = stdout_cap.getvalue()
        if result_value is not None:
            out += repr(result_value) + "\n"

        if out:
            self.append_output(out, style="output")

        # Notify game for S2 objective checking (Python validators need code + output)
        self._game.on_exec(code, out)

    def _build_namespace(self):
        import builtins
        safe = {n: getattr(builtins, n) for n in [
            "print","len","range","enumerate","zip","map","filter",
            "list","dict","set","tuple","str","int","float","bool",
            "sorted","reversed","min","max","sum","abs","round",
            "type","isinstance","repr",
        ]}
        return {"__builtins__": safe, "db": self._db, "game": self._game}

    # ── Hint / Help / Clues ───────────────────────────────────────────────────

    def _on_hint(self):
        """Two-tier hint system.
        Click 1 → Sam gives a specific, helpful tip in his dialogue bubble.
        Click 2+ → Big answer card: exact command + copy button.

        Special case: if a between-scene RECALL GATE is pending, skip straight
        to the answer card — the player is already stuck enough.
        """
        # ── Recall gate: player is answering a between-scene quiz ─────────────
        if self._game._recall_pending is not None:
            ch = self._game._recall_pending
            answer = ch.get("answer", "")
            if answer:
                self._add_widget(self._make_answer_card(answer))
                self._autoscroll()
            else:
                self.append_dialogue("Sam",
                    "Just type a SELECT query that matches the question above.")
            return

        # ── Normal objective hint ─────────────────────────────────────────────
        hint = self._game.get_hint()

        for obj in self._game.objectives_for_scene(self._game.scene):
            if obj["id"] not in self._game.completed:
                attr = f"_hint_idx_{obj['id']}"
                idx = getattr(self._game, attr, 0)

                if idx == 1:
                    # First click: Sam speaks a direct, useful tip
                    self.append_dialogue("Sam", hint)
                else:
                    # Second click+: show the full answer card
                    solution = self._focus_cmd.text().strip()
                    if not solution:
                        self.append_dialogue("Sam", hint)
                    else:
                        self._add_widget(self._make_answer_card(solution))
                        self._autoscroll()
                return

        # All objectives done — trigger scene advancement.
        self._game._check_scene_unlock()

    def _make_answer_card(self, command: str) -> QWidget:
        """Big styled answer card — dark terminal aesthetic, clear copy button."""
        frame = QFrame()
        frame.setMaximumWidth(self._msg_max_w + 60)
        frame.setStyleSheet(f"""
            QFrame {{
                background: #0d1117;
                border: 2px solid #3fb950;
                border-radius: 10px;
            }}
        """)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(12)

        # Header
        hdr = QLabel("HERE'S THE ANSWER")
        hdr.setStyleSheet(
            "color: #3fb950; font-family: 'Segoe UI', sans-serif; "
            "font-size: 11px; font-weight: 800; letter-spacing: 2.5px; border: none;"
        )
        layout.addWidget(hdr)

        # Sub-label
        sub = QLabel("Type this exactly — or use the copy button below:")
        sub.setStyleSheet(
            "color: #8b949e; font-size: 12px; font-style: italic; border: none;"
        )
        layout.addWidget(sub)

        # Command block
        cmd_lbl = QLabel(command)
        cmd_lbl.setWordWrap(True)
        cmd_lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        cmd_lbl.setStyleSheet(f"""
            color: #e6edf3;
            font-family: 'Consolas', 'Courier New', monospace;
            font-size: 15px;
            font-weight: 600;
            background: #161b22;
            border: 1px solid #3fb950;
            border-radius: 6px;
            padding: 12px 14px;
        """)
        layout.addWidget(cmd_lbl)

        # Copy button — big, green, obvious
        copy_btn = QPushButton("📋   Copy Command")
        copy_btn.setFixedHeight(40)
        copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        copy_btn.setStyleSheet("""
            QPushButton {
                background: #3fb950;
                color: #0d1117;
                border: none;
                border-radius: 7px;
                font-size: 14px;
                font-weight: 800;
                letter-spacing: 0.5px;
            }
            QPushButton:hover {
                background: #22c55e;
            }
            QPushButton:pressed {
                background: #16a34a;
            }
        """)

        def _do_copy():
            from PySide6.QtWidgets import QApplication
            QApplication.clipboard().setText(command)
            copy_btn.setText("✓   Copied!")
            copy_btn.setStyleSheet(copy_btn.styleSheet().replace("#3fb950", "#1a7f37"))
            QTimer.singleShot(2500, lambda: (
                copy_btn.setText("📋   Copy Command"),
                copy_btn.setStyleSheet(copy_btn.styleSheet().replace("#1a7f37", "#3fb950"))
            ))

        copy_btn.clicked.connect(_do_copy)
        layout.addWidget(copy_btn)

        return frame

    def _on_reset(self):
        self.append_output("\n⚠  Are you sure? Type  yes  to start a brand new game.\n", style="warning")
        self._pending_reset = True

    def _do_reset(self):
        """Wipe the save and restart the application."""
        import os
        from core.db import DB_PATH

        # Close the DB connection
        if self._db._conn:
            self._db._conn.close()
            self._db._conn = None

        # Delete world.db so it reseeds on next launch
        try:
            os.remove(DB_PATH)
        except OSError:
            pass

        self.append_output("\n✔  Save cleared. Restarting...\n", style="success")

        # Relaunch the application
        from PySide6.QtWidgets import QApplication
        from PySide6.QtCore import QProcess
        QProcess.startDetached(sys.executable, sys.argv)
        QApplication.instance().quit()

    def _show_help(self):
        self.append_output(
            "\n── COMMANDS ─────────────────────────────────────────────\n"
            "  db.tables()          List all tables\n"
            "  db.schema('name')    Show columns for a table\n"
            "  db.query(sql)        Run any SQL query\n"
            "  hint                 Get a hint for current objective\n"
            "  clues                Show everything discovered so far\n"
            "  reset                Start a new game from scratch\n"
            "  help                 Show this list\n"
            "  ↑ / ↓               Navigate command history\n"
            "─────────────────────────────────────────────────────────\n",
            style="dim"
        )

    def _show_clues(self):
        clues = self._game.clues
        if not clues:
            self.append_output("\nNo clues discovered yet.\n", style="dim")
            return
        self.append_output("\n── CLUE LOG ─────────────────────────────────────────────\n", style="success")
        for clue in clues:
            self.append_output(f"  {clue}\n", style="success")
        self.append_output("─────────────────────────────────────────────────────────\n", style="dim")
