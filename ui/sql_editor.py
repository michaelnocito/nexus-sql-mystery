# ui/sql_editor.py
# SQLEditor — a multi-line code input with SQL syntax highlighting.
# Ctrl+Enter (or Shift+Enter) to execute. Regular Enter adds a new line.

import re
from PySide6.QtWidgets import QPlainTextEdit, QWidget, QTextEdit
from PySide6.QtCore import Qt, Signal, QRect
from PySide6.QtGui import (
    QFont, QColor, QTextCharFormat, QSyntaxHighlighter,
    QPainter, QPen, QKeySequence, QShortcut, QTextFormat,
)


# ── Palette (light theme) ────────────────────────────────────────────────────

KW_COLOR    = "#0969da"   # SQL keywords — blue
STR_COLOR   = "#1a7f37"   # strings — green
NUM_COLOR   = "#9a6700"   # numbers — amber
FUNC_COLOR  = "#6639ba"   # functions — purple
COMMENT_COL = "#6e7781"   # comments — grey
TEXT_COL    = "#1f2328"   # default text
BG_COL      = "#ffffff"
LINE_BG     = "#f6f8fa"   # current line highlight
BORDER_COL  = "#d0d7de"
ACCENT      = "#0969da"


# ── SQL keywords ──────────────────────────────────────────────────────────────

SQL_KEYWORDS = {
    "SELECT", "FROM", "WHERE", "GROUP", "BY", "ORDER", "ASC", "DESC",
    "JOIN", "INNER", "LEFT", "RIGHT", "OUTER", "CROSS", "ON",
    "AS", "IN", "AND", "OR", "NOT", "IS", "NULL", "BETWEEN", "LIKE",
    "HAVING", "LIMIT", "OFFSET", "DISTINCT", "ALL", "EXISTS",
    "UNION", "EXCEPT", "INTERSECT",
    "INSERT", "INTO", "VALUES", "UPDATE", "SET", "DELETE",
    "CREATE", "TABLE", "DROP", "ALTER", "INDEX",
    "CASE", "WHEN", "THEN", "ELSE", "END",
    "TRUE", "FALSE", "DEFAULT",
}

SQL_FUNCTIONS = {
    "COUNT", "SUM", "AVG", "MIN", "MAX",
    "COALESCE", "IFNULL", "NULLIF",
    "UPPER", "LOWER", "LENGTH", "SUBSTR", "TRIM", "REPLACE",
    "ROUND", "ABS", "CAST", "TYPEOF",
    "DATE", "TIME", "DATETIME", "STRFTIME",
    "GROUP_CONCAT", "TOTAL",
}


# ── Syntax highlighter ───────────────────────────────────────────────────────

def _fmt(hex_color, bold=False, italic=False):
    fmt = QTextCharFormat()
    fmt.setForeground(QColor(hex_color))
    if bold:
        fmt.setFontWeight(QFont.Weight.Bold)
    if italic:
        fmt.setFontItalic(True)
    return fmt


class SQLHighlighter(QSyntaxHighlighter):
    """Basic SQL syntax highlighter for QPlainTextEdit."""

    def __init__(self, parent=None):
        super().__init__(parent)

        self._rules = []

        # Keywords (word-bounded, case insensitive)
        kw_fmt = _fmt(KW_COLOR, bold=True)
        for kw in SQL_KEYWORDS:
            pattern = rf"\b{kw}\b"
            self._rules.append((re.compile(pattern, re.IGNORECASE), kw_fmt))

        # Functions (word + open paren)
        func_fmt = _fmt(FUNC_COLOR, bold=True)
        for fn in SQL_FUNCTIONS:
            pattern = rf"\b{fn}\s*(?=\()"
            self._rules.append((re.compile(pattern, re.IGNORECASE), func_fmt))

        # Numbers
        num_fmt = _fmt(NUM_COLOR)
        self._rules.append((re.compile(r"\b\d+\.?\d*\b"), num_fmt))

        # Single-quoted strings
        str_fmt = _fmt(STR_COLOR)
        self._rules.append((re.compile(r"'[^']*'"), str_fmt))

        # Dot notation (db.query, db.tables, etc.)
        dot_fmt = _fmt(ACCENT)
        self._rules.append((re.compile(r"\bdb\.\w+"), dot_fmt))

        # Comments (-- to end of line)
        comment_fmt = _fmt(COMMENT_COL, italic=True)
        self._rules.append((re.compile(r"--.*$"), comment_fmt))

        # Python strings with double quotes (the outer db.query("..."))
        self._rules.append((re.compile(r'"[^"]*"'), str_fmt))

    def highlightBlock(self, text):
        for pattern, fmt in self._rules:
            for match in pattern.finditer(text):
                start = match.start()
                length = match.end() - start
                self.setFormat(start, length, fmt)


# ── Line number gutter ───────────────────────────────────────────────────────

class LineNumberArea(QWidget):
    """Draws line numbers in the left margin of the editor."""

    def __init__(self, editor):
        super().__init__(editor)
        self._editor = editor

    def sizeHint(self):
        return self._editor._line_number_area_width()

    def paintEvent(self, event):
        self._editor._paint_line_numbers(event)


# ── SQL Editor widget ─────────────────────────────────────────────────────────

    # ── Autocomplete candidates ────────────────────────────────────────────────

AUTOCOMPLETE_WORDS = sorted(
    list(SQL_KEYWORDS) + list(SQL_FUNCTIONS) + [
        # Table names
        "employees", "transactions", "vendors", "departments", "save_state",
        # Column names
        "id", "name", "title", "department_id", "salary", "hire_date", "email",
        "vendor_id", "amount", "date", "description", "approved_by", "category",
        "contact_email", "address", "verified",
        "budget", "head_count",
        # db methods
        "db.tables()", "db.query(", "db.schema(",
    ],
    key=str.lower,
)


class SQLEditor(QPlainTextEdit):
    """
    Multi-line SQL input with syntax highlighting and line numbers.
    Emits execute_requested(str) on Ctrl+Enter or Shift+Enter.
    Tab triggers autocomplete for SQL keywords, table names, and column names.
    """

    execute_requested = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        # Monospace font
        font = QFont("Consolas", 13)
        font.setStyleHint(QFont.StyleHint.Monospace)
        self.setFont(font)

        # Tab = 2 spaces
        self.setTabStopDistance(self.fontMetrics().horizontalAdvance("  "))

        self.setStyleSheet(f"""
            QPlainTextEdit {{
                background: {BG_COL};
                color: {TEXT_COL};
                border: none;
                selection-background-color: #b6d4fb;
                padding-left: 4px;
            }}
        """)

        self.setPlaceholderText("type SQL or Python here…    Ctrl+Enter to run  |  Tab to autocomplete")
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)

        # Syntax highlighter
        self._highlighter = SQLHighlighter(self.document())

        # Line numbers
        self._line_area = LineNumberArea(self)
        self.blockCountChanged.connect(self._update_line_area_width)
        self.updateRequest.connect(self._update_line_area)
        self.cursorPositionChanged.connect(self._highlight_current_line)
        self._update_line_area_width()
        self._highlight_current_line()

        # Command history
        self._history: list[str] = []
        self._hist_idx: int = -1

        # Autocomplete state
        self._ac_matches: list[str] = []
        self._ac_idx: int = 0
        self._ac_prefix: str = ""

    # ── Key handling ──────────────────────────────────────────────────────────

    def keyPressEvent(self, event):
        mods = event.modifiers()
        key = event.key()

        # Ctrl+Enter or Shift+Enter → execute
        if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if mods & (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier):
                self._execute()
                return
            # Plain Enter → newline (normal behavior)
            self._ac_matches = []  # reset autocomplete on newline

        # Tab → autocomplete (or cycle matches), Shift+Tab → 2 spaces
        if key == Qt.Key.Key_Tab:
            if mods & Qt.KeyboardModifier.ShiftModifier:
                self.insertPlainText("  ")
                return
            self._autocomplete()
            return

        # Escape → cancel autocomplete cycle
        if key == Qt.Key.Key_Escape:
            self._ac_matches = []
            return

        # Ctrl+Up / Ctrl+Down → history navigation
        if mods & Qt.KeyboardModifier.ControlModifier:
            if key == Qt.Key.Key_Up:
                self._hist_up()
                return
            elif key == Qt.Key.Key_Down:
                self._hist_down()
                return

        # Any other key resets autocomplete cycling
        self._ac_matches = []
        super().keyPressEvent(event)

    def _autocomplete(self):
        """Tab-triggered autocomplete: match partial word against SQL keywords, tables, columns."""
        cursor = self.textCursor()

        if self._ac_matches:
            # Already cycling — remove the last completion and insert the next
            # Remove the previously inserted completion (everything after prefix)
            for _ in range(len(self._ac_matches[self._ac_idx]) - len(self._ac_prefix)):
                cursor.deletePreviousChar()
            self._ac_idx = (self._ac_idx + 1) % len(self._ac_matches)
            suffix = self._ac_matches[self._ac_idx][len(self._ac_prefix):]
            cursor.insertText(suffix)
            self.setTextCursor(cursor)
            return

        # Extract the word fragment before the cursor
        cursor.movePosition(cursor.MoveOperation.StartOfBlock, cursor.MoveMode.KeepAnchor)
        line_before = cursor.selectedText()
        # Restore cursor position
        cursor = self.textCursor()

        # Find the partial word (letters, digits, underscores, dots)
        match = re.search(r'[\w.]+$', line_before)
        if not match:
            self.insertPlainText("  ")  # no word to complete → just indent
            return

        prefix = match.group()
        prefix_lower = prefix.lower()

        # Find all matches
        matches = [w for w in AUTOCOMPLETE_WORDS if w.lower().startswith(prefix_lower) and w.lower() != prefix_lower]

        if not matches:
            self.insertPlainText("  ")  # no matches → indent
            return

        if len(matches) == 1:
            # Single match — complete it immediately
            suffix = matches[0][len(prefix):]
            cursor.insertText(suffix)
            self.setTextCursor(cursor)
            return

        # Multiple matches — enter cycling mode
        self._ac_matches = matches
        self._ac_idx = 0
        self._ac_prefix = prefix
        suffix = matches[0][len(prefix):]
        cursor.insertText(suffix)
        self.setTextCursor(cursor)

    def _execute(self):
        code = self.toPlainText().strip()
        if not code:
            return
        # Save to history
        if not self._history or self._history[-1] != code:
            self._history.append(code)
        self._hist_idx = len(self._history)

        self.execute_requested.emit(code)
        self.clear()

    # ── History ───────────────────────────────────────────────────────────────

    def _hist_up(self):
        if not self._history:
            return
        self._hist_idx = max(0, self._hist_idx - 1)
        self.setPlainText(self._history[self._hist_idx])
        # Move cursor to end
        cursor = self.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.setTextCursor(cursor)

    def _hist_down(self):
        if not self._history:
            return
        self._hist_idx = min(len(self._history), self._hist_idx + 1)
        if self._hist_idx == len(self._history):
            self.clear()
        else:
            self.setPlainText(self._history[self._hist_idx])
            cursor = self.textCursor()
            cursor.movePosition(cursor.MoveOperation.End)
            self.setTextCursor(cursor)

    # ── Line numbers ──────────────────────────────────────────────────────────

    def _line_number_area_width(self):
        digits = max(2, len(str(self.blockCount())))
        return 10 + self.fontMetrics().horizontalAdvance("9") * digits

    def _update_line_area_width(self):
        self.setViewportMargins(self._line_number_area_width(), 0, 0, 0)

    def _update_line_area(self, rect, dy):
        if dy:
            self._line_area.scroll(0, dy)
        else:
            self._line_area.update(0, rect.y(), self._line_area.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self._update_line_area_width()

    def _paint_line_numbers(self, event):
        painter = QPainter(self._line_area)
        painter.fillRect(event.rect(), QColor(LINE_BG))

        block = self.firstVisibleBlock()
        block_num = block.blockNumber()
        top = int(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + int(self.blockBoundingRect(block).height())

        painter.setFont(QFont("Consolas", 10))
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                painter.setPen(QPen(QColor(COMMENT_COL)))
                painter.drawText(
                    0, top,
                    self._line_area.width() - 6,
                    self.fontMetrics().height(),
                    Qt.AlignmentFlag.AlignRight,
                    str(block_num + 1)
                )
            block = block.next()
            top = bottom
            bottom = top + int(self.blockBoundingRect(block).height())
            block_num += 1

        painter.end()

    def _highlight_current_line(self):
        extras = []
        if not self.isReadOnly():
            sel = QTextEdit.ExtraSelection()
            sel.format.setBackground(QColor(LINE_BG))
            sel.format.setProperty(QTextFormat.Property.FullWidthSelection, True)
            sel.cursor = self.textCursor()
            sel.cursor.clearSelection()
            extras.append(sel)
        self.setExtraSelections(extras)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self._line_area.setGeometry(
            QRect(cr.left(), cr.top(), self._line_number_area_width(), cr.height())
        )
