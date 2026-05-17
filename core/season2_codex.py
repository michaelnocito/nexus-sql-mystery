# core/season2_codex.py
# CODEX — Season 2 concept library (SQL-CORE EDITION).
#
# Each entry teaches one intermediate SQL concept — the next tier after
# Season 1. Shown as a popup card after the player completes an objective
# that uses it. Same structure as core/codex.py:
#   id, title, what, why, syntax, analogy, gotcha


S2_CONCEPTS = {

    "s2_like": {
        "id":      "s2_like",
        "title":   "LIKE — Pattern Matching",
        "what":    "LIKE filters text by a pattern instead of an exact value. % matches any run of characters; _ matches exactly one.",
        "why":     "Season 1's WHERE col = 'x' only finds exact matches. Real data is messy — you need 'contains', 'starts with', 'ends with'. LIKE is how you search inside strings.",
        "syntax":  "WHERE name LIKE 'A%'        -- starts with A\nWHERE email LIKE '%@nexus.co' -- ends with that\nWHERE ts LIKE '%03:03%'      -- contains 03:03",
        "analogy": "WHERE = is asking 'is this exactly the key I'm holding?'. LIKE is asking 'does this look roughly like the shape I'm describing?'.",
        "gotcha":  "% matches zero OR more characters, so '%03:03%' also matches a row that is only '03:03'. To match a literal % you'd need an ESCAPE clause.",
    },

    "s2_datetime": {
        "id":      "s2_datetime",
        "title":   "Date/Time Functions — strftime",
        "what":    "strftime(format, column) pulls pieces out of a date/time string. '%H' = hour, '%M' = minute, '%Y' = year, '%H:%M' = hour:minute.",
        "why":     "Timestamps hide patterns. 'Everything happens at 3:03am' is invisible until you can extract just the time and compare it.",
        "syntax":  "strftime('%H:%M', timestamp) = '03:03'\nstrftime('%Y', hire_date)   = '2024'\nstrftime('%H', timestamp)    = '03'",
        "analogy": "A timestamp is a sentence. strftime is a highlighter that grabs only the word you care about.",
        "gotcha":  "strftime needs a clean 'YYYY-MM-DD HH:MM:SS' string. Garbage-formatted dates return NULL silently — no error, just nothing matches.",
    },

    "s2_subquery": {
        "id":      "s2_subquery",
        "title":   "Subqueries — A Query Inside a Query",
        "what":    "A subquery is a SELECT nested inside another statement. The inner query runs first; the outer query uses its result.",
        "why":     "Some questions depend on an answer you don't know yet — 'rows above the average', 'records not in the other table'. The subquery computes that answer on the fly.",
        "syntax":  "SELECT * FROM sales\nWHERE amount > (SELECT AVG(amount) FROM sales)",
        "analogy": "Asking 'who earns more than the company average?' — you must first work out the average, then compare. The subquery does step one for you, inside the same query.",
        "gotcha":  "A subquery used with > or = must return ONE value (one row, one column). Returning many values there throws an error — use IN for a list.",
    },

    "s2_having": {
        "id":      "s2_having",
        "title":   "HAVING — Filtering Groups",
        "what":    "HAVING filters the results of GROUP BY. It works like WHERE, but it runs AFTER aggregation, so it can test SUM, COUNT, AVG.",
        "why":     "WHERE can't see a SUM — the sum doesn't exist until rows are grouped. HAVING is how you ask 'only show groups whose total is over 10'.",
        "syntax":  "SELECT vendor_id, SUM(amount)\nFROM transactions\nGROUP BY vendor_id\nHAVING SUM(amount) > 100000",
        "analogy": "WHERE checks each person before they get into teams. HAVING checks each TEAM after it's formed.",
        "gotcha":  "Order matters: WHERE before GROUP BY (filters rows), HAVING after (filters groups). Don't put an aggregate in WHERE — that's a HAVING job.",
    },

    "s2_groupby_having": {
        "id":      "s2_groupby_having",
        "title":   "GROUP BY + HAVING COUNT — Proving a Pattern",
        "what":    "Bucket rows with GROUP BY, count each bucket with COUNT(*), then keep only the suspicious buckets with HAVING COUNT(*) > n.",
        "why":     "This is how you turn a hunch ('it always happens at 3:03') into evidence ('this time slot has 14 hits; the next-highest has 1').",
        "syntax":  "SELECT strftime('%H:%M', ts) AS t, COUNT(*)\nFROM server_logs\nGROUP BY t\nHAVING COUNT(*) > 5",
        "analogy": "Sorting mail into pigeonholes (GROUP BY), counting each pile (COUNT), then pulling only the overflowing ones (HAVING).",
        "gotcha":  "The column you GROUP BY should also be what you SELECT, or the output rows won't line up with their counts.",
    },

    "s2_case": {
        "id":      "s2_case",
        "title":   "CASE WHEN — SQL's If/Else",
        "what":    "CASE WHEN condition THEN value [ELSE value] END produces a new value per row based on a test — without modifying the table.",
        "why":     "Reports need labels, not raw codes. CASE turns status='ANOMALY' into a human-readable 'PHANTOM' right in the result set.",
        "syntax":  "SELECT ts,\n  CASE WHEN status='ANOMALY' THEN 'PHANTOM'\n       ELSE 'normal' END AS verdict\nFROM server_logs",
        "analogy": "A stamp at a checkpoint: each row walks past, you read one field, and you stamp a verdict on it. The row itself is unchanged.",
        "gotcha":  "Don't forget END. Without an ELSE, non-matching rows get NULL — usually you want an explicit ELSE.",
    },

    "s2_derived_table": {
        "id":      "s2_derived_table",
        "title":   "Derived Tables — Subquery in FROM",
        "what":    "You can put a SELECT in the FROM clause and treat its result like a table (give it an alias). That's a derived table.",
        "why":     "To compare two slices of the same table — January vs March snapshots — you make each slice its own mini-table and JOIN them.",
        "syntax":  "SELECT j.t, j.cnt, m.cnt\nFROM (SELECT ... WHERE date='2024-01-01') j\nJOIN (SELECT ... WHERE date='2024-03-01') m\n  ON j.t = m.t",
        "analogy": "Photocopying two pages of a ledger, laying them side by side on the desk, and drawing lines between matching rows.",
        "gotcha":  "Every derived table needs an alias (the j and m above). Without it, SQLite can't refer to its columns.",
    },

    "s2_distinct": {
        "id":      "s2_distinct",
        "title":   "DISTINCT — Unique Values",
        "what":    "SELECT DISTINCT col collapses duplicate rows so you see each unique value once.",
        "why":     "Hundreds of log rows, but how many actual sources? DISTINCT cuts the noise and reveals the one address that doesn't belong.",
        "syntax":  "SELECT DISTINCT ip_address FROM server_logs\nSELECT DISTINCT department, title FROM employees",
        "analogy": "Dumping a jar of mixed coins on the table and keeping just one of each denomination to see what types you actually have.",
        "gotcha":  "DISTINCT applies to the WHOLE row you selected. SELECT DISTINCT a, b dedupes on the pair (a,b), not on a alone.",
    },

    "s2_substr": {
        "id":      "s2_substr",
        "title":   "SUBSTR — Cutting Strings",
        "what":    "SUBSTR(text, start, length) returns part of a string. Positions start at 1. SUBSTR(x, 1, 1) is the first character.",
        "why":     "The hidden message lives in the first letter of each action. You need surgical control over text to extract it.",
        "syntax":  "SUBSTR(action, 1, 1)     -- first char\nSUBSTR(email, 1, 5)      -- first 5 chars\nSUBSTR(ts, 12, 5)        -- the 'HH:MM' slice",
        "analogy": "Scissors with a ruler: start cutting at position N, cut a piece L long, keep that piece.",
        "gotcha":  "SQL strings are 1-indexed, not 0-indexed like most programming languages. SUBSTR(x,1,1) — not (x,0,1).",
    },

    "s2_group_concat": {
        "id":      "s2_group_concat",
        "title":   "GROUP_CONCAT — Many Rows Into One String",
        "what":    "GROUP_CONCAT(col, separator) is an aggregate that glues the values from many rows into a single combined string.",
        "why":     "Reading a hidden message down a column works, but GROUP_CONCAT hands you the whole assembled message in one cell — the payoff moment.",
        "syntax":  "SELECT GROUP_CONCAT(SUBSTR(action,1,1), '')\nFROM (SELECT * FROM server_logs\n      WHERE status='ANOMALY' ORDER BY timestamp)",
        "analogy": "COUNT turns many rows into one number. SUM turns them into one total. GROUP_CONCAT turns them into one string.",
        "gotcha":  "Row order inside GROUP_CONCAT isn't guaranteed unless you feed it a pre-ordered subquery. ORDER BY in the inner SELECT fixes it.",
    },

    "s2_capstone": {
        "id":      "s2_capstone",
        "title":   "Capstone — Composing It All",
        "what":    "Real analyst queries stack the pieces: a subquery feeds a CASE label, wrapped in a date/time filter, all in one statement.",
        "why":     "Each concept is a tool. Mastery is using them together — this is the query that names the ghost using nothing but SQL.",
        "syntax":  "SELECT ts, action,\n  CASE WHEN ip = (SELECT DISTINCT ip ... WHERE status='ANOMALY')\n       THEN 'PHANTOM SOURCE' ELSE 'normal' END\nFROM server_logs\nWHERE strftime('%H', ts) = '03'",
        "analogy": "You learned the chords; this is the song. Nothing new — just everything at once, in time.",
        "gotcha":  "Build it in layers: get the subquery returning the right single value first, then wrap CASE around it, then add the WHERE. Don't write all three at once.",
    },
}
