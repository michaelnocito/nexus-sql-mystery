# core/season2_game.py
# Season 2: "The Ghost in the Machine" — SQL-CORE EDITION
#
# Season 2's main path is 100% intermediate SQL. The player solves the
# ghost mystery with the next tier of SQL after Season 1:
#   LIKE · date/time (strftime) · subqueries · HAVING · CASE
#   derived tables · DISTINCT · SUBSTR · GROUP_CONCAT
#
# Python is NOT required here. The original Python objectives are
# preserved in core/season2_sidequests.py for the future Pro-Panel
# side-quest spec.
#
# Each objective teaches exactly ONE new SQL concept, scaffolded in
# three layers (what it is → why this scene needs it → exact example).
#
# Validators use the Season-1 signature: validate(sql, result) -> bool
# where `result` is a QueryResult. The player runs db.query("...") which
# routes through GameState.on_query() exactly like Season 1.

import re


# -- Scene constants (unchanged — season2_scenes.py imports these) ------------

S2_SCENE_SERVER_LOGS      = "s2_server_logs"
S2_SCENE_GHOST_RECORDS    = "s2_ghost_records"
S2_SCENE_TIMESTAMP        = "s2_timestamp_analysis"
S2_SCENE_ARCHIVE          = "s2_data_archaeology"
S2_SCENE_PATTERN_DECODER  = "s2_pattern_decoder"
S2_SCENE_THE_SIGNAL       = "s2_the_signal"


# -- Validator helpers (SQL — same shape as core/game.py) --------------------

def _sql_has(*fragments):
    """All fragments must appear in the SQL (case-insensitive) and rows returned."""
    frags = [f.lower() for f in fragments]
    def validate(sql, result):
        low = sql.lower()
        return all(f in low for f in frags) and len(result) > 0
    return validate

def _sql_has_any(*fragments):
    """Any one fragment appears in the SQL and rows returned."""
    frags = [f.lower() for f in fragments]
    def validate(sql, result):
        low = sql.lower()
        return any(f in low for f in frags) and len(result) > 0
    return validate

def _sql_all(*checks):
    """Compose multiple validators (all must pass)."""
    def validate(sql, result):
        return all(c(sql, result) for c in checks)
    return validate


# -- Objective definitions (SQL core) -----------------------------------------
# Object IDs are kept identical to the original file so the scene→objective
# lists in season2_scenes.py keep working unchanged. The player never sees
# these IDs; only labels/step-text/hints, which are all SQL now.

S2_OBJECTIVES = [

    # ── Scene 1: Server Logs ────────────────────────────────────────────────
    {
        "id":        "store_result",
        "scene":     S2_SCENE_SERVER_LOGS,
        "label":     "Found the phantom entries with LIKE",
        "detail":    "Used LIKE pattern matching to pull every log entry timestamped at 3:03am.",
        "concept":   "s2_like",
        "validator": _sql_has("like", "server_logs"),
    },
    {
        "id":        "loop_records",
        "scene":     S2_SCENE_SERVER_LOGS,
        "label":     "Isolated 3:03am activity by time",
        "detail":    "Filtered server_logs by the time portion of the timestamp using a date/time function.",
        "concept":   "s2_datetime",
        "validator": _sql_all(
            _sql_has("server_logs"),
            _sql_has_any("strftime", "status", "anomaly"),
        ),
    },

    # ── Scene 2: Ghost Records ──────────────────────────────────────────────
    {
        "id":        "list_comp_filter",
        "scene":     S2_SCENE_GHOST_RECORDS,
        "label":     "Found the outlier with a subquery",
        "detail":    "Used a subquery in WHERE to find the deleted record restored far more than average.",
        "concept":   "s2_subquery",
        "validator": _sql_all(
            _sql_has("deleted_records"),
            _sql_has("select", "(", ")"),
            lambda sql, r: sql.lower().count("select") >= 2,
        ),
    },
    {
        "id":        "find_ghost_employee",
        "scene":     S2_SCENE_GHOST_RECORDS,
        "label":     "Exposed the revenant record with HAVING",
        "detail":    "Used GROUP BY + HAVING to surface the table whose rows keep being restored.",
        "concept":   "s2_having",
        "validator": _sql_all(
            _sql_has("deleted_records", "group by", "having"),
        ),
    },

    # ── Scene 3: Timestamp Analysis ─────────────────────────────────────────
    {
        "id":        "parse_timestamps",
        "scene":     S2_SCENE_TIMESTAMP,
        "label":     "Proved 3:03 is no coincidence",
        "detail":    "Grouped log entries by time and used HAVING COUNT to prove the 3:03 cluster.",
        "concept":   "s2_groupby_having",
        "validator": _sql_all(
            _sql_has("server_logs", "group by", "having"),
            _sql_has("count"),
        ),
    },
    {
        "id":        "count_anomalies",
        "scene":     S2_SCENE_TIMESTAMP,
        "label":     "Labelled every entry with CASE",
        "detail":    "Used CASE WHEN to tag each log row as PHANTOM or normal.",
        "concept":   "s2_case",
        "validator": _sql_has("case", "when", "server_logs"),
    },

    # ── Scene 4: Archive ────────────────────────────────────────────────────
    {
        "id":        "compare_backups",
        "scene":     S2_SCENE_ARCHIVE,
        "label":     "Compared snapshots with a derived table",
        "detail":    "Built a subquery in FROM (a derived table) to compare two backup snapshots side by side.",
        "concept":   "s2_derived_table",
        "validator": _sql_all(
            _sql_has("backup_snapshots", "from", "("),
            lambda sql, r: sql.lower().count("select") >= 2,
        ),
    },
    {
        "id":        "build_summary",
        "scene":     S2_SCENE_ARCHIVE,
        "label":     "Unmasked the phantom's source with DISTINCT",
        "detail":    "Used DISTINCT to reveal the single internal IP every phantom query comes from.",
        "concept":   "s2_distinct",
        "validator": _sql_has("distinct", "server_logs"),
    },

    # ── Scene 5: Pattern Decoder ────────────────────────────────────────────
    {
        "id":        "decode_pattern",
        "scene":     S2_SCENE_PATTERN_DECODER,
        "label":     "Extracted the first letters with SUBSTR",
        "detail":    "Used SUBSTR to pull the first character of each phantom action, in timestamp order.",
        "concept":   "s2_substr",
        "validator": _sql_all(
            _sql_has_any("substr", "substring"),
            _sql_has("server_logs"),
        ),
    },
    {
        "id":        "correlate_times",
        "scene":     S2_SCENE_PATTERN_DECODER,
        "label":     "Assembled the hidden message with GROUP_CONCAT",
        "detail":    "Used GROUP_CONCAT to stitch the extracted letters into the ghost's message.",
        "concept":   "s2_group_concat",
        "validator": _sql_has("group_concat", "server_logs"),
    },

    # ── Scene 6: The Signal ─────────────────────────────────────────────────
    {
        "id":        "write_report_function",
        "scene":     S2_SCENE_THE_SIGNAL,
        "label":     "Built the capstone query",
        "detail":    "Combined a subquery, CASE, and a date filter into one analyst-grade query.",
        "concept":   "s2_capstone",
        "validator": _sql_all(
            _sql_has("server_logs", "case"),
            _sql_has("("),
            lambda sql, r: sql.lower().count("select") >= 2,
        ),
    },
    {
        "id":        "identify_source",
        "scene":     S2_SCENE_THE_SIGNAL,
        "label":     "Closed the case",
        "detail":    "Cross-referenced the phantom logs with the deleted record to name the source.",
        "concept":   "s2_capstone",
        "validator": _sql_all(
            _sql_has("server_logs"),
            _sql_has_any("deleted_records", "join", "union"),
        ),
    },
]

# Fast lookup by id
S2_OBJECTIVES_BY_ID = {o["id"]: o for o in S2_OBJECTIVES}


# -- Scene intro text ---------------------------------------------------------

S2_SCENE_INTROS = {
    S2_SCENE_GHOST_RECORDS: (
        "The database terminal boots with its usual hum. But today there's\n"
        "an extra line in the system log: 'Record restored: employees #11.'\n"
        "You deleted that record last week. You WATCHED it delete.\n\n"
        "Your SQL just got sharper. Subqueries let one query ask a question\n"
        "inside another. Time to find what's coming back from the dead."
    ),
    S2_SCENE_TIMESTAMP: (
        "Back at your desk. Coffee. Notepad. A growing sense of unease.\n"
        "The server logs show activity at 3:03am. Every single night.\n"
        "Nobody works at 3:03am. Nobody human, anyway.\n\n"
        "You don't need a gut feeling — you need proof. GROUP BY and\n"
        "HAVING turn 'it feels suspicious' into a number nobody can argue with."
    ),
    S2_SCENE_ARCHIVE: (
        "Archive Room. Fluorescent lights that haven't been changed since\n"
        "the Clinton administration. Dust on everything.\n"
        "But the backup tapes are here, and backup tapes don't lie.\n\n"
        "Put two snapshots side by side with a derived table.\n"
        "Find the discrepancy. Build the evidence."
    ),
    S2_SCENE_PATTERN_DECODER: (
        "You're back in the server room. It's 2:47am. You couldn't sleep.\n"
        "The phantom queries run at 3:03. You want to watch it happen.\n\n"
        "The logs aren't random. There's a pattern in the action fields.\n"
        "SQL can cut strings apart with SUBSTR and stitch them back\n"
        "together with GROUP_CONCAT.\n\n"
        "Someone — or something — is trying to communicate."
    ),
    S2_SCENE_THE_SIGNAL: (
        "Rachel Kim opens her office door before you knock.\n"
        "'I've been expecting this,' she says.\n\n"
        "You show her the decoded message. The frequency analysis.\n"
        "The backup discrepancies. The employee who was deleted but won't stay dead.\n\n"
        "'That employee,' Rachel says slowly, 'was a whistleblower.\n"
        "She set up an automated script before she was fired.\n"
        "A dead man's switch. In case someone tried to bury the evidence.'\n\n"
        "The ghost in the machine was never a ghost.\n"
        "It was a warning — and you read it with SQL alone."
    ),
}


# -- Step guidance text (3-layer: what · why · exact example) -----------------

S2_STEP_TEXT = {
    "store_result": (
        "The server room smells like ozone and paranoia.\n\n"
        "In Season 1 you used WHERE with exact matches (= 4). Now you need\n"
        "WHERE with a PATTERN. That's what LIKE does — % means 'anything here'.\n\n"
        "Every phantom entry is timestamped at 3:03am. Find them:\n\n"
        "  db.query(\"SELECT * FROM server_logs WHERE timestamp LIKE '%03:03%'\")\n\n"
        "The % wildcards mean 'any date, then 03:03, then anything'."
    ),
    "loop_records": (
        "Good. Those 14 rows are your phantom. Now confirm it a second way.\n\n"
        "SQLite can read the TIME out of a timestamp with strftime().\n"
        "It pulls pieces from a date string — '%H:%M' means hour:minute.\n\n"
        "  db.query(\"SELECT * FROM server_logs \"\n"
        "           \"WHERE strftime('%H:%M', timestamp) = '03:03'\")\n\n"
        "(Or the simple route: WHERE status = 'ANOMALY'. Both work — the\n"
        "point is you can slice time itself.)"
    ),
    "list_comp_filter": (
        "The deleted_records table tracks every removed row, with a\n"
        "restored_count. One record's count is wildly higher than the rest.\n\n"
        "A SUBQUERY lets a query ask its own question first. Here: 'which\n"
        "rows are above the AVERAGE restored_count?' The inner SELECT runs,\n"
        "then the outer one uses its answer.\n\n"
        "  db.query(\"SELECT * FROM deleted_records \"\n"
        "           \"WHERE restored_count > \"\n"
        "           \"(SELECT AVG(restored_count) FROM deleted_records)\")"
    ),
    "find_ghost_employee": (
        "You can see the revenant row. Now prove it the way an analyst does.\n\n"
        "WHERE filters rows. HAVING filters GROUPS — it runs AFTER GROUP BY,\n"
        "so you can filter on a SUM or COUNT.\n\n"
        "  db.query(\"SELECT original_table, SUM(restored_count) \"\n"
        "           \"FROM deleted_records GROUP BY original_table \"\n"
        "           \"HAVING SUM(restored_count) > 10\")\n\n"
        "Only the 'employees' group survives — 47 restorations."
    ),
    "parse_timestamps": (
        "Diana wants proof, not vibes. Time to make 3:03 undeniable.\n\n"
        "Group every log by its time, count each group, and keep only\n"
        "the groups that happen suspiciously often. GROUP BY buckets the\n"
        "rows; HAVING COUNT(*) filters those buckets.\n\n"
        "  db.query(\"SELECT strftime('%H:%M', timestamp) AS t, COUNT(*) \"\n"
        "           \"FROM server_logs GROUP BY t HAVING COUNT(*) > 5\")\n\n"
        "One time slot towers over the rest."
    ),
    "count_anomalies": (
        "Numbers are good. A labelled list is better for the report.\n\n"
        "CASE WHEN is SQL's if/else. It writes a new value per row based\n"
        "on a condition — without changing the data.\n\n"
        "  db.query(\"SELECT timestamp, \"\n"
        "           \"CASE WHEN status = 'ANOMALY' THEN 'PHANTOM' \"\n"
        "           \"ELSE 'normal' END AS verdict FROM server_logs\")\n\n"
        "Now every row carries its own verdict."
    ),
    "compare_backups": (
        "The backup_snapshots table has row counts at different dates.\n"
        "If data was tampered with, the counts won't line up.\n\n"
        "A DERIVED TABLE is a subquery in the FROM clause — you query the\n"
        "result of a query. Put the Jan snapshot and the Mar snapshot\n"
        "side by side and compare.\n\n"
        "  db.query(\"SELECT j.table_name, j.row_count AS jan, m.row_count AS mar \"\n"
        "           \"FROM (SELECT * FROM backup_snapshots WHERE snapshot_date='2024-01-01') j \"\n"
        "           \"JOIN (SELECT * FROM backup_snapshots WHERE snapshot_date='2024-03-01') m \"\n"
        "           \"ON j.table_name = m.table_name WHERE j.row_count != m.row_count\")"
    ),
    "build_summary": (
        "Every phantom entry came from somewhere. One internal address.\n\n"
        "DISTINCT collapses duplicates — it answers 'what are the UNIQUE\n"
        "values in this column?' Run it on ip_address.\n\n"
        "  db.query(\"SELECT DISTINCT ip_address FROM server_logs\")\n\n"
        "Staff sit on 10.0.1.x. The phantom always uses one lone address\n"
        "that doesn't belong to any human in this building."
    ),
    "decode_pattern": (
        "The phantom actions aren't noise. Take the FIRST letter of each,\n"
        "in timestamp order, and something spells out.\n\n"
        "SUBSTR(text, start, length) cuts a piece out of a string.\n"
        "SUBSTR(action, 1, 1) = the first character.\n\n"
        "  db.query(\"SELECT SUBSTR(action, 1, 1) FROM server_logs \"\n"
        "           \"WHERE status='ANOMALY' ORDER BY timestamp\")\n\n"
        "Read the column top to bottom."
    ),
    "correlate_times": (
        "Reading letters down a column works — but SQL can hand you the\n"
        "whole message in one cell.\n\n"
        "GROUP_CONCAT glues many rows' values into a single string.\n"
        "Feed it the ordered first-letters and it assembles the message.\n\n"
        "  db.query(\"SELECT GROUP_CONCAT(SUBSTR(action,1,1), '') \"\n"
        "           \"FROM (SELECT * FROM server_logs \"\n"
        "           \"WHERE status='ANOMALY' ORDER BY timestamp)\")\n\n"
        "The ghost's message, in one line of SQL."
    ),
    "write_report_function": (
        "Final analysis. Everything you've learned, in one query.\n\n"
        "Combine a subquery, a CASE label, and a date/time filter:\n"
        "flag every 3am row whose IP matches the phantom's address.\n\n"
        "  db.query(\"SELECT timestamp, action, \"\n"
        "           \"CASE WHEN ip_address = \"\n"
        "           \"(SELECT DISTINCT ip_address FROM server_logs WHERE status='ANOMALY') \"\n"
        "           \"THEN 'PHANTOM SOURCE' ELSE 'normal' END AS verdict \"\n"
        "           \"FROM server_logs WHERE strftime('%H', timestamp) = '03'\")"
    ),
    "identify_source": (
        "Name it. Put the phantom logs and the record that won't die\n"
        "in ONE result set. UNION stacks the rows of two SELECTs into\n"
        "a single answer — as long as both sides have the same columns.\n\n"
        "  db.query(\"SELECT id, timestamp, action, status \"\n"
        "           \"FROM server_logs WHERE status='ANOMALY' \"\n"
        "           \"UNION \"\n"
        "           \"SELECT id, deleted_at, record_data, 'REVENANT' \"\n"
        "           \"FROM deleted_records WHERE restored_count > 10\")\n\n"
        "The dead man's switch and its target, side by side.\n"
        "You did this with SQL alone."
    ),
}


# -- Per-objective focus commands ("Try this:" box) --------------------------

S2_OBJECTIVE_FOCUS = {
    "store_result":          ("Match a pattern with LIKE:",  "db.query(\"SELECT * FROM server_logs WHERE timestamp LIKE '%03:03%'\")"),
    "loop_records":          ("Slice the time out:",         "db.query(\"SELECT * FROM server_logs WHERE strftime('%H:%M', timestamp) = '03:03'\")"),
    "list_comp_filter":      ("Ask a question inside a query:", "db.query(\"SELECT * FROM deleted_records WHERE restored_count > (SELECT AVG(restored_count) FROM deleted_records)\")"),
    "find_ghost_employee":   ("Filter the groups with HAVING:", "db.query(\"SELECT original_table, SUM(restored_count) FROM deleted_records GROUP BY original_table HAVING SUM(restored_count) > 10\")"),
    "parse_timestamps":      ("Prove it with GROUP BY + HAVING:", "db.query(\"SELECT strftime('%H:%M', timestamp) AS t, COUNT(*) FROM server_logs GROUP BY t HAVING COUNT(*) > 5\")"),
    "count_anomalies":       ("Label rows with CASE:",        "db.query(\"SELECT timestamp, CASE WHEN status='ANOMALY' THEN 'PHANTOM' ELSE 'normal' END AS verdict FROM server_logs\")"),
    "compare_backups":       ("Compare with a derived table:", "db.query(\"SELECT j.table_name, j.row_count, m.row_count FROM (SELECT * FROM backup_snapshots WHERE snapshot_date='2024-01-01') j JOIN (SELECT * FROM backup_snapshots WHERE snapshot_date='2024-03-01') m ON j.table_name=m.table_name WHERE j.row_count!=m.row_count\")"),
    "build_summary":         ("Find unique values:",          "db.query(\"SELECT DISTINCT ip_address FROM server_logs\")"),
    "decode_pattern":        ("Cut a string with SUBSTR:",    "db.query(\"SELECT SUBSTR(action,1,1) FROM server_logs WHERE status='ANOMALY' ORDER BY timestamp\")"),
    "correlate_times":       ("Stitch it with GROUP_CONCAT:", "db.query(\"SELECT GROUP_CONCAT(SUBSTR(action,1,1),'') FROM (SELECT * FROM server_logs WHERE status='ANOMALY' ORDER BY timestamp)\")"),
    "write_report_function": ("Combine everything:",          "db.query(\"SELECT timestamp, action, CASE WHEN ip_address=(SELECT DISTINCT ip_address FROM server_logs WHERE status='ANOMALY') THEN 'PHANTOM SOURCE' ELSE 'normal' END AS verdict FROM server_logs WHERE strftime('%H',timestamp)='03'\")"),
    "identify_source":       ("Close the case with UNION:",   "db.query(\"SELECT id, timestamp, action, status FROM server_logs WHERE status='ANOMALY' UNION SELECT id, deleted_at, record_data, 'REVENANT' FROM deleted_records WHERE restored_count > 10\")"),
}


# -- Progressive hints (vague → specific → answer) ---------------------------

S2_HINTS = {
    "store_result": [
        "WHERE = 'x' only matches exactly. You need to match a PATTERN inside the timestamp text. SQL has a keyword for that.",
        "Use LIKE with % wildcards. % means 'any characters here'. The phantom always runs at 03:03.",
        "db.query(\"SELECT * FROM server_logs WHERE timestamp LIKE '%03:03%'\")",
    ],
    "loop_records": [
        "You can pull just the time out of a timestamp string. SQLite has a function for reading date/time pieces.",
        "strftime('%H:%M', timestamp) returns just 'HH:MM'. Compare it to '03:03'. (Or filter WHERE status='ANOMALY'.)",
        "db.query(\"SELECT * FROM server_logs WHERE strftime('%H:%M', timestamp) = '03:03'\")",
    ],
    "list_comp_filter": [
        "One deleted record is restored far more than the others. Let the query compute the average itself, then compare against it.",
        "A subquery in WHERE: WHERE restored_count > (SELECT AVG(restored_count) FROM deleted_records).",
        "db.query(\"SELECT * FROM deleted_records WHERE restored_count > (SELECT AVG(restored_count) FROM deleted_records)\")",
    ],
    "find_ghost_employee": [
        "WHERE can't filter on a SUM. There's a different clause that filters AFTER you GROUP BY.",
        "GROUP BY original_table, then HAVING SUM(restored_count) > 10 to keep only the heavily-restored group.",
        "db.query(\"SELECT original_table, SUM(restored_count) FROM deleted_records GROUP BY original_table HAVING SUM(restored_count) > 10\")",
    ],
    "parse_timestamps": [
        "To prove 3:03 isn't chance, count how many logs fall in each time slot and keep only the busy ones.",
        "GROUP BY the time, then HAVING COUNT(*) > 5 to surface the suspicious cluster.",
        "db.query(\"SELECT strftime('%H:%M', timestamp) AS t, COUNT(*) FROM server_logs GROUP BY t HAVING COUNT(*) > 5\")",
    ],
    "count_anomalies": [
        "You want a new column that says PHANTOM or normal per row — without editing the table. SQL has an if/else expression.",
        "CASE WHEN status='ANOMALY' THEN 'PHANTOM' ELSE 'normal' END.",
        "db.query(\"SELECT timestamp, CASE WHEN status='ANOMALY' THEN 'PHANTOM' ELSE 'normal' END AS verdict FROM server_logs\")",
    ],
    "compare_backups": [
        "Put two snapshots next to each other. You can SELECT from the result of a SELECT — a derived table in FROM.",
        "JOIN a (Jan snapshot) subquery to a (Mar snapshot) subquery on table_name, then keep rows where the counts differ.",
        "db.query(\"SELECT j.table_name, j.row_count, m.row_count FROM (SELECT * FROM backup_snapshots WHERE snapshot_date='2024-01-01') j JOIN (SELECT * FROM backup_snapshots WHERE snapshot_date='2024-03-01') m ON j.table_name=m.table_name WHERE j.row_count!=m.row_count\")",
    ],
    "build_summary": [
        "Every phantom entry shares one trait you haven't checked yet: where it came from. What are the UNIQUE addresses?",
        "SELECT DISTINCT ip_address FROM server_logs — staff use 10.0.1.x; one address stands alone.",
        "db.query(\"SELECT DISTINCT ip_address FROM server_logs\")",
    ],
    "decode_pattern": [
        "The first letter of each phantom action, read in timestamp order, spells something. You need to cut one character out of each string.",
        "SUBSTR(action, 1, 1) = first character. Filter to ANOMALY rows, ORDER BY timestamp.",
        "db.query(\"SELECT SUBSTR(action,1,1) FROM server_logs WHERE status='ANOMALY' ORDER BY timestamp\")",
    ],
    "correlate_times": [
        "Instead of reading the column by eye, have SQL glue all those letters into one string for you.",
        "GROUP_CONCAT(SUBSTR(action,1,1), '') over the ordered anomaly rows assembles the message.",
        "db.query(\"SELECT GROUP_CONCAT(SUBSTR(action,1,1),'') FROM (SELECT * FROM server_logs WHERE status='ANOMALY' ORDER BY timestamp)\")",
    ],
    "write_report_function": [
        "The capstone: flag every 3am row whose IP matches the phantom's. That needs a subquery, a CASE, and a time filter together.",
        "CASE WHEN ip_address = (SELECT DISTINCT ip_address ... WHERE status='ANOMALY') THEN 'PHANTOM SOURCE' ... and WHERE strftime('%H',timestamp)='03'.",
        "db.query(\"SELECT timestamp, action, CASE WHEN ip_address=(SELECT DISTINCT ip_address FROM server_logs WHERE status='ANOMALY') THEN 'PHANTOM SOURCE' ELSE 'normal' END AS verdict FROM server_logs WHERE strftime('%H',timestamp)='03'\")",
    ],
    "identify_source": [
        "Final query. Put the phantom logs and the revenant record into ONE result. There's a keyword that stacks two SELECTs.",
        "UNION combines the rows of two SELECTs — both must have the same number of columns. One side: anomaly server_logs. Other side: the heavily-restored deleted_records row.",
        "db.query(\"SELECT id, timestamp, action, status FROM server_logs WHERE status='ANOMALY' UNION SELECT id, deleted_at, record_data, 'REVENANT' FROM deleted_records WHERE restored_count > 10\")",
    ],
}


# -- Recall challenges (between-scene retrieval practice) ---------------------

S2_RECALL_CHALLENGES = {
    "s2_like": {
        "question": "Write SQL to find rows in 'logs' where the 'msg' column contains the word 'error' anywhere.",
        "answer":   "SELECT * FROM logs WHERE msg LIKE '%error%'",
        "keywords": ["like", "%error%"],
        "concept":  "s2_like",
    },
    "s2_subquery": {
        "question": "How do you select sales rows whose amount is above the average amount in the same table?",
        "answer":   "SELECT * FROM sales WHERE amount > (SELECT AVG(amount) FROM sales)",
        "keywords": ["select", "avg", "(", ")"],
        "concept":  "s2_subquery",
    },
    "s2_having": {
        "question": "What clause filters GROUPS after GROUP BY (e.g. keep groups with SUM > 100)?",
        "answer":   "HAVING (e.g. HAVING SUM(x) > 100)",
        "keywords": ["having"],
        "concept":  "s2_having",
    },
    "s2_case": {
        "question": "Write a CASE expression that outputs 'high' when score > 90, else 'low'.",
        "answer":   "CASE WHEN score > 90 THEN 'high' ELSE 'low' END",
        "keywords": ["case", "when", "then", "else", "end"],
        "concept":  "s2_case",
    },
    "s2_distinct": {
        "question": "How do you list the unique values of the 'country' column in 'users'?",
        "answer":   "SELECT DISTINCT country FROM users",
        "keywords": ["distinct", "country"],
        "concept":  "s2_distinct",
    },
    "s2_group_concat": {
        "question": "Which SQLite function glues many rows' values into one combined string?",
        "answer":   "GROUP_CONCAT()",
        "keywords": ["group_concat"],
        "concept":  "s2_group_concat",
    },
}


# -- Cliffhanger teasers (unchanged narrative beats) -------------------------

S2_CLIFFHANGERS = {
    S2_SCENE_SERVER_LOGS: (
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "  END OF EPISODE 1: \"Strange Entries\"\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "  The server logs don't lie. Something is running\n"
        "  queries when the building is empty.\n"
        "  And it's been doing it for months.\n\n"
        "  NEXT: A deleted employee record that won't stay dead.\n\n"
        "  📄 Page 1 of The SQL Codex unlocked.\n"
    ),
    S2_SCENE_GHOST_RECORDS: (
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "  END OF EPISODE 2: \"The Revenant Row\"\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "  Employee #11. Deleted three months ago.\n"
        "  Restored 47 times since. Always at 3:03am.\n"
        "  Someone — or something — wants this record to exist.\n\n"
        "  NEXT: Timestamp analysis. What happens at 3:03?\n\n"
        "  📄 Page 2 of The SQL Codex unlocked.\n"
    ),
    S2_SCENE_TIMESTAMP: (
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "  END OF EPISODE 3: \"The Witching Hour\"\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "  14 phantom queries. All at 03:03:00.\n"
        "  Not 03:02. Not 03:04. Exactly 03:03.\n"
        "  That's not a ghost. That's a cron job.\n\n"
        "  NEXT: The archive room. Old backups hold old secrets.\n\n"
        "  📄 Page 3 of The SQL Codex unlocked.\n"
    ),
    S2_SCENE_ARCHIVE: (
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "  END OF EPISODE 4: \"Buried Data\"\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "  The backup row counts don't match.\n"
        "  Someone altered the production database\n"
        "  after the last clean backup. The phantom script\n"
        "  is restoring what they tried to erase.\n\n"
        "  NEXT: The server room at night. The message in the machine.\n\n"
        "  📄 Page 4 of The SQL Codex unlocked.\n"
    ),
    S2_SCENE_PATTERN_DECODER: (
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "  END OF EPISODE 5: \"The Cipher\"\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "  The phantom queries spell a message.\n"
        "  Someone left breadcrumbs in the machine.\n"
        "  Not a haunting. A confession.\n\n"
        "  NEXT: Rachel Kim's office. The truth.\n\n"
        "  📄 Page 5 of The SQL Codex unlocked.\n"
    ),
}
