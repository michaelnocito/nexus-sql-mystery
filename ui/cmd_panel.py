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
    QLabel, QFrame, QPushButton,
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import (
    QFont, QTextCursor, QColor, QTextCharFormat,
    QTextBlockFormat,
)
from ui.sql_editor import SQLEditor

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


# ── Text format helpers ───────────────────────────────────────────────────────

def _prose_fmt(hex_color, bold=False, italic=False, size=15):
    fmt = QTextCharFormat()
    fmt.setForeground(QColor(hex_color))
    fmt.setFont(QFont("Segoe UI", size, QFont.Weight.Bold if bold else QFont.Weight.Normal, italic))
    return fmt

def _code_fmt(hex_color, bold=False, size=13):
    fmt = QTextCharFormat()
    fmt.setForeground(QColor(hex_color))
    fmt.setFont(QFont("Consolas", size, QFont.Weight.Bold if bold else QFont.Weight.Normal))
    return fmt

def _code_bg_fmt(hex_color, bg_color, size=13):
    fmt = QTextCharFormat()
    fmt.setForeground(QColor(hex_color))
    fmt.setBackground(QColor(bg_color))
    fmt.setFont(QFont("Consolas", size))
    return fmt


# Style map — each style has a QTextCharFormat
STYLES = {
    # ── Prose (sans-serif, readable) ─────────────────────────────────────────
    "scene":    _prose_fmt(SCENE_COL,  bold=True,  size=16),   # scene intros
    "guidance": _prose_fmt(GUIDANCE,   bold=False, size=15),   # step instructions
    "normal":   _prose_fmt(TEXT_MAIN,  bold=False, size=15),   # general prose
    "dim":      _prose_fmt(TEXT_DIM,   italic=True, size=14),  # ambient / meta
    "warning":  _prose_fmt(WARNING,    bold=False, size=15),   # hints

    # ── Emphasis (sans-serif, stands out) ────────────────────────────────────
    "success":  _prose_fmt(SUCCESS,    bold=True,  size=15),   # ✔ objective done
    "error":    _prose_fmt(ERROR_COL,  bold=True,  size=15),   # SQL errors

    # ── Code (monospace, tinted bg) ──────────────────────────────────────────
    "input":    _code_fmt(ACCENT,      bold=True,  size=14),   # >>> echo
    "output":   _code_bg_fmt(TEXT_MAIN, CODE_BG,  size=13),   # SQL result tables

    # ── Spirit guide (subtle, italic) ────────────────────────────────────────
    "spirit":   _prose_fmt("#768ea8",  italic=True, size=13),  # ghostly tips
}


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

        # ── Narrative output ─────────────────────────────────────────────────
        self._narrative = QTextEdit()
        self._narrative.setObjectName("narrative")
        self._narrative.setReadOnly(True)
        self._narrative.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        self._narrative.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        layout.addWidget(self._narrative, stretch=1)

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

        # Top bar: prompt label + hint button
        bar = QHBoxLayout()
        bar.setContentsMargins(12, 6, 12, 2)
        bar.setSpacing(8)

        prompt = QLabel(">>>  SQL Editor")
        prompt.setObjectName("prompt_label")
        bar.addWidget(prompt)
        bar.addStretch()

        run_label = QLabel("Ctrl+Enter to run")
        run_label.setStyleSheet(f"color: {TEXT_DIM}; font-size: 11px; font-style: italic;")
        bar.addWidget(run_label)

        self._hint_btn = QPushButton("hint")
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

    def append_output(self, text: str, style: str = "normal") -> None:
        fmt = STYLES.get(style, STYLES["normal"])
        cursor = self._narrative.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)

        # ── Visual grouping: different block backgrounds per style ────────
        block_fmt = QTextBlockFormat()
        if style == "scene":
            # Scene intros: left purple border
            block_fmt.setLeftMargin(12)
            block_fmt.setProperty(QTextBlockFormat.Property.BlockLeftMargin, 12)
        elif style == "input":
            # Player commands: slight grey bg via left/right margins
            block_fmt.setLeftMargin(8)
        elif style == "output":
            # Query results: code background handled by char format
            block_fmt.setLeftMargin(16)
            block_fmt.setRightMargin(16)
        elif style == "success":
            # Clue found: green-tinted
            block_fmt.setLeftMargin(8)
        elif style == "guidance":
            # Step guidance: blue-tinted left border effect
            block_fmt.setLeftMargin(12)
        elif style == "warning":
            # Hints: amber left margin
            block_fmt.setLeftMargin(12)

        cursor.setBlockFormat(block_fmt)
        cursor.insertText(text, fmt)

        # Reset block format for next insertion
        plain_block = QTextBlockFormat()
        cursor.setBlockFormat(plain_block)

        self._narrative.setTextCursor(cursor)
        self._narrative.ensureCursorVisible()

    def _echo_input(self, text):
        self.append_output(f"\n>>> {text}\n", style="input")

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
        if out:
            self.append_output(out, style="output")

        if result_value is not None:
            self.append_output(repr(result_value) + "\n", style="output")

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

        if is_dialogue:
            prefix = "\n"
            style = "guidance"
        else:
            prefix = "\n💡  "
            style = "warning"

        # Split hint into prose vs code parts
        # Look for patterns like: db.query("...") or db.tables() or SQL keywords on their own line
        parts = _re.split(r'((?:db\.\w+\([^)]*\))|(?:(?:SELECT|WHERE|GROUP BY|ORDER BY|JOIN|FROM|SUM|COUNT|IN)\b[^\n]*))', hint)

        cursor = self._narrative.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)

        fmt = STYLES.get(style, STYLES["normal"])
        code_fmt = STYLES["output"]

        # Insert prefix
        cursor.insertText(prefix, fmt)

        for i, part in enumerate(parts):
            part = part.strip()
            if not part:
                continue

            # Check if this part looks like code
            is_code = (
                part.startswith("db.") or
                _re.match(r'^(SELECT|WHERE|GROUP BY|ORDER BY|JOIN|FROM|SUM|COUNT|IN)\b', part, _re.IGNORECASE)
            )

            if is_code:
                # Render as copyable code block
                block_fmt = QTextBlockFormat()
                block_fmt.setLeftMargin(20)
                block_fmt.setRightMargin(20)
                cursor.setBlockFormat(block_fmt)
                cursor.insertText(f"\n  {part}\n", code_fmt)
                # Reset
                cursor.setBlockFormat(QTextBlockFormat())
            else:
                cursor.insertText(part + " ", fmt)

        cursor.insertText("\n", fmt)
        self._narrative.setTextCursor(cursor)
        self._narrative.ensureCursorVisible()

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
