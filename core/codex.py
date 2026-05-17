# core/codex.py
# CODEX — the in-game concept library.
#
# Each entry teaches one SQL or Python concept.
# Shown as a popup card after the player completes an objective that uses it.
#
# Structure per concept:
#   id          — matches "concept" key in game.py OBJECTIVES
#   title       — short name (shown in card header)
#   what        — one sentence: what is this?
#   why         — one sentence: why does a data analyst actually use it?
#   syntax      — code example (shown in monospace box)
#   analogy     — real-world comparison (no jargon)
#   gotcha      — common mistake beginners make


CONCEPTS = {

    # ── SQL Foundations ──────────────────────────────────────────────────────

    "tables": {
        "id":      "tables",
        "title":   "Database Tables",
        "what":    "A table stores data in rows (records) and columns (fields) — like a spreadsheet tab.",
        "why":     "Every piece of data you'll ever analyze lives in a table. You need to know what tables exist before you can query anything.",
        "syntax":  "SELECT name FROM sqlite_master WHERE type='table';\n-- or just: db.tables()",
        "analogy": "A database is a filing cabinet. Each table is a drawer labeled 'Employees' or 'Transactions.'",
        "gotcha":  "Table names are case-sensitive in some databases. Always check the exact name first.",
    },

    "select_star": {
        "id":      "select_star",
        "title":   "SELECT * FROM",
        "what":    "SELECT retrieves data. * means 'every column.' FROM names the table.",
        "why":     "The first thing you do with any new dataset: look at it. SELECT * is your starting point.",
        "syntax":  "SELECT * FROM employees;\nSELECT * FROM transactions;",
        "analogy": "Opening a spreadsheet and scrolling through all the rows before you decide what to focus on.",
        "gotcha":  "SELECT * on a million-row table can be slow. Add LIMIT 10 to preview safely.",
    },

    "aggregate_count": {
        "id":      "aggregate_count",
        "title":   "COUNT(*) — Counting Rows",
        "what":    "COUNT(*) is an aggregate function — it collapses all matching rows into a single number.",
        "why":     "'How many customers do we have?' 'How many orders came in this week?' COUNT answers those instantly.",
        "syntax":  "SELECT COUNT(*) FROM employees;\nSELECT COUNT(*) FROM transactions WHERE vendor_id = 4;",
        "analogy": "Asking someone to count the people in a room vs. listing every person's name.",
        "gotcha":  "COUNT(*) counts rows including NULLs. COUNT(column) skips rows where that column is NULL.",
    },

    "where_filter": {
        "id":      "where_filter",
        "title":   "WHERE — Filtering Rows",
        "what":    "WHERE limits your results to only rows that match a condition.",
        "why":     "Real datasets have millions of rows. WHERE is how you zoom in on just what matters.",
        "syntax":  "SELECT * FROM vendors WHERE verified = 0;\nSELECT * FROM employees WHERE department = 'Finance';",
        "analogy": "Ctrl+F in a spreadsheet — but instead of highlighting, it hides everything that doesn't match.",
        "gotcha":  "Strings need quotes: WHERE name = 'Alex'. Numbers don't: WHERE id = 4.",
    },

    "group_by_sum": {
        "id":      "group_by_sum",
        "title":   "GROUP BY + SUM()",
        "what":    "GROUP BY bundles rows that share a value; SUM() adds up a column within each bundle.",
        "why":     "'How much did we spend per vendor?' 'Total revenue by region?' This is the combo that answers both.",
        "syntax":  "SELECT vendor_id, SUM(amount) as total\nFROM transactions\nGROUP BY vendor_id\nORDER BY total DESC;",
        "analogy": "Sorting receipts by category and totalling each pile — groceries, utilities, restaurants.",
        "gotcha":  "Every column in SELECT must either be in GROUP BY or wrapped in an aggregate (SUM, COUNT, AVG).",
    },

    "inner_join": {
        "id":      "inner_join",
        "title":   "JOIN — Connecting Tables",
        "what":    "JOIN combines rows from two tables where a column matches — like a VLOOKUP that works properly.",
        "why":     "Data is split across tables on purpose. JOINs let you combine them for analysis.",
        "syntax":  "SELECT t.date, t.amount, v.name\nFROM transactions t\nJOIN vendors v ON t.vendor_id = v.id;",
        "analogy": "You have a list of order IDs and a separate list of customer names. JOIN links them by the shared ID.",
        "gotcha":  "If the join column has NULLs, those rows are dropped. Use LEFT JOIN to keep them.",
    },

    "where_equals": {
        "id":      "where_equals",
        "title":   "WHERE with = (Exact Match)",
        "what":    "The = operator filters for rows where a column is exactly equal to a value.",
        "why":     "Lookup queries — 'find this customer,' 'show me this order' — are the most common queries in any job.",
        "syntax":  "SELECT * FROM employees WHERE id = 4;\nSELECT * FROM transactions WHERE department = 'Finance';",
        "analogy": "Searching a contact list for a specific name — exact match, nothing approximate.",
        "gotcha":  "In SQL, a single = is for comparison. You won't use == like in Python.",
    },

    "primary_key_lookup": {
        "id":      "primary_key_lookup",
        "title":   "Primary Keys",
        "what":    "A primary key is a unique ID column — no two rows can share it. It's how tables identify individual records.",
        "why":     "When you see a foreign key (like approved_by), it points to the primary key of another table. That's how data links together.",
        "syntax":  "-- employees.id is a primary key\nSELECT * FROM employees WHERE id = 4;\n-- transactions.approved_by is a foreign key → employees.id",
        "analogy": "A social security number — unique per person, used to link records across different systems.",
        "gotcha":  "Primary keys are usually integers that auto-increment. Never assume IDs start at 1 in real databases.",
    },

    "order_by": {
        "id":      "order_by",
        "title":   "ORDER BY — Sorting Results",
        "what":    "ORDER BY sorts your output. ASC = smallest first (default). DESC = largest first.",
        "why":     "'Who are our top 10 customers?' 'What's our biggest expense?' Sorting reveals the outliers immediately.",
        "syntax":  "SELECT * FROM departments ORDER BY budget DESC;\nSELECT * FROM employees ORDER BY salary ASC;",
        "analogy": "Sorting a spreadsheet column — clicking the column header to flip between A→Z and Z→A.",
        "gotcha":  "ORDER BY runs after WHERE and GROUP BY. You're sorting the final result, not the raw table.",
    },

    "sum_where": {
        "id":      "sum_where",
        "title":   "SUM() + WHERE Together",
        "what":    "Combining SUM with WHERE gives you a total for a specific subset of rows.",
        "why":     "'How much did we pay this vendor?' 'What's our Q3 revenue?' These need both filtering and totalling.",
        "syntax":  "SELECT SUM(amount) as total\nFROM transactions\nWHERE vendor_id = 4;",
        "analogy": "Adding up only the grocery receipts in your expense folder — filter first, then total.",
        "gotcha":  "SUM returns NULL if no rows match your WHERE clause. Use COALESCE(SUM(amount), 0) to get 0 instead.",
    },

    "order_by_date": {
        "id":      "order_by_date",
        "title":   "Sorting by Date",
        "what":    "Dates stored as text (YYYY-MM-DD) sort correctly with ORDER BY because the format is zero-padded.",
        "why":     "Time-series analysis — spotting trends, escalations, seasonality — is core analyst work.",
        "syntax":  "SELECT date, amount\nFROM transactions\nWHERE vendor_id = 4\nORDER BY date;",
        "analogy": "Sorting your bank statements by date to see where your spending spiked.",
        "gotcha":  "Only works reliably with ISO format (YYYY-MM-DD). Mixed date formats in real data are a notorious headache.",
    },

    "in_clause": {
        "id":      "in_clause",
        "title":   "IN — Matching a List",
        "what":    "IN lets you match a column against multiple values at once, without stacking ORs.",
        "why":     "'Show me orders from these 5 customers' — IN is cleaner and faster than writing OR five times.",
        "syntax":  "SELECT * FROM transactions\nWHERE vendor_id IN (4, 7);\n\n-- Same as:\n-- WHERE vendor_id = 4 OR vendor_id = 7",
        "analogy": "A guest list check — is this name on the list? If yes, let them in.",
        "gotcha":  "IN with a subquery is powerful: WHERE id IN (SELECT id FROM ...). Very common in real analysis.",
    },

    "subquery_or_having": {
        "id":      "subquery_or_having",
        "title":   "Combining Aggregates",
        "what":    "You can SUM across multiple groups, or filter aggregated results with HAVING (like WHERE, but after GROUP BY).",
        "why":     "Final audit numbers — 'total fraud across all shell vendors' — often require combining grouped totals.",
        "syntax":  "-- Total across all matching rows:\nSELECT SUM(amount) FROM transactions\nWHERE vendor_id IN (4, 7);\n\n-- Or grouped:\nSELECT vendor_id, SUM(amount)\nFROM transactions\nWHERE vendor_id IN (4, 7)\nGROUP BY vendor_id;",
        "analogy": "Adding up the subtotals from each expense category to get a grand total on a report.",
        "gotcha":  "HAVING filters after aggregation. WHERE filters before. Mix them up and you get wrong numbers.",
    },
}


def get_concept(concept_id: str) -> dict | None:
    """Return a concept dict by id, or None if not found."""
    return CONCEPTS.get(concept_id)


def all_concepts() -> list[dict]:
    """Return all concepts in definition order."""
    return list(CONCEPTS.values())
