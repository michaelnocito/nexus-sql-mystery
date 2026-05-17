# core/season2_sidequests.py
# PRESERVED — Season 2 Python content (the original Python-primary design).
#
# Season 2's main path is now 100% SQL (see core/season2_game.py). These
# Python objectives/step-text/hints are intentionally KEPT, not deleted:
# they are the raw material for the future Pro-Panel "optional Python
# side quest" spec — one opt-in side quest per scene.
#
# Nothing imports this module yet. It is a deliberate, reusable archive
# so the original Python build (12 objectives, validators, hints, recall)
# is not lost. Do not delete.
#
# ---------------------------------------------------------------------------
# Original header:
# Season 2: "The Ghost in the Machine"
# GameState extension — Python objective definitions, validators, hints,
# step text, recall challenges. The player writes REAL Python that
# executes in the cmd_panel sandbox; validators check code + output.

import re


# -- Scene constants ----------------------------------------------------------

S2_SCENE_SERVER_LOGS      = "s2_server_logs"
S2_SCENE_GHOST_RECORDS    = "s2_ghost_records"
S2_SCENE_TIMESTAMP        = "s2_timestamp_analysis"
S2_SCENE_ARCHIVE          = "s2_data_archaeology"
S2_SCENE_PATTERN_DECODER  = "s2_pattern_decoder"
S2_SCENE_THE_SIGNAL       = "s2_the_signal"


# -- Validator helpers --------------------------------------------------------

def _code_uses(*fragments):
    """Check that the player's code contains all specified fragments."""
    frags = [f.lower() for f in fragments]
    def validate(code, output):
        low = code.lower()
        return all(f in low for f in frags)
    return validate


def _output_contains(*fragments):
    """Check that the execution output contains all specified strings."""
    frags = [f.lower() for f in fragments]
    def validate(code, output):
        low = output.lower()
        return all(f in low for f in frags)
    return validate


def _code_and_output(code_frags, output_frags):
    """Check both code constructs and output content."""
    code_check = _code_uses(*code_frags)
    out_check  = _output_contains(*output_frags)
    def validate(code, output):
        return code_check(code, output) and out_check(code, output)
    return validate


# -- Objective definitions ----------------------------------------------------
# Each objective has:
#   id        - unique string key
#   scene     - which scene it belongs to
#   label     - short display label (shown in HUD / clue log)
#   detail    - longer description for codex / popup
#   concept   - codex concept id (Season 2 Python concepts)
#   validator - callable(code, output) -> bool

S2_OBJECTIVES = [

    # -- Scene: server_logs ---------------------------------------------------
    {
        "id":        "store_result",
        "scene":     S2_SCENE_SERVER_LOGS,
        "label":     "Stored query results in a variable",
        "detail":    "Used a variable to capture db.query() output — the first step to Python-powered analysis.",
        "concept":   "s2_variables",
        "validator": lambda code, output: (
            "=" in code and
            "db.query" in code and
            re.search(r'^\s*\w+\s*=\s*db\.query', code, re.MULTILINE) is not None and
            len(output.strip()) > 0
        ),
    },
    {
        "id":        "loop_records",
        "scene":     S2_SCENE_SERVER_LOGS,
        "label":     "Looped through server log records",
        "detail":    "Used a for loop to iterate through query results and print matching entries.",
        "concept":   "s2_for_loops",
        "validator": lambda code, output: (
            "for " in code and
            "print" in code and
            ("server_logs" in code.lower() or "log" in output.lower()) and
            len(output.strip()) > 0
        ),
    },

    # -- Scene: ghost_records -------------------------------------------------
    {
        "id":        "list_comp_filter",
        "scene":     S2_SCENE_GHOST_RECORDS,
        "label":     "Filtered records with a list comprehension",
        "detail":    "Used a list comprehension to filter query results — Python's elegant one-liner.",
        "concept":   "s2_list_comprehensions",
        "validator": lambda code, output: (
            "[" in code and
            "for " in code and
            "in " in code and
            # Must have the list comp pattern: [expr for x in y]
            re.search(r'\[.+\bfor\b.+\bin\b.+\]', code) is not None and
            len(output.strip()) > 0
        ),
    },
    {
        "id":        "find_ghost_employee",
        "scene":     S2_SCENE_GHOST_RECORDS,
        "label":     "Found the record that won't stay deleted",
        "detail":    "Queried deleted_records and discovered one entry keeps incrementing its restored_count.",
        "concept":   "s2_variables",
        "validator": lambda code, output: (
            "deleted_records" in code.lower() and
            ("restored" in output.lower() or "restored_count" in code.lower()) and
            len(output.strip()) > 0
        ),
    },

    # -- Scene: timestamp_analysis --------------------------------------------
    {
        "id":        "parse_timestamps",
        "scene":     S2_SCENE_TIMESTAMP,
        "label":     "Parsed timestamps from log entries",
        "detail":    "Used string methods to extract the hour from timestamp strings — always 3:03am.",
        "concept":   "s2_string_methods",
        "validator": lambda code, output: (
            ("split" in code or "find" in code or "index" in code or
             "slice" in code or "[" in code or "replace" in code or
             "strip" in code) and
            ("03:03" in output or "3:03" in output or "03" in output) and
            len(output.strip()) > 0
        ),
    },
    {
        "id":        "count_anomalies",
        "scene":     S2_SCENE_TIMESTAMP,
        "label":     "Wrote a function to count anomalies",
        "detail":    "Defined a Python function that counts entries matching anomalous criteria.",
        "concept":   "s2_functions",
        "validator": lambda code, output: (
            "def " in code and
            ("count" in code.lower() or "anomal" in code.lower() or "len(" in code) and
            # Must call the function too
            re.search(r'\w+\(', code.split("def ")[0] if "def " in code else "") is not None or
            (code.count("(") >= 2 and "def " in code) and
            len(output.strip()) > 0
        ),
    },

    # -- Scene: data_archaeology ----------------------------------------------
    {
        "id":        "compare_backups",
        "scene":     S2_SCENE_ARCHIVE,
        "label":     "Compared backup snapshots for discrepancies",
        "detail":    "Used Python to compare two query results and spot mismatched row counts.",
        "concept":   "s2_list_comprehensions",
        "validator": lambda code, output: (
            "backup_snapshots" in code.lower() and
            ("!=" in code or "==" in code or "differ" in output.lower() or
             "mismatch" in output.lower() or "not" in code.lower()) and
            len(output.strip()) > 0
        ),
    },
    {
        "id":        "build_summary",
        "scene":     S2_SCENE_ARCHIVE,
        "label":     "Built a summary dictionary of findings",
        "detail":    "Created a dictionary organizing investigation findings by category.",
        "concept":   "s2_dictionaries",
        "validator": lambda code, output: (
            "{" in code and
            ":" in code and
            # Must look like a dict literal or dict assignment
            re.search(r'(\{[^}]*:[^}]*\}|dict\()', code) is not None and
            len(output.strip()) > 0
        ),
    },

    # -- Scene: pattern_decoder -----------------------------------------------
    {
        "id":        "decode_pattern",
        "scene":     S2_SCENE_PATTERN_DECODER,
        "label":     "Decoded the hidden message in log entries",
        "detail":    "Used a loop to extract characters from log actions — spelling out a message from the ghost.",
        "concept":   "s2_for_loops",
        "validator": lambda code, output: (
            "for " in code and
            ("[" in code or "append" in code or "join" in code or "+" in code) and
            len(output.strip()) > 0
        ),
    },
    {
        "id":        "correlate_times",
        "scene":     S2_SCENE_PATTERN_DECODER,
        "label":     "Built a frequency dict of query times",
        "detail":    "Created a dictionary counting how many phantom queries occurred at each timestamp.",
        "concept":   "s2_dictionaries",
        "validator": lambda code, output: (
            "{" in code and
            ("for " in code or "get(" in code) and
            ("03:03" in output or "3:03" in output or "count" in code.lower() or
             "freq" in code.lower()) and
            len(output.strip()) > 0
        ),
    },

    # -- Scene: the_signal ----------------------------------------------------
    {
        "id":        "write_report_function",
        "scene":     S2_SCENE_THE_SIGNAL,
        "label":     "Wrote a reusable report function",
        "detail":    "Defined a function that generates a formatted investigation report.",
        "concept":   "s2_functions",
        "validator": lambda code, output: (
            "def " in code and
            "return" in code and
            ("report" in code.lower() or "summary" in code.lower() or
             "print" in code) and
            len(output.strip()) > 0
        ),
    },
    {
        "id":        "identify_source",
        "scene":     S2_SCENE_THE_SIGNAL,
        "label":     "Identified the automated script",
        "detail":    "Combined SQL queries and Python analysis to reveal the phantom was a whistleblower's scheduled script.",
        "concept":   "s2_functions",
        "validator": lambda code, output: (
            "db.query" in code and
            ("def " in code or "for " in code or "[" in code) and
            len(output.strip()) > 0
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
        "Time to figure out what's coming back from the dead."
    ),
    S2_SCENE_TIMESTAMP: (
        "Back at your desk. Coffee. Notepad. A growing sense of unease.\n"
        "The server logs show activity at 3:03am. Every single night.\n"
        "Nobody works at 3:03am. Nobody human, anyway.\n\n"
        "String methods are your scalpel. Time to dissect these timestamps."
    ),
    S2_SCENE_ARCHIVE: (
        "Archive Room. Fluorescent lights that haven't been changed since\n"
        "the Clinton administration. Dust on everything.\n"
        "But the backup tapes are here, and backup tapes don't lie.\n\n"
        "Compare the snapshots. Find the discrepancy. Build the evidence."
    ),
    S2_SCENE_PATTERN_DECODER: (
        "You're back in the server room. It's 2:47am. You couldn't sleep.\n"
        "The phantom queries run at 3:03. You want to watch it happen.\n\n"
        "The logs aren't random. There's a pattern in the action fields.\n"
        "First letters. Or last letters. Something deliberate.\n\n"
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
        "It was a warning."
    ),
}


# -- Step guidance text -------------------------------------------------------
# Shown in the narrative panel when an objective becomes the active goal.

S2_STEP_TEXT = {
    "store_result": (
        "The server room smells like ozone and paranoia.\n\n"
        "First things first: pull the server logs and STORE them.\n"
        "In Python, you save data to a variable with  = \n\n"
        "  logs = db.query(\"SELECT * FROM server_logs\")\n\n"
        "Now  logs  holds your query results. You can inspect them,\n"
        "loop through them, filter them — Python makes data come alive."
    ),
    "loop_records": (
        "Good. You've got the logs stored. Now walk through them.\n\n"
        "A for loop visits each row one at a time:\n"
        "  for row in logs:\n"
        "      print(row)\n\n"
        "But you don't want all of them. You want the weird ones.\n"
        "Add an if inside the loop to filter for anomalies.\n\n"
        "Look for entries where the status is... off."
    ),
    "list_comp_filter": (
        "The deleted_records table is disturbing. Records that should\n"
        "be gone are tracked here — with a restored_count.\n\n"
        "Use a list comprehension to filter in one clean line:\n"
        "  weird = [r for r in results if some_condition]\n\n"
        "It's a for loop and a filter, collapsed into a single expression.\n"
        "Find the records where restored_count is suspiciously high."
    ),
    "find_ghost_employee": (
        "One of these deleted records keeps coming back.\n\n"
        "Query the deleted_records table. Look at restored_count.\n"
        "One entry has been restored dozens of times.\n"
        "Every night. At 3:03am.\n\n"
        "  result = db.query(\"SELECT * FROM deleted_records\")\n"
        "  print(result)\n\n"
        "Who is this ghost employee?"
    ),
    "parse_timestamps": (
        "Every phantom query runs at exactly 3:03am.\n\n"
        "The timestamp column has strings like '2024-03-15 03:03:00'.\n"
        "Extract the hour using string methods:\n\n"
        "  timestamp = '2024-03-15 03:03:00'\n"
        "  time_part = timestamp.split(' ')[1]   # '03:03:00'\n"
        "  hour = time_part.split(':')[0]         # '03'\n\n"
        ".split() breaks a string into a list at every space (or whatever\n"
        "character you pass it). Then index into the result with [1]."
    ),
    "count_anomalies": (
        "You've been doing this by hand. Time to automate it.\n\n"
        "Write a function — a reusable block of code with a name:\n\n"
        "  def count_anomalies(logs):\n"
        "      count = 0\n"
        "      for row in logs:\n"
        "          if '03:03' in str(row):\n"
        "              count = count + 1\n"
        "      return count\n\n"
        "Then call it:  print(count_anomalies(logs))\n\n"
        "def defines it. The parentheses hold the input.\n"
        "return sends back the answer."
    ),
    "compare_backups": (
        "The backup snapshots table has row counts from different dates.\n"
        "If someone's been tampering with data, the counts won't match.\n\n"
        "Pull two snapshots and compare them:\n"
        "  old = db.query(\"SELECT * FROM backup_snapshots WHERE snapshot_date = '2024-01-01'\")\n"
        "  new = db.query(\"SELECT * FROM backup_snapshots WHERE snapshot_date = '2024-06-01'\")\n\n"
        "Compare the row_count values. Are they the same?\n"
        "Discrepancies mean someone added or removed data between snapshots."
    ),
    "build_summary": (
        "Time to organize your findings. A dictionary maps keys to values:\n\n"
        "  summary = {\n"
        "      'phantom_queries': 14,\n"
        "      'time': '03:03',\n"
        "      'ghost_employee': 'unknown',\n"
        "      'backup_discrepancies': 2\n"
        "  }\n"
        "  print(summary)\n\n"
        "Curly braces { }. Key-value pairs separated by colons.\n"
        "It's like a labeled filing system — everything has a name."
    ),
    "decode_pattern": (
        "The phantom queries aren't random noise. They're a message.\n\n"
        "Pull the 3:03am log entries and look at the action field.\n"
        "Take the first letter of each action. Or the last. Try both.\n\n"
        "  entries = db.query(\"SELECT action FROM server_logs WHERE timestamp LIKE '%03:03%' ORDER BY timestamp\")\n"
        "  message = ''\n"
        "  for row in entries:\n"
        "      message = message + row[0][0]  # first letter of action\n"
        "  print(message)\n\n"
        "Someone left a message in the machine."
    ),
    "correlate_times": (
        "How often does the phantom strike? Build a frequency count.\n\n"
        "A dictionary is perfect for counting:\n"
        "  freq = {}\n"
        "  for row in logs:\n"
        "      time = str(row[1]).split(' ')[1]  # extract time\n"
        "      freq[time] = freq.get(time, 0) + 1\n"
        "  print(freq)\n\n"
        ".get(key, default) returns the value if the key exists,\n"
        "or the default if it doesn't. Perfect for counting."
    ),
    "write_report_function": (
        "Rachel's going to want this in writing.\n\n"
        "Write a function that generates a report:\n\n"
        "  def generate_report(findings):\n"
        "      report = 'INVESTIGATION REPORT\\n'\n"
        "      report = report + '=' * 40 + '\\n'\n"
        "      for key in findings:\n"
        "          report = report + key + ': ' + str(findings[key]) + '\\n'\n"
        "      return report\n\n"
        "  print(generate_report(summary))\n\n"
        "Functions that return strings can be printed, saved, emailed.\n"
        "They're tools you build once and use forever."
    ),
    "identify_source": (
        "Final step. Connect all the pieces.\n\n"
        "Query the server_logs for the phantom entries.\n"
        "Cross-reference with the deleted employee.\n"
        "Use Python to build the complete picture.\n\n"
        "The 'ghost' is an automated script. Left by someone who\n"
        "knew the data was being tampered with. A dead man's switch.\n\n"
        "Write the query. Run the analysis. Prove it.\n"
        "Then tell Rachel everything."
    ),
}


# -- Per-objective focus commands ---------------------------------------------
# Shown in the "Try this:" box. Updated dynamically as objectives complete.

S2_OBJECTIVE_FOCUS = {
    "store_result":         ("Try this first:",          'logs = db.query("SELECT * FROM server_logs")'),
    "loop_records":         ("Loop through the logs:",   'for row in logs:\n    print(row)'),
    "list_comp_filter":     ("Filter with a list comp:", 'weird = [r for r in results if r[5] > 1]'),
    "find_ghost_employee":  ("Find the ghost:",          'db.query("SELECT * FROM deleted_records ORDER BY restored_count DESC")'),
    "parse_timestamps":     ("Parse the timestamps:",    "times = [str(r[1]).split(' ')[1] for r in logs]"),
    "count_anomalies":      ("Write a function:",        'def count_anomalies(logs):\n    return len([r for r in logs if "03:03" in str(r)])'),
    "compare_backups":      ("Compare snapshots:",       'db.query("SELECT * FROM backup_snapshots ORDER BY snapshot_date")'),
    "build_summary":        ("Build a summary dict:",    'summary = {"phantom_count": 14, "time": "03:03", "suspect": "unknown"}'),
    "decode_pattern":       ("Decode the message:",      'msg = "".join(row[0][0] for row in entries)'),
    "correlate_times":      ("Count the frequencies:",   'freq = {}\nfor r in logs:\n    t = str(r[1]).split(" ")[1]\n    freq[t] = freq.get(t, 0) + 1'),
    "write_report_function":("Write a report function:", 'def report(data):\n    return "\\n".join(f"{k}: {v}" for k, v in data.items())'),
    "identify_source":      ("Put it all together:",     'phantom = db.query("SELECT * FROM server_logs WHERE timestamp LIKE \'%03:03%\'")\nprint(phantom)'),
}


# -- Progressive hints --------------------------------------------------------
# Each list goes from vague -> specific -> gives away the answer.

S2_HINTS = {
    "store_result": [
        "You need to save those query results somewhere. In Python, you use = to assign a value to a variable name.",
        "Try: logs = db.query(\"SELECT * FROM server_logs\") — now 'logs' holds your data.",
        "Type exactly: logs = db.query(\"SELECT * FROM server_logs\")  then  print(logs)",
    ],
    "loop_records": [
        "You've got the data stored. Now walk through it row by row — a for loop visits each item in sequence.",
        "for row in logs:  starts the loop. Indent the next line and print(row) to see each one.",
        "for row in logs:\n    print(row)\n\nAdd an 'if' inside to filter: if 'anomaly' in str(row):",
    ],
    "list_comp_filter": [
        "A list comprehension is a for loop squeezed into one line inside square brackets. Think: [what_i_want for item in collection if condition].",
        "Try: filtered = [r for r in results if some_condition_about_r]  — it creates a new list with only matching items.",
        "weird = [r for r in db.query(\"SELECT * FROM deleted_records\") if r[5] > 0]\nprint(weird)",
    ],
    "find_ghost_employee": [
        "The deleted_records table tracks records that were removed. One of them keeps coming back. Check the restored_count column.",
        "db.query(\"SELECT * FROM deleted_records ORDER BY restored_count DESC\")  — the top result is your ghost.",
        "result = db.query(\"SELECT * FROM deleted_records WHERE restored_count > 10\")\nprint(result)",
    ],
    "parse_timestamps": [
        "The timestamp strings look like '2024-03-15 03:03:00'. You need to extract the time part. Python strings have methods for cutting them up.",
        "Use .split(' ') to break on spaces, then [1] to grab the second piece. That gives you the time.",
        "logs = db.query(\"SELECT * FROM server_logs WHERE timestamp LIKE '%03:03%'\")\nfor r in logs:\n    t = str(r[1]).split(' ')[1]\n    print(t)",
    ],
    "count_anomalies": [
        "You've been counting by hand. Write a function — def function_name(parameters): — that does it automatically.",
        "def count_anomalies(data):\n    count = 0\n    for row in data:\n        if '03:03' in str(row):\n            count = count + 1\n    return count",
        "def count_anomalies(data):\n    return len([r for r in data if '03:03' in str(r)])\n\nlogs = db.query(\"SELECT * FROM server_logs\")\nprint(count_anomalies(logs))",
    ],
    "compare_backups": [
        "The backup_snapshots table has row counts from different dates. If someone tampered with data, the numbers won't match between snapshots.",
        "Query backup_snapshots and compare row_count values across dates. Look for tables where the count changed unexpectedly.",
        "snaps = db.query(\"SELECT * FROM backup_snapshots ORDER BY snapshot_date, table_name\")\nfor s in snaps:\n    print(s)",
    ],
    "build_summary": [
        "A dictionary uses curly braces and colons: {key: value, key2: value2}. It's the perfect way to organize named findings.",
        "summary = {'phantom_queries': 14, 'time': '03:03', 'ghost_employee': '???'}",
        "summary = {'phantom_queries': 14, 'always_at': '03:03', 'ghost_id': 11, 'backup_discrepancies': 2}\nprint(summary)",
    ],
    "decode_pattern": [
        "The phantom queries have action descriptions. There's a pattern in the text — try taking the first letter of each action.",
        "Pull the 3:03am entries ordered by timestamp. Loop through them and grab the first character of each action field.",
        "entries = db.query(\"SELECT action FROM server_logs WHERE timestamp LIKE '%03:03%' ORDER BY timestamp\")\nmsg = ''.join(str(r[0])[0] for r in entries)\nprint(msg)",
    ],
    "correlate_times": [
        "Build a dictionary where keys are timestamps and values are how many times each one appears. Use .get(key, 0) + 1 to count.",
        "freq = {}\nfor row in logs:\n    t = str(row[1]).split(' ')[1]\n    freq[t] = freq.get(t, 0) + 1",
        "logs = db.query(\"SELECT * FROM server_logs\")\nfreq = {}\nfor r in logs:\n    t = str(r[1]).split(' ')[1]\n    freq[t] = freq.get(t, 0) + 1\nprint(freq)",
    ],
    "write_report_function": [
        "A report function takes your findings dict and formats it into readable text. Use def, a for loop over the dict, and return.",
        "def generate_report(data):\n    lines = ['=== INVESTIGATION REPORT ===']\n    for k in data:\n        lines.append(f'{k}: {data[k]}')\n    return '\\n'.join(lines)",
        "def generate_report(data):\n    lines = ['=== INVESTIGATION REPORT ===']\n    for k, v in data.items():\n        lines.append(f'  {k}: {v}')\n    return '\\n'.join(lines)\n\nprint(generate_report({'phantom': 14, 'time': '03:03'}))",
    ],
    "identify_source": [
        "Connect the dots: the ghost employee, the 3:03am queries, the decoded message. One final analysis ties it all together.",
        "Query server_logs for the phantom entries. Cross-reference with deleted_records. The source is an automated script.",
        "phantom = db.query(\"SELECT * FROM server_logs WHERE timestamp LIKE '%03:03%'\")\nghost = db.query(\"SELECT * FROM deleted_records WHERE restored_count > 10\")\nprint('Phantom queries:', len(phantom))\nprint('Ghost record:', ghost)\nprint('Source: automated whistleblower script')",
    ],
}


# -- Recall challenges -------------------------------------------------------
# Shown between scene transitions as quick retrieval practice.

S2_RECALL_CHALLENGES = {
    "s2_variables": {
        "question": "How do you store the result of db.query() in a variable called 'data'?",
        "answer":   "data = db.query(\"SELECT ...\")",
        "keywords": ["data", "=", "db.query"],
        "concept":  "s2_variables",
    },
    "s2_for_loops": {
        "question": "Write a for loop that prints each item in a list called 'records'.",
        "answer":   "for r in records:\n    print(r)",
        "keywords": ["for", "in", "records", "print"],
        "concept":  "s2_for_loops",
    },
    "s2_list_comprehensions": {
        "question": "Write a list comprehension that keeps only items where x > 10 from a list called 'numbers'.",
        "answer":   "[x for x in numbers if x > 10]",
        "keywords": ["[", "for", "if", "]"],
        "concept":  "s2_list_comprehensions",
    },
    "s2_functions": {
        "question": "How do you define a function called 'analyze' that takes one parameter called 'data'?",
        "answer":   "def analyze(data):",
        "keywords": ["def", "analyze", "data"],
        "concept":  "s2_functions",
    },
    "s2_string_methods": {
        "question": "How do you split the string '2024-03-15 03:03:00' on spaces and get the time part?",
        "answer":   "'2024-03-15 03:03:00'.split(' ')[1]",
        "keywords": ["split", "[1]"],
        "concept":  "s2_string_methods",
    },
    "s2_dictionaries": {
        "question": "Create a dictionary with keys 'name' and 'count' set to 'Alex' and 5.",
        "answer":   "{'name': 'Alex', 'count': 5}",
        "keywords": ["{", "name", "count", "}"],
        "concept":  "s2_dictionaries",
    },
}


# -- Cliffhanger teasers -----------------------------------------------------
# Shown between scenes as a dramatic "end of episode" beat.

S2_CLIFFHANGERS = {
    S2_SCENE_SERVER_LOGS: (
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "  END OF EPISODE 1: \"Strange Entries\"\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "  The server logs don't lie. Something is running\n"
        "  queries when the building is empty.\n"
        "  And it's been doing it for months.\n\n"
        "  NEXT: A deleted employee record that won't stay dead.\n\n"
        "  📄 Page 1 of The Python Codex unlocked.\n"
    ),
    S2_SCENE_GHOST_RECORDS: (
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "  END OF EPISODE 2: \"The Revenant Row\"\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "  Employee #11. Deleted three months ago.\n"
        "  Restored 47 times since. Always at 3:03am.\n"
        "  Someone — or something — wants this record to exist.\n\n"
        "  NEXT: Timestamp analysis. What happens at 3:03?\n\n"
        "  📄 Page 2 of The Python Codex unlocked.\n"
    ),
    S2_SCENE_TIMESTAMP: (
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "  END OF EPISODE 3: \"The Witching Hour\"\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "  14 phantom queries. All at 03:03:00.\n"
        "  Not 03:02. Not 03:04. Exactly 03:03.\n"
        "  That's not a ghost. That's a cron job.\n\n"
        "  NEXT: The archive room. Old backups hold old secrets.\n\n"
        "  📄 Page 3 of The Python Codex unlocked.\n"
    ),
    S2_SCENE_ARCHIVE: (
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "  END OF EPISODE 4: \"Buried Data\"\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "  The backup checksums don't match.\n"
        "  Someone altered the production database\n"
        "  after the last backup. The phantom script\n"
        "  is restoring what they tried to erase.\n\n"
        "  NEXT: The server room at night. The message in the machine.\n\n"
        "  📄 Page 4 of The Python Codex unlocked.\n"
    ),
    S2_SCENE_PATTERN_DECODER: (
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "  END OF EPISODE 5: \"The Cipher\"\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "  The phantom queries spell a message.\n"
        "  Someone left breadcrumbs in the machine.\n"
        "  Not a haunting. A confession.\n\n"
        "  NEXT: Rachel Kim's office. The truth.\n\n"
        "  📄 Page 5 of The Python Codex unlocked.\n"
    ),
}
