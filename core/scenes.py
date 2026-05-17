# core/scenes.py
# SCENES — the narrative spine of NEXUS.
#
# Each scene is a dict with:
#   id          — matches SCENE_* constants in game.py
#   title       — location name shown in HUD
#   art_key     — which QPainter scene to draw (ui/scene_view.py)
#   intro       — shown once when player arrives
#   focus       — the ONE command the player is being guided toward right now
#                 (displayed prominently in the sidebar)
#   focus_label — short label above the focus command box
#   objectives  — list of objective IDs that must be completed here
#   ambient     — short atmospheric lines shown periodically / on 'look'
#   exits       — where the player can go (unlocked after objectives complete)
#
# The step-by-step tutorial text lives in STEPS (below) — one message per
# objective, shown as that objective becomes the active goal.

from core.game import (
    SCENE_YOUR_DESK,
    SCENE_DB_TERMINAL,
    SCENE_HR_FILES,
    SCENE_CFO_DEPT,
    SCENE_AUDIT_TRAIL,
    SCENE_CONFRONTATION,
)


SCENES = {

    SCENE_YOUR_DESK: {
        "id":          SCENE_YOUR_DESK,
        "title":       "Your Desk — Analytics Department",
        "art_key":     "desk",
        "intro": (
            "Day one at Nexus Analytics Corp.\n\n"
            "Your monitor glows. There's a sticky note on your keyboard\n"
            "from Diana Reeves, Senior Analyst:\n\n"
            "  'Welcome aboard, Alex. Get familiar with the database\n"
            "   before the 9am standup. — D.R.'\n\n"
            "She left you a tool called  db  that connects to the\n"
            "company database. Time to see what's in it."
        ),
        "focus_label": "Try this first:",
        "focus":       'db.tables()',
        "objectives":  ["list_tables", "examine_employees", "count_employees"],
        "ambient": [
            "The office is mostly empty. It's 7:43am.",
            "Somewhere down the hall a coffee machine gurgles.",
            "Your phone shows 3 unread Slack messages. You ignore them.",
            "The Analytics floor smells like dry-erase markers.",
        ],
        "exits": {SCENE_DB_TERMINAL: "server_room"},
    },

    SCENE_DB_TERMINAL: {
        "id":          SCENE_DB_TERMINAL,
        "title":       "Server Room — Basement Level B1",
        "art_key":     "server_room",
        "intro": (
            "The elevator opens onto a grey corridor.\n"
            "A laminated sign: B1 — Authorized Personnel Only.\n\n"
            "Diana badge-swiped you in earlier this week.\n"
            "'The real data is down here,' she said. 'Don't touch the red switches.'\n\n"
            "The transaction log is enormous. Every payment the company has ever made.\n"
            "Something feels off. Start by figuring out which vendors get the most money."
        ),
        "focus_label": "Investigate vendor spend:",
        "focus":       'db.query("SELECT vendor_id, SUM(amount) as total\\n  FROM transactions\\n  GROUP BY vendor_id\\n  ORDER BY total DESC")',
        "objectives":  ["find_high_spend_vendors", "spot_unverified_vendors", "join_transactions_vendors"],
        "ambient": [
            "The server racks hum at a frequency you can feel in your molars.",
            "A blinking red LED on rack 3. You decide not to ask.",
            "The temperature in here is exactly 68°F. Always.",
            "Your query results scroll past. Numbers don't lie.",
        ],
        "exits": {SCENE_HR_FILES: "hr_office"},
    },

    SCENE_HR_FILES: {
        "id":          SCENE_HR_FILES,
        "title":       "HR Office — 2nd Floor",
        "art_key":     "hr_office",
        "intro": (
            "Vanessa Cole's office is empty. Her monitor shows an out-of-office screensaver.\n\n"
            "The filing cabinet is labeled PERSONNEL — CONFIDENTIAL.\n"
            "You're not supposed to be in here. But you found two vendors with no address\n"
            "and no verification, pulling in hundreds of thousands of dollars.\n\n"
            "Every transaction has an approved_by column. Someone signed off on this.\n"
            "Find out who."
        ),
        "focus_label": "Find the approver:",
        "focus":       'db.query("SELECT approved_by, COUNT(*) as approvals\\n  FROM transactions\\n  GROUP BY approved_by\\n  ORDER BY approvals DESC")',
        "objectives":  ["find_approver", "lookup_employee_4", "check_special_projects_budget"],
        "ambient": [
            "The filing cabinet drawer slides open with a metallic shink.",
            "Org charts. Performance reviews. Salary bands. The usual.",
            "A framed poster: 'PEOPLE ARE OUR GREATEST ASSET.' You almost laugh.",
            "You keep one ear on the hallway.",
        ],
        "exits": {SCENE_CFO_DEPT: "cfo_office"},
    },

    SCENE_CFO_DEPT: {
        "id":          SCENE_CFO_DEPT,
        "title":       "CFO's Office — Executive Floor",
        "art_key":     "cfo_office",
        "intro": (
            "Corner office. Floor-to-ceiling windows. A view of downtown.\n\n"
            "Marcus Webb's desktop is open to a budget dashboard.\n"
            "His wastebasket has a crumpled printout — Apex Solutions LLC invoice.\n"
            "$243,000. Dated last December.\n\n"
            "You need hard numbers. Pull the total spend to Apex (vendor_id = 4)\n"
            "and then look at how the amounts have changed over time."
        ),
        "focus_label": "Quantify the damage:",
        "focus":       'db.query("SELECT SUM(amount) as total_paid\\n  FROM transactions\\n  WHERE vendor_id = 4")',
        "objectives":  ["total_apex_spend", "escalation_pattern"],
        "ambient": [
            "A Bloomberg terminal scrolls market data nobody's reading.",
            "Family photo on the desk. Two kids. A golden retriever.",
            "His screensaver kicks in. A Nexus logo bounces corner to corner.",
            "You hear the elevator ping. You hold your breath. It passes.",
        ],
        "exits": {SCENE_AUDIT_TRAIL: "your_desk"},
    },

    SCENE_AUDIT_TRAIL: {
        "id":          SCENE_AUDIT_TRAIL,
        "title":       "Your Desk — Building the Case",
        "art_key":     "desk_night",
        "intro": (
            "It's 6:47pm. The Analytics floor is empty.\n\n"
            "You've been at this for hours. Two vendor IDs — 4 and 7.\n"
            "Apex Solutions LLC and Pinnacle Strategy.\n"
            "Both unverified. Both without a real address. Both approved by the CFO.\n\n"
            "Now you build the complete picture. Pull all transactions for both vendors.\n"
            "Calculate the total. This is what goes in the report."
        ),
        "focus_label": "Complete the audit:",
        "focus":       'db.query("SELECT vendor_id, SUM(amount) as total\\n  FROM transactions\\n  WHERE vendor_id IN (4, 7)\\n  GROUP BY vendor_id")',
        "objectives":  ["dual_vendor_fraud", "total_fraud_amount"],
        "ambient": [
            "The cleaning crew vacuums somewhere two floors up.",
            "Your cold coffee tastes like regret.",
            "Outside the window: Austin at night. Office towers and traffic.",
            "You've run 30+ queries today. You know what you found.",
        ],
        "exits": {SCENE_CONFRONTATION: "coo_office"},
    },

    SCENE_CONFRONTATION: {
        "id":          SCENE_CONFRONTATION,
        "title":       "COO's Office — The Reckoning",
        "art_key":     "coo_office",
        "intro": (
            "Rachel Kim's office is smaller than Marcus's. Intentionally, you suspect.\n\n"
            "'Close the door,' she says.\n\n"
            "You lay it out. Apex Solutions. Pinnacle Strategy. $1.87 million.\n"
            "Thirteen months. All approved by the CFO. All charged to Special Projects.\n"
            "Both vendors: no address, not verified, contact emails that bounce.\n\n"
            "Rachel doesn't say anything for a long time.\n\n"
            "'How did you find this?'\n\n"
            "You: 'SQL.'\n\n"
            "She almost smiles. Almost.\n\n"
            "'I need this in writing. Everything. Every query output. Tonight.'\n\n"
            "You nod.\n\n"
            "You open a new file. You start typing.\n\n"
            "────────────────────────────────────────────────\n"
            "              CASE CLOSED.\n"
            "────────────────────────────────────────────────\n\n"
            "You uncovered $1,870,000 in fraudulent payments.\n"
            "Marcus Webb was placing them with shell companies he controlled.\n"
            "Nexus Analytics Corp will never be the same.\n\n"
            "And you did it with SQL.\n\n"
            "Congratulations, Data Analyst."
        ),
        "focus_label":  "",
        "focus":        "",
        "objectives":  [],
        "ambient":     [],
        "exits":       {},
    },
}


# ── Step guidance ─────────────────────────────────────────────────────────────
# Text shown in the narrative panel when an objective becomes the active goal.
# Keyed by objective id. One message per objective, escalating the story beat.

STEP_TEXT = {
    "list_tables": (
        "Type  db.tables()  below and press Enter.\n\n"
        "A table in SQL is like a spreadsheet tab — rows and columns.\n"
        "You can't analyze what you don't know exists."
    ),
    "examine_employees": (
        "Good. You can see the tables.\n\n"
        "Now look at the  employees  table.\n"
        "Type:  db.query(\"SELECT * FROM employees\")\n\n"
        "SELECT * means 'give me every column.'\n"
        "FROM employees tells SQL which table to read.\n"
        "You should see yourself in there — Alex Chen, Junior Analyst."
    ),
    "count_employees": (
        "Nice work. The roster is visible.\n\n"
        "Sam just pinged you: 'Quick question — how many people are we at now?'\n\n"
        "Use COUNT(*) to answer:\n"
        "  db.query(\"SELECT COUNT(*) FROM employees\")\n\n"
        "COUNT(*) counts every row. Handy when someone needs a headcount fast."
    ),
    "find_high_spend_vendors": (
        "The transaction log has 28 entries spanning last year.\n\n"
        "Before you read every row, get a bird's-eye view:\n"
        "which vendors are getting the biggest payments?\n\n"
        "GROUP BY bundles all transactions for the same vendor together.\n"
        "SUM(amount) adds them up. ORDER BY ... DESC puts the biggest first.\n\n"
        "Run the focus query in the sidebar, or write your own."
    ),
    "spot_unverified_vendors": (
        "Interesting pattern in the totals.\n\n"
        "Now check the vendors table itself. Not every vendor has been vetted.\n"
        "There's a  verified  column — 1 means approved, 0 means not.\n\n"
        "db.query(\"SELECT * FROM vendors WHERE verified = 0\")\n\n"
        "WHERE filters rows. Only rows matching the condition come back."
    ),
    "join_transactions_vendors": (
        "You found two unverified vendors. But your transaction data only shows\n"
        "vendor_id numbers — not names.\n\n"
        "A JOIN connects two tables on a shared column:\n"
        "  transactions.vendor_id  →  vendors.id\n\n"
        "Try:\n"
        "  db.query(\"SELECT t.date, t.amount, v.name, v.verified\n"
        "    FROM transactions t\n"
        "    JOIN vendors v ON t.vendor_id = v.id\n"
        "    WHERE v.verified = 0\n"
        "    ORDER BY t.date\")\n\n"
        "Now you can see names. And the pattern becomes clear."
    ),
    "find_approver": (
        "Every transaction was approved by someone — the approved_by column holds their employee id.\n\n"
        "Is the same person approving all the suspicious payments?\n\n"
        "Group transactions by approved_by and count them:\n"
        "  db.query(\"SELECT approved_by, COUNT(*) as approvals\n"
        "    FROM transactions\n"
        "    GROUP BY approved_by\n"
        "    ORDER BY approvals DESC\")\n\n"
        "One id is going to stand out."
    ),
    "lookup_employee_4": (
        "Employee id 4 approved a lot of transactions.\n\n"
        "Now find out who that is:\n"
        "  db.query(\"SELECT * FROM employees WHERE id = 4\")\n\n"
        "WHERE id = 4 returns only the row with that primary key.\n"
        "One row. One person. This is who signed off on everything."
    ),
    "check_special_projects_budget": (
        "All the suspicious transactions are charged to 'Special Projects.'\n\n"
        "Look at the departments table. How does Special Projects' budget\n"
        "compare to every other department?\n\n"
        "  db.query(\"SELECT * FROM departments ORDER BY budget DESC\")\n\n"
        "ORDER BY budget DESC sorts biggest first. You're going to raise an eyebrow."
    ),
    "total_apex_spend": (
        "Apex Solutions LLC. Vendor id 4. Unverified. No address.\n\n"
        "How much has Nexus paid them in total?\n\n"
        "  db.query(\"SELECT SUM(amount) as total_paid\n"
        "    FROM transactions\n"
        "    WHERE vendor_id = 4\")\n\n"
        "SUM adds up all the  amount  values that match your WHERE filter.\n"
        "The number is going to be uncomfortable."
    ),
    "escalation_pattern": (
        "Now pull those transactions in order by date.\n\n"
        "  db.query(\"SELECT date, amount, description\n"
        "    FROM transactions\n"
        "    WHERE vendor_id = 4\n"
        "    ORDER BY date\")\n\n"
        "Watch what happens to the amounts. Month by month.\n"
        "This is not a flat consulting retainer. This is a pattern."
    ),
    "dual_vendor_fraud": (
        "There are two shell vendors — Apex (id 4) and Pinnacle (id 7).\n"
        "Pull all transactions for both in a single query.\n\n"
        "SQL's  IN  clause matches any value in a list:\n"
        "  WHERE vendor_id IN (4, 7)\n\n"
        "  db.query(\"SELECT date, amount, v.name, approved_by\n"
        "    FROM transactions t\n"
        "    JOIN vendors v ON t.vendor_id = v.id\n"
        "    WHERE t.vendor_id IN (4, 7)\n"
        "    ORDER BY date\")\n\n"
        "One approver. Two vendors. Thirteen months."
    ),
    "total_fraud_amount": (
        "Last query. The number that goes in the report.\n\n"
        "Total payments to both shell vendors combined:\n"
        "  db.query(\"SELECT SUM(amount) as total_fraud\n"
        "    FROM transactions\n"
        "    WHERE vendor_id IN (4, 7)\")\n\n"
        "This is the figure Rachel Kim needs.\n"
        "This is what you found."
    ),
}


# ── Per-objective focus commands ──────────────────────────────────────────────
# Shown in the "Try this:" box. Updated dynamically as objectives complete.
# Format: objective_id → (label, command_string)

OBJECTIVE_FOCUS = {
    "list_tables":              ("Try this first:",        'db.tables()'),
    "examine_employees":        ("Now look inside:",       'db.query("SELECT * FROM employees")'),
    "count_employees":          ("Count the headcount:",   'db.query("SELECT COUNT(*) FROM employees")'),
    "find_high_spend_vendors":  ("Find top spenders:",     'db.query("SELECT vendor_id, SUM(amount) as total FROM transactions GROUP BY vendor_id ORDER BY total DESC")'),
    "spot_unverified_vendors":  ("Check vendor status:",   'db.query("SELECT * FROM vendors WHERE verified = 0")'),
    "join_transactions_vendors":("Link names to ids:",     'db.query("SELECT t.date, t.amount, v.name FROM transactions t JOIN vendors v ON t.vendor_id = v.id WHERE v.verified = 0")'),
    "find_approver":            ("Who approved these?",    'db.query("SELECT approved_by, COUNT(*) as n FROM transactions GROUP BY approved_by ORDER BY n DESC")'),
    "lookup_employee_4":        ("Look up that employee:", 'db.query("SELECT * FROM employees WHERE id = 4")'),
    "check_special_projects_budget": ("Compare budgets:",  'db.query("SELECT * FROM departments ORDER BY budget DESC")'),
    "total_apex_spend":         ("Total the damage:",      'db.query("SELECT SUM(amount) as total_paid FROM transactions WHERE vendor_id = 4")'),
    "escalation_pattern":       ("See the pattern:",       'db.query("SELECT date, amount, description FROM transactions WHERE vendor_id = 4 ORDER BY date")'),
    "dual_vendor_fraud":        ("Both shell companies:",  'db.query("SELECT t.date, t.amount, v.name FROM transactions t JOIN vendors v ON t.vendor_id = v.id WHERE t.vendor_id IN (4, 7) ORDER BY date")'),
    "total_fraud_amount":       ("Grand total stolen:",    'db.query("SELECT SUM(amount) as total_fraud FROM transactions WHERE vendor_id IN (4, 7)")'),
}
