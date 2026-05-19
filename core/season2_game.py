# core/season2_game.py
# Season 2: "The Ghost in the Machine" — SQL-CORE, VARIED-PRACTICE EDITION
#
# Pedagogy (per SPEC_NARRATIVE_FUSION.md §7b): instead of 12 one-shot
# concepts, Season 2 teaches SIX core SQL skills, each PRACTICED TWICE
# across 12 story beats in a slightly different investigative context with
# escalating difficulty. Concept card shows on first encounter only; the
# second rep is varied practice ("you've done this — here's the twist").
#
#   1. s2_like      LIKE pattern matching        (obj1 timestamp, obj4 JSON col)
#   2. s2_datetime  strftime date/time extract   (obj2 time, obj6 dates)
#   3. s2_subquery  query inside a query         (obj3 scalar, obj7 correlated)
#   4. s2_groupby   GROUP BY + HAVING aggregate  (obj5 by time, obj8 by table)
#   5. s2_string    SUBSTR / GROUP_CONCAT        (obj9 extract, obj10 assemble)
#   6. s2_case      CASE WHEN conditional label  (obj11 status, obj12 capstone)
#
# Narrative is delivered in three fused pieces per objective:
#   SETUP    -> STORY panel: the in-world question only the DB can answer
#   YOUR_MOVE-> BRIEFING (left panel): GOAL + the plain-language path
#   REACTION -> STORY panel: reacts to what the correct query exposed
#
# Validators use the Season-1 signature validate(sql, result) -> bool.
# The player runs db.query(...), routed through GameState.on_query().

import re


# -- Scene constants (season2_scenes.py imports these) -----------------------

S2_SCENE_SERVER_LOGS      = "s2_server_logs"
S2_SCENE_GHOST_RECORDS    = "s2_ghost_records"
S2_SCENE_TIMESTAMP        = "s2_timestamp_analysis"
S2_SCENE_ARCHIVE          = "s2_data_archaeology"
S2_SCENE_PATTERN_DECODER  = "s2_pattern_decoder"
S2_SCENE_THE_SIGNAL       = "s2_the_signal"


# -- Validator helpers --------------------------------------------------------

def _has(*frags):
    low = [f.lower() for f in frags]
    def v(sql, result):
        s = sql.lower()
        return all(f in s for f in low) and len(result) > 0
    return v

def _has_any(group, *also):
    glow = [g.lower() for g in group]
    alow = [a.lower() for a in also]
    def v(sql, result):
        s = sql.lower()
        return any(g in s for g in glow) and all(a in s for a in alow) and len(result) > 0
    return v

def _subquery(*frags):
    low = [f.lower() for f in frags]
    def v(sql, result):
        s = sql.lower()
        return all(f in s for f in low) and s.count("select") >= 2 and len(result) > 0
    return v


# -- Objectives (12; IDs unchanged so season2_scenes.py keeps working) -------

S2_OBJECTIVES = [
    # ── Scene 1: Server Logs ────────────────────────────────────────────────
    {
        "id": "store_result", "scene": S2_SCENE_SERVER_LOGS,
        "skill": "s2_like", "concept": "s2_like", "rep": 1,
        "label": "Pulled the 3:03 entries with LIKE",
        "detail": "Matched a pattern inside the timestamp text instead of an exact value.",
        "validator": _has("like", "server_logs"),
    },
    {
        "id": "loop_records", "scene": S2_SCENE_SERVER_LOGS,
        "skill": "s2_datetime", "concept": "s2_datetime", "rep": 1,
        "label": "Confirmed the time with strftime",
        "detail": "Sliced the hour:minute out of the timestamp to prove it's exactly 03:03.",
        "validator": _has_any(["strftime", "status"], "server_logs"),
    },

    # ── Scene 2: Ghost Records ──────────────────────────────────────────────
    {
        "id": "list_comp_filter", "scene": S2_SCENE_GHOST_RECORDS,
        "skill": "s2_subquery", "concept": "s2_subquery", "rep": 1,
        "label": "Found the outlier with a subquery",
        "detail": "Let the query compute the average restore count, then beat it.",
        "validator": _subquery("deleted_records"),
    },
    {
        "id": "find_ghost_employee", "scene": S2_SCENE_GHOST_RECORDS,
        "skill": "s2_like", "concept": "s2_like", "rep": 2,
        "label": "Identified the revenant as an employee",
        "detail": "Reused LIKE — this time against the record_data text, not a timestamp.",
        "validator": _has("like", "deleted_records"),
    },

    # ── Scene 3: Timestamp Analysis ─────────────────────────────────────────
    {
        "id": "parse_timestamps", "scene": S2_SCENE_TIMESTAMP,
        "skill": "s2_groupby", "concept": "s2_groupby", "rep": 1,
        "label": "Proved the cluster with GROUP BY + HAVING",
        "detail": "Bucketed every log by time, counted each bucket, kept the damning one.",
        "validator": _has("group by", "having", "server_logs", "count"),
    },
    {
        "id": "count_anomalies", "scene": S2_SCENE_TIMESTAMP,
        "skill": "s2_datetime", "concept": "s2_datetime", "rep": 2,
        "label": "Mapped the phantom's run of nights",
        "detail": "Reused strftime — this time pulling the DATE, not the time.",
        "validator": _has_any(["strftime"], "server_logs"),
    },

    # ── Scene 4: Archive ────────────────────────────────────────────────────
    {
        "id": "compare_backups", "scene": S2_SCENE_ARCHIVE,
        "skill": "s2_subquery", "concept": "s2_subquery", "rep": 2,
        "label": "Caught the tampering with a correlated subquery",
        "detail": "Reused the subquery idea — this time one that references the outer row.",
        "validator": _subquery("backup_snapshots"),
    },
    {
        "id": "build_summary", "scene": S2_SCENE_ARCHIVE,
        "skill": "s2_groupby", "concept": "s2_groupby", "rep": 2,
        "label": "Listed every tampered table",
        "detail": "Reused GROUP BY + HAVING — this time grouping by table, not time.",
        "validator": _has("backup_snapshots", "group by"),
    },

    # ── Scene 5: Pattern Decoder ────────────────────────────────────────────
    {
        "id": "decode_pattern", "scene": S2_SCENE_PATTERN_DECODER,
        "skill": "s2_string", "concept": "s2_string", "rep": 1,
        "label": "Cut the first letters out with SUBSTR",
        "detail": "Pulled one character from each phantom action, in order.",
        "validator": _has("substr", "server_logs"),
    },
    {
        "id": "correlate_times", "scene": S2_SCENE_PATTERN_DECODER,
        "skill": "s2_string", "concept": "s2_string", "rep": 2,
        "label": "Assembled the message with GROUP_CONCAT",
        "detail": "Reused string surgery — this time stitching the letters into one line.",
        "validator": _has("group_concat", "server_logs"),
    },

    # ── Scene 6: The Signal ─────────────────────────────────────────────────
    {
        "id": "write_report_function", "scene": S2_SCENE_THE_SIGNAL,
        "skill": "s2_case", "concept": "s2_case", "rep": 1,
        "label": "Labelled every row with CASE",
        "detail": "Tagged each log PHANTOM or normal without touching the data.",
        "validator": _has("case", "when", "server_logs"),
    },
    {
        "id": "identify_source", "scene": S2_SCENE_THE_SIGNAL,
        "skill": "s2_case", "concept": "s2_case", "rep": 2,
        "label": "Named the source — the capstone query",
        "detail": "Reused CASE — its condition now driven by a subquery. Everything at once.",
        "validator": _subquery("case", "server_logs"),
    },
]

S2_OBJECTIVES_BY_ID = {o["id"]: o for o in S2_OBJECTIVES}

# Order of objectives within each scene (for setup→next-setup chaining)
S2_SCENE_OBJ_ORDER = {}
for _o in S2_OBJECTIVES:
    S2_SCENE_OBJ_ORDER.setdefault(_o["scene"], []).append(_o["id"])


# -- Scene WHY (persistent premise — STORY panel, top, on scene entry) -------

S2_SCENE_WHY = {
    S2_SCENE_SERVER_LOGS: (
        "Two weeks after Marcus Webb. Diana told you to keep an eye on things.\n"
        "The access log shows entries at 3:03 a.m. — every night, building empty.\n"
        "Someone, or something, is in the database when no one's here."
    ),
    S2_SCENE_GHOST_RECORDS: (
        "There's a table you've never seen before: deleted_records.\n"
        "One row keeps coming back from the dead. Find out which —\n"
        "and who it belonged to."
    ),
    S2_SCENE_TIMESTAMP: (
        "A hunch isn't evidence. Diana wants proof the 3:03 pattern is\n"
        "real and deliberate, not coincidence. Make the timestamps testify."
    ),
    S2_SCENE_ARCHIVE: (
        "Basement B2. Backup tapes nobody's touched since the migration.\n"
        "If someone altered the live database, the old snapshots won't\n"
        "match the new ones. Backups don't lie."
    ),
    S2_SCENE_PATTERN_DECODER: (
        "2:47 a.m. You stayed in the building. The phantom's actions\n"
        "aren't random noise — there's a message buried in them. Read it."
    ),
    S2_SCENE_THE_SIGNAL: (
        "Rachel Kim's office. Put every piece in one place and name the\n"
        "source. No Python, no guesswork — you did this with SQL alone."
    ),
}


# -- SETUP beats (STORY panel — the in-world question, per objective) --------

S2_SETUP = {
    "store_result": (
        "The access log is thousands of lines. You can't read it by eye —\n"
        "but you saw the shape of it: 3:03 a.m., over and over. You don't\n"
        "know the exact dates, so an exact match is useless.\n\n"
        "You need every row whose timestamp *contains* 03:03."
    ),
    "loop_records": (
        "Fourteen rows. But a skeptic — Diana — will say '03:03 appears in\n"
        "the date too, you got lucky.' Kill that argument.\n\n"
        "Return only the server_logs rows where the time-of-day itself is\n"
        "exactly 03:03 — not just digits sitting somewhere in the string."
    ),
    "list_comp_filter": (
        "deleted_records logs every removed row, with a restored_count.\n"
        "Most are 0 or close to it. One is absurdly high — but you don't\n"
        "know the threshold. Don't guess a number.\n\n"
        "Ask the table what its own average is, then find what towers over it."
    ),
    "find_ghost_employee": (
        "One record, restored 47 times. The record_data is a blob of text.\n"
        "What KIND of record keeps clawing its way back — vendor?\n"
        "transaction? a person?\n\n"
        "Return the deleted_records row whose record_data text contains\n"
        "the word 'terminated'. Same tool as the logs — now on record_data."
    ),
    "parse_timestamps": (
        "Diana: 'Fourteen rows isn't proof. Maybe 3:03 is just a busy minute.'\n"
        "She's wrong, and you can show it. Bucket every log by its time of\n"
        "day, count each bucket, and surface only the times that fire\n"
        "suspiciously often."
    ),
    "count_anomalies": (
        "One time slot, fourteen hits, nothing else close. Now: how long\n"
        "has this been running? You need the distinct DATES the phantom\n"
        "struck — same timestamp tool, a different piece of it."
    ),
    "compare_backups": (
        "backup_snapshots holds row counts per table on three dates.\n"
        "If the live data was tampered with, January won't agree with March.\n"
        "For each table, compare its own old count to its own new count —\n"
        "a query that, row by row, asks a question about that same row."
    ),
    "build_summary": (
        "You can see one table shrank. But Rachel needs the full list:\n"
        "every table whose row count is NOT stable across the snapshots.\n"
        "Group the snapshots by table and keep the ones that changed."
    ),
    "decode_pattern": (
        "The phantom's action text isn't filler. Pull the 3:03 entries in\n"
        "time order and take the FIRST letter of each action. Something is\n"
        "spelled there. You need surgical control of the string."
    ),
    "correlate_times": (
        "Reading letters down a column works — but you want the whole\n"
        "message in one cell, undeniable, paste-into-the-report clean.\n"
        "Same string skill, one step further: glue them together."
    ),
    "write_report_function": (
        "Rachel wants a readable exhibit, not raw status codes. Produce a\n"
        "column that says PHANTOM or normal for every row — a verdict —\n"
        "without altering a single byte of the underlying data."
    ),
    "identify_source": (
        "Last query. Name it. Flag every 3 a.m. row whose address matches\n"
        "the phantom's — and let the query discover that address itself.\n"
        "Everything you've practiced, in one statement."
    ),
}


# -- YOUR MOVE (BRIEFING / left panel — GOAL line + the plain path) ----------
# Tuple: (goal_one_liner, move_text). No full-SQL spoiler here; the
# "show solution" box (S2_OBJECTIVE_FOCUS) still holds the canonical query.

S2_YOUR_MOVE = {
    "store_result": (
        "Find every log entry from 3:03 a.m.",
        "From the server_logs table, return every row whose timestamp "
        "column contains '03:03' anywhere in it. Use LIKE with % wildcards: "
        "timestamp LIKE '%03:03%'.",
    ),
    "loop_records": (
        "Prove the time is exactly 03:03",
        "From server_logs, return only the rows where the time-of-day is "
        "exactly 03:03. Pull the time with strftime('%H:%M', timestamp) "
        "and check it equals '03:03'.",
    ),
    "list_comp_filter": (
        "Find the record restored far above average",
        "From deleted_records, return the row whose restored_count is "
        "greater than the table's average restored_count. Put the average "
        "in a subquery: WHERE restored_count > (SELECT AVG(restored_count) "
        "FROM deleted_records).",
    ),
    "find_ghost_employee": (
        "Find what kind of record keeps returning",
        "From deleted_records, return the row whose record_data text "
        "contains the word 'terminated'. Same tool as before — LIKE — "
        "this time on record_data: record_data LIKE '%terminated%'.",
    ),
    "parse_timestamps": (
        "Prove 3:03 is no coincidence",
        "From server_logs, return each time-of-day and how many rows have "
        "it — but only times that occur more than 5 times. GROUP BY "
        "strftime('%H:%M', timestamp); filter the groups with "
        "HAVING COUNT(*) > 5.",
    ),
    "count_anomalies": (
        "Find every date the phantom struck",
        "From server_logs where status = 'ANOMALY', return every distinct "
        "DATE. Pull the date with strftime('%Y-%m-%d', timestamp) and wrap "
        "it in SELECT DISTINCT.",
    ),
    "compare_backups": (
        "Catch the table that shrank after tampering",
        "From backup_snapshots, return each 2024-01-01 row whose row_count "
        "is higher than the SAME table's 2024-03-01 row_count. Compare "
        "using a subquery matched on table_name.",
    ),
    "build_summary": (
        "List every table whose count changed",
        "From backup_snapshots, return every table_name whose row_count is "
        "NOT the same across all snapshots. GROUP BY table_name; keep "
        "groups with HAVING COUNT(DISTINCT row_count) > 1.",
    ),
    "decode_pattern": (
        "Extract the first letter of each phantom action",
        "From server_logs where status = 'ANOMALY', ordered by timestamp, "
        "return the first character of each action. Cut it with "
        "SUBSTR(action, 1, 1).",
    ),
    "correlate_times": (
        "Assemble the hidden message into one string",
        "Return ONE value: every first-letter joined into a single string. "
        "Use GROUP_CONCAT(SUBSTR(action,1,1), '') over the status='ANOMALY' "
        "rows, ordered by timestamp (order them in a subquery).",
    ),
    "write_report_function": (
        "Tag every row PHANTOM or normal",
        "From server_logs, return every row plus a new column that reads "
        "'PHANTOM' when status = 'ANOMALY' and 'normal' otherwise. Build it "
        "with CASE WHEN status='ANOMALY' THEN 'PHANTOM' ELSE 'normal' END.",
    ),
    "identify_source": (
        "Flag the phantom's source in one query",
        "From server_logs, return the 3 a.m. rows with a new column that "
        "reads 'PHANTOM SOURCE' when ip_address equals the phantom's "
        "address. Find that address with a subquery "
        "(SELECT DISTINCT ip_address ... WHERE status='ANOMALY') inside a "
        "CASE; filter with strftime('%H', timestamp) = '03'.",
    ),
}


# -- RESULT REACTION (STORY panel — fires on correct query) ------------------

S2_RESULT_REACTION = {
    "store_result": (
        "Fourteen rows. Every one timestamped 03:03:00. User field: [SYSTEM].\n"
        "Status: ANOMALY. No human logs in as [SYSTEM]. Whatever this is,\n"
        "it doesn't sleep — and it's been here every night for two weeks."
    ),
    "loop_records": (
        "03:03. Not 03:02. Not 03:04. Exactly 03:03, fourteen times.\n"
        "That's not a person fumbling in late. That's a schedule.\n"
        "Something is running on a timer. A cron job has a heartbeat."
    ),
    "list_comp_filter": (
        "One row answers back: restored_count 47. The next highest is 0.\n"
        "Forty-seven times something deleted this record and forty-seven\n"
        "times it came back. Deleted. Restored. Like a pulse."
    ),
    "find_ghost_employee": (
        "It's a person. An employee record — status 'terminated'.\n"
        "Employee #11. Elena Gutierrez. Fired three months ago, and yet\n"
        "the database refuses to let her go. Someone wants her on the books."
    ),
    "parse_timestamps": (
        "One bar towers over the chart: 03:03, fourteen hits. Every other\n"
        "minute of the day: one, maybe two. This isn't noise. Diana goes\n"
        "quiet when she sees it. 'Okay,' she says. 'That's real.'"
    ),
    "count_anomalies": (
        "Fourteen distinct nights. An unbroken run — it hasn't missed once.\n"
        "Reliable as payroll. Whoever built this built it to last, and to\n"
        "be found by someone who'd think to look."
    ),
    "compare_backups": (
        "Every table is smaller than it was in January. employees: 11 → 10.\n"
        "vendors: 9 → 8. transactions: 29 → 28. Rows didn't expire.\n"
        "They were removed — after the clean backup. This was deliberate."
    ),
    "build_summary": (
        "Three tables, all unstable across the snapshots: employees,\n"
        "vendors, transactions. The exact tables tied to Elena's case.\n"
        "Someone scrubbed the live data and the backups remember."
    ),
    "decode_pattern": (
        "The first letters, in time order, aren't gibberish:\n"
        "C-H-E-C-K-T-H-E-D-A-T-A-L-E. 'CHECK THE DATA…' — a message,\n"
        "left one letter per night. Not a haunting. A breadcrumb trail."
    ),
    "correlate_times": (
        "One cell, the whole message assembled: a deliberate signal,\n"
        "hidden in plain log text, waiting for an analyst patient enough\n"
        "to read it character by character. You were."
    ),
    "write_report_function": (
        "Every row now wears a verdict. The PHANTOM rows line up in a\n"
        "perfect nightly column. Printed out, it's not a theory anymore —\n"
        "it's an exhibit. Rachel can hand this to anyone."
    ),
    "identify_source": (
        "The query names it: every PHANTOM SOURCE row traces to one\n"
        "internal address — Elena's old workstation, still scheduled,\n"
        "still running her script. A dead man's switch. She knew they'd\n"
        "bury it, so she built something that would dig itself back up.\n\n"
        "The ghost in the machine was never a ghost. It was a warning —\n"
        "and you read it with SQL alone."
    ),
}


# -- "Show solution" canonical queries (focus box reveal — unchanged role) ---

S2_OBJECTIVE_FOCUS = {
    "store_result":          ("Match a pattern with LIKE:",  "db.query(\"SELECT * FROM server_logs WHERE timestamp LIKE '%03:03%'\")"),
    "loop_records":          ("Slice the time out:",         "db.query(\"SELECT * FROM server_logs WHERE strftime('%H:%M', timestamp) = '03:03'\")"),
    "list_comp_filter":      ("Ask a question inside a query:", "db.query(\"SELECT * FROM deleted_records WHERE restored_count > (SELECT AVG(restored_count) FROM deleted_records)\")"),
    "find_ghost_employee":   ("LIKE on a different column:",  "db.query(\"SELECT * FROM deleted_records WHERE record_data LIKE '%terminated%'\")"),
    "parse_timestamps":      ("GROUP BY + HAVING:",           "db.query(\"SELECT strftime('%H:%M', timestamp) AS t, COUNT(*) FROM server_logs GROUP BY t HAVING COUNT(*) > 5\")"),
    "count_anomalies":       ("strftime for the dates:",      "db.query(\"SELECT DISTINCT strftime('%Y-%m-%d', timestamp) FROM server_logs WHERE status='ANOMALY'\")"),
    "compare_backups":       ("Correlated subquery:",         "db.query(\"SELECT * FROM backup_snapshots b WHERE b.snapshot_date='2024-01-01' AND b.row_count > (SELECT row_count FROM backup_snapshots WHERE snapshot_date='2024-03-01' AND table_name=b.table_name)\")"),
    "build_summary":         ("Group by table:",              "db.query(\"SELECT table_name, COUNT(DISTINCT row_count) AS c FROM backup_snapshots GROUP BY table_name HAVING COUNT(DISTINCT row_count) > 1\")"),
    "decode_pattern":        ("Cut a string with SUBSTR:",    "db.query(\"SELECT SUBSTR(action,1,1) FROM server_logs WHERE status='ANOMALY' ORDER BY timestamp\")"),
    "correlate_times":       ("Stitch it with GROUP_CONCAT:", "db.query(\"SELECT GROUP_CONCAT(SUBSTR(action,1,1),'') FROM (SELECT * FROM server_logs WHERE status='ANOMALY' ORDER BY timestamp)\")"),
    "write_report_function": ("Label rows with CASE:",        "db.query(\"SELECT timestamp, CASE WHEN status='ANOMALY' THEN 'PHANTOM' ELSE 'normal' END AS verdict FROM server_logs\")"),
    "identify_source":       ("CASE driven by a subquery:",   "db.query(\"SELECT timestamp, action, CASE WHEN ip_address=(SELECT DISTINCT ip_address FROM server_logs WHERE status='ANOMALY') THEN 'PHANTOM SOURCE' ELSE 'normal' END AS verdict FROM server_logs WHERE strftime('%H',timestamp)='03'\")"),
}


# -- Progressive hints (console, on the hint button: vague → answer) ---------

S2_HINTS = {
    "store_result": [
        "WHERE = 'x' only finds an exact value. You need to match a PATTERN inside the timestamp text.",
        "LIKE with % wildcards. % means 'any characters'. The phantom runs at 03:03.",
        "db.query(\"SELECT * FROM server_logs WHERE timestamp LIKE '%03:03%'\")",
    ],
    "loop_records": [
        "'03:03' could appear in a date too. Isolate just the TIME of day.",
        "strftime('%H:%M', timestamp) returns 'HH:MM'. Compare it to '03:03'.",
        "db.query(\"SELECT * FROM server_logs WHERE strftime('%H:%M', timestamp) = '03:03'\")",
    ],
    "list_comp_filter": [
        "Don't hardcode a threshold. Let the query compute the average itself.",
        "A subquery in WHERE: WHERE restored_count > (SELECT AVG(restored_count) FROM deleted_records).",
        "db.query(\"SELECT * FROM deleted_records WHERE restored_count > (SELECT AVG(restored_count) FROM deleted_records)\")",
    ],
    "find_ghost_employee": [
        "Same skill as the logs — LIKE — but on the deleted_records.record_data text.",
        "Search record_data for a word that proves it's a person, like 'terminated'.",
        "db.query(\"SELECT * FROM deleted_records WHERE record_data LIKE '%terminated%'\")",
    ],
    "parse_timestamps": [
        "Count how many logs fall in each time-of-day; keep only the busy ones.",
        "GROUP BY strftime('%H:%M', timestamp), then HAVING COUNT(*) > 5.",
        "db.query(\"SELECT strftime('%H:%M', timestamp) AS t, COUNT(*) FROM server_logs GROUP BY t HAVING COUNT(*) > 5\")",
    ],
    "count_anomalies": [
        "Same strftime tool — pull the DATE part, not the time.",
        "strftime('%Y-%m-%d', timestamp), DISTINCT, over the anomaly rows.",
        "db.query(\"SELECT DISTINCT strftime('%Y-%m-%d', timestamp) FROM server_logs WHERE status='ANOMALY'\")",
    ],
    "compare_backups": [
        "Compare each table's January count to its OWN March count.",
        "Correlated subquery: WHERE b.row_count > (SELECT row_count FROM backup_snapshots WHERE snapshot_date='2024-03-01' AND table_name=b.table_name).",
        "db.query(\"SELECT * FROM backup_snapshots b WHERE b.snapshot_date='2024-01-01' AND b.row_count > (SELECT row_count FROM backup_snapshots WHERE snapshot_date='2024-03-01' AND table_name=b.table_name)\")",
    ],
    "build_summary": [
        "Group all snapshots by table; a stable table has one unique row_count.",
        "GROUP BY table_name HAVING COUNT(DISTINCT row_count) > 1.",
        "db.query(\"SELECT table_name, COUNT(DISTINCT row_count) AS c FROM backup_snapshots GROUP BY table_name HAVING COUNT(DISTINCT row_count) > 1\")",
    ],
    "decode_pattern": [
        "Take one character — the first — from each phantom action, in order.",
        "SUBSTR(action,1,1), filter status='ANOMALY', ORDER BY timestamp.",
        "db.query(\"SELECT SUBSTR(action,1,1) FROM server_logs WHERE status='ANOMALY' ORDER BY timestamp\")",
    ],
    "correlate_times": [
        "Glue all those first-letters into one string instead of reading them.",
        "GROUP_CONCAT(SUBSTR(action,1,1),'') over an ordered subquery.",
        "db.query(\"SELECT GROUP_CONCAT(SUBSTR(action,1,1),'') FROM (SELECT * FROM server_logs WHERE status='ANOMALY' ORDER BY timestamp)\")",
    ],
    "write_report_function": [
        "Make a new column that says PHANTOM/normal — don't change the data.",
        "CASE WHEN status='ANOMALY' THEN 'PHANTOM' ELSE 'normal' END.",
        "db.query(\"SELECT timestamp, CASE WHEN status='ANOMALY' THEN 'PHANTOM' ELSE 'normal' END AS verdict FROM server_logs\")",
    ],
    "identify_source": [
        "CASE again — but the condition compares ip_address to a subquery's result.",
        "CASE WHEN ip_address=(SELECT DISTINCT ip_address FROM server_logs WHERE status='ANOMALY') THEN 'PHANTOM SOURCE' ELSE 'normal' END, filtered to 3 a.m.",
        "db.query(\"SELECT timestamp, action, CASE WHEN ip_address=(SELECT DISTINCT ip_address FROM server_logs WHERE status='ANOMALY') THEN 'PHANTOM SOURCE' ELSE 'normal' END AS verdict FROM server_logs WHERE strftime('%H',timestamp)='03'\")",
    ],
}


# -- Recall challenges (keyed by SKILL — fired as a between-scene gate) ------
# Story-framed, one question. Engine matches keyword subset (case-insensitive).

S2_RECALL_CHALLENGES = {
    "s2_like": {
        "concept": "s2_like",
        "question": ("Before you move on — quick gut check. You're handed a fresh\n"
                     "table 'logs'. Write SQL that pulls every row whose 'msg'\n"
                     "column contains the word 'error' anywhere in it."),
        "answer": "SELECT * FROM logs WHERE msg LIKE '%error%'",
        "keywords": ["like", "%error%"],
    },
    "s2_datetime": {
        "concept": "s2_datetime",
        "question": ("Quick recall. Given a column 'ts' holding a full timestamp,\n"
                     "how do you pull out just the hour (e.g. '03')?"),
        "answer": "strftime('%H', ts)",
        "keywords": ["strftime", "%h"],
    },
    "s2_subquery": {
        "concept": "s2_subquery",
        "question": ("Recall: select every row from 'sales' whose amount is above\n"
                     "the table's own average amount. Let the query find the average."),
        "answer": "SELECT * FROM sales WHERE amount > (SELECT AVG(amount) FROM sales)",
        "keywords": ["select", "avg", "(", ")"],
    },
    "s2_groupby": {
        "concept": "s2_groupby",
        "question": ("Recall: in server_logs, count rows per user and keep only\n"
                     "users with more than five entries."),
        "answer": "SELECT user, COUNT(*) FROM server_logs GROUP BY user HAVING COUNT(*) > 5",
        "keywords": ["group by", "having", "count"],
    },
    "s2_string": {
        "concept": "s2_string",
        "question": ("Recall: write the expression that returns the first\n"
                     "character of a column called 'action'."),
        "answer": "SUBSTR(action, 1, 1)",
        "keywords": ["substr"],
    },
    "s2_case": {
        "concept": "s2_case",
        "question": ("Recall: write a CASE expression that outputs 'high' when a\n"
                     "column n is greater than 10, otherwise 'low'."),
        "answer": "CASE WHEN n > 10 THEN 'high' ELSE 'low' END",
        "keywords": ["case", "when", "then", "else", "end"],
    },
}


# -- Cliffhangers — dramatic "end of episode" cards between scenes ───────────

S2_CLIFFHANGERS = {
    S2_SCENE_SERVER_LOGS: {
        "eyebrow":  "EPISODE 2",
        "headline": "Ghost Records",
        "teaser":   (
            "The logs don't lie.\n"
            "But they also don't explain the rows that shouldn't exist.\n\n"
            "Deleted records. Coming back.\n"
            "Something in the database has memory."
        ),
        "cta": "Into the Ghost Records →",
    },
    S2_SCENE_GHOST_RECORDS: {
        "eyebrow":  "EPISODE 3",
        "headline": "Timestamp Anomalies",
        "teaser":   (
            "The records aren't corrupted. They're signed.\n"
            "Whoever — whatever — is putting them back\n"
            "is leaving timestamps.\n\n"
            "3:03am. Every time."
        ),
        "cta": "Follow the Timestamps →",
    },
    S2_SCENE_TIMESTAMP: {
        "eyebrow":  "EPISODE 4",
        "headline": "Into the Archive",
        "teaser":   (
            "The pattern is too precise to be noise.\n"
            "There's a schema in the backup archive\n"
            "that was never meant to be found.\n\n"
            "Someone hid something before they left."
        ),
        "cta": "Open the Archive →",
    },
    S2_SCENE_ARCHIVE: {
        "eyebrow":  "EPISODE 5",
        "headline": "Decode the Pattern",
        "teaser":   (
            "There's a message in the data.\n"
            "Not metaphorically. Literally.\n\n"
            "The values form a sequence.\n"
            "You need to read it."
        ),
        "cta": "Decode the Signal →",
    },
    S2_SCENE_PATTERN_DECODER: {
        "eyebrow":  "EPISODE 6",
        "headline": "The Signal",
        "teaser":   (
            "The message decoded.\n"
            "It's a name. A date. A location.\n\n"
            "Elena Vasquez knew this would happen.\n"
            "She left you a key.\n"
            "Use it."
        ),
        "cta": "Final Transmission →",
    },
}


# -- Step text kept as an alias so any legacy import still resolves ----------
S2_STEP_TEXT = {oid: mv[1] for oid, mv in S2_YOUR_MOVE.items()}
S2_SCENE_INTROS = dict(S2_SCENE_WHY)
