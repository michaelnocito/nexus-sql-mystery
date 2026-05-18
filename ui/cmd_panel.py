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

        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Narrative output — scrollable typed-message list ─────────────────
        self._scroll = QScrollArea()
        self._scroll.setObjectName("msg_scroll")
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self._scroll.setStyleSheet(
            f"QScrollArea#msg_scroll {{ background: {PANEL_BG}; border: none; }}"
            f"QWidget#msg_container {{ background: {PANEL_BG}; }}"
        )

        self._msg_container = QWidget()
        self._msg_container.setObjectName("msg_container")
        self._msg_layout = QVBoxLayout(self._msg_container)
        self._msg_layout.setContentsMargins(22, 18, 22, 18)
        self._msg_layout.setSpacing(12)          # inter-chunk gap (research: real gap, not blank lines)
        self._msg_layout.addStretch(1)           # keeps messages top-aligned

        self._scroll.setWidget(self._msg_container)
        layout.addWidget(self._scroll, stretch=1)

        # Max readable column width — ~60 chars for novices (research-backed)
        self._msg_max_w = 560

        # ── Focus command box ─────────────────────────────────────────────────
        self._focus_frame = QFrame()
        self._focus_frame.setObjectName("focus_frame")
        fl = QVBoxLayout(self._focus_frame)
        fl.setContentsMargins(20, 10, 20, 10)
        fl.setSpacing(6)

        # Top row: label + reveal toggle + copy
        top_row = QHBoxLayout()
        top_row.setSpacing(8)

        self._focus_label = QLabel("TRY THIS FIRST:")
        self._focus_label.setObjectName("focus_label")
        top_row.addWidget(self._focus_label)
        top_row.addStretch()

        # Reveal toggle — Ctrl+S shortcut
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
        self._copy_btn.hide()   # only visible when solution is revealed
        top_row.addWidget(self._copy_btn)
        fl.addLayout(top_row)

        # Solution command — hidden until player clicks "show solution"
        self._focus_cmd = QLabel("")
        self._focus_cmd.setObjectName("focus_cmd")
        self._focus_cmd.setWordWrap(True)
        self._focus_cmd.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self._focus_cmd.hide()
        fl.addWidget(self._focus_cmd)

        self._solution_revealed = False
        self._focus_frame.adjustSize()
        layout.addWidget(self._focus_frame)

        # ── SQL Editor input ──────────────────────────────────────────────────
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

        self._hint_btn = QPushButton("💡 hint  (Ctrl+H)")
        self._hint_btn.setObjectName("hint_btn")
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

        layout.addWidget(input_frame)

        # ── Keyboard shortcuts ───────────────────────────────────────────────
        from PySide6.QtGui import QShortcut, QKeySequence
        hint_shortcut = QShortcut(QKeySequence("Ctrl+H"), self)
        hint_shortcut.activated.connect(self._on_hint)

        reveal_shortcut = QShortcut(QKeySequence("Ctrl+S"), self)
        reveal_shortcut.activated.connect(self._toggle_reveal)

        copy_shortcut = QShortcut(QKeySequence("Ctrl+D"), self)
        copy_shortcut.activated.connect(self._copy_focus)

        QTimer.singleShot(0, self._editor.setFocus)

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

        if kind == "dialogue":
            # Sam speaking via the old spirit channel — strip any "Sam whispers:" prefix
            body = text.strip()
            for pre in ("👻  Sam whispers:", "Sam whispers:", "Sam pings you:", "👻"):
                if body.startswith(pre):
                    body = body[len(pre):].strip()
            body = body.strip().strip("'\"").strip()
            self.append_dialogue("Sam", body)
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

    def append_concept(self, concept: dict, story: str = "") -> None:
        """
        Render the concept card INLINE in the message stream (no modal).
        Scrolls so the TOP of the card sits at the top of the viewport —
        the player reads it in place and keeps going, no flow break.
        """
        card = self._make_concept(concept, story)
        self._add_widget(card)

        def _show_top():
            self._scroll.verticalScrollBar().setValue(max(0, card.y() - 8))
        QTimer.singleShot(0, _show_top)
        QTimer.singleShot(40, _show_top)   # after layout settles

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

    def _echo_input(self, text):
        self.append_output(f">>> {text}", style="input")

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
            self.append_output("Try: db.tables()  to see what's in the database.\n", style="guidance")
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
            self.append_output(f"\n  ✖  {friendly}\n", style="error")
            self.append_output("  Type  hint  if you're stuck.\n", style="dim")
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
        hint = self._game.get_hint()
        # Check which hint tier we're on for the current objective
        for obj in self._game.objectives_for_scene(self._game.scene):
            if obj["id"] not in self._game.completed:
                attr = f"_hint_idx_{obj['id']}"
                idx = getattr(self._game, attr, 0)
                # idx was just incremented by get_hint(), so idx=1 means first hint was just given
                if idx == 1:
                    # First hint: show as story dialogue, not as "hint"
                    self._append_hint_formatted(hint, is_dialogue=True)
                else:
                    # Subsequent hints: show as explicit hint with 💡
                    self._append_hint_formatted(hint, is_dialogue=False)
                return
        # Fallback
        self.append_output(f"\n💡  {hint}\n", style="warning")

    def _append_hint_formatted(self, hint: str, is_dialogue: bool = False):
        """Format hint text, rendering SQL code blocks in monospace with a tinted background."""
        import re as _re

        style = "guidance" if is_dialogue else "warning"
        prefix = "" if is_dialogue else "💡  "

        # Split hint into prose vs code parts
        parts = _re.split(r'((?:db\.\w+\([^)]*\))|(?:(?:SELECT|WHERE|GROUP BY|ORDER BY|JOIN|FROM|SUM|COUNT|IN)\b[^\n]*))', hint)

        prose_parts = []
        for part in parts:
            part = part.strip()
            if not part:
                continue
            is_code = (
                part.startswith("db.") or
                _re.match(r'^(SELECT|WHERE|GROUP BY|ORDER BY|JOIN|FROM|SUM|COUNT|IN)\b', part, _re.IGNORECASE)
            )
            if is_code:
                # Flush any accumulated prose
                if prose_parts:
                    self.append_output(prefix + " ".join(prose_parts), style=style)
                    prose_parts = []
                    prefix = ""
                self.append_output(f"  {part}", style="output")
            else:
                prose_parts.append(part)

        # Flush remaining prose
        if prose_parts:
            self.append_output(prefix + " ".join(prose_parts), style=style)

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
