# core/season2_collectibles.py
# Collectible Documents — "The Python Codex"
#
# One document unlocks per completed scene. By the end of Season 2,
# the player has assembled a 5-page codex summarizing every Python
# technique they learned during the ghost investigation.
#
# Same structure as core/collectibles.py.
# The final scene (the_signal) doesn't unlock a page — it IS the payoff.

from core.season2_game import (
    S2_SCENE_SERVER_LOGS,
    S2_SCENE_GHOST_RECORDS,
    S2_SCENE_TIMESTAMP,
    S2_SCENE_ARCHIVE,
    S2_SCENE_PATTERN_DECODER,
)


S2_FIELD_GUIDE_PAGES = [
    {
        "id":       "s2_page_1_variables",
        "scene":    S2_SCENE_SERVER_LOGS,
        "title":    "Page 1: Name Everything",
        "subtitle": "Data without a name disappears.",
        "body": (
            "SQL gives you answers. Python lets you keep them.\n\n"
            "The first thing you learn: store query results in variables.\n"
            "logs = db.query(...). Now 'logs' exists. You can loop through it,\n"
            "filter it, count it, reference it ten lines later.\n\n"
            "Then you learn to walk through data with for loops.\n"
            "Each row, one at a time. Looking for the thing\n"
            "that doesn't belong.\n\n"
            "Rule #1: If you ran a query and didn't save the result,\n"
            "you'll run it again. Variables save you from yourself."
        ),
        "skill_summary": "variables  |  for loops  |  = assignment  |  print()",
    },
    {
        "id":       "s2_page_2_filtering",
        "scene":    S2_SCENE_GHOST_RECORDS,
        "title":    "Page 2: Filter the Noise",
        "subtitle": "Most data is irrelevant. Find what isn't.",
        "body": (
            "30 log entries. Only 14 matter. A for loop with an if\n"
            "statement gets you there — but Python has something faster.\n\n"
            "List comprehensions: [item for item in data if condition].\n"
            "One line. No loop body. No append. Just the filtered result.\n\n"
            "It's the analytical equivalent of panning for gold.\n"
            "Pour in the river. Keep only the glint.\n\n"
            "Rule #2: The best analysts don't process more data.\n"
            "They eliminate more noise."
        ),
        "skill_summary": "list comprehensions  |  [x for x in data if ...]  |  filtering",
    },
    {
        "id":       "s2_page_3_parsing",
        "scene":    S2_SCENE_TIMESTAMP,
        "title":    "Page 3: Break It Apart",
        "subtitle": "Text is data in disguise.",
        "body": (
            "A timestamp looks like a single value: '2024-03-15 03:03:00'.\n"
            "But it's actually six pieces of data glued together with\n"
            "dashes, spaces, and colons.\n\n"
            ".split() breaks it open. [1] grabs the piece you need.\n"
            ".find() tells you where a pattern lives.\n"
            "Slicing with [11:16] extracts by position.\n\n"
            "Then you wrap it in a function: def count_anomalies(data).\n"
            "Define once. Call forever. Never retype the logic.\n\n"
            "Rule #3: If you've typed the same code three times,\n"
            "it's time to write a function."
        ),
        "skill_summary": ".split()  |  .find()  |  slicing  |  def / return",
    },
    {
        "id":       "s2_page_4_organizing",
        "scene":    S2_SCENE_ARCHIVE,
        "title":    "Page 4: Label Your Evidence",
        "subtitle": "A list remembers order. A dictionary remembers meaning.",
        "body": (
            "Lists are sequences: item 0, item 1, item 2.\n"
            "Good for ordered data. Bad for named data.\n\n"
            "Dictionaries map names to values:\n"
            "  findings['phantom_count'] = 14\n"
            "  findings['time'] = '03:03'\n\n"
            "When you compare backup snapshots, you need to know\n"
            "WHICH table had a discrepancy, not just that one did.\n"
            "Dictionaries give your data labels.\n\n"
            "Rule #4: Use a list when order matters.\n"
            "Use a dictionary when identity matters.\n"
            "An investigation needs both."
        ),
        "skill_summary": "dictionaries  |  {key: value}  |  .get()  |  comparison",
    },
    {
        "id":       "s2_page_5_synthesis",
        "scene":    S2_SCENE_PATTERN_DECODER,
        "title":    "Page 5: Read the Signal",
        "subtitle": "The data was talking. You learned to listen.",
        "body": (
            "The phantom queries weren't random. They were a message.\n"
            "Hidden in the first letters of each action field.\n"
            "Left by someone who knew the data would be watched.\n\n"
            "You decoded it with a loop. You confirmed it with a\n"
            "frequency dictionary. You documented it with a function.\n\n"
            "Variables, loops, comprehensions, functions, string methods,\n"
            "dictionaries — six tools. Combined with SQL, they let you\n"
            "see what the data was trying to tell you all along.\n\n"
            "Rule #5: Data doesn't just answer questions.\n"
            "Sometimes, if you listen carefully enough,\n"
            "it asks them."
        ),
        "skill_summary": "pattern decoding  |  string indexing  |  .join()  |  synthesis",
    },
]


# Fast lookup
S2_PAGES_BY_SCENE = {p["scene"]: p for p in S2_FIELD_GUIDE_PAGES}
S2_PAGES_BY_ID = {p["id"]: p for p in S2_FIELD_GUIDE_PAGES}


def s2_unlocked_pages(completed_scenes: list[str]) -> list[dict]:
    """Return Season 2 pages unlocked by scenes the player has completed."""
    return [p for p in S2_FIELD_GUIDE_PAGES if p["scene"] in completed_scenes]


def s2_is_page_unlocked(page_id: str, completed_scenes: list[str]) -> bool:
    page = S2_PAGES_BY_ID.get(page_id)
    return page is not None and page["scene"] in completed_scenes
