# core/season2_scenes.py
# SCENES — the narrative spine of Season 2: "The Ghost in the Machine."
#
# Same structure as core/scenes.py. Each scene is a dict with:
#   id, title, art_key, intro, focus, focus_label, objectives, ambient, exits
#
# After the fraud case, something is wrong in the server room.
# Data appears that shouldn't exist. A deleted record keeps returning.
# Queries run at 3:03am when nobody's in the building.

from core.season2_game import (
    S2_SCENE_SERVER_LOGS,
    S2_SCENE_GHOST_RECORDS,
    S2_SCENE_TIMESTAMP,
    S2_SCENE_ARCHIVE,
    S2_SCENE_PATTERN_DECODER,
    S2_SCENE_THE_SIGNAL,
)


S2_SCENES = {

    S2_SCENE_SERVER_LOGS: {
        "id":          S2_SCENE_SERVER_LOGS,
        "title":       "Server Room — Post-Audit",
        "art_key":     "server_room",
        "intro": (
            "Two weeks since the Marcus Webb thing. The office has that\n"
            "post-scandal energy — half relief, half paranoia.\n"
            "Diana asked you to 'keep an eye on things.' Her exact words.\n\n"
            "So here you are. Server room. Basement B1. Again.\n\n"
            "You pull up the access logs, mostly out of habit.\n"
            "And that's when you see them: entries timestamped at 3:03am.\n"
            "Last night. The night before. Every night for two weeks.\n"
            "User field: blank. IP address: internal.\n\n"
            "Someone — or something — is querying the database\n"
            "while the building is empty.\n\n"
            "You're going to need more than SQL this time.\n"
            "Time to learn some Python."
        ),
        "focus_label": "Try this first:",
        "focus":       'logs = db.query("SELECT * FROM server_logs")',
        "objectives":  ["store_result", "loop_records"],
        "ambient": [
            "The server racks hum at a frequency that wasn't there two weeks ago. You're sure of it.",
            "A cable you've never noticed snakes behind rack 7. It's warm to the touch.",
            "The access log refreshes. A new entry from 3:03am. Right on schedule.",
            "Your coffee is cold. It's been cold for an hour. You didn't notice.",
            "The LED on rack 3 flickers. Red. Green. Red. Almost like morse code.",
            "You hear footsteps in the corridor. You hold your breath. Nobody comes in.",
            "Someone wrote 'CHECK THE BACKUPS' on a sticky note. It's stuck to the underside of the terminal desk.",
        ],
        "exits": {S2_SCENE_GHOST_RECORDS: "db_terminal"},
    },

    S2_SCENE_GHOST_RECORDS: {
        "id":          S2_SCENE_GHOST_RECORDS,
        "title":       "Database Terminal — The Revenant Row",
        "art_key":     "server_room",
        "intro": (
            "You switch to the main database terminal. The one with the\n"
            "cracked Enter key that nobody's fixed since 2021.\n\n"
            "There's a table you've never seen before: deleted_records.\n"
            "It tracks every row that's been removed from the database.\n"
            "Standard audit trail stuff. Boring.\n\n"
            "Except one record has a restored_count of 47.\n\n"
            "Forty-seven times. The same row. Deleted, then restored.\n"
            "Deleted. Restored. Like a heartbeat.\n\n"
            "The record belongs to Employee #11.\n"
            "You check the employees table. There is no Employee #11.\n\n"
            "There hasn't been for three months.\n\n"
            "And yet."
        ),
        "focus_label": "Filter the dead records:",
        "focus":       'results = db.query("SELECT * FROM deleted_records")\nweird = [r for r in results if r[5] > 10]\nprint(weird)',
        "objectives":  ["list_comp_filter", "find_ghost_employee"],
        "ambient": [
            "The terminal cursor blinks at exactly 303 milliseconds. You timed it.",
            "Row 11 appears in your query results. Then it doesn't. Then it does again.",
            "A draft from nowhere ruffles the papers on the desk. The windows are sealed.",
            "The screen flickers. For one frame, you see a name you don't recognize.",
            "Your phone buzzes: an email from a Nexus address that doesn't exist anymore.",
            "The temperature drops two degrees. The thermostat reads normal.",
        ],
        "exits": {S2_SCENE_TIMESTAMP: "your_desk"},
    },

    S2_SCENE_TIMESTAMP: {
        "id":          S2_SCENE_TIMESTAMP,
        "title":       "Your Desk — The 3:03 Problem",
        "art_key":     "desk",
        "intro": (
            "You need to think. Not in the server room with its\n"
            "humming racks and flickering LEDs. At your desk.\n"
            "With coffee. And your notepad.\n\n"
            "The facts:\n"
            "  - Phantom queries running at 3:03am every night\n"
            "  - A deleted employee (#11) restored 47 times\n"
            "  - No user credentials in the log entries\n"
            "  - All from an internal IP address\n\n"
            "The timestamps are strings. '2024-03-15 03:03:00'.\n"
            "You need to parse them — extract the hour, the minute.\n"
            "Prove that 3:03 isn't a coincidence.\n\n"
            "Python has string methods for this. .split(), .find(),\n"
            "slicing with [ ]. Your scalpel for dissecting text."
        ),
        "focus_label": "Parse the timestamps:",
        "focus":       "logs = db.query(\"SELECT * FROM server_logs WHERE timestamp LIKE '%03:03%'\")\nfor r in logs:\n    print(str(r[1]).split(' ')[1])",
        "objectives":  ["parse_timestamps", "count_anomalies"],
        "ambient": [
            "Your notepad has three pages of timestamps. All 03:03. All identical.",
            "Diana walks by. 'You look like you've seen a ghost.' You don't laugh.",
            "The office coffee machine makes that cat noise again. You barely notice anymore.",
            "Sam pings you: 'everything ok? you've been staring at your screen for 20 minutes.'",
            "You write '3:03' on your notepad. Then cross it out. Then write it again.",
            "The cleaning crew arrives. 5:30pm. Everyone's leaving. You're staying.",
        ],
        "exits": {S2_SCENE_ARCHIVE: "archive_room"},
    },

    S2_SCENE_ARCHIVE: {
        "id":          S2_SCENE_ARCHIVE,
        "title":       "Archive Room — Basement B2",
        "art_key":     "archive",
        "intro": (
            "Below B1, there's B2. Nobody told you about B2.\n\n"
            "Diana mentioned it once: 'The archive room. Backup tapes.\n"
            "Haven't been touched since the server migration. 2022 maybe.'\n\n"
            "The door requires a physical key. Vanessa from HR has one.\n"
            "She didn't ask why you wanted it. She looked like she wanted to.\n\n"
            "Inside: metal shelves. Labeled tape drives. A terminal\n"
            "that boots with a CRT glow that makes everything feel\n"
            "like 1997.\n\n"
            "The backup_snapshots table has row counts from different dates.\n"
            "If someone tampered with the production data, the backups\n"
            "will show the discrepancy.\n\n"
            "Backups don't lie. That's kind of their whole thing."
        ),
        "focus_label": "Compare the snapshots:",
        "focus":       'db.query("SELECT * FROM backup_snapshots ORDER BY snapshot_date")',
        "objectives":  ["compare_backups", "build_summary"],
        "ambient": [
            "The CRT terminal hums at a pitch that makes your fillings ache.",
            "Dust motes float in the fluorescent light. Nothing else moves.",
            "A tape labeled 'Q4-2023 FINAL' has been removed from its slot. Recently.",
            "You find a sticky note in the tape rack: 'DO NOT OVERWRITE — EG'",
            "The terminal clock is 3 minutes fast. Or the wall clock is 3 minutes slow.",
            "Something skitters behind the shelves. Probably a mouse. Probably.",
        ],
        "exits": {S2_SCENE_PATTERN_DECODER: "server_room"},
    },

    S2_SCENE_PATTERN_DECODER: {
        "id":          S2_SCENE_PATTERN_DECODER,
        "title":       "Server Room — 2:47am",
        "art_key":     "server_room_night",
        "intro": (
            "You told your roommate you'd be working late.\n"
            "That was six hours ago.\n\n"
            "The building is empty. Security did their sweep at midnight.\n"
            "You hid in the bathroom on the 3rd floor like a rational\n"
            "adult professional.\n\n"
            "Now you're in the server room. It's 2:47am.\n"
            "In sixteen minutes, the phantom runs again.\n\n"
            "You've been staring at the log entries. The action column.\n"
            "Checking access logs. Reading configuration files.\n"
            "Scanning memory dumps. Testing backup integrity.\n"
            "Logging network traffic. Examining security patches.\n\n"
            "The first letters. C-R-S-T-L-E.\n\n"
            "No. Wait. Read them in timestamp order.\n\n"
            "Someone left a message in the machine."
        ),
        "focus_label": "Decode the message:",
        "focus":       'entries = db.query("SELECT action FROM server_logs WHERE timestamp LIKE \'%03:03%\' ORDER BY timestamp")\nmsg = \'\'.join(str(r[0])[0] for r in entries)\nprint(msg)',
        "objectives":  ["decode_pattern", "correlate_times"],
        "ambient": [
            "2:58am. The server fans cycle to a higher speed. No reason.",
            "Your phone screen is the brightest thing in the room. It hurts your eyes.",
            "A notification: 'Scheduled maintenance window: 03:00-03:15.' You didn't schedule that.",
            "The query log updates in real time. You watch. Waiting.",
            "3:01am. Nothing yet. Your hands are shaking. Caffeine or adrenaline. Probably both.",
            "3:02am. The terminal cursor stops blinking. Just for a second.",
            "3:03am. A query runs. You didn't type it. Nobody did.",
            "The server room feels ten degrees colder than it did an hour ago.",
        ],
        "exits": {S2_SCENE_THE_SIGNAL: "coo_office"},
    },

    S2_SCENE_THE_SIGNAL: {
        "id":          S2_SCENE_THE_SIGNAL,
        "title":       "Rachel Kim's Office — The Truth",
        "art_key":     "coo_office",
        "intro": (
            "Rachel Kim doesn't look surprised when you show her the evidence.\n\n"
            "'Sit down,' she says. You sit.\n\n"
            "She pulls up a personnel file. Employee #11.\n"
            "Elena Gutierrez. Senior Database Administrator.\n"
            "Terminated three months ago. Official reason: 'restructuring.'\n\n"
            "'Unofficial reason,' Rachel says, 'is that Elena found something.\n"
            "During the Webb investigation — the one YOU kicked off — she was\n"
            "running her own parallel analysis. She found more. A lot more.\n"
            "Before she could report it, she was let go.'\n\n"
            "'But Elena was smart. She set up an automated script.\n"
            "A dead man's switch. If her account was deleted, the script\n"
            "would keep running. Restoring her record. Logging phantom queries.\n"
            "Leaving breadcrumbs for anyone paying attention.'\n\n"
            "Rachel looks at you.\n\n"
            "'And you paid attention.'\n\n"
            "Write the final report. Document everything.\n"
            "Then we figure out what else Elena found."
        ),
        "focus_label":  "Write the final report:",
        "focus":        'def report(data):\n    return "\\n".join(f"{k}: {v}" for k, v in data.items())',
        "objectives":  ["write_report_function", "identify_source"],
        "ambient": [
            "Rachel's office is quieter than the server room. Somehow that's worse.",
            "The personnel file for Elena Gutierrez has a sticky note: 'EG — do not discuss.'",
            "Through Rachel's window, the Austin skyline glows. The city doesn't know what you know.",
            "Your phone buzzes. An email from IT: 'Scheduled task #303 — status: completed.'",
        ],
        "exits": {},
    },
}


# -- Step guidance text (re-exported from season2_game for convenience) -------

from core.season2_game import S2_STEP_TEXT, S2_OBJECTIVE_FOCUS, S2_CLIFFHANGERS
