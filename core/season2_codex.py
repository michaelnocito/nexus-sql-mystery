# core/season2_codex.py
# CODEX — Season 2 concept library.
#
# Each entry teaches one Python concept.
# Shown as a popup card after the player completes an objective that uses it.
#
# Same structure as core/codex.py:
#   id, title, what, why, syntax, analogy, gotcha


S2_CONCEPTS = {

    # -- Python Foundations --------------------------------------------------

    "s2_variables": {
        "id":      "s2_variables",
        "title":   "Variables — Naming Your Data",
        "what":    "A variable is a name you give to a piece of data so you can refer to it later.",
        "why":     "Without variables, every query result vanishes the moment you run it. Variables let you store, reuse, and combine data across multiple steps.",
        "syntax":  "logs = db.query(\"SELECT * FROM server_logs\")\ncount = len(logs)\nname = 'Alex'\nprint(logs)   # uses the stored result",
        "analogy": "A labeled box. You put something in, write a name on the outside, and grab it whenever you need it. The box can hold anything — numbers, text, even entire query results.",
        "gotcha":  "Variable names are case-sensitive: 'Logs' and 'logs' are different variables. Stick to lowercase with underscores: total_count, not TotalCount.",
    },

    "s2_for_loops": {
        "id":      "s2_for_loops",
        "title":   "For Loops — Walking Through Data",
        "what":    "A for loop visits each item in a collection, one at a time, running the indented code for each.",
        "why":     "Databases return rows. You need to examine each row — print it, check it, count it. A for loop automates that walk-through.",
        "syntax":  "for row in logs:\n    print(row)\n\n# With a condition:\nfor row in logs:\n    if row[5] == 'ANOMALY':\n        print('Found:', row)",
        "analogy": "Flipping through a stack of index cards. You look at each one, decide if it matters, then move to the next. The loop does the flipping for you.",
        "gotcha":  "Indentation matters in Python. The code inside the loop MUST be indented (4 spaces). Forget the indent and Python throws an error.",
    },

    "s2_list_comprehensions": {
        "id":      "s2_list_comprehensions",
        "title":   "List Comprehensions — One-Line Filters",
        "what":    "A list comprehension builds a new list by transforming and/or filtering items from an existing collection — all in one line.",
        "why":     "Analysts filter data constantly. List comprehensions are Python's elegant shorthand for 'give me only the items that match this condition.'",
        "syntax":  "# Full form:\nanomalies = [row for row in logs if row[5] == 'ANOMALY']\n\n# Transform + filter:\ntimes = [str(r[1]).split(' ')[1] for r in logs if r[5] == 'ANOMALY']\n\n# Same as:\nanomalies = []\nfor row in logs:\n    if row[5] == 'ANOMALY':\n        anomalies.append(row)",
        "analogy": "A coffee filter for data. Pour everything in, only the matching bits drip through into your new list.",
        "gotcha":  "Don't nest too many comprehensions. [x for x in [y for y in z if a] if b] is clever but unreadable. If it takes more than one line to understand, use a regular for loop.",
    },

    "s2_functions": {
        "id":      "s2_functions",
        "title":   "Functions — Reusable Tools",
        "what":    "A function is a named block of code you can call whenever you need it. Define once, use everywhere.",
        "why":     "You're going to count anomalies more than once. You're going to format reports more than once. Functions save you from retyping the same logic.",
        "syntax":  "def count_anomalies(data):\n    total = 0\n    for row in data:\n        if 'ANOMALY' in str(row):\n            total = total + 1\n    return total\n\n# Call it:\nresult = count_anomalies(logs)\nprint(result)",
        "analogy": "A recipe card. Write down the steps once. Every time you want to make that dish, you follow the card instead of reinventing it from scratch.",
        "gotcha":  "A function without 'return' returns None. If you want a value back, you MUST include return. print() inside a function shows output but doesn't return it.",
    },

    "s2_string_methods": {
        "id":      "s2_string_methods",
        "title":   "String Methods — Dissecting Text",
        "what":    "Strings (text) come with built-in methods for splitting, searching, replacing, and extracting pieces.",
        "why":     "Log entries, timestamps, names — data is full of text. String methods let you carve it up, find patterns, and extract exactly the piece you need.",
        "syntax":  "ts = '2024-03-15 03:03:00'\n\nts.split(' ')        # ['2024-03-15', '03:03:00']\nts.split(' ')[1]     # '03:03:00'\nts.find('03:03')     # 11 (position where it starts)\nts.replace('-', '/') # '2024/03/15 03:03:00'\nts.startswith('2024')# True\nts.upper()           # '2024-03-15 03:03:00' (no letters to uppercase)\nts[11:16]            # '03:03' (slicing by position)",
        "analogy": "A Swiss Army knife for text. .split() is the blade that cuts it apart. .find() is the magnifying glass. .replace() is the eraser and pen.",
        "gotcha":  "Strings are immutable — .replace() doesn't change the original, it returns a NEW string. You must save the result: new_ts = ts.replace('-', '/').",
    },

    "s2_dictionaries": {
        "id":      "s2_dictionaries",
        "title":   "Dictionaries — Labeled Data",
        "what":    "A dictionary maps keys to values — like a real dictionary maps words to definitions. Each key is unique.",
        "why":     "When you need to organize findings, count frequencies, or build structured reports, dictionaries give every piece of data a meaningful name.",
        "syntax":  "# Creating:\nfindings = {\n    'phantom_count': 14,\n    'time': '03:03',\n    'suspect': 'unknown'\n}\n\n# Accessing:\nprint(findings['time'])  # '03:03'\n\n# Counting pattern:\nfreq = {}\nfor item in data:\n    freq[item] = freq.get(item, 0) + 1",
        "analogy": "A filing cabinet with labeled folders. Each folder (key) holds exactly one document (value). You find things by name, not by position.",
        "gotcha":  "Keys must be unique. If you set freq['03:03'] = 5 and then freq['03:03'] = 10, the first value is gone. Use .get(key, default) to safely check before overwriting.",
    },
}


def get_s2_concept(concept_id: str) -> dict | None:
    """Return a Season 2 concept dict by id, or None if not found."""
    return S2_CONCEPTS.get(concept_id)


def all_s2_concepts() -> list[dict]:
    """Return all Season 2 concepts in definition order."""
    return list(S2_CONCEPTS.values())
