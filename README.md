# NEXUS

**Learn SQL by solving a corporate fraud mystery.**

NEXUS is a narrative-driven game that teaches SQL (and eventually Python) through an interactive investigation. You play as Alex Chen, a junior data analyst who discovers a $1.87 million embezzlement scheme on their first day at Nexus Analytics Corp.

No slides. No lectures. You write real SQL queries against a live database to uncover the fraud.

## Quick Start

```bash
# Clone and run
git clone https://github.com/michaelnocito/nexus-sql-mystery.git
cd nexus-sql-mystery
pip install -r requirements.txt
python main.py
```

**Requirements:** Python 3.10+ and PySide6. Windows recommended (uses `winsound` for audio cues).

## What You'll Learn

**Season 1: "The Audit"** (available now)
- `SELECT`, `FROM`, `WHERE` — querying tables
- `COUNT`, `SUM` — aggregate functions
- `GROUP BY`, `ORDER BY` — sorting and grouping
- `JOIN` — connecting tables
- `IN` — matching lists of values
- Primary keys, foreign keys, and how data links together

Each concept is taught through the investigation. You don't memorize syntax — you use it to catch a thief.

## Features

- **Real SQL execution** — your queries run against a live SQLite database
- **13 guided objectives** across 6 investigation scenes
- **Concept cards** — unlock SQL reference cards as you progress
- **The Analyst's Field Guide** — collectible documents that summarize each chapter
- **SQL autocomplete** — Tab-completion for keywords, tables, and columns
- **Progressive hints** — story-style nudges that escalate to full solutions
- **Cliffhanger endings** — each episode ends with a dramatic teaser
- **Auto-save** — pick up where you left off

## Seasons Roadmap

| Season | Title | Skills | Status |
|--------|-------|--------|--------|
| 1 | The Audit | SQL fundamentals | Available |
| 2 | The Ghost in the Machine | Python basics + SQL | Planned |
| 3 | The Network | Advanced SQL + pandas | Planned |
| 4 | The Reveal | Advanced Python + SQL | Planned |

## Tech Stack

- **PySide6** — Qt for Python (LGPL)
- **SQLite** — both game engine and teaching tool
- **QPainter** — vector scene illustrations (no image assets)

## License

MIT

---

*Built with SQL, coffee, and a healthy suspicion of shell companies.*
