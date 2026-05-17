# ui/main_window.py
# MainWindow — the outer shell of NEXUS.
# QMainWindow that wires together all UI panels and connects to GameState.

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QSplitter, QFrame, QApplication,
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont, QFontDatabase, QIcon

from ui.hud import HUDBar
from ui.scene_view import SceneView
from ui.cmd_panel import CmdPanel
from ui.concept_popup import ConceptPopup
from ui.codex_panel import CodexPanel
from ui.celebrations import ToastBanner, ScreenFlash, play_chime, play_victory_chime

from core.db import DatabaseInterface
from core.game import GameState
from core.scenes import SCENES, STEP_TEXT, OBJECTIVE_FOCUS
from core.codex import get_concept, all_concepts


# ── Light theme palette ───────────────────────────────────────────────────────

BG           = "#f6f8fa"   # page background
PANEL_BG     = "#ffffff"   # card / panel surface
BORDER       = "#d0d7de"   # subtle border
ACCENT       = "#0969da"   # blue — focus commands, links, prompt
TEXT_MAIN    = "#1f2328"   # primary text
TEXT_DIM     = "#57606a"   # secondary / ambient
SUCCESS      = "#1a7f37"   # green — objective complete
ERROR        = "#cf222e"   # red — SQL errors
WARNING      = "#9a6700"   # amber — hints
SCENE_TITLE  = "#6639ba"   # purple — scene headers / narrative
CODE_BG      = "#eaeef2"   # code block background
INPUT_BG     = "#ffffff"

SCENE_PANEL_W = 420
WINDOW_W      = 1280


GLOBAL_QSS = f"""
/* ── Base ── */
QMainWindow, QWidget {{
    background: {BG};
    color: {TEXT_MAIN};
    font-family: 'Segoe UI', 'SF Pro Text', Arial, sans-serif;
    font-size: 14px;
}}

/* ── Scroll bars ── */
QScrollBar:vertical {{
    background: {BG};
    width: 7px;
    margin: 0;
    border-radius: 3px;
}}
QScrollBar::handle:vertical {{
    background: {BORDER};
    border-radius: 3px;
    min-height: 24px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}
QScrollBar:horizontal {{
    background: {BG};
    height: 7px;
}}
QScrollBar::handle:horizontal {{
    background: {BORDER};
    border-radius: 3px;
}}

/* ── Splitter ── */
QSplitter::handle {{
    background: {BORDER};
    width: 1px;
    height: 1px;
}}

/* ── Frame separators ── */
QFrame[frameShape="4"],
QFrame[frameShape="5"] {{
    color: {BORDER};
    background: {BORDER};
}}

/* ── Tooltip ── */
QToolTip {{
    background: {PANEL_BG};
    color: {TEXT_MAIN};
    border: 1px solid {BORDER};
    padding: 4px 8px;
    border-radius: 4px;
}}
"""


# ── MainWindow ────────────────────────────────────────────────────────────────

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("NEXUS  |  Data Analyst Mystery")
        self.setMinimumSize(QSize(900, 600))
        # Start maximized so input bar is always visible regardless of screen size
        self.showMaximized()

        # Apply global stylesheet
        QApplication.instance().setStyleSheet(GLOBAL_QSS)

        # ── Build game model ─────────────────────────────────────────────────
        self._game = GameState(None)        # db set below
        self._db   = DatabaseInterface(self._game)
        self._game._db = self._db           # complete the circular reference

        # Wire game callbacks
        self._game.on_output       = self._on_output
        self._game.on_popup        = self._on_popup
        self._game.on_scene_change = self._on_scene_change
        self._game.on_status       = self._on_status
        self._game.on_progress     = self._on_progress

        # ── Try to load existing save ────────────────────────────────────────
        self._game.load()

        # ── Build UI ─────────────────────────────────────────────────────────
        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # HUD (top bar)
        self._hud = HUDBar()
        root_layout.addWidget(self._hud)

        # Thin separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFixedHeight(1)
        root_layout.addWidget(sep)

        # Main content: scene art (left) | cmd panel (right)
        self._splitter = QSplitter(Qt.Orientation.Horizontal)
        self._splitter.setHandleWidth(1)
        root_layout.addWidget(self._splitter, stretch=1)

        # Left — scene art
        self._scene_view = SceneView()
        self._scene_view.setMinimumWidth(300)
        self._scene_view.setMaximumWidth(480)
        self._splitter.addWidget(self._scene_view)

        # Right — command panel
        self._cmd = CmdPanel(self._game, self._db)
        self._splitter.addWidget(self._cmd)

        # Splitter proportions: ~38% art, ~62% cmd
        self._splitter.setSizes([SCENE_PANEL_W, WINDOW_W - SCENE_PANEL_W])
        self._splitter.setStretchFactor(0, 0)
        self._splitter.setStretchFactor(1, 1)

        # ── Concept popup (hidden until needed) ─────────────────────────────
        self._popup = ConceptPopup(self)
        self._popup.hide()

        # ── Celebration overlays ──────────────────────────────────────────────
        self._toast = ToastBanner(central)
        self._flash = ScreenFlash(central)

        # ── Codex browser ────────────────────────────────────────────────────
        self._codex = CodexPanel(
            self._game,
            all_concepts(),
            self._show_concept_card,
            parent=self,
        )
        self._hud.codex_btn.clicked.connect(self._open_codex)

        # ── Initial scene render ─────────────────────────────────────────────
        self._render_current_scene()

    # ── Game callbacks ────────────────────────────────────────────────────────

    def _on_output(self, text: str, style: str = "normal") -> None:
        self._cmd.append_output(text, style)

    def _on_popup(self, concept_id: str) -> None:
        concept = get_concept(concept_id)
        if concept:
            self._show_concept_card(concept)

    def _show_concept_card(self, concept: dict) -> None:
        self._popup.load_concept(concept)
        self._popup.show_centered(self)

    def _open_codex(self) -> None:
        self._codex.refresh()
        self._codex.exec()

    def _on_scene_change(self, scene_id: str) -> None:
        self._scene_view.set_scene(scene_id)
        self._render_current_scene()

    def _on_status(self, label: str, value) -> None:
        if label == "clues":
            self._hud.set_clues(value)

    def _on_progress(self, completed_objective_id: str) -> None:
        """Called after each objective completes — celebrate + advance."""
        pct = self._game.progress_pct()
        self._hud.set_progress(pct)
        self._update_focus_box()
        self._show_next_objective_guidance()

        # ── Celebration ──────────────────────────────────────────────────────
        from core.game import OBJECTIVES_BY_ID
        obj = OBJECTIVES_BY_ID.get(completed_objective_id, {})
        label = obj.get("label", "Clue found!")
        done = len(self._game.completed)

        # Green screen flash on every objective
        self._flash.flash("#16a34a", peak_alpha=35, duration=450)

        # Toast banner
        if pct == 100:
            # Final objective — big gold celebration
            self._toast.show_toast(
                "🏆  CASE CLOSED  🏆\nYou uncovered $1,869,500 in fraud.",
                style="gold", duration=5000
            )
            play_victory_chime()
        elif done % 3 == 0:
            # Every 3rd clue — milestone toast
            self._toast.show_toast(
                f"🔥  {done} clues found — keep digging!",
                style="gold", duration=2500
            )
            play_chime()
        else:
            # Regular objective
            self._toast.show_toast(
                f"✔  {label}",
                style="success", duration=2200
            )
            play_chime()

    # ── Scene rendering ───────────────────────────────────────────────────────

    def _render_current_scene(self) -> None:
        scene = SCENES.get(self._game.scene)
        if not scene:
            return

        # Update HUD
        self._hud.set_scene(scene["title"])
        self._hud.set_progress(self._game.progress_pct())
        self._hud.set_clues(len(self._game.clues))

        # Update scene art
        self._scene_view.set_scene(self._game.scene)

        # Update focus command in cmd panel
        self._update_focus_box()

        # Show intro text (if first visit)
        visit_key = f"_visited_{self._game.scene}"
        if not getattr(self, visit_key, False):
            setattr(self, visit_key, True)
            self._cmd.append_output(scene["intro"], style="scene")

        # Show guidance for first incomplete objective
        self._show_next_objective_guidance()

    def _update_focus_box(self) -> None:
        """Set focus box to the first incomplete objective's command."""
        for obj in self._game.objectives_for_scene(self._game.scene):
            oid = obj["id"]
            if oid not in self._game.completed:
                if oid in OBJECTIVE_FOCUS:
                    label, cmd = OBJECTIVE_FOCUS[oid]
                    self._cmd.set_focus(label, cmd)
                return
        # All done in this scene — hide the box
        self._cmd.set_focus("", "")

    def _show_next_objective_guidance(self) -> None:
        for obj in self._game.objectives_for_scene(self._game.scene):
            oid = obj["id"]
            if oid not in self._game.completed:
                text = STEP_TEXT.get(oid)
                if text:
                    self._cmd.append_output(f"\n{text}\n", style="guidance")
                break

    # ── Window close ──────────────────────────────────────────────────────────

    def closeEvent(self, event):
        self._game._save()
        event.accept()
