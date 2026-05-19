# core/season2_codex.py
# CODEX — Season 2 concept library (SIX core SQL skills).
#
# One card per skill, shown the FIRST time the player uses that skill.
# The second (varied-practice) rep does NOT re-show the card — by then
# they're practising, not learning. Same structure as core/codex.py:
#   id, title, what, why, syntax, analogy, gotcha


S2_CONCEPTS = {

    "s2_like": {
        "id": "s2_like",
        "title": "LIKE — Pattern Matching",
        "what": "LIKE filters text by a pattern instead of an exact value. % matches any run of characters; _ matches exactly one.",
        "why": "Season 1's WHERE col = 'x' only finds exact matches. Real investigations need 'contains', 'starts with', 'ends with' — searching inside messy text. You'll use this again on a totally different column later; the skill travels.",
        "syntax": "WHERE name  LIKE 'A%'         -- starts with A\nWHERE email LIKE '%@nexus.co'  -- ends with that\nWHERE ts    LIKE '%03:03%'     -- contains 03:03",
        "analogy": "WHERE = asks 'is this exactly my key?'. LIKE asks 'does this look roughly like the shape I'm describing?'.",
        "gotcha": "% matches zero OR more characters, so '%03:03%' also matches a value that is only '03:03'. To match a literal % you need an ESCAPE clause.",
    },

    "s2_datetime": {
        "id": "s2_datetime",
        "title": "strftime — Reading Pieces of a Date/Time",
        "what": "strftime(format, column) pulls a piece out of a date/time string. '%H'=hour, '%M'=minute, '%Y'=year, '%Y-%m-%d'=the date, '%H:%M'=hour:minute.",
        "why": "Timestamps hide patterns. 'It always happens at 3:03' and 'it ran every night for two weeks' are invisible until you can extract just the part you care about — once the time, later the date. Same tool, different cut.",
        "syntax": "strftime('%H:%M', timestamp) = '03:03'\nstrftime('%Y-%m-%d', timestamp)       -- the date\nstrftime('%H', timestamp)    = '03'",
        "analogy": "A timestamp is a sentence. strftime is a highlighter that grabs only the word you need.",
        "gotcha": "strftime needs a clean 'YYYY-MM-DD HH:MM:SS' string. A malformed date returns NULL silently — no error, just nothing matches.",
    },

    "s2_subquery": {
        "id": "s2_subquery",
        "title": "Subqueries — A Query Inside a Query",
        "what": "A SELECT nested inside another statement. The inner query runs first; the outer one uses its result. Later you'll meet a *correlated* subquery that re-runs per outer row.",
        "why": "Some questions depend on an answer you don't have yet — 'rows above the average', 'this row vs the same row in another snapshot'. The subquery computes that answer on the fly so you never hardcode a guess.",
        "syntax": "SELECT * FROM sales\nWHERE amount > (SELECT AVG(amount) FROM sales)\n\n-- correlated (references the outer row):\nWHERE b.row_count >\n  (SELECT row_count FROM snaps s WHERE s.tbl = b.tbl)",
        "analogy": "'Who earns above the company average?' — you must work out the average first, then compare. The subquery does step one, inside the same query.",
        "gotcha": "A subquery used with > or = must return ONE value (one row, one column). Need a list? Use IN (...) instead.",
    },

    "s2_groupby": {
        "id": "s2_groupby",
        "title": "GROUP BY + HAVING — Aggregate, Then Filter Groups",
        "what": "GROUP BY buckets rows by a column; COUNT/SUM/etc. summarise each bucket; HAVING filters those buckets (WHERE can't — it runs before grouping).",
        "why": "This turns a hunch into evidence: 'this minute has 14 hits, the next-highest has 1.' You'll group by time once, and by table later — the move is identical, only the column changes.",
        "syntax": "SELECT user, COUNT(*)\nFROM server_logs\nGROUP BY user\nHAVING COUNT(*) > 5",
        "analogy": "Sort mail into pigeonholes (GROUP BY), count each pile (COUNT), keep only the overflowing ones (HAVING).",
        "gotcha": "WHERE filters rows before grouping; HAVING filters groups after. Putting an aggregate in WHERE is an error — that's HAVING's job.",
    },

    "s2_string": {
        "id": "s2_string",
        "title": "SUBSTR & GROUP_CONCAT — String Surgery",
        "what": "SUBSTR(text, start, length) cuts a piece out of a string (positions start at 1). GROUP_CONCAT(col, sep) is an aggregate that glues many rows' values into one string.",
        "why": "Evidence is sometimes hidden IN the text — a message spelled one letter per row. First you extract the letters (SUBSTR), then you assemble them (GROUP_CONCAT). Two reps of one skill: take apart, put together.",
        "syntax": "SUBSTR(action, 1, 1)            -- first char\nGROUP_CONCAT(SUBSTR(action,1,1), '')\n  FROM (SELECT ... ORDER BY ts)",
        "analogy": "SUBSTR is scissors with a ruler. GROUP_CONCAT is the glue stick that lays the cut pieces back in a row.",
        "gotcha": "SQL strings are 1-indexed (not 0). GROUP_CONCAT's row order isn't guaranteed unless you feed it a pre-ORDERed subquery.",
    },

    "s2_case": {
        "id": "s2_case",
        "title": "CASE WHEN — SQL's If/Else",
        "what": "CASE WHEN condition THEN value [ELSE value] END produces a new value per row from a test — without modifying the table.",
        "why": "Reports need verdicts, not raw codes: turn status='ANOMALY' into 'PHANTOM'. Simple at first; later the condition itself is driven by a subquery — same CASE, sharper teeth.",
        "syntax": "SELECT ts,\n  CASE WHEN status='ANOMALY' THEN 'PHANTOM'\n       ELSE 'normal' END AS verdict\nFROM server_logs",
        "analogy": "A stamp at a checkpoint: each row walks past, you read one field, you stamp a verdict. The row itself is unchanged.",
        "gotcha": "Don't forget END. With no ELSE, non-matching rows become NULL — usually you want an explicit ELSE.",
    },
}
