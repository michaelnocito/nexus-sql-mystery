# core/collectibles.py
# Collectible Documents — "The Analyst's Field Guide"
#
# One document unlocks per completed scene. By the end of Season 1,
# the player has assembled a 5-page field guide that summarizes
# every investigative technique they learned.
#
# The confrontation scene doesn't unlock a page — it IS the payoff.

from core.game import (
    SCENE_YOUR_DESK, SCENE_DB_TERMINAL, SCENE_HR_FILES,
    SCENE_CFO_DEPT, SCENE_AUDIT_TRAIL, SCENE_CONFRONTATION,
)


FIELD_GUIDE_PAGES = [
    {
        "id":       "page_1_tables",
        "scene":    SCENE_YOUR_DESK,
        "title":    "Page 1: Know Your Data",
        "subtitle": "Before you investigate, you observe.",
        "body": (
            "Every investigation starts the same way: you sit down,\n"
            "open the database, and ask the simplest question possible.\n\n"
            "What tables exist? What columns do they have? How many rows?\n\n"
            "SELECT, FROM, COUNT — these aren't just keywords.\n"
            "They're the analyst's equivalent of walking the crime scene\n"
            "before you touch anything.\n\n"
            "Rule #1: Never write a complex query until you've\n"
            "looked at the raw data first."
        ),
        "skill_summary": "SELECT * FROM  |  COUNT(*)  |  db.tables()",
    },
    {
        "id":       "page_2_patterns",
        "scene":    SCENE_DB_TERMINAL,
        "title":    "Page 2: Follow the Money",
        "subtitle": "Patterns hide in aggregates.",
        "body": (
            "Raw transaction logs are noise. Thousands of rows\n"
            "that blur together. But GROUP BY turns noise into signal.\n\n"
            "Bundle transactions by vendor. Add up the amounts.\n"
            "Sort by total, biggest first. Suddenly, outliers scream.\n\n"
            "Then verify: is the vendor real? WHERE verified = 0.\n"
            "JOIN to attach names to IDs.\n\n"
            "Rule #2: If a number looks wrong, it probably is.\n"
            "Trust your instinct, then prove it with data."
        ),
        "skill_summary": "GROUP BY + SUM  |  WHERE  |  JOIN  |  ORDER BY DESC",
    },
    {
        "id":       "page_3_people",
        "scene":    SCENE_HR_FILES,
        "title":    "Page 3: Follow the People",
        "subtitle": "Data doesn't commit fraud. People do.",
        "body": (
            "Money flows through systems, but it's approved by humans.\n"
            "The approved_by column is a foreign key — it points\n"
            "to a person in the employees table.\n\n"
            "GROUP BY approved_by. COUNT the approvals.\n"
            "One ID dominates? That's your lead.\n\n"
            "WHERE id = 4. One row. One name. One answer.\n\n"
            "Rule #3: Always follow the chain from transaction\n"
            "to approval to person to department.\n"
            "The trail is in the foreign keys."
        ),
        "skill_summary": "Foreign Keys  |  WHERE id =  |  ORDER BY budget DESC",
    },
    {
        "id":       "page_4_evidence",
        "scene":    SCENE_CFO_DEPT,
        "title":    "Page 4: Build the Evidence",
        "subtitle": "Gut feelings don't go in reports. Numbers do.",
        "body": (
            "You suspect fraud. Now prove it.\n\n"
            "SUM + WHERE gives you the total damage.\n"
            "ORDER BY date reveals the timeline.\n\n"
            "When amounts escalate month over month — $87K, $112K,\n"
            "$180K, $243K — that's not a flat retainer.\n"
            "That's someone getting bolder.\n\n"
            "Rule #4: Escalation patterns are the fingerprint\n"
            "of confidence. The longer it goes undetected,\n"
            "the bigger the numbers get."
        ),
        "skill_summary": "SUM + WHERE  |  ORDER BY date  |  Escalation Detection",
    },
    {
        "id":       "page_5_case",
        "scene":    SCENE_AUDIT_TRAIL,
        "title":    "Page 5: Close the Case",
        "subtitle": "One query to rule them all.",
        "body": (
            "The final audit combines everything.\n\n"
            "IN (4, 7) captures both shell companies in one clause.\n"
            "SUM gives the grand total. GROUP BY breaks it down.\n\n"
            "You started with db.tables(). You end with a\n"
            "complete fraud report: $1,869,500 across two vendors,\n"
            "thirteen months, all approved by one person.\n\n"
            "Rule #5: The best analysts don't just find problems.\n"
            "They present them so clearly that the solution\n"
            "becomes obvious to everyone in the room."
        ),
        "skill_summary": "IN clause  |  SUM across groups  |  Complete Audit",
    },
]


# Fast lookup
PAGES_BY_SCENE = {p["scene"]: p for p in FIELD_GUIDE_PAGES}
PAGES_BY_ID = {p["id"]: p for p in FIELD_GUIDE_PAGES}


def unlocked_pages(completed_scenes: list[str]) -> list[dict]:
    """Return pages unlocked by scenes the player has completed."""
    return [p for p in FIELD_GUIDE_PAGES if p["scene"] in completed_scenes]


def is_page_unlocked(page_id: str, completed_scenes: list[str]) -> bool:
    page = PAGES_BY_ID.get(page_id)
    return page is not None and page["scene"] in completed_scenes
