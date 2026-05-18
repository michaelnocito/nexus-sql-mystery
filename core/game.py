# core/game.py
# GameState — the brain of NEXUS.
# Manages scene progression, objective tracking, clue discovery,
# and routes events to the UI layer via callback slots.

import json
import re
from datetime import datetime


# ── Scene/step progress constants ────────────────────────────────────────────

SCENE_YOUR_DESK       = "your_desk"
SCENE_DB_TERMINAL     = "db_terminal"
SCENE_HR_FILES        = "hr_files"
SCENE_CFO_DEPT        = "cfo_dept"
SCENE_AUDIT_TRAIL     = "audit_trail"
SCENE_CONFRONTATION   = "confrontation"


# ── Objective definitions ─────────────────────────────────────────────────────
# Each objective has:
#   id        — unique string key
#   scene     — which scene it belongs to
#   label     — short display label (shown in HUD / clue log)
#   detail    — longer description for the codex / popup
#   validator — callable(sql, result) → bool: did this query satisfy it?

def _sql_contains(*fragments):
    """Return a validator that checks all fragments appear in the SQL (case-insensitive)."""
    frags = [f.lower() for f in fragments]
    def validate(sql, result):
        low = sql.lower()
        return all(f in low for f in frags) and len(result) > 0
    return validate

def _result_has_value(column, value):
    """Return a validator that checks a column contains a specific value in any row."""
    def validate(sql, result):
        if not result.columns:
            return False
        try:
            idx = [c.lower() for c in result.columns].index(column.lower())
            return any(str(row[idx]) == str(value) for row in result.rows)
        except ValueError:
            return False
    return validate

def _result_row_count(minimum):
    """Return a validator that checks result has at least N rows."""
    def validate(sql, result):
        return len(result) >= minimum
    return validate


OBJECTIVES = [
    # ── Scene: your_desk ─────────────────────────────────────────────────────
    {
        "id":        "list_tables",
        "scene":     SCENE_YOUR_DESK,
        "label":     "Discovered available tables",
        "detail":    "Used db.tables() or queried sqlite_master to see what data exists.",
        "concept":   "tables",
        "validator": lambda sql, r: (
            "sqlite_master" in sql.lower() or
            ("name" in [c.lower() for c in r.columns] and len(r) >= 3)
        ),
    },
    {
        "id":        "examine_employees",
        "scene":     SCENE_YOUR_DESK,
        "label":     "Pulled the employee roster",
        "detail":    "Ran SELECT on the employees table — confirmed your own record is in there.",
        "concept":   "select_star",
        "validator": _sql_contains("select", "from", "employees"),
    },
    {
        "id":        "count_employees",
        "scene":     SCENE_YOUR_DESK,
        "label":     "Counted total headcount",
        "detail":    "Used COUNT(*) to measure how many employees Nexus has.",
        "concept":   "aggregate_count",
        "validator": _sql_contains("count", "employees"),
    },

    # ── Scene: db_terminal ───────────────────────────────────────────────────
    {
        "id":        "find_high_spend_vendors",
        "scene":     SCENE_DB_TERMINAL,
        "label":     "Found top vendors by spend",
        "detail":    "Used GROUP BY + SUM to rank vendors by total transaction amount.",
        "concept":   "group_by_sum",
        "validator": lambda sql, r: _sql_contains("group by", "vendor_id")(sql, r) and _sql_contains("sum")(sql, r),
    },
    {
        "id":        "spot_unverified_vendors",
        "scene":     SCENE_DB_TERMINAL,
        "label":     "Flagged unverified vendors",
        "detail":    "Queried vendors WHERE verified = 0 — found two with no address.",
        "concept":   "where_filter",
        "validator": _sql_contains("vendor", "verified"),
    },
    {
        "id":        "join_transactions_vendors",
        "scene":     SCENE_DB_TERMINAL,
        "label":     "Linked transactions to vendor names",
        "detail":    "Wrote a JOIN to attach vendor names to transaction records.",
        "concept":   "inner_join",
        "validator": _sql_contains("join", "vendor", "transaction"),
    },

    # ── Scene: hr_files ──────────────────────────────────────────────────────
    {
        "id":        "find_approver",
        "scene":     SCENE_HR_FILES,
        "label":     "Identified the approver",
        "detail":    "Discovered that approved_by = 4 on every suspicious transaction.",
        "concept":   "where_equals",
        "validator": _sql_contains("approved_by"),
    },
    {
        "id":        "lookup_employee_4",
        "scene":     SCENE_HR_FILES,
        "label":     "Looked up employee #4",
        "detail":    "Queried employees WHERE id = 4 — Marcus Webb, CFO.",
        "concept":   "primary_key_lookup",
        "validator": _sql_contains("employees", "id", "4"),
    },
    {
        "id":        "check_special_projects_budget",
        "scene":     SCENE_HR_FILES,
        "label":     "Checked Special Projects budget",
        "detail":    "Found Special Projects has a $4.8M budget — far larger than any other dept.",
        "concept":   "order_by",
        "validator": _sql_contains("department", "budget"),
    },

    # ── Scene: cfo_dept ──────────────────────────────────────────────────────
    {
        "id":        "total_apex_spend",
        "scene":     SCENE_CFO_DEPT,
        "label":     "Totalled Apex Solutions payments",
        "detail":    "SUM of all transactions to vendor_id 4 (Apex Solutions LLC) — over $1.2M.",
        "concept":   "sum_where",
        "validator": _sql_contains("sum", "vendor_id"),
    },
    {
        "id":        "escalation_pattern",
        "scene":     SCENE_CFO_DEPT,
        "label":     "Spotted the escalation pattern",
        "detail":    "Ordered Apex transactions by date — amounts grew from $87K to $243K in 9 months.",
        "concept":   "order_by_date",
        "validator": _sql_contains("vendor_id", "order by", "date"),
    },

    # ── Scene: audit_trail ───────────────────────────────────────────────────
    {
        "id":        "dual_vendor_fraud",
        "scene":     SCENE_AUDIT_TRAIL,
        "label":     "Linked Apex + Pinnacle to same approver",
        "detail":    "Both shell vendors were approved exclusively by Marcus Webb (id=4).",
        "concept":   "in_clause",
        "validator": _sql_contains("vendor_id", "in"),
    },
    {
        "id":        "total_fraud_amount",
        "scene":     SCENE_AUDIT_TRAIL,
        "label":     "Calculated total fraudulent spend",
        "detail":    "Combined SUM of Apex + Pinnacle payments — the full theft amount.",
        "concept":   "subquery_or_having",
        "validator": lambda sql, r: _sql_contains("sum")(sql, r) and _sql_contains("vendor_id")(sql, r),
    },
]

# Fast lookup by id
OBJECTIVES_BY_ID = {o["id"]: o for o in OBJECTIVES}


# ── GameState ─────────────────────────────────────────────────────────────────

class GameState:
    """
    Central controller for NEXUS.

    The UI layer hooks into this via three callbacks:
        state.on_output   = fn(text, style)   — narrative / result text
        state.on_popup    = fn(concept_id)     — show concept card
        state.on_scene_change = fn(scene_id)  — repaint scene art
    """

    def __init__(self, db):
        self._db   = db   # DatabaseInterface (circular ref is fine — db holds game)
        self.scene = SCENE_YOUR_DESK
        self.step  = 0     # step index within current scene

        # Completed objective ids (ordered by discovery time)
        self.completed: list[str] = []

        # Clues: free-form strings the narrative layer appends
        self.clues: list[str] = []

        # Pending concept popups queue (strings — codex concept ids)
        self.pending_popups: list[str] = []

        # Current season (1 or 2) — persisted in save_state
        self.current_season: int = 1

        # ── UI callbacks (set by MainWindow after construction) ───────────────
        self.on_output:       callable = lambda text, style="normal": None
        self.on_dialogue:     callable = lambda speaker, text: None  # NPC speech bubble
        self.on_popup:        callable = lambda concept_id: None
        self.on_scene_change: callable = lambda scene_id: None
        self.on_status:       callable = lambda label, value: None  # HUD update
        self.on_progress:     callable = lambda objective_id: None  # console celebration
        self.on_season_change: callable = lambda season: None       # season transition
        # STORY panel (WHY + beat + reaction + recall) — never in the feed
        self.on_story:        callable = lambda kind, text: None     # kind: why|beat|recall
        # BRIEFING (left panel): in-story GOAL + the plain-language path
        self.on_briefing:     callable = lambda goal, move: None

        # Track query count for pacing
        self._query_count = 0

        # Varied-practice / narrative state
        self._concepts_shown: set = set()   # skill cards shown once only
        self._recall_pending = None         # active between-scene recall gate
        self._recall_tries = 0
        self._recall_done: set = set()      # scenes whose exit-gate cleared

    # ── Objective tracking ────────────────────────────────────────────────────

    def _active_objectives(self) -> list[dict]:
        """Return the full objective list for the current season."""
        if self.current_season == 2:
            from core.season2_game import S2_OBJECTIVES
            return S2_OBJECTIVES
        return OBJECTIVES

    def on_query(self, sql: str, result) -> None:
        """Called by DatabaseInterface after every successful query."""
        self._query_count += 1

        # A between-scene recall gate intercepts everything until cleared.
        if self._recall_pending is not None:
            self._handle_recall(sql)
            return

        # Only validate the CURRENT scene's objectives. This keeps
        # progression strictly linear — a broad query can't pre-complete
        # a later scene (S2's SQL validators are loose and all touch
        # server_logs, which previously let players skip ahead and land
        # on an already-finished scene with nothing to do).
        for obj in list(self.objectives_for_scene(self.scene)):
            if obj["id"] in self.completed:
                continue
            try:
                if obj["validator"](sql, result):
                    self._complete_objective(obj)
            except Exception:
                pass  # validator bugs should never crash the game

        # Concept popup is now deferred — MainWindow fires it via QTimer
        # after the query result has rendered in the narrative panel.
        # See MainWindow._on_progress() for the delayed popup trigger.

    def _complete_objective(self, obj: dict) -> None:
        self.completed.append(obj["id"])
        clue = f"[CLUE #{len(self.completed)}] {obj['label']}"
        self.clues.append(clue)

        # Concept card shows ONCE per skill (first encounter). The second,
        # varied-practice rep deliberately does not re-teach.
        concept = obj.get("concept")
        if concept and concept not in self._concepts_shown:
            self._concepts_shown.add(concept)
            self.pending_popups.append(concept)

        # The UI layer must never strand the player — if a render/celebration
        # callback throws, progression still has to run. Surface, don't swallow.
        try:
            self.on_output(f"\n✔  {obj['label']}\n", style="success")
            self.on_status("clues", len(self.completed))
            if self.current_season == 2:
                self._emit_completion_story(obj)
            self.on_progress(obj["id"])
        except Exception:
            import traceback, sys
            traceback.print_exc(file=sys.stderr)
        finally:
            # Always check scene unlock, even if the UI callbacks failed.
            self._check_scene_unlock()

    def _emit_completion_story(self, obj: dict) -> None:
        """STORY panel: the result-reaction, then chain the next setup beat."""
        from core.season2_game import (
            S2_RESULT_REACTION, S2_SETUP, S2_YOUR_MOVE, S2_SCENE_OBJ_ORDER,
        )
        oid = obj["id"]
        reaction = S2_RESULT_REACTION.get(oid, "")
        order = S2_SCENE_OBJ_ORDER.get(obj["scene"], [])
        nxt, seen = None, False
        for x in order:
            if x == oid:
                seen = True
                continue
            if seen and x not in self.completed:
                nxt = x
                break
        if nxt:
            beat = reaction + "\n\n— — — — — — —\n\n" + S2_SETUP.get(nxt, "")
            self.on_story("beat", beat)
            g, m = S2_YOUR_MOVE.get(nxt, ("", ""))
            self.on_briefing(g, m)
        else:
            self.on_story("beat", reaction)

    def _emit_scene_state(self) -> None:
        """STORY panel WHY + current setup beat + BRIEFING for the active objective."""
        if self.current_season != 2:
            return
        from core.season2_game import S2_SCENE_WHY, S2_SETUP, S2_YOUR_MOVE
        self.on_story("why", S2_SCENE_WHY.get(self.scene, ""))
        for obj in self.objectives_for_scene(self.scene):
            if obj["id"] not in self.completed:
                self.on_story("beat", S2_SETUP.get(obj["id"], ""))
                g, m = S2_YOUR_MOVE.get(obj["id"], ("", ""))
                self.on_briefing(g, m)
                return

    def emit_scene_state(self) -> None:
        """Public: let the UI (re)paint the STORY/BRIEFING for the current scene."""
        self._emit_scene_state()

    def _handle_recall(self, sql: str) -> None:
        """Non-punishing between-scene retrieval gate. 2 misses -> reveal+pass."""
        ch = self._recall_pending
        s = sql.lower()
        if all(k.lower() in s for k in ch["keywords"]):
            self.on_story("recall", "✔  Correct. That one's yours. Moving on.")
            self._recall_done.add(self.scene)
            self._recall_pending = None
            self._check_scene_unlock()
            return
        self._recall_tries += 1
        if self._recall_tries >= 2:
            self.on_story("recall",
                "No worries — here's the shape of it:\n\n    "
                + ch["answer"] + "\n\nKeep it in your pocket. Moving on.")
            self._recall_done.add(self.scene)
            self._recall_pending = None
            self._check_scene_unlock()
        else:
            self.on_story("recall",
                "Not quite — give it one more shot.\n\n" + ch["question"])

    def on_exec(self, code: str, output: str) -> None:
        """
        Called after raw Python code executes. Season 2's main path is now
        SQL — objectives validate through on_query(sql, result) like Season 1
        (the player runs db.query(...), which routes there). This hook is a
        no-op until the future Pro-Panel Python side-quest spec wires it up.
        """
        return

    def on_error(self, msg: str) -> None:
        """Called by DatabaseInterface on SQL errors."""
        self.on_output(f"\n⚠  {msg}\n", style="error")

    # ── Scene progression ─────────────────────────────────────────────────────

    def objectives_for_scene(self, scene_id: str) -> list[dict]:
        return [o for o in self._active_objectives() if o["scene"] == scene_id]

    def scene_complete(self, scene_id: str) -> bool:
        needed = {o["id"] for o in self.objectives_for_scene(scene_id)}
        return needed.issubset(set(self.completed))

    def _check_scene_unlock(self) -> None:
        if self.current_season == 1:
            order = [
                SCENE_YOUR_DESK, SCENE_DB_TERMINAL, SCENE_HR_FILES,
                SCENE_CFO_DEPT, SCENE_AUDIT_TRAIL, SCENE_CONFRONTATION,
            ]
            # Keep advancing while the current scene is fully complete —
            # never strand the player on a finished scene.
            while self.scene in order and self.scene_complete(self.scene):
                idx = order.index(self.scene)
                if idx < len(order) - 1:
                    self._advance_to_scene(order[idx + 1])
                elif self.s1_complete():
                    self.transition_to_season2()
                    return
                else:
                    break
        else:
            from core.season2_game import (
                S2_SCENE_SERVER_LOGS, S2_SCENE_GHOST_RECORDS,
                S2_SCENE_TIMESTAMP, S2_SCENE_ARCHIVE,
                S2_SCENE_PATTERN_DECODER, S2_SCENE_THE_SIGNAL,
            )
            order = [
                S2_SCENE_SERVER_LOGS, S2_SCENE_GHOST_RECORDS,
                S2_SCENE_TIMESTAMP, S2_SCENE_ARCHIVE,
                S2_SCENE_PATTERN_DECODER, S2_SCENE_THE_SIGNAL,
            ]
            while self.scene in order and self.scene_complete(self.scene):
                idx = order.index(self.scene)
                if idx < len(order) - 1:
                    # Between-scene RECALL GATE: practise a skill again before
                    # moving on. Non-punishing; never hard-blocks.
                    if self.scene not in self._recall_done:
                        ch = self.get_recall_challenge()
                        if ch:
                            self._recall_pending = ch
                            self._recall_tries = 0
                            self.on_story("recall",
                                "Before the next room — prove you've still got "
                                "this. Answer in the editor:\n\n" + ch["question"])
                            return
                        self._recall_done.add(self.scene)  # nothing to recall
                    self._advance_to_scene(order[idx + 1])
                else:
                    self._finish_season2()
                    break

    def s1_complete(self) -> bool:
        """True when every Season 1 objective has been completed."""
        s1_ids = {o["id"] for o in OBJECTIVES}
        return s1_ids.issubset(set(self.completed))

    def transition_to_season2(self) -> None:
        """Flip to Season 2, seed the DB, and load the first S2 scene."""
        from core.season2_game import S2_SCENE_SERVER_LOGS
        self.current_season = 2
        self.scene = S2_SCENE_SERVER_LOGS
        self.step  = 0
        self._save()
        self.on_season_change(2)

    def _finish_season2(self) -> None:
        """Season 2 fully solved — real ending via the STORY panel."""
        if getattr(self, "_s2_finished", False):
            return
        self._s2_finished = True
        self._save()
        self.on_story("why",
            "SEASON 2 COMPLETE — THE GHOST IN THE MACHINE\n\n"
            "You proved it with SQL alone. The phantom was Elena's dead\n"
            "man's switch — a whistleblower's last safeguard. Every query\n"
            "you wrote was evidence. The case holds.\n\n"
            "Season 3 is coming. For now: well done, analyst.")
        self.on_briefing("Case closed", "Season 2 complete — Season 3 is coming.")
        self.on_output("\n✔  Season 2 complete.\n", style="success")

    def _advance_to_scene(self, scene_id: str) -> None:
        if self.current_season == 1:
            # Season 1 unchanged: cliffhanger + intro in the feed.
            from core.scenes import CLIFFHANGERS
            cliffhanger = CLIFFHANGERS.get(self.scene)
            if cliffhanger:
                self.on_output(f"\n{cliffhanger}\n", style="scene")
            self.scene = scene_id
            self.step  = 0
            self.on_scene_change(scene_id)
            self._save()
            intro = SCENE_INTROS.get(scene_id, "")
            if intro:
                self.on_output(f"\n{'─'*60}\n{intro}\n{'─'*60}\n", style="scene")
        else:
            # Season 2: story lives in the STORY panel, never the feed.
            self.scene = scene_id
            self.step  = 0
            self.on_scene_change(scene_id)
            self._save()
            self._emit_scene_state()

    # ── Hint system ──────────────────────────────────────────────────────────

    def get_hint(self) -> str:
        """Return the next hint for the first incomplete objective in this scene."""
        if self.current_season == 2:
            from core.season2_game import S2_HINTS
            hint_bank = S2_HINTS
        else:
            hint_bank = HINTS
        for obj in self.objectives_for_scene(self.scene):
            if obj["id"] not in self.completed:
                hints = hint_bank.get(obj["id"], [])
                attr = f"_hint_idx_{obj['id']}"
                idx = getattr(self, attr, 0)
                if idx < len(hints):
                    setattr(self, attr, idx + 1)
                    return hints[idx]
                elif hints:
                    return hints[-1]
                else:
                    return f"Focus on this goal: {obj['label']}"
        return "You've cleared every objective in this area — nothing more to query here. Read the latest entry above."

    # ── Recall Gate (spaced retrieval) ────────────────────────────────────────

    def get_recall_challenge(self) -> dict | None:
        """
        Return a recall challenge for a recently completed concept, or None.
        Called between scene transitions.
        """
        if len(self.completed) < 2:
            return None
        target_id = self.completed[-2]
        if self.current_season == 2:
            from core.season2_game import S2_OBJECTIVES_BY_ID, S2_RECALL_CHALLENGES
            obj = S2_OBJECTIVES_BY_ID.get(target_id)
            challenge = S2_RECALL_CHALLENGES.get(obj.get("concept")) if obj else None
        else:
            obj = OBJECTIVES_BY_ID.get(target_id)
            challenge = RECALL_CHALLENGES.get(obj.get("concept")) if obj else None
        return challenge

    # ── Persistence ───────────────────────────────────────────────────────────

    def _save(self) -> None:
        try:
            conn = self._db._connect()
            conn.execute(
                "UPDATE save_state SET scene=?, clues=?, objectives=?, saved_at=?, season=? WHERE id=1",
                (
                    self.scene,
                    json.dumps(self.clues),
                    json.dumps(self.completed),
                    datetime.now().isoformat(timespec="seconds"),
                    self.current_season,
                )
            )
            conn.commit()
        except Exception:
            pass  # Save failure should never crash the game

    def load(self) -> None:
        """Restore from save_state table. Migrates older saves that lack the season column."""
        try:
            conn = self._db._connect()
            # Add season column if this is an older save without it
            cols = [r[1] for r in conn.execute("PRAGMA table_info(save_state)").fetchall()]
            if "season" not in cols:
                conn.execute("ALTER TABLE save_state ADD COLUMN season INTEGER DEFAULT 1")
                conn.commit()
            row = conn.execute("SELECT * FROM save_state WHERE id=1").fetchone()
            if row:
                self.scene          = row["scene"]      or SCENE_YOUR_DESK
                self.clues          = json.loads(row["clues"]       or "[]")
                self.completed      = json.loads(row["objectives"]  or "[]")
                self.current_season = row["season"] if row["season"] is not None else 1
        except Exception:
            pass

    # ── Utility ───────────────────────────────────────────────────────────────

    def progress_pct(self) -> int:
        from core.season2_game import S2_OBJECTIVES
        all_objs = OBJECTIVES if self.current_season == 1 else S2_OBJECTIVES
        total = len(all_objs)
        s1_done = sum(1 for c in self.completed if c in {o["id"] for o in OBJECTIVES})
        s2_done = sum(1 for c in self.completed if c not in {o["id"] for o in OBJECTIVES})
        done = s1_done if self.current_season == 1 else s2_done
        return int(100 * done / total) if total else 0

    def __repr__(self):
        return (
            f"<GameState season={self.current_season} scene={self.scene!r} "
            f"clues={len(self.clues)}>"
        )


# ── Scene intro text ─────────────────────────────────────────────────────────

SCENE_INTROS = {
    SCENE_DB_TERMINAL: (
        "You plug into the secure terminal. The server room hums like a living thing.\n"
        "Nobody comes down to B1 unless they have to.\n"
        "The full transaction log is open. Every payment. Every vendor. Every dollar.\n\n"
        "Something in this data doesn't add up. Start digging."
    ),
    SCENE_HR_FILES: (
        "Vanessa's still at lunch. The filing cabinet is unlocked.\n"
        "You pull the personnel records. Every transaction has an approved_by field.\n"
        "Someone signed off on those suspicious payments.\n\n"
        "Time to find out who."
    ),
    SCENE_CFO_DEPT: (
        "Marcus Webb — board meeting until 4pm.\n"
        "His assistant waves you in to 'drop off a budget report.'\n"
        "You have maybe 20 minutes. His desktop is still logged in.\n\n"
        "Don't waste them."
    ),
    SCENE_AUDIT_TRAIL: (
        "Back at your desk. The office is dark. Everyone's gone home.\n"
        "You've got the pieces — now build the case.\n"
        "Numbers that hold up. Evidence that doesn't blink.\n\n"
        "Gut feelings don't go in an audit report. SQL does."
    ),
    SCENE_CONFRONTATION: (
        "You have everything. Apex Solutions. Pinnacle Strategy. $1.87M.\n"
        "All approved by the CFO. All billed to 'Special Projects.'\n\n"
        "Your phone buzzes: Rachel Kim (COO) — 'Got a minute? My office.'\n"
        "Four words that change everything."
    ),
}


# ── Progressive hints ─────────────────────────────────────────────────────────
# Each list goes from vague → specific → gives away the answer.

HINTS = {
    "list_tables": [
        "Diana's note said to get familiar with the database. You can't investigate what you can't see — what's even in this thing?",
        "Use db.tables() to see what's available. Or if you're feeling fancy: db.query(\"SELECT name FROM sqlite_master WHERE type='table'\")",
    ],
    "examine_employees": [
        "You know the tables now. Pick one and peek inside — the employees table seems like a good place to start.",
        "db.query(\"SELECT * FROM employees\")  — SELECT * means 'show me everything.'",
    ],
    "count_employees": [
        "Sam from accounting just pinged you: 'Hey new person — quick question. How many of us are there?' SQL can count.",
        "db.query(\"SELECT COUNT(*) FROM employees\")  — COUNT(*) counts every row in the table.",
    ],
    "find_high_spend_vendors": [
        "28 transactions. You could read them all, or you could be smart about it. Which vendors are getting the biggest checks?",
        "GROUP BY bundles rows together. SUM(amount) adds them up. Put the biggest first with ORDER BY ... DESC.",
        "db.query(\"SELECT vendor_id, SUM(amount) FROM transactions GROUP BY vendor_id ORDER BY SUM(amount) DESC\")",
    ],
    "spot_unverified_vendors": [
        "Some of these vendor numbers look suspicious. But are they legit companies? The vendors table should tell you who's been verified.",
        "The verified column is 1 for yes, 0 for no. Use WHERE to filter.",
        "db.query(\"SELECT * FROM vendors WHERE verified = 0\")",
    ],
    "join_transactions_vendors": [
        "Vendor IDs are just numbers. You need names. The trick? Connect the transactions table to the vendors table.",
        "JOIN links two tables on a shared column — transactions.vendor_id matches vendors.id.",
        "db.query(\"SELECT t.*, v.name FROM transactions t JOIN vendors v ON t.vendor_id = v.id\")",
    ],
    "find_approver": [
        "Every one of these transactions was approved by somebody. The approved_by column has their employee ID. Is it always the same person?",
        "db.query(\"SELECT approved_by, COUNT(*) FROM transactions GROUP BY approved_by ORDER BY COUNT(*) DESC\")",
    ],
    "lookup_employee_4": [
        "That employee ID keeps showing up. It's time to put a face to the number.",
        "db.query(\"SELECT * FROM employees WHERE id = 4\")  — one row, one person, one answer.",
    ],
    "check_special_projects_budget": [
        "All the suspicious money flows through 'Special Projects.' How does that department's budget compare to the others?",
        "db.query(\"SELECT * FROM departments ORDER BY budget DESC\")  — biggest budgets first.",
    ],
    "total_apex_spend": [
        "Apex Solutions LLC. Unverified. No address. No phone number. How much has Nexus paid this ghost company?",
        "db.query(\"SELECT SUM(amount) FROM transactions WHERE vendor_id = 4\")  — brace yourself.",
    ],
    "escalation_pattern": [
        "Pull the Apex transactions in order by date. Watch the amounts. Month by month. See if you notice anything.",
        "db.query(\"SELECT date, amount, description FROM transactions WHERE vendor_id = 4 ORDER BY date\")",
    ],
    "dual_vendor_fraud": [
        "Two shell companies. Same pattern. SQL's IN clause lets you query for both in a single shot.",
        "db.query(\"SELECT * FROM transactions WHERE vendor_id IN (4, 7) ORDER BY date\")",
    ],
    "total_fraud_amount": [
        "Last query. The number that goes in the report. Total payments to both shell companies combined.",
        "db.query(\"SELECT SUM(amount) FROM transactions WHERE vendor_id IN (4, 7)\")  — this is the figure Rachel needs.",
    ],
}


# ── Recall challenges ─────────────────────────────────────────────────────────
# Shown between scene transitions as a quick retrieval practice card.
# Format: question + expected_keywords (any match counts as correct)

RECALL_CHALLENGES = {
    "select_star": {
        "question": "What SQL command retrieves every column from a table called 'sales'?",
        "answer":   "SELECT * FROM sales",
        "keywords": ["select", "from", "sales"],
        "concept":  "select_star",
    },
    "aggregate_count": {
        "question": "Write SQL to count the total number of rows in the 'orders' table.",
        "answer":   "SELECT COUNT(*) FROM orders",
        "keywords": ["count", "orders"],
        "concept":  "aggregate_count",
    },
    "where_filter": {
        "question": "How would you get only the rows where the 'status' column equals 'active'?",
        "answer":   "WHERE status = 'active'",
        "keywords": ["where", "status", "active"],
        "concept":  "where_filter",
    },
    "group_by_sum": {
        "question": "What two keywords do you need to total up sales amounts per region?",
        "answer":   "GROUP BY and SUM()",
        "keywords": ["group by", "sum"],
        "concept":  "group_by_sum",
    },
    "inner_join": {
        "question": "What SQL keyword connects rows from two tables based on a shared column?",
        "answer":   "JOIN (or INNER JOIN)",
        "keywords": ["join"],
        "concept":  "inner_join",
    },
    "order_by": {
        "question": "What clause sorts your query results from highest to lowest?",
        "answer":   "ORDER BY ... DESC",
        "keywords": ["order by", "desc"],
        "concept":  "order_by",
    },
    "in_clause": {
        "question": "What SQL keyword lets you match a column against a list of values (e.g., ids 4 and 7)?",
        "answer":   "IN (4, 7)",
        "keywords": ["in"],
        "concept":  "in_clause",
    },
}
