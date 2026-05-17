# ui/main_window.py
# MainWindow — the outer shell of NEXUS.
# QMainWindow that wires together all UI panels and connects to GameState.

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QSplitter, QFrame, QApplication,
)
from PySide6.QtCore import Qt, QSize, QTimer
from PySide6.QtGui import QFont, QFontDatabase, QIcon

from ui.hud import HUDBar
from ui.scene_view import SceneView
from ui.cmd_panel import CmdPanel
from ui.concept_popup import ConceptPopup
from ui.codex_panel import CodexPanel
from ui.collectibles_panel import CollectiblesPanel
from ui.celebrations import ToastBanner, ScreenFlash, ParticleOverlay, play_chime, play_victory_chime

from core.db import DatabaseInterface
from core.game import GameState
from core.scenes import SCENES, STEP_TEXT, OBJECTIVE_FOCUS
from core.codex import get_concept, all_concepts
from core.collectibles import FIELD_GUIDE_PAGES


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
        self._particles = ParticleOverlay(central)

        # ── Codex browser ────────────────────────────────────────────────────
        self._codex = CodexPanel(
            self._game,
            all_concepts(),
            self._show_concept_card,
            parent=self,
        )
        self._hud.codex_btn.clicked.connect(self._open_codex)

        # ── Collectibles (Field Guide) ──────────────────────────────────────
        self._collectibles = CollectiblesPanel(
            self._game, FIELD_GUIDE_PAGES, parent=self,
        )
        self._hud.docs_btn.clicked.connect(self._open_field_guide)

        # ── Spirit guide ambient tips ────────────────────────────────────────
        self._spirit_timer = QTimer(self)
        self._spirit_timer.timeout.connect(self._spirit_tip)
        self._spirit_timer.start(90_000)  # check every 90 seconds
        self._last_query_count = 0

        # ── Initial scene render ─────────────────────────────────────────────
        self._scene_view.set_clues(self._game.clues)
        self._render_current_scene()

    # ── Game callbacks ────────────────────────────────────────────────────────

    def _on_output(self, text: str, style: str = "normal") -> None:
        self._cmd.append_output(text, style)

    def _on_popup(self, concept_id: str) -> None:
        concept = get_concept(concept_id)
        if concept:
            self._show_concept_card(concept)

    def _show_concept_card(self, concept: dict) -> None:
        # Build "Story So Far" — narrative recap of what the player did
        story = self._build_story_recap()
        self._popup.load_concept(concept, story_so_far=story)
        self._popup.show_centered(self)

    def _build_story_recap(self) -> str:
        """Build a plain-English narrative of the investigation so far."""
        from core.game import OBJECTIVES_BY_ID

        # Map objective IDs → story beats (what happened + what you found)
        STORY_BEATS = {
            "list_tables":
                "You logged into the Nexus database and found 5 tables: "
                "employees, vendors, transactions, departments, and projects.",
            "examine_employees":
                "You pulled the employee roster — 10 people including yourself, Alex Chen.",
            "count_employees":
                "You counted 10 employees total. Sam from accounting was impressed.",
            "find_high_spend_vendors":
                "You ranked vendors by total spend. Two vendors stood out with "
                "massive payments — vendor IDs 4 and 7.",
            "spot_unverified_vendors":
                "You checked which vendors aren't verified. Two came back: "
                "Apex Solutions LLC and Pinnacle Strategy Group. No address. No phone.",
            "join_transactions_vendors":
                "You linked transactions to vendor names and confirmed — all the "
                "big unverified payments go to Apex and Pinnacle.",
            "find_approver":
                "You checked who approved these payments. One employee ID kept "
                "showing up on every suspicious transaction: employee #4.",
            "lookup_employee_4":
                "You looked up employee #4. Marcus Webb — the CFO.",
            "check_special_projects_budget":
                "You checked department budgets. Special Projects has $4.8M — "
                "way more than any other department. That's where the money hides.",
            "total_apex_spend":
                "You totalled all payments to Apex Solutions: over $1.2 million "
                "to a company with no address.",
            "escalation_pattern":
                "You pulled Apex transactions by date. The amounts are escalating — "
                "$87K → $243K in 9 months. He's getting bolder.",
            "dual_vendor_fraud":
                "You queried both shell companies together. Same approver, "
                "same pattern, thirteen months of payments.",
            "total_fraud_amount":
                "You calculated the total: $1,869,500 stolen through two "
                "shell companies, all approved by the CFO.",
        }

        completed = self._game.completed
        if not completed:
            return ""

        # Build recap from completed objectives in order
        beats = []
        for oid in completed:
            beat = STORY_BEATS.get(oid)
            if beat:
                beats.append(f"→ {beat}")

        if not beats:
            return ""

        return "\n".join(beats)

    def _open_codex(self) -> None:
        self._codex.refresh()
        self._codex.exec()

    def _open_field_guide(self) -> None:
        self._collectibles.refresh()
        self._collectibles.exec()

    def _spirit_tip(self) -> None:
        """Sam the spirit guide drops occasional contextual tips."""
        import random

        # Only trigger if the player seems stuck (no new queries since last check)
        current_qc = self._game._query_count
        if current_qc == self._last_query_count and current_qc > 0:
            tips = [
                "👻  Sam whispers: 'Try typing  hint  if you're stuck. No shame in it.'",
                "👻  Sam whispers: 'Remember — you can press Tab to autocomplete SQL keywords.'",
                "👻  Sam whispers: 'Check your Clue Log on the left. Sometimes the answer is in what you already found.'",
                "👻  Sam whispers: 'The  show solution  toggle won't judge you. Promise.'",
                "👻  Sam whispers: 'Ctrl+Up brings back your last command. Saves typing.'",
                "👻  Sam whispers: '...is it cold in here, or is that just the server room?'",
            ]
            tip = random.choice(tips)
            self._cmd.append_output(f"\n{tip}\n", style="spirit")
        self._last_query_count = current_qc

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

        # ── Update clue sidebar ──────────────────────────────────────────────
        self._scene_view.set_clues(self._game.clues)

        # ── Celebration ──────────────────────────────────────────────────────
        from core.game import OBJECTIVES_BY_ID
        obj = OBJECTIVES_BY_ID.get(completed_objective_id, {})
        label = obj.get("label", "Clue found!")
        done = len(self._game.completed)

        # Green screen flash on every objective
        self._flash.flash("#16a34a", peak_alpha=35, duration=450)

        # Toast banner + particles
        if pct == 100:
            # Final objective — massive celebration
            self._toast.show_toast(
                "🏆  CASE CLOSED  🏆\nYou uncovered $1,869,500 in fraud.",
                style="final", duration=15000,
            )
            self._particles.burst("final")
            play_victory_chime()
        elif done % 3 == 0:
            # Every 3rd clue — milestone toast + particle burst
            self._toast.show_toast(
                f"🔥  {done} clues found — keep digging!",
                style="gold", duration=10000,
            )
            self._particles.burst("gold")
            play_chime()
        else:
            # Regular objective — center-screen with career messaging
            self._toast.show_toast(
                f"✔  {label}",
                style="success", duration=10000,
            )
            self._particles.burst("success")
            play_chime()

        # ── Delayed concept popup — fires AFTER celebration is visible ───────
        if self._game.pending_popups:
            concept_id = self._game.pending_popups.pop(0)
            # Dismiss toast before showing popup, then open popup
            def _show_popup_after_toast(cid=concept_id):
                self._toast._dismiss()
                QTimer.singleShot(400, lambda: self._on_popup(cid))
            QTimer.singleShot(3000, _show_popup_after_toast)

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
