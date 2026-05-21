# NEXUS

### Learn SQL by solving a corporate fraud mystery.

A narrative-driven game by [Michael Nocito](https://www.linkedin.com/in/michaelnocito).

**[🌐 nexus-sql-mystery website](https://michaelnocito.github.io/nexus-sql-mystery/)** &nbsp;·&nbsp; [Releases](https://github.com/michaelnocito/nexus-sql-mystery/releases) &nbsp;·&nbsp; [SQL Foundations Guide](https://github.com/michaelnocito/nexus-sql-mystery/blob/master/docs/sql-foundations.md)

<!--
VISUAL PLACEMENT 1 — Hero banner / gameplay screenshot
Future path: docs/images/hero-banner.png
Alt text: NEXUS — learn SQL by investigating corporate fraud
To create: a wide screenshot (~1600x900) showing the game in action —
3-column layout visible: dialogue thread left, cartoon terminal center, investigation log right.
When ready, replace this comment with:
![NEXUS — learn SQL by investigating corporate fraud](docs/images/hero-banner.png)
-->

---

It's your first day at Nexus Analytics Corp. You're a junior data analyst.
Nobody showed you where the coffee is. Nobody showed you where anything is.

By lunch you'll discover $1.87 million in fraudulent payments. Two shell
companies. One CFO. Thirteen months of fake invoices charged to a department
called "Special Projects." And the only tool you have is SQL.

No slides. No lectures. You write real queries against a live database,
and the story moves forward when you find something. Every `SELECT`,
every `WHERE`, every `JOIN` — they're not exercises. They're evidence.

Things get weird after you close the Webb case. The building empties out.
The server logs show queries running at 3:03am when nobody's in the building.
A deleted employee's record keeps coming back from the dead.

Day one isn't over yet.

---

## See It In Action

<!--
VISUAL PLACEMENT 2 — Gameplay GIF or screenshot
Future path: docs/images/gameplay.gif (or .png)
Alt text: Running a SQL query in NEXUS and discovering a clue
To create: a 10-15 second GIF of typing a query in the cartoon terminal,
seeing results, and a concept unlock with Matrix rain animation.
When ready, replace this comment with:
![Running a SQL query in NEXUS and discovering a clue](docs/images/gameplay.gif)
-->

You type real SQL into a cartoon cel-shaded terminal. The game runs it against
a live SQLite database. When your query uncovers something, the story advances —
Diana and Sam react in the dialogue thread, you get a concept card explaining
what you just learned, and a nudge toward the next piece of the puzzle.

No right/wrong binary. No fill-in-the-blank. You investigate.

---

## Quick Start

```bash
git clone https://github.com/michaelnocito/nexus-sql-mystery.git
cd nexus-sql-mystery
pip install -r requirements.txt
python main.py
```

**Requirements:** Python 3.10+ and PySide6. Windows recommended (uses `winsound` for audio cues).

> The game auto-saves your progress. Type `reset` in the terminal to start fresh.

---

## The UI

The game uses a **3-column layout**:

| Column | What It Shows |
|--------|---------------|
| **Left — Dialogue thread** | Diana and Sam talk. Scene narration, hints, recall gate prompts, and your command echoes all flow here as chat bubbles. |
| **Center — Cartoon terminal** | A cel-shaded CRT monitor. Type queries here. SQL errors and Python errors appear only in this panel — never in the dialogue thread. |
| **Right — Investigation log** | Completed objectives, clues found, and your progress through the case. |

**Hint system (2-click):** Press the hint button once and Sam drops a story-style nudge. Press it again and a full answer card appears with a copy button. Between scenes, a **recall gate** asks you to recall a concept you just used — it validates your SQL text directly (no execution needed) and advances you on 2 misses anyway.

**Concepts panel:** When you unlock a new SQL concept, a Matrix rain animation plays, a Morpheus-style message appears, and the "◆ Concepts" HUD button flashes green. Click it to browse every concept card you've unlocked.

---

## What You'll Learn

### Season 1 — The Audit (16 objectives, 6 scenes)

SQL fundamentals, taught by catching a CFO:

| Concept | What It Does | When You'll Use It |
|---|---|---|
| `SELECT` / `FROM` | Pull data from a table | Reading the employee roster |
| `WHERE` | Filter rows by condition | Finding unverified vendors |
| `COUNT` | Count rows | Headcount for Sam in accounting |
| `SUM` | Add up values | Totalling payments to a ghost company |
| `GROUP BY` | Bundle rows and aggregate | Ranking vendors by total spend |
| `ORDER BY` | Sort results | Spotting the escalation pattern |
| `JOIN` | Connect two tables | Linking vendor names to transaction IDs |
| `IN` | Match a list of values | Querying both shell companies at once |

You don't memorize syntax. You use it to catch a thief.

### Season 2 — The Ghost in the Machine (12 objectives, 6 scenes)

Advanced SQL, taught by chasing a phantom:

| Concept | What It Does | When You'll Use It |
|---|---|---|
| `LIKE` | Pattern-match text | Finding the 3:03am log entries |
| `strftime` | Extract date/time parts | Proving the timestamp is exactly 03:03 |
| Subqueries | A query inside a query | Finding a row above the table's own average |
| `GROUP BY` + `HAVING` | Aggregate with a filter | Proving the time pattern isn't coincidence |
| `SUBSTR` / `GROUP_CONCAT` | String surgery | Reading the hidden message in the logs |
| `CASE WHEN` | Conditional column labels | Tagging every row PHANTOM or normal |

Each concept is taught twice — once as an introduction, once as varied practice in a new context.

---

## Features

- **Real SQL execution** — queries run against a live SQLite database
- **3-column layout** — dialogue thread, cartoon terminal, investigation log
- **Cartoon cel-shaded terminal** — the game's visual centerpiece
- **16 Season 1 objectives** across 6 investigation scenes
- **12 Season 2 objectives** across 6 server-room scenes
- **◆ Concepts panel** — unlock SQL reference cards as you progress; Matrix rain plays on each unlock
- **The Analyst's Field Guide** — collectible documents that recap each chapter
- **SQL autocomplete** — Tab-completion for keywords, tables, and columns
- **2-click hints** — Sam tip on click 1, full answer card with copy button on click 2
- **Recall gates** — between-scene spaced-retrieval quizzes (2-miss safety net)
- **Error isolation** — SQL and Python errors route to the terminal only, never the dialogue thread
- **Celebrations** — toast banners, particle effects, and career motivation messages
- **Auto-save** — pick up where you left off
- **Keyboard shortcuts** — Ctrl+Enter run, Ctrl+H hint, Ctrl+S solution, Ctrl+D copy

---

## Seasons Roadmap

NEXUS is one game built in seasons — each season adds new skills,
new story, and a new collectible document. All seasons ship in this repo.

| Season | Title | Skills | Story | Status |
|--------|-------|--------|-------|--------|
| 1 | **The Audit** | SQL fundamentals | Corporate fraud, $1.87M embezzlement scheme | **Available now** |
| 2 | **The Ghost in the Machine** | Advanced SQL | Server anomalies, a phantom cron job, a dead man's switch | **Available now** |
| 3 | **The Network** | Advanced SQL + pandas | Cross-company investigation, connected conspiracies | Planned |
| 4 | **The Reveal** | Advanced Python + SQL | Grand conspiracy, full reveal | Planned |

Each season launch = a new [GitHub Release](https://github.com/michaelnocito/nexus-sql-mystery/releases).

---

## Who This Is For

- **SQL beginners** who learn best by doing real things, not watching tutorials
- **Career changers** studying data analytics who want something more engaging than textbook exercises
- **CS students** looking for a portfolio project that's actually interesting
- **Teachers and bootcamps** who want a guided, narrative SQL lab
- **Anyone** who liked detective games growing up and wouldn't mind learning a job skill while playing one

No prior SQL experience needed. You bring the curiosity; the game teaches the rest.

---

## Tech Stack

- **PySide6** — Qt for Python (LGPL)
- **SQLite** — both game engine and teaching tool
- **QPainter** — vector scene illustrations and terminal widget (no image assets needed)

---

## Project Structure

```text
nexus/
├── main.py                          <- launch the game
├── requirements.txt                 <- pip install -r requirements.txt
├── core/
│   ├── game.py                      <- GameState: objectives, hints, recall gates, save/load
│   ├── db.py                        <- SQLite interface + seed data (both seasons)
│   ├── scenes.py                    <- Season 1 story text, objectives, hints, recall challenges
│   ├── season2_game.py              <- Season 2 objectives, hints, recall challenges
│   ├── season2_scenes.py            <- Season 2 scene definitions
│   ├── season2_data.py              <- Season 2 DB seed data
│   ├── codex.py                     <- SQL concept definitions (Season 1)
│   ├── season2_codex.py             <- SQL concept definitions (Season 2)
│   ├── collectibles.py              <- Field Guide page content (Season 1)
│   └── season2_collectibles.py     <- Field Guide page content (Season 2)
├── ui/
│   ├── main_window.py               <- app shell, wires everything together
│   ├── cmd_panel.py                 <- 3-column layout: dialogue thread, hint system, error routing
│   ├── terminal_widget.py           <- cartoon cel-shaded monitor widget (SQL input/output)
│   ├── scene_view.py                <- QPainter scene illustrations
│   ├── sql_editor.py                <- autocomplete SQL editor widget
│   ├── hud.py                       <- top bar (scene, progress, ◆ Concepts button)
│   ├── concept_popup.py             <- concept card dialog (Matrix rain → Morpheus → card)
│   ├── portraits.py                 <- character portrait rendering (Diana, Sam, narrator)
│   ├── codex_panel.py               <- browsable concept reference panel
│   ├── collectibles_panel.py        <- Field Guide document viewer
│   └── celebrations.py             <- toast banners, particles, screen flash
├── data/
│   └── world.db                     <- generated at runtime (auto-seeded)
└── README.md                        <- you are here
```

---

## Contributing

Found a bug? Have an idea? Open an issue or send a pull request —
every experience level is welcome.

---

## More from Michael Nocito

**[📊 SQL Prep Kit](https://michaelnocito.github.io/sql-prep-kit/)** —
Learn SQL for analyst interviews by reading every query out loud, line by line.
Browser-based, real SQLite, honest readiness score. No install.

**[🗂️ RecordForge](https://michaelnocito.github.io/recordforge/)** —
Generate fictional PDFs, Word docs, Excel datasets, and HTML files for QA, demos, and ETL testing.
Free Windows app + Python package. No real data, fully offline.

**[🧼 Spreadsheet Cleaner](https://michaelnocito.github.io/spreadsheet-cleaner/)** —
A beginner Python project where you build a real data-cleaning tool layer by layer.
Guided comments throughout. No experience needed.

**[LinkedIn](https://www.linkedin.com/in/michaelnocito)** — data analyst · 8 years enterprise implementation

---

## License

MIT

---

If this project helped you learn something, the best thing you can do is
[star the repo](https://github.com/michaelnocito/nexus-sql-mystery)
— it helps other learners find it.

If you'd like to support the work, a coffee is always appreciated but never expected.

<a href="https://buymeacoffee.com/michaelnocito" target="_blank">
  <img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" height="50">
</a>

---

Built with SQL, coffee, and a healthy suspicion of shell companies. | Maintained by [Michael Nocito](https://github.com/michaelnocito)
