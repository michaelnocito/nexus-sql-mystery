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

    # ── Season 1: the 8 core SQL skills (each practised twice) ───────────────

    "s1_select": {
        "id":      "s1_select",
        "title":   "SELECT / FROM — Asking for Data",
        "what":    "SELECT names the columns you want; FROM names the table they live in.",
        "why":     "It's the spine of every query you'll ever write. Pulling the right columns (not blindly SELECT *) keeps results readable and fast.",
        "syntax":  "SELECT name, salary FROM employees;\nSELECT name FROM sqlite_master WHERE type='table';",
        "analogy": "Walking up to a filing cabinet and saying exactly which folder and which pages you want — not dumping the whole drawer on the desk.",
        "gotcha":  "SELECT * grabs every column. Fine to peek; bad in real reports — name the columns you actually need.",
    },

    "s1_where": {
        "id":      "s1_where",
        "title":   "WHERE — Filtering Rows",
        "what":    "WHERE keeps only the rows that match a condition.",
        "why":     "You almost never want every row. WHERE is how you isolate the unverified vendor, the one employee, the suspicious slice.",
        "syntax":  "SELECT * FROM vendors  WHERE verified = 0;\nSELECT * FROM employees WHERE id = 4;",
        "analogy": "A bouncer at the door: only rows meeting the condition get through; everything else stays out.",
        "gotcha":  "Text needs quotes ('Finance'); numbers don't (4). = is exact — for patterns you'd need LIKE.",
    },

    "s1_count": {
        "id":      "s1_count",
        "title":   "COUNT — How Many Rows",
        "what":    "COUNT(*) returns the number of rows, optionally after a WHERE filter.",
        "why":     "'How many?' is one of the first questions in any analysis — headcount, how many payments, how often something happened.",
        "syntax":  "SELECT COUNT(*) FROM employees;\nSELECT COUNT(*) FROM transactions WHERE vendor_id = 4;",
        "analogy": "Tallying people in a room instead of writing down every name.",
        "gotcha":  "COUNT(*) counts rows including NULLs; COUNT(column) skips rows where that column is NULL.",
    },

    "s1_sum": {
        "id":      "s1_sum",
        "title":   "SUM — Adding a Column Up",
        "what":    "SUM(column) totals the numeric values in that column across the matching rows.",
        "why":     "The damning number in a fraud case is a total: how much money went to this vendor, this department, in total.",
        "syntax":  "SELECT SUM(amount) FROM transactions WHERE vendor_id = 4;\nSELECT SUM(amount) FROM transactions WHERE department='Special Projects';",
        "analogy": "Running every receipt through an adding machine and reading the tape's last number.",
        "gotcha":  "SUM ignores NULLs. Filter with WHERE first, or you'll total the whole table by accident.",
    },

    "s1_groupby": {
        "id":      "s1_groupby",
        "title":   "GROUP BY — One Row Per Bucket",
        "what":    "GROUP BY collapses rows that share a value into one row, so COUNT/SUM apply per group.",
        "why":     "'Total per vendor' or 'payments per approver' — GROUP BY is how a list of transactions becomes a ranking that exposes the outlier.",
        "syntax":  "SELECT vendor_id, SUM(amount) FROM transactions\nGROUP BY vendor_id ORDER BY SUM(amount) DESC;",
        "analogy": "Sorting a pile of receipts into one envelope per vendor, then writing the total on each envelope.",
        "gotcha":  "Every selected column must be either grouped or inside an aggregate (SUM/COUNT), or the result is meaningless.",
    },

    "s1_join": {
        "id":      "s1_join",
        "title":   "JOIN — Linking Two Tables",
        "what":    "JOIN combines rows from two tables that share a key (e.g. transactions.vendor_id = vendors.id).",
        "why":     "IDs are useless in a report. JOIN swaps vendor_id 4 for 'Apex Solutions', approved_by 4 for 'Marcus Webb'.",
        "syntax":  "SELECT t.*, v.name\nFROM transactions t JOIN vendors v ON t.vendor_id = v.id;",
        "analogy": "Two spreadsheets with a shared ID column, taped together so each row carries both sides.",
        "gotcha":  "Forget the ON clause and you get every row paired with every row — a giant nonsense result.",
    },

    "s1_orderby": {
        "id":      "s1_orderby",
        "title":   "ORDER BY — Sorting Results",
        "what":    "ORDER BY sorts the result set by a column; DESC = highest first, ASC (default) = lowest first.",
        "why":     "Patterns hide in unsorted data. Sort by budget and the giant line jumps out; sort by date and an escalation reveals itself.",
        "syntax":  "SELECT * FROM departments ORDER BY budget DESC;\nSELECT date, amount FROM transactions WHERE vendor_id=4 ORDER BY date;",
        "analogy": "Fanning a deck of cards into order so the high ones (or the trend) are obvious at a glance.",
        "gotcha":  "ORDER BY only arranges the output — it never filters. Default is ascending; add DESC for biggest-first.",
    },

    "s1_in": {
        "id":      "s1_in",
        "title":   "IN — Match Any of a List",
        "what":    "WHERE col IN (a, b, c) keeps rows where the column equals any value in the list.",
        "why":     "Two shell vendors, several departments — IN asks one clean question instead of stacking OR after OR.",
        "syntax":  "SELECT * FROM transactions WHERE vendor_id IN (4, 7);\nSELECT * FROM employees WHERE department IN ('Finance','Executive');",
        "analogy": "A guest list: if your name is on it (any entry), you're in.",
        "gotcha":  "Quote text values inside IN ('Finance','Executive'); leave numbers bare (4, 7).",
    },

}


def get_concept(concept_id: str) -> dict | None:
    """Return a concept dict by id, or None if not found."""
    return CONCEPTS.get(concept_id)


def all_concepts() -> list[dict]:
    """Return all concepts in definition order."""
    return list(CONCEPTS.values())
