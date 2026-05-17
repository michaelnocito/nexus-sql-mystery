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

        # ── UI callbacks (set by MainWindow after construction) ───────────────
        self.on_output:       callable = lambda text, style="normal": None
        self.on_popup:        callable = lambda concept_id: None
        self.on_scene_change: callable = lambda scene_id: None
        self.on_status:       callable = lambda label, value: None  # HUD update
        self.on_progress:     callable = lambda objective_id: None  # focus box update

        # Track query count for pacing
        self._query_count = 0

    # ── Objective tracking ────────────────────────────────────────────────────

    def on_query(self, sql: str, result) -> None:
        """Called by DatabaseInterface after every successful query."""
        self._query_count += 1

        # Check every incomplete objective for the current (and previous) scenes
        for obj in OBJECTIVES:
            if obj["id"] in self.completed:
                continue
            try:
                if obj["validator"](sql, result):
                    self._complete_objective(obj)
            except Exception:
                pass  # validator bugs should never crash the game

        # Route concept popup if one is queued
        if self.pending_popups:
            concept = self.pending_popups.pop(0)
            self.on_popup(concept)

    def _complete_objective(self, obj: dict) -> None:
        self.completed.append(obj["id"])
        clue = f"[CLUE #{len(self.completed)}] {obj['label']}"
        self.clues.append(clue)

        # Queue the teaching concept for a popup
        if "concept" in obj:
            self.pending_popups.append(obj["concept"])

        # Emit narrative feedback
        self.on_output(
            f"\n✔  {obj['label']}\n"
            f"   {obj['detail']}\n",
            style="success"
        )
        self.on_status("clues", len(self.completed))
        self.on_progress(obj["id"])

        # Check if this unlocks the next scene
        self._check_scene_unlock()

    def on_error(self, msg: str) -> None:
        """Called by DatabaseInterface on SQL errors."""
        self.on_output(f"\n⚠  {msg}\n", style="error")

    # ── Scene progression ─────────────────────────────────────────────────────

    def objectives_for_scene(self, scene_id: str) -> list[dict]:
        return [o for o in OBJECTIVES if o["scene"] == scene_id]

    def scene_complete(self, scene_id: str) -> bool:
        needed = {o["id"] for o in self.objectives_for_scene(scene_id)}
        return needed.issubset(set(self.completed))

    def _check_scene_unlock(self) -> None:
        scene_order = [
            SCENE_YOUR_DESK,
            SCENE_DB_TERMINAL,
            SCENE_HR_FILES,
            SCENE_CFO_DEPT,
            SCENE_AUDIT_TRAIL,
            SCENE_CONFRONTATION,
        ]
        current_idx = scene_order.index(self.scene)
        if self.scene_complete(self.scene) and current_idx < len(scene_order) - 1:
            next_scene = scene_order[current_idx + 1]
            self._advance_to_scene(next_scene)

    def _advance_to_scene(self, scene_id: str) -> None:
        self.scene = scene_id
        self.step  = 0
        self.on_scene_change(scene_id)

        # Save progress to DB
        self._save()

        intro = SCENE_INTROS.get(scene_id, "")
        if intro:
            self.on_output(f"\n{'─'*60}\n{intro}\n{'─'*60}\n", style="scene")

    # ── Hint system ──────────────────────────────────────────────────────────

    def get_hint(self) -> str:
        """Return the next hint for the first incomplete objective in this scene."""
        for obj in self.objectives_for_scene(self.scene):
            if obj["id"] not in self.completed:
                hints = HINTS.get(obj["id"], [])
                # Track how many times hinted
                attr = f"_hint_idx_{obj['id']}"
                idx = getattr(self, attr, 0)
                if idx < len(hints):
                    setattr(self, attr, idx + 1)
                    return hints[idx]
                elif hints:
                    return hints[-1]   # Repeat the last (most explicit) hint
                else:
                    return f"Try running a SQL query related to: {obj['label']}"
        return "You've completed all objectives in this area. Look around for what changed."

    # ── Recall Gate (spaced retrieval) ────────────────────────────────────────

    def get_recall_challenge(self) -> dict | None:
        """
        Return a recall challenge for a recently completed concept, or None.
        Called between scene transitions.
        """
        if len(self.completed) < 2:
            return None
        # Pick second-most-recent completed objective
        target_id = self.completed[-2]
        obj = OBJECTIVES_BY_ID.get(target_id)
        if not obj:
            return None
        challenge = RECALL_CHALLENGES.get(obj.get("concept"))
        return challenge  # may be None if no challenge defined yet

    # ── Persistence ───────────────────────────────────────────────────────────

    def _save(self) -> None:
        try:
            conn = self._db._connect()
            conn.execute(
                "UPDATE save_state SET scene=?, clues=?, objectives=?, saved_at=? WHERE id=1",
                (
                    self.scene,
                    json.dumps(self.clues),
                    json.dumps(self.completed),
                    datetime.now().isoformat(timespec="seconds"),
                )
            )
            conn.commit()
        except Exception:
            pass  # Save failure should never crash the game

    def load(self) -> None:
        """Restore from save_state table."""
        try:
            conn = self._db._connect()
            row = conn.execute("SELECT * FROM save_state WHERE id=1").fetchone()
            if row:
                self.scene     = row["scene"]     or SCENE_YOUR_DESK
                self.clues     = json.loads(row["clues"]      or "[]")
                self.completed = json.loads(row["objectives"] or "[]")
        except Exception:
            pass

    # ── Utility ───────────────────────────────────────────────────────────────

    def progress_pct(self) -> int:
        total = len(OBJECTIVES)
        done  = len(self.completed)
        return int(100 * done / total) if total else 0

    def __repr__(self):
        return (
            f"<GameState scene={self.scene!r} "
            f"objectives={len(self.completed)}/{len(OBJECTIVES)} "
            f"clues={len(self.clues)}>"
        )


# ── Scene intro text ─────────────────────────────────────────────────────────

SCENE_INTROS = {
    SCENE_DB_TERMINAL: (
        "You plug your laptop into the secure terminal in the server room.\n"
        "The fan hum is louder here. Nobody comes down to B1 unless they have to.\n"
        "The full transaction log is open in front of you. Start digging."
    ),
    SCENE_HR_FILES: (
        "The HR filing cabinet is unlocked — Vanessa's still at lunch.\n"
        "You pull the personnel records. Every transaction has an approved_by field.\n"
        "Time to find out who signed off on those payments."
    ),
    SCENE_CFO_DEPT: (
        "You're standing outside Marcus Webb's office. He's in a board meeting until 4pm.\n"
        "His assistant waves you in to drop off a 'budget report.'\n"
        "You have maybe 20 minutes. His desktop is still logged in."
    ),
    SCENE_AUDIT_TRAIL: (
        "Back at your desk. You've got the pieces — now build the full picture.\n"
        "You need numbers that will hold up. Gut feelings don't go in an audit report."
    ),
    SCENE_CONFRONTATION: (
        "You have everything. Apex Solutions LLC. Pinnacle Strategy. $1.87M.\n"
        "All approved by the CFO. All billed to Special Projects.\n"
        "Your phone buzzes: Rachel Kim (COO) — 'Got a minute? My office.'\n"
        "This is it."
    ),
}


# ── Progressive hints ─────────────────────────────────────────────────────────
# Each list goes from vague → specific → gives away the answer.

HINTS = {
    "list_tables": [
        "The database is a black box until you know what's in it. What command shows you the tables?",
        "Try: db.tables()  — or write the SQL yourself: SELECT name FROM sqlite_master WHERE type='table'",
    ],
    "examine_employees": [
        "Start simple. Pick one table and look at everything in it.",
        "Try: db.query(\"SELECT * FROM employees\")",
    ],
    "count_employees": [
        "How many people work at Nexus? SQL has a function for counting rows.",
        "Try: db.query(\"SELECT COUNT(*) FROM employees\")",
    ],
    "find_high_spend_vendors": [
        "You want to know which vendors are getting the most money. Think: group the transactions by vendor, then add up the amounts.",
        "Keyword: GROUP BY.  Also: SUM(amount).",
        "Try: db.query(\"SELECT vendor_id, SUM(amount) FROM transactions GROUP BY vendor_id ORDER BY SUM(amount) DESC\")",
    ],
    "spot_unverified_vendors": [
        "Not every vendor on the list has been properly vetted. The vendors table has a column that tracks this.",
        "Look for vendors WHERE verified = 0",
        "Try: db.query(\"SELECT * FROM vendors WHERE verified = 0\")",
    ],
    "join_transactions_vendors": [
        "Right now you have vendor IDs in your transactions — not names. To see names, you need to connect two tables.",
        "The keyword is JOIN. You're linking transactions.vendor_id to vendors.id.",
        "Try: db.query(\"SELECT t.*, v.name FROM transactions t JOIN vendors v ON t.vendor_id = v.id\")",
    ],
    "find_approver": [
        "Every transaction was approved by someone. Check the approved_by column — is it always the same person?",
        "Try: db.query(\"SELECT approved_by, COUNT(*) FROM transactions GROUP BY approved_by ORDER BY COUNT(*) DESC\")",
    ],
    "lookup_employee_4": [
        "You found an employee ID that keeps showing up. Now look up who that actually is.",
        "Try: db.query(\"SELECT * FROM employees WHERE id = 4\")",
    ],
    "check_special_projects_budget": [
        "Follow the money. Which department has the largest budget? Query the departments table.",
        "Try: db.query(\"SELECT * FROM departments ORDER BY budget DESC\")",
    ],
    "total_apex_spend": [
        "You know Apex Solutions (vendor_id 4) is suspicious. How much have they been paid in total?",
        "Try: db.query(\"SELECT SUM(amount) FROM transactions WHERE vendor_id = 4\")",
    ],
    "escalation_pattern": [
        "Pull all transactions to vendor 4, ordered by date. Watch what happens to the amounts over time.",
        "Try: db.query(\"SELECT date, amount, description FROM transactions WHERE vendor_id = 4 ORDER BY date\")",
    ],
    "dual_vendor_fraud": [
        "Both suspicious vendors (ids 4 and 7) need to appear in one query. SQL has an IN clause for this.",
        "Try: db.query(\"SELECT * FROM transactions WHERE vendor_id IN (4, 7) ORDER BY date\")",
    ],
    "total_fraud_amount": [
        "Get the grand total paid to both shell companies combined.",
        "Try: db.query(\"SELECT SUM(amount) FROM transactions WHERE vendor_id IN (4, 7)\")",
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
