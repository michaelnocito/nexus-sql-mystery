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


def _no_star(sql, r):
    low = sql.lower()
    return ("select" in low and "from" in low and "employees" in low
            and "*" not in sql and len(r) > 0)

# Season 1 — VARIED PRACTICE: 8 core SQL skills, each practised TWICE
# across 16 beats in a slightly different context + escalating difficulty.
# Skill = concept id; card shows on rep 1 only (rep 2 is silent practice).
#   s1_select · s1_where · s1_count · s1_sum · s1_groupby · s1_join
#   · s1_orderby · s1_in
OBJECTIVES = [
    # ── your_desk ────────────────────────────────────────────────────────────
    {
        "id": "list_tables", "scene": SCENE_YOUR_DESK,
        "concept": "s1_select", "rep": 1,
        "label": "Ran your first query",
        "detail": "SELECT * FROM employees — the universal first SQL query.",
        "validator": lambda sql, r: (
            "select" in sql.lower() and "from" in sql.lower()
            and "employees" in sql.lower() and "*" in sql
            and "count" not in sql.lower() and len(r) > 0),
    },
    {
        "id": "view_employees", "scene": SCENE_YOUR_DESK,
        "concept": "s1_select", "rep": 2,
        "label": "Pulled specific employee columns",
        "detail": "Selected named columns from employees (not SELECT *).",
        "validator": _no_star,
    },
    {
        "id": "count_headcount", "scene": SCENE_YOUR_DESK,
        "concept": "s1_count", "rep": 1,
        "label": "Counted the headcount",
        "detail": "Used COUNT(*) to measure how many people work at Nexus.",
        "validator": _sql_contains("count", "employees"),
    },

    # ── db_terminal ──────────────────────────────────────────────────────────
    {
        "id": "vendor_spend", "scene": SCENE_DB_TERMINAL,
        "concept": "s1_groupby", "rep": 1,
        "label": "Ranked vendors by total spend",
        "detail": "GROUP BY vendor_id + SUM(amount) to rank where the money goes.",
        "validator": lambda sql, r: _sql_contains("group by", "vendor_id")(sql, r) and "sum" in sql.lower(),
    },
    {
        "id": "unverified_vendors", "scene": SCENE_DB_TERMINAL,
        "concept": "s1_where", "rep": 1,
        "label": "Flagged the unverified vendors",
        "detail": "WHERE verified = 0 — two vendors, no address on file.",
        "validator": _sql_contains("vendors", "verified"),
    },
    {
        "id": "join_vendor_names", "scene": SCENE_DB_TERMINAL,
        "concept": "s1_join", "rep": 1,
        "label": "Joined transactions to vendor names",
        "detail": "JOIN transactions to vendors to put names on the numbers.",
        "validator": _sql_contains("join", "vendor", "transaction"),
    },

    # ── hr_files ─────────────────────────────────────────────────────────────
    {
        "id": "lookup_webb", "scene": SCENE_HR_FILES,
        "concept": "s1_where", "rep": 2,
        "label": "Looked up employee #4",
        "detail": "WHERE id = 4 — a precise lookup. Marcus Webb, CFO.",
        "validator": _sql_contains("employees", "id", "4"),
    },
    {
        "id": "approver_counts", "scene": SCENE_HR_FILES,
        "concept": "s1_groupby", "rep": 2,
        "label": "Counted approvals per employee",
        "detail": "GROUP BY approved_by + COUNT — same skill, new column.",
        "validator": lambda sql, r: _sql_contains("group by", "approved_by")(sql, r) and "count" in sql.lower(),
    },
    {
        "id": "dept_budgets", "scene": SCENE_HR_FILES,
        "concept": "s1_orderby", "rep": 1,
        "label": "Ranked the department budgets",
        "detail": "ORDER BY budget DESC — Special Projects dwarfs the rest.",
        "validator": _sql_contains("departments", "order by", "budget"),
    },

    # ── cfo_dept ─────────────────────────────────────────────────────────────
    {
        "id": "apex_total", "scene": SCENE_CFO_DEPT,
        "concept": "s1_sum", "rep": 1,
        "label": "Totalled Apex's payments",
        "detail": "SUM(amount) WHERE vendor_id = 4 — over a million dollars.",
        "validator": _sql_contains("sum", "vendor_id"),
    },
    {
        "id": "apex_count", "scene": SCENE_CFO_DEPT,
        "concept": "s1_count", "rep": 2,
        "label": "Counted Apex's payments",
        "detail": "COUNT(*) WHERE vendor_id = 4 — same skill, filtered set.",
        "validator": _sql_contains("count", "vendor_id"),
    },
    {
        "id": "escalation", "scene": SCENE_CFO_DEPT,
        "concept": "s1_orderby", "rep": 2,
        "label": "Traced the escalation by date",
        "detail": "ORDER BY date on the Apex rows — amounts climb fast.",
        "validator": _sql_contains("vendor_id", "order by", "date"),
    },

    # ── audit_trail ──────────────────────────────────────────────────────────
    {
        "id": "dual_vendor", "scene": SCENE_AUDIT_TRAIL,
        "concept": "s1_in", "rep": 1,
        "label": "Pulled both shell vendors with IN",
        "detail": "WHERE vendor_id IN (4, 7) — Apex and Pinnacle together.",
        "validator": _sql_contains("vendor_id", "in"),
    },
    {
        "id": "special_total", "scene": SCENE_AUDIT_TRAIL,
        "concept": "s1_sum", "rep": 2,
        "label": "Totalled Special Projects spend",
        "detail": "SUM(amount) WHERE department = 'Special Projects'.",
        "validator": lambda sql, r: "sum" in sql.lower() and (
            "special projects" in sql.lower() or "department" in sql.lower()) and len(r) > 0,
    },
    {
        "id": "approver_join", "scene": SCENE_AUDIT_TRAIL,
        "concept": "s1_join", "rep": 2,
        "label": "Named the approver via JOIN",
        "detail": "JOIN employees ON approved_by — same skill, new key.",
        "validator": _sql_contains("join", "employees", "approved_by"),
    },

    # ── confrontation ────────────────────────────────────────────────────────
    {
        "id": "finance_exec", "scene": SCENE_CONFRONTATION,
        "concept": "s1_in", "rep": 2,
        "label": "Identified the Finance/Executive staff",
        "detail": "WHERE department IN ('Finance','Executive') — the rooms it ran through.",
        "validator": _sql_contains("employees", "department", "in"),
    },
]

# Fast lookup by id
OBJECTIVES_BY_ID = {o["id"]: o for o in OBJECTIVES}

S1_SCENE_ORDER = [
    SCENE_YOUR_DESK, SCENE_DB_TERMINAL, SCENE_HR_FILES,
    SCENE_CFO_DEPT, SCENE_AUDIT_TRAIL, SCENE_CONFRONTATION,
]

S1_SCENE_OBJ_ORDER = {}
for _o in OBJECTIVES:
    S1_SCENE_OBJ_ORDER.setdefault(_o["scene"], []).append(_o["id"])


# ── Season 1 narrative (STORY panel WHY/beat + BRIEFING + recall) ────────────

S1_SCENE_WHY = {
    SCENE_YOUR_DESK: (
        "Day one at Nexus Analytics. You're the new data analyst. Diana's\n"
        "note says: get familiar with the database before the 9am standup.\n\n"
        "There are four tables: employees, vendors, transactions, and\n"
        "departments. Start with the one you're in — employees."
    ),
    SCENE_DB_TERMINAL: (
        "Basement B1. The full transaction log — every dollar Nexus ever\n"
        "paid out. Diana's hunch: some of these vendors don't smell right.\n"
        "Follow the money."
    ),
    SCENE_HR_FILES: (
        "HR records. Every payment was signed off by someone. If the same\n"
        "name keeps appearing on the suspicious ones, that's not a\n"
        "coincidence — that's a thread to pull."
    ),
    SCENE_CFO_DEPT: (
        "The CFO's department. One vendor — Apex Solutions — has been bled\n"
        "money like a faucet. How much, how often, and is it getting worse?"
    ),
    SCENE_AUDIT_TRAIL: (
        "Build the case. Two shell vendors, one approver, one department.\n"
        "Numbers that hold up in a room with lawyers in it."
    ),
    SCENE_CONFRONTATION: (
        "Rachel Kim's office. You have the whole picture. One last query\n"
        "to name the people in the rooms where this was signed."
    ),
}

S1_SETUP = {
    "list_tables": (
        "Before you can investigate anything, you need to see the data.\n"
        "The employees table is the obvious place to start — it's got\n"
        "you in it. Pull the whole thing and look around."
    ),
    "view_employees": (
        "The employees table is the place to start — it's got you in it.\n"
        "You don't need every column; just who people are and what they earn."
    ),
    "count_headcount": (
        "Sam from accounting pings you: 'Quick — how many people work\n"
        "here? Need it for a report.' Don't count by hand."
    ),
    "vendor_spend": (
        "Twenty-eight payments. Reading them one by one is useless. You\n"
        "want the total paid to each vendor, biggest first — so the\n"
        "money trail jumps out on its own."
    ),
    "unverified_vendors": (
        "A real vendor has an address and a verified flag. A fake one\n"
        "doesn't. Find the vendors that were never verified."
    ),
    "join_vendor_names": (
        "The transactions table only stores vendor_id — numbers, no names.\n"
        "Useless for a report. Stitch the names back on."
    ),
    "lookup_webb": (
        "The suspicious payments keep pointing at one approver id: 4.\n"
        "Put a face to the number — pull that exact employee."
    ),
    "approver_counts": (
        "One id approving a lot would be damning. Count how many payments\n"
        "each approver signed — let the tally expose them."
    ),
    "dept_budgets": (
        "Money this size has to be hiding in a big budget line. Rank the\n"
        "departments by budget and see which one could swallow it."
    ),
    "apex_total": (
        "Apex Solutions — unverified, no address, paid repeatedly. The\n"
        "first damning number: how much has Nexus paid them in total?"
    ),
    "apex_count": (
        "A big total could be one freak invoice. How many separate Apex\n"
        "payments were there? Frequency is the tell."
    ),
    "escalation": (
        "If this is theft, it gets bolder over time. Pull Apex's payments\n"
        "in date order and watch the amounts move."
    ),
    "dual_vendor": (
        "Apex isn't alone. Pinnacle Strategy fits the same profile. Pull\n"
        "both vendors' payments in a single query."
    ),
    "special_total": (
        "All of it runs through one department. What's the full amount\n"
        "charged to Special Projects?"
    ),
    "approver_join": (
        "The report needs a name, not 'approved_by = 4'. Join the\n"
        "approver's real name onto the shell-vendor payments."
    ),
    "finance_exec": (
        "Last query. The sign-offs lived in Finance and the Executive\n"
        "suite. Name everyone in those two departments — the rooms this\n"
        "passed through on its way to $1.87M."
    ),
}

S1_YOUR_MOVE = {
    "list_tables": (
        "See everything in the employees table",
        "Return every row and every column from the employees table. The "
        "simplest query there is: SELECT * FROM employees — the * means "
        "'all columns'.",
    ),
    "view_employees": (
        "Pull name + salary for all staff",
        "From the employees table, return just the name and salary columns "
        "for every row. List the columns explicitly — do not use SELECT *.",
    ),
    "count_headcount": (
        "Count all employees",
        "Return a single number: how many rows are in the employees table. "
        "Use SELECT COUNT(*) FROM employees.",
    ),
    "vendor_spend": (
        "Total spend per vendor, biggest first",
        "From transactions, return each vendor_id with the SUM of its "
        "amount, grouped by vendor_id, ordered highest total first. "
        "GROUP BY vendor_id; ORDER BY SUM(amount) DESC.",
    ),
    "unverified_vendors": (
        "Find the unverified vendors",
        "From the vendors table, return every row where verified = 0. "
        "WHERE verified = 0.",
    ),
    "join_vendor_names": (
        "Attach vendor names to transactions",
        "Return transactions with the vendor's name alongside. JOIN "
        "transactions to vendors ON transactions.vendor_id = vendors.id.",
    ),
    "lookup_webb": (
        "Pull employee #4",
        "From employees, return the single row where id = 4. "
        "WHERE id = 4.",
    ),
    "approver_counts": (
        "Count payments per approver",
        "From transactions, return each approved_by value with how many "
        "rows it has, most first. GROUP BY approved_by; COUNT(*); "
        "ORDER BY COUNT(*) DESC.",
    ),
    "dept_budgets": (
        "Rank departments by budget",
        "From the departments table, return every row ordered by budget "
        "highest first. ORDER BY budget DESC.",
    ),
    "apex_total": (
        "Total everything paid to Apex",
        "From transactions, return the SUM of amount for vendor_id = 4. "
        "SELECT SUM(amount) ... WHERE vendor_id = 4.",
    ),
    "apex_count": (
        "Count Apex's payments",
        "From transactions, return how many rows have vendor_id = 4. "
        "SELECT COUNT(*) ... WHERE vendor_id = 4.",
    ),
    "escalation": (
        "List Apex's payments oldest to newest",
        "From transactions where vendor_id = 4, return date and amount "
        "ordered by date ascending. WHERE vendor_id = 4 ORDER BY date.",
    ),
    "dual_vendor": (
        "Pull Apex AND Pinnacle together",
        "From transactions, return every row whose vendor_id is 4 or 7. "
        "WHERE vendor_id IN (4, 7).",
    ),
    "special_total": (
        "Total the Special Projects spend",
        "From transactions, return the SUM of amount where department = "
        "'Special Projects'. SUM(amount) ... WHERE department='Special Projects'.",
    ),
    "approver_join": (
        "Put the approver's name on the shell payments",
        "Return the shell-vendor rows with the approver's name. JOIN "
        "transactions to employees ON transactions.approved_by = "
        "employees.id, filtered to vendor_id IN (4,7).",
    ),
    "finance_exec": (
        "Name everyone in Finance or Executive",
        "From employees, return every row whose department is 'Finance' "
        "or 'Executive'. WHERE department IN ('Finance','Executive').",
    ),
}

S1_RESULT_REACTION = {
    "list_tables": (
        "Ten people. The whole company fits on one screen. There you\n"
        "are — Alex Chen, Junior Analyst. And at the top, the CFO at\n"
        "$310k. Small shop. Everyone's one query away from everyone\n"
        "else. That's your first SQL query. It won't be your last."
    ),
    "view_employees": (
        "Two columns, and the story's already loud: salaries run $68k\n"
        "for a junior up to $310k for the CFO and $450k for the CEO.\n"
        "Picking the columns you want — instead of dumping the table —\n"
        "is how you make data say something. Remember the CFO number."
    ),
    "count_headcount": (
        "Ten. Exactly ten employees run this entire operation. A company\n"
        "this small, $1.87M doesn't just vanish unnoticed — unless\n"
        "someone made sure no one was counting."
    ),
    "vendor_spend": (
        "The ranking is lopsided. Two vendor IDs — 4 and 7 — tower over\n"
        "everything else, hundreds of thousands each. The rest are office\n"
        "supplies and software. Those two don't belong."
    ),
    "unverified_vendors": (
        "Two rows. Apex Solutions LLC and Pinnacle Strategy. Both\n"
        "verified = 0. Both '(no address on file)'. The two biggest\n"
        "vendors in the company are ghosts."
    ),
    "join_vendor_names": (
        "Now the log reads in plain English — and the big Consulting\n"
        "payments all carry the same two names: Apex and Pinnacle.\n"
        "Same story, now with faces."
    ),
    "lookup_webb": (
        "Employee #4: Marcus Webb. CFO. Salary $310,000. The man whose\n"
        "id is stamped on every suspicious approval — and he signs his\n"
        "own paychecks too."
    ),
    "approver_counts": (
        "One number drowns the rest: approver 4, signing far more than\n"
        "anyone else. Webb approved the shell-vendor payments himself,\n"
        "over and over. Not delegated. Personal."
    ),
    "dept_budgets": (
        "Special Projects: $4.8 million. Triple the next line. A budget\n"
        "that big with that vague a name isn't a department — it's a\n"
        "place to hide things."
    ),
    "apex_total": (
        "Over $1.2 million to a company with no address. One vendor.\n"
        "Money that left Nexus and went somewhere nobody can point to\n"
        "on a map."
    ),
    "apex_count": (
        "Not one big invoice — many. A steady drip of large payments,\n"
        "spaced out, routine. Designed to look boring. Designed not to\n"
        "be counted."
    ),
    "escalation": (
        "Watch the column climb: $87K, then $112K, $143K, $198K,\n"
        "$243K. It didn't stay careful. It got greedy. Greed leaves\n"
        "a slope you can measure."
    ),
    "dual_vendor": (
        "Apex and Pinnacle, side by side: same Consulting category,\n"
        "same Special Projects department, same approver. Two shells,\n"
        "one hand running both."
    ),
    "special_total": (
        "The Special Projects total is almost entirely these two\n"
        "vendors. The 'department' was a funnel, and nearly every\n"
        "dollar in it went to ghosts."
    ),
    "approver_join": (
        "Every shell payment, now with a name attached to the\n"
        "signature: Marcus Webb. Not a system. Not a glitch. A person,\n"
        "signing, again and again."
    ),
    "finance_exec": (
        "Finance and Executive — Webb, the controller, the CEO, the\n"
        "people with the authority to see this and the access to move\n"
        "it. You have the vendors, the amounts, the escalation, and the\n"
        "name. $1,869,500. Two shells. One CFO.\n\n"
        "Rachel reads your query results in silence. Then: 'Get your\n"
        "coat. We're taking this upstairs.' Case closed — in SQL."
    ),
}

S1_OBJECTIVE_FOCUS = {
    "list_tables":        ("See everything in employees:", "SELECT * FROM employees"),
    "view_employees":     ("Pick specific columns:",  "SELECT name, salary FROM employees"),
    "count_headcount":    ("Count the rows:",         "SELECT COUNT(*) FROM employees"),
    "vendor_spend":       ("Group + sum + sort:",     "SELECT vendor_id, SUM(amount) FROM transactions GROUP BY vendor_id ORDER BY SUM(amount) DESC"),
    "unverified_vendors": ("Filter with WHERE:",      "SELECT * FROM vendors WHERE verified = 0"),
    "join_vendor_names":  ("Join two tables:",        "SELECT t.*, v.name FROM transactions t JOIN vendors v ON t.vendor_id = v.id"),
    "lookup_webb":        ("Exact lookup:",           "SELECT * FROM employees WHERE id = 4"),
    "approver_counts":    ("Group by approver:",      "SELECT approved_by, COUNT(*) FROM transactions GROUP BY approved_by ORDER BY COUNT(*) DESC"),
    "dept_budgets":       ("Order by budget:",        "SELECT * FROM departments ORDER BY budget DESC"),
    "apex_total":         ("Sum with a filter:",      "SELECT SUM(amount) FROM transactions WHERE vendor_id = 4"),
    "apex_count":         ("Count with a filter:",    "SELECT COUNT(*) FROM transactions WHERE vendor_id = 4"),
    "escalation":         ("Order by date:",          "SELECT date, amount FROM transactions WHERE vendor_id = 4 ORDER BY date"),
    "dual_vendor":        ("Match a list with IN:",   "SELECT * FROM transactions WHERE vendor_id IN (4, 7)"),
    "special_total":      ("Sum by department:",      "SELECT SUM(amount) FROM transactions WHERE department = 'Special Projects'"),
    "approver_join":      ("Join on approved_by:",    "SELECT t.id, e.name FROM transactions t JOIN employees e ON t.approved_by = e.id WHERE t.vendor_id IN (4,7)"),
    "finance_exec":       ("IN on a text list:",      "SELECT * FROM employees WHERE department IN ('Finance','Executive')"),
}

S1_HINTS = {
    "list_tables": [
        "You can't investigate what you can't see. Pull the employees table and look.",
        "SELECT * FROM employees — the * means 'every column'.",
        "SELECT * FROM employees",
    ],
    "view_employees": [
        "You don't need every column — just name and salary. Name the columns instead of using *.",
        "SELECT name, salary FROM employees.",
        "SELECT name, salary FROM employees",
    ],
    "count_headcount": [
        "Don't count rows by eye. SQL has a function for it.",
        "SELECT COUNT(*) FROM employees.",
        "SELECT COUNT(*) FROM employees",
    ],
    "vendor_spend": [
        "You want one total per vendor, biggest first. Bucket the rows, sum each bucket, sort.",
        "GROUP BY vendor_id, SUM(amount), ORDER BY SUM(amount) DESC.",
        "SELECT vendor_id, SUM(amount) FROM transactions GROUP BY vendor_id ORDER BY SUM(amount) DESC",
    ],
    "unverified_vendors": [
        "A fake vendor was never verified. Filter the vendors table on that flag.",
        "WHERE verified = 0.",
        "SELECT * FROM vendors WHERE verified = 0",
    ],
    "join_vendor_names": [
        "transactions has vendor_id; vendors has the name. Connect them on that key.",
        "JOIN vendors ON transactions.vendor_id = vendors.id.",
        "SELECT t.*, v.name FROM transactions t JOIN vendors v ON t.vendor_id = v.id",
    ],
    "lookup_webb": [
        "One exact employee. Filter the employees table to that id.",
        "WHERE id = 4.",
        "SELECT * FROM employees WHERE id = 4",
    ],
    "approver_counts": [
        "Count rows per approver — same bucketing skill, different column.",
        "GROUP BY approved_by, COUNT(*), ORDER BY COUNT(*) DESC.",
        "SELECT approved_by, COUNT(*) FROM transactions GROUP BY approved_by ORDER BY COUNT(*) DESC",
    ],
    "dept_budgets": [
        "Which department could hide seven figures? Sort them by budget.",
        "ORDER BY budget DESC on the departments table.",
        "SELECT * FROM departments ORDER BY budget DESC",
    ],
    "apex_total": [
        "Add up every payment to Apex (vendor_id 4). One number.",
        "SUM(amount) with WHERE vendor_id = 4.",
        "SELECT SUM(amount) FROM transactions WHERE vendor_id = 4",
    ],
    "apex_count": [
        "Same filter, different question: how MANY payments, not how much.",
        "COUNT(*) with WHERE vendor_id = 4.",
        "SELECT COUNT(*) FROM transactions WHERE vendor_id = 4",
    ],
    "escalation": [
        "Pull Apex's payments and sort them in time order to see the trend.",
        "WHERE vendor_id = 4 ORDER BY date.",
        "SELECT date, amount FROM transactions WHERE vendor_id = 4 ORDER BY date",
    ],
    "dual_vendor": [
        "Two vendor ids at once — don't write two queries. There's a keyword for a list.",
        "WHERE vendor_id IN (4, 7).",
        "SELECT * FROM transactions WHERE vendor_id IN (4, 7)",
    ],
    "special_total": [
        "Total the money charged to one department.",
        "SUM(amount) WHERE department = 'Special Projects'.",
        "SELECT SUM(amount) FROM transactions WHERE department = 'Special Projects'",
    ],
    "approver_join": [
        "The report needs a name, not id 4. Join employees on the approved_by key.",
        "JOIN employees ON transactions.approved_by = employees.id, filter vendor_id IN (4,7).",
        "SELECT t.id, e.name FROM transactions t JOIN employees e ON t.approved_by = e.id WHERE t.vendor_id IN (4,7)",
    ],
    "finance_exec": [
        "Same IN skill as the vendors — now on a text column with two values.",
        "WHERE department IN ('Finance','Executive').",
        "SELECT * FROM employees WHERE department IN ('Finance','Executive')",
    ],
}

S1_RECALL_CHALLENGES = {
    "s1_select": {
        "concept": "s1_select",
        "question": ("Before you move on — quick gut check. From a table\n"
                     "called 'orders', return just the customer and total\n"
                     "columns for every row."),
        "answer": "SELECT customer, total FROM orders",
        "keywords": ["select", "customer", "total", "orders"],
    },
    "s1_where": {
        "concept": "s1_where",
        "question": ("Recall: from a 'users' table, return only the rows\n"
                     "where the status column equals 'active'."),
        "answer": "SELECT * FROM users WHERE status = 'active'",
        "keywords": ["where", "status", "active"],
    },
    "s1_count": {
        "concept": "s1_count",
        "question": ("Recall: return a single number — how many rows are\n"
                     "in a table called 'orders'."),
        "answer": "SELECT COUNT(*) FROM orders",
        "keywords": ["count", "orders"],
    },
    "s1_sum": {
        "concept": "s1_sum",
        "question": ("Recall: from 'sales', return the total of the amount\n"
                     "column for rows where region = 'West'."),
        "answer": "SELECT SUM(amount) FROM sales WHERE region = 'West'",
        "keywords": ["sum", "amount", "where", "west"],
    },
    "s1_groupby": {
        "concept": "s1_groupby",
        "question": ("Recall: from 'sales', return each region with the\n"
                     "total amount for that region."),
        "answer": "SELECT region, SUM(amount) FROM sales GROUP BY region",
        "keywords": ["group by", "region", "sum"],
    },
    "s1_join": {
        "concept": "s1_join",
        "question": ("Recall: join 'orders' to 'customers' on\n"
                     "orders.customer_id = customers.id."),
        "answer": "SELECT * FROM orders JOIN customers ON orders.customer_id = customers.id",
        "keywords": ["join", "on", "customer"],
    },
    "s1_orderby": {
        "concept": "s1_orderby",
        "question": ("Recall: return every row of 'products' sorted by\n"
                     "price, highest first."),
        "answer": "SELECT * FROM products ORDER BY price DESC",
        "keywords": ["order by", "price", "desc"],
    },
    "s1_in": {
        "concept": "s1_in",
        "question": ("Recall: from 'orders', return rows whose status is\n"
                     "either 'shipped' or 'delivered' — use one keyword."),
        "answer": "SELECT * FROM orders WHERE status IN ('shipped','delivered')",
        "keywords": ["in", "shipped", "delivered"],
    },
}


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

    def _content(self) -> dict:
        """Active season's narrative + objective maps. Season-agnostic flow."""
        if self.current_season == 2:
            from core import season2_game as M
            from core.season2_game import (
                S2_SCENE_SERVER_LOGS, S2_SCENE_GHOST_RECORDS,
                S2_SCENE_TIMESTAMP, S2_SCENE_ARCHIVE,
                S2_SCENE_PATTERN_DECODER, S2_SCENE_THE_SIGNAL,
            )
            return {
                "objectives": M.S2_OBJECTIVES,
                "by_id": M.S2_OBJECTIVES_BY_ID,
                "scene_why": M.S2_SCENE_WHY,
                "setup": M.S2_SETUP,
                "your_move": M.S2_YOUR_MOVE,
                "reaction": M.S2_RESULT_REACTION,
                "focus": M.S2_OBJECTIVE_FOCUS,
                "hints": M.S2_HINTS,
                "recall": M.S2_RECALL_CHALLENGES,
                "obj_order": M.S2_SCENE_OBJ_ORDER,
                "scene_order": [
                    S2_SCENE_SERVER_LOGS, S2_SCENE_GHOST_RECORDS,
                    S2_SCENE_TIMESTAMP, S2_SCENE_ARCHIVE,
                    S2_SCENE_PATTERN_DECODER, S2_SCENE_THE_SIGNAL,
                ],
            }
        return {
            "objectives": OBJECTIVES,
            "by_id": OBJECTIVES_BY_ID,
            "scene_why": S1_SCENE_WHY,
            "setup": S1_SETUP,
            "your_move": S1_YOUR_MOVE,
            "reaction": S1_RESULT_REACTION,
            "focus": S1_OBJECTIVE_FOCUS,
            "hints": S1_HINTS,
            "recall": S1_RECALL_CHALLENGES,
            "obj_order": S1_SCENE_OBJ_ORDER,
            "scene_order": S1_SCENE_ORDER,
        }

    def _active_objectives(self) -> list[dict]:
        """Return the full objective list for the current season."""
        return self._content()["objectives"]

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
        c = self._content()
        oid = obj["id"]
        reaction = c["reaction"].get(oid, "")
        order = c["obj_order"].get(obj["scene"], [])
        nxt, seen = None, False
        for x in order:
            if x == oid:
                seen = True
                continue
            if seen and x not in self.completed:
                nxt = x
                break
        if nxt:
            beat = reaction + "\n\n— — — — — — —\n\n" + c["setup"].get(nxt, "")
            self.on_story("beat", beat)
            g, m = c["your_move"].get(nxt, ("", ""))
            self.on_briefing(g, m)
        else:
            self.on_story("beat", reaction)

    def _emit_scene_state(self) -> None:
        """STORY panel WHY + current setup beat + BRIEFING for the active objective."""
        c = self._content()
        self.on_story("why", c["scene_why"].get(self.scene, ""))
        for obj in self.objectives_for_scene(self.scene):
            if obj["id"] not in self.completed:
                self.on_story("beat", c["setup"].get(obj["id"], ""))
                g, m = c["your_move"].get(obj["id"], ("", ""))
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
        # Guard: if a recall gate is already waiting for an answer, do nothing.
        # Without this, every call (hint click, post-load timer, etc.) would
        # re-show the question and reset the tries counter.
        if self._recall_pending is not None:
            return

        # One season-agnostic path. Keep advancing while the current scene
        # is fully complete; a between-scene RECALL GATE practises a prior
        # skill before each transition (non-punishing, never hard-blocks).
        order = self._content()["scene_order"]
        while self.scene in order and self.scene_complete(self.scene):
            idx = order.index(self.scene)
            if idx < len(order) - 1:
                if self.scene not in self._recall_done:
                    ch = self.get_recall_challenge()
                    if ch:
                        self._recall_pending = ch
                        self._recall_tries = 0
                        self.on_story("recall",
                            "Before the next room — prove you've still got "
                            "this. Answer in the editor:\n\n" + ch["question"])
                        return
                    self._recall_done.add(self.scene)  # nothing to recall yet
                self._advance_to_scene(order[idx + 1])
            elif self.current_season == 1:
                if self.s1_complete():
                    self.transition_to_season2()
                return
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
        # Both seasons: story lives in the STORY panel, never the feed.
        self.scene = scene_id
        self.step  = 0
        self.on_scene_change(scene_id)
        self._save()
        self._emit_scene_state()

    # ── Hint system ──────────────────────────────────────────────────────────

    def get_hint(self) -> str:
        """Return the next hint for the first incomplete objective in this scene."""
        hint_bank = self._content()["hints"]
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
        c = self._content()
        target_id = self.completed[-2]
        obj = c["by_id"].get(target_id)
        return c["recall"].get(obj.get("concept")) if obj else None

    # ── Persistence ───────────────────────────────────────────────────────────

    def _save(self) -> None:
        try:
            conn = self._db._connect()
            # Migrate: add recall_done column if missing
            cols = [r[1] for r in conn.execute("PRAGMA table_info(save_state)").fetchall()]
            if "recall_done" not in cols:
                conn.execute("ALTER TABLE save_state ADD COLUMN recall_done TEXT DEFAULT '[]'")
                conn.commit()
            conn.execute(
                "UPDATE save_state SET scene=?, clues=?, objectives=?, saved_at=?, season=?, recall_done=? WHERE id=1",
                (
                    self.scene,
                    json.dumps(self.clues),
                    json.dumps(self.completed),
                    datetime.now().isoformat(timespec="seconds"),
                    self.current_season,
                    json.dumps(list(self._recall_done)),
                )
            )
            conn.commit()
        except Exception:
            pass  # Save failure should never crash the game

    def load(self) -> None:
        """Restore from save_state table. Migrates older saves that lack columns."""
        try:
            conn = self._db._connect()
            cols = [r[1] for r in conn.execute("PRAGMA table_info(save_state)").fetchall()]
            if "season" not in cols:
                conn.execute("ALTER TABLE save_state ADD COLUMN season INTEGER DEFAULT 1")
                conn.commit()
            if "recall_done" not in cols:
                conn.execute("ALTER TABLE save_state ADD COLUMN recall_done TEXT DEFAULT '[]'")
                conn.commit()
            row = conn.execute("SELECT * FROM save_state WHERE id=1").fetchone()
            if row:
                self.scene          = row["scene"]      or SCENE_YOUR_DESK
                self.clues          = json.loads(row["clues"]       or "[]")
                self.completed      = json.loads(row["objectives"]  or "[]")
                self.current_season = row["season"] if row["season"] is not None else 1
                self._recall_done   = set(json.loads(row["recall_done"] or "[]"))
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

