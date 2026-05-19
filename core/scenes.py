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
            "First day at Nexus Analytics Corp. Nobody told you where the\n"
            "good coffee is. Nobody told you where anything is, actually.\n\n"
            "Your monitor blinks awake. There's a sticky note on your keyboard,\n"
            "handwriting that somehow manages to be both neat and threatening:\n\n"
            "  'Welcome aboard, Alex. Get familiar with the database\n"
            "   before the 9am standup. Don't be late. — Diana Reeves'\n\n"
            "Diana left you a tool called  db  that connects to the\n"
            "company database. Seems straightforward enough.\n\n"
            "Famous last words."
        ),
        "focus_label": "Try this first:",
        "focus":       'db.tables()',
        "objectives":  ["list_tables", "examine_employees", "count_employees"],
        "ambient": [
            "The office is mostly empty. It's 7:43am. Only psychopaths are here this early.",
            "Somewhere down the hall, a coffee machine makes a sound like a cat in distress.",
            "Your phone shows 3 unread Slack messages. All from 'Fun Committee.' You ignore them.",
            "The Analytics floor smells like dry-erase markers and ambition.",
            "Someone left a half-eaten donut on the printer. Corporate America.",
        ],
        "exits": {SCENE_DB_TERMINAL: "server_room"},
    },

    SCENE_DB_TERMINAL: {
        "id":          SCENE_DB_TERMINAL,
        "title":       "Server Room — Basement Level B1",
        "art_key":     "server_room",
        "intro": (
            "The elevator descends to B1. The doors open onto a grey corridor\n"
            "lit by the kind of fluorescent lights that make everyone look guilty.\n\n"
            "A laminated sign: AUTHORIZED PERSONNEL ONLY.\n"
            "(Diana badge-swiped you in. 'The real data is down here,' she said.\n"
            "'Don't touch the red switches. I mean it, Alex.')\n\n"
            "The transaction log is massive. Every payment Nexus has ever made.\n"
            "You start scrolling and something catches your eye — certain vendors\n"
            "are getting a LOT of money.\n\n"
            "That weird feeling in your stomach? That's called instinct. Follow it."
        ),
        "focus_label": "Investigate vendor spend:",
        "focus":       'SELECT vendor_id, SUM(amount) as total\n  FROM transactions\n  GROUP BY vendor_id\n  ORDER BY total DESC',
        "objectives":  ["find_high_spend_vendors", "spot_unverified_vendors", "join_transactions_vendors"],
        "ambient": [
            "The server racks hum at a frequency you can feel in your molars.",
            "A blinking red LED on rack 3. Don't touch the red switches. DON'T.",
            "The temperature is exactly 68°F. It has been 68°F since 2019. Always.",
            "Your query results scroll past. Numbers don't lie. People do.",
            "You swear one of the server fans just coughed.",
            "For a second, your terminal shows a query you didn't type. Then it's gone.",
            "The lights flicker. Just once. Probably the HVAC.",
        ],
        "exits": {SCENE_HR_FILES: "hr_office"},
    },

    SCENE_HR_FILES: {
        "id":          SCENE_HR_FILES,
        "title":       "HR Office — 2nd Floor",
        "art_key":     "hr_office",
        "intro": (
            "Vanessa Cole's office. Her monitor shows a screensaver of kittens.\n"
            "She's at lunch. She's always at lunch from 11:30 to 1:15. Like clockwork.\n\n"
            "The filing cabinet is labeled PERSONNEL — CONFIDENTIAL.\n"
            "(You tell yourself you'll just take a quick look.)\n\n"
            "Here's what's bugging you: you found two vendors with no address,\n"
            "no verification, pulling in hundreds of thousands of dollars.\n"
            "Somebody approved those payments. Every single one.\n\n"
            "The approved_by column has an employee ID.\n"
            "Time to put a name to a number."
        ),
        "focus_label": "Find the approver:",
        "focus":       'SELECT approved_by, COUNT(*) as approvals\n  FROM transactions\n  GROUP BY approved_by\n  ORDER BY approvals DESC',
        "objectives":  ["find_approver", "lookup_employee_4", "check_special_projects_budget"],
        "ambient": [
            "The filing cabinet drawer slides open with a metallic shink. You flinch.",
            "Org charts. Performance reviews. Someone got a 2% raise. Thrilling.",
            "A framed poster: 'PEOPLE ARE OUR GREATEST ASSET.' Sure, Vanessa.",
            "You keep one ear on the hallway. If anyone asks, you're looking for a stapler.",
            "There's a motivational calendar on the wall. Today's quote: 'Trust the process.'",
        ],
        "exits": {SCENE_CFO_DEPT: "cfo_office"},
    },

    SCENE_CFO_DEPT: {
        "id":          SCENE_CFO_DEPT,
        "title":       "CFO's Office — Executive Floor",
        "art_key":     "cfo_office",
        "intro": (
            "Corner office. Floor-to-ceiling windows. Downtown Austin in the distance.\n"
            "This is where the money lives.\n\n"
            "Marcus Webb's desktop is open — he left a budget dashboard running.\n"
            "Rookie move, Marcus.\n\n"
            "But it's the wastebasket that gets you. A crumpled printout:\n"
            "Apex Solutions LLC. $243,000. Dated last December.\n"
            "He didn't even shred it.\n\n"
            "You need hard numbers. Total spend to Apex. The pattern over time.\n"
            "Your hands are shaking slightly. You tell yourself it's the coffee."
        ),
        "focus_label": "Quantify the damage:",
        "focus":       'SELECT SUM(amount) as total_paid\n  FROM transactions\n  WHERE vendor_id = 4',
        "objectives":  ["total_apex_spend", "escalation_pattern"],
        "ambient": [
            "A Bloomberg terminal scrolls market data nobody's reading.",
            "Family photo on the desk. Two kids. A golden retriever named 'Buddy.' Nice.",
            "His screensaver kicks in. A Nexus logo bouncing corner to corner. Hypnotic.",
            "You hear the elevator ping. You hold your breath. It passes. Exhale.",
            "A 'World's Best Boss' mug. The irony could power a small city.",
        ],
        "exits": {SCENE_AUDIT_TRAIL: "your_desk"},
    },

    SCENE_AUDIT_TRAIL: {
        "id":          SCENE_AUDIT_TRAIL,
        "title":       "Your Desk — Building the Case",
        "art_key":     "desk_night",
        "intro": (
            "6:47pm. Everyone's gone home.\n\n"
            "The cleaning crew won't reach this floor for another hour.\n"
            "It's just you, your monitor, and a coffee that stopped being\n"
            "drinkable around 3pm.\n\n"
            "You've got the pieces. Two vendor IDs — 4 and 7.\n"
            "Apex Solutions LLC. Pinnacle Strategy.\n"
            "Both unverified. Both ghosts. Both signed off by the CFO.\n\n"
            "Now you build the case. Pull everything for both vendors.\n"
            "Calculate the total. This is the number that goes in the report.\n\n"
            "No more gut feelings. Just data."
        ),
        "focus_label": "Complete the audit:",
        "focus":       'SELECT vendor_id, SUM(amount) as total\n  FROM transactions\n  WHERE vendor_id IN (4, 7)\n  GROUP BY vendor_id',
        "objectives":  ["dual_vendor_fraud", "total_fraud_amount"],
        "ambient": [
            "The cleaning crew vacuums somewhere two floors up. At least someone's working.",
            "Your cold coffee tastes like regret and poor life choices.",
            "Outside: Austin at night. Office towers glowing. People going home to dinner.",
            "You've run 30+ queries today. Your keyboard has feelings about this.",
            "The office plant by the window is dead. Has been for months. Nobody noticed.",
            "Your cursor jumps three lines on its own. You blink. It's back to normal.",
            "A notification pops up: 'Someone else is viewing this file.' You are alone.",
            "The monitor dims for exactly one second. When it comes back, your last query result has an extra row. ...no it doesn't. Does it?",
        ],
        "exits": {SCENE_CONFRONTATION: "coo_office"},
    },

    SCENE_CONFRONTATION: {
        "id":          SCENE_CONFRONTATION,
        "title":       "COO's Office — The Reckoning",
        "art_key":     "coo_office",
        "intro": (
            "Rachel Kim's office is smaller than Marcus's.\n"
            "Intentionally, you suspect. Rachel doesn't need a corner office\n"
            "to make you nervous.\n\n"
            "'Close the door,' she says. Not a request.\n\n"
            "You lay it out. Apex Solutions. Pinnacle Strategy. $1.87 million.\n"
            "Thirteen months. Every payment approved by the CFO.\n"
            "Every dollar charged to 'Special Projects.'\n"
            "Both vendors: no address, not verified, contact emails that bounce.\n\n"
            "Rachel doesn't say anything for what feels like a week.\n\n"
            "'How did you find this?'\n\n"
            "'SQL.'\n\n"
            "She almost smiles. Almost.\n\n"
            "'I need this in writing. Everything. Every query, every output.\n"
            "Tonight. Before Marcus gets back from his quote-unquote\n"
            "business trip to Cabo.'\n\n"
            "You nod. You open a new file. You start typing.\n\n"
            "────────────────────────────────────────────────\n"
            "              CASE CLOSED.\n"
            "────────────────────────────────────────────────\n\n"
            "You uncovered $1,870,000 in fraudulent payments.\n"
            "Marcus Webb was routing company money to shell companies\n"
            "he controlled. Thirteen months. Two fake vendors. Zero shame.\n\n"
            "Nexus Analytics Corp will never be the same.\n"
            "Neither will you.\n\n"
            "And you did it all with SQL.\n\n"
            "Not bad for day one, Alex."
        ),
        "focus_label":  "",
        "focus":        "",
        "objectives":  [],
        "ambient":     [],
        "exits":       {},
    },
}


# ── Cliffhanger teasers ───────────────────────────────────────────────────────
# Shown as a dramatic "end of scene" card when the player completes a scene
# and advances. Keyed by the scene being LEFT.

S1_CLIFFHANGERS = {
    SCENE_YOUR_DESK: {
        "eyebrow":  "CHAPTER 2",
        "headline": "Follow the Money",
        "teaser":   (
            "Two vendors. No address. No phone number.\n"
            "Half a million dollars between them.\n\n"
            "Someone at Nexus signed off on every payment.\n"
            "The transaction log is in Basement B1.\n"
            "So is the truth."
        ),
        "cta": "Head to the Server Room →",
    },
    SCENE_DB_TERMINAL: {
        "eyebrow":  "CHAPTER 3",
        "headline": "Follow the People",
        "teaser":   (
            "The vendors are fake. That much is clear.\n"
            "But someone with an employee ID kept approving them.\n\n"
            "One number. One name.\n"
            "The HR files are on the second floor."
        ),
        "cta": "Up to HR →",
    },
    SCENE_HR_FILES: {
        "eyebrow":  "CHAPTER 4",
        "headline": "The CFO's Office",
        "teaser":   (
            "Marcus Webb. Chief Financial Officer.\n"
            "Every single suspicious payment: his signature.\n\n"
            "Now find out how much.\n"
            "All of it. Every dollar."
        ),
        "cta": "Into the CFO's Department →",
    },
    SCENE_CFO_DEPT: {
        "eyebrow":  "CHAPTER 5",
        "headline": "Build the Case",
        "teaser":   (
            "$1.2 million to one fake company.\n"
            "And that's just Apex.\n\n"
            "There's a second vendor.\n"
            "The audit trail will tell you everything."
        ),
        "cta": "Pull the Audit Trail →",
    },
    SCENE_AUDIT_TRAIL: {
        "eyebrow":  "CHAPTER 6",
        "headline": "The Confrontation",
        "teaser":   (
            "You have the numbers.\n"
            "$1,869,500. Two shell companies. Thirteen months.\n\n"
            "Rachel Kim is waiting.\n"
            "Close the door."
        ),
        "cta": "Rachel Kim's Office →",
    },
}


# ── Step guidance ─────────────────────────────────────────────────────────────
# Text shown in the narrative panel when an objective becomes the active goal.
# Keyed by objective id. One message per objective, escalating the story beat.

STEP_TEXT = {
    "list_tables": (
        "Type  db.tables()  below and press Ctrl+Enter.\n\n"
        "That's a shortcut to list every table in the database.\n"
        "A table in SQL is like a spreadsheet tab — rows and columns.\n"
        "You can't analyze what you don't know exists.\n\n"
        "From here on, you'll write real SQL. The game handles the rest."
    ),
    "examine_employees": (
        "Good. You can see the tables.\n\n"
        "Now look at the  employees  table.\n"
        "Type:  SELECT * FROM employees\n\n"
        "SELECT * means 'give me every column.'\n"
        "FROM employees tells SQL which table to read.\n"
        "You should see yourself in there — Alex Chen, Junior Analyst."
    ),
    "count_employees": (
        "Nice work. The roster is visible.\n\n"
        "Sam just pinged you: 'Quick question — how many people are we at now?'\n\n"
        "Use COUNT(*) to answer:\n"
        "  SELECT COUNT(*) FROM employees\n\n"
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
        "SELECT * FROM vendors WHERE verified = 0\n\n"
        "WHERE filters rows. Only rows matching the condition come back."
    ),
    "join_transactions_vendors": (
        "You found two unverified vendors. But your transaction data only shows\n"
        "vendor_id numbers — not names.\n\n"
        "A JOIN connects two tables on a shared column:\n"
        "  transactions.vendor_id  →  vendors.id\n\n"
        "Try:\n"
        "  SELECT t.date, t.amount, v.name, v.verified\n"
        "    FROM transactions t\n"
        "    JOIN vendors v ON t.vendor_id = v.id\n"
        "    WHERE v.verified = 0\n"
        "    ORDER BY t.date\n\n"
        "Now you can see names. And the pattern becomes clear."
    ),
    "find_approver": (
        "Every transaction was approved by someone — the approved_by column holds their employee id.\n\n"
        "Is the same person approving all the suspicious payments?\n\n"
        "Group transactions by approved_by and count them:\n"
        "  SELECT approved_by, COUNT(*) as approvals\n"
        "    FROM transactions\n"
        "    GROUP BY approved_by\n"
        "    ORDER BY approvals DESC\n\n"
        "One id is going to stand out."
    ),
    "lookup_employee_4": (
        "Employee id 4 approved a lot of transactions.\n\n"
        "Now find out who that is:\n"
        "  SELECT * FROM employees WHERE id = 4\n\n"
        "WHERE id = 4 returns only the row with that primary key.\n"
        "One row. One person. This is who signed off on everything."
    ),
    "check_special_projects_budget": (
        "All the suspicious transactions are charged to 'Special Projects.'\n\n"
        "Look at the departments table. How does Special Projects' budget\n"
        "compare to every other department?\n\n"
        "  SELECT * FROM departments ORDER BY budget DESC\n\n"
        "ORDER BY budget DESC sorts biggest first. You're going to raise an eyebrow."
    ),
    "total_apex_spend": (
        "Apex Solutions LLC. Vendor id 4. Unverified. No address.\n\n"
        "How much has Nexus paid them in total?\n\n"
        "  SELECT SUM(amount) as total_paid\n"
        "    FROM transactions\n"
        "    WHERE vendor_id = 4\n\n"
        "SUM adds up all the  amount  values that match your WHERE filter.\n"
        "The number is going to be uncomfortable."
    ),
    "escalation_pattern": (
        "Now pull those transactions in order by date.\n\n"
        "  SELECT date, amount, description\n"
        "    FROM transactions\n"
        "    WHERE vendor_id = 4\n"
        "    ORDER BY date\n\n"
        "Watch what happens to the amounts. Month by month.\n"
        "This is not a flat consulting retainer. This is a pattern."
    ),
    "dual_vendor_fraud": (
        "There are two shell vendors — Apex (id 4) and Pinnacle (id 7).\n"
        "Pull all transactions for both in a single query.\n\n"
        "SQL's  IN  clause matches any value in a list:\n"
        "  WHERE vendor_id IN (4, 7)\n\n"
        "  SELECT date, amount, v.name, approved_by\n"
        "    FROM transactions t\n"
        "    JOIN vendors v ON t.vendor_id = v.id\n"
        "    WHERE t.vendor_id IN (4, 7)\n"
        "    ORDER BY date\n\n"
        "One approver. Two vendors. Thirteen months."
    ),
    "total_fraud_amount": (
        "Last query. The number that goes in the report.\n\n"
        "Total payments to both shell vendors combined:\n"
        "  SELECT SUM(amount) as total_fraud\n"
        "    FROM transactions\n"
        "    WHERE vendor_id IN (4, 7)\n\n"
        "This is the figure Rachel Kim needs.\n"
        "This is what you found."
    ),
}


# ── Per-objective focus commands ──────────────────────────────────────────────
# Shown in the "Try this:" box. Updated dynamically as objectives complete.
# Format: objective_id → (label, command_string)

OBJECTIVE_FOCUS = {
    "list_tables":              ("Try this first:",        'db.tables()'),
    "examine_employees":        ("Now look inside:",       'SELECT * FROM employees'),
    "count_employees":          ("Count the headcount:",   'SELECT COUNT(*) FROM employees'),
    "find_high_spend_vendors":  ("Find top spenders:",     'SELECT vendor_id, SUM(amount) as total\nFROM transactions\nGROUP BY vendor_id\nORDER BY total DESC'),
    "spot_unverified_vendors":  ("Check vendor status:",   'SELECT * FROM vendors WHERE verified = 0'),
    "join_transactions_vendors":("Link names to ids:",     'SELECT t.date, t.amount, v.name\nFROM transactions t\nJOIN vendors v ON t.vendor_id = v.id\nWHERE v.verified = 0'),
    "find_approver":            ("Who approved these?",    'SELECT approved_by, COUNT(*) as n\nFROM transactions\nGROUP BY approved_by\nORDER BY n DESC'),
    "lookup_employee_4":        ("Look up that employee:", 'SELECT * FROM employees WHERE id = 4'),
    "check_special_projects_budget": ("Compare budgets:",  'SELECT * FROM departments ORDER BY budget DESC'),
    "total_apex_spend":         ("Total the damage:",      'SELECT SUM(amount) as total_paid\nFROM transactions\nWHERE vendor_id = 4'),
    "escalation_pattern":       ("See the pattern:",       'SELECT date, amount, description\nFROM transactions\nWHERE vendor_id = 4\nORDER BY date'),
    "dual_vendor_fraud":        ("Both shell companies:",  'SELECT t.date, t.amount, v.name\nFROM transactions t\nJOIN vendors v ON t.vendor_id = v.id\nWHERE t.vendor_id IN (4, 7)\nORDER BY date'),
    "total_fraud_amount":       ("Grand total stolen:",    'SELECT SUM(amount) as total_fraud\nFROM transactions\nWHERE vendor_id IN (4, 7)'),
}


# ── Cliffhanger teasers ─────────────────────────────────────────────────────
# Shown between scenes as a dramatic "end of episode" beat.
# Format: from_scene → teaser text shown before transitioning.

CLIFFHANGERS = {
    SCENE_YOUR_DESK: (
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "  END OF EPISODE 1: \"First Day\"\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "  You've seen the tables. You've counted the heads.\n"
        "  But Diana's sticky note said \"get familiar.\"\n"
        "  She didn't say what you'd find when you did.\n\n"
        "  NEXT: The transaction log. Something doesn't add up.\n\n"
        "  📄 Page 1 of The Analyst's Field Guide unlocked.\n"
    ),
    SCENE_DB_TERMINAL: (
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "  END OF EPISODE 2: \"Follow the Money\"\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "  Two vendors. No address. No verification.\n"
        "  Hundreds of thousands of dollars.\n"
        "  Someone approved every single payment.\n\n"
        "  NEXT: The personnel files. Who signed off on this?\n\n"
        "  📄 Page 2 of The Analyst's Field Guide unlocked.\n"
    ),
    SCENE_HR_FILES: (
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "  END OF EPISODE 3: \"The Name\"\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "  Marcus Webb. CFO. Employee #4.\n"
        "  Special Projects: $4.8 million budget.\n"
        "  You have a name. Now you need proof.\n\n"
        "  NEXT: The CFO's office. He's in a board meeting.\n"
        "  You have 20 minutes.\n\n"
        "  📄 Page 3 of The Analyst's Field Guide unlocked.\n"
    ),
    SCENE_CFO_DEPT: (
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "  END OF EPISODE 4: \"The Pattern\"\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "  The amounts are escalating. $87K → $243K in 9 months.\n"
        "  He's getting bolder. He thinks nobody's watching.\n"
        "  He's wrong.\n\n"
        "  NEXT: Build the case. Every dollar. Every date.\n"
        "  The kind of evidence that doesn't blink.\n\n"
        "  📄 Page 4 of The Analyst's Field Guide unlocked.\n"
    ),
    SCENE_AUDIT_TRAIL: (
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "  END OF EPISODE 5: \"The Number\"\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "  $1,869,500.\n"
        "  Two shell companies. One approver. Thirteen months.\n"
        "  Your phone buzzes.\n\n"
        "  NEXT: Rachel Kim wants to see you. Now.\n\n"
        "  📄 Page 5 of The Analyst's Field Guide unlocked.\n"
    ),
}
