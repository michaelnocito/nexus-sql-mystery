# NEXUS

### Learn SQL by solving a corporate fraud mystery.

A narrative-driven game by [Michael Nocito](https://github.com/michaelnocito).

<!--
VISUAL PLACEMENT 1 — Hero banner / gameplay screenshot
Future path: docs/images/hero-banner.png
Alt text: NEXUS — learn SQL by investigating corporate fraud
To create: a wide screenshot (~1600x900) showing the game in action —
scene art on the left, narrative + SQL editor on the right, concept card
popup visible. Capture during a mid-game moment with clues in the sidebar.
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

Things get weird around 6pm. The office empties out. Your monitor flickers.
A query you didn't type appears on screen for half a second.

Day one isn't over yet.

---

## See It In Action

<!--
VISUAL PLACEMENT 2 — Gameplay GIF or screenshot
Future path: docs/images/gameplay.gif (or .png)
Alt text: Running a SQL query in NEXUS and discovering a clue
To create: a 10-15 second GIF of typing a query, seeing results,
and the celebration toast + concept card popup. Or a clean PNG of
mid-game state showing narrative, SQL results, and clue sidebar.
When ready, replace this comment with:
![Running a SQL query in NEXUS and discovering a clue](docs/images/gameplay.gif)
-->

You type real SQL. The game runs it against a live SQLite database.
When your query uncovers something, the story advances — you get a clue,
a concept card explaining what you just learned, and a nudge toward the
next piece of the puzzle.

No right/wrong binary. No fill-in-the-blank. You investigate.

---

## New to GitHub? Start Here

GitHub is where this project lives online. To play it, you download
a copy onto your own computer — that's called **cloning a repository**.
In plain terms: you grab the project files so you can run them locally.

Set up these three things once, and you're ready:

**Step 1 — Install Git**
Git is the tool that lets your computer talk to GitHub and download files.
-> [git-scm.com/downloads](https://git-scm.com/downloads) — download and run the installer. Default settings are fine.

**Step 2 — Install Python 3**
Python is the programming language NEXUS runs on.
-> [python.org/downloads](https://python.org/downloads) — grab the latest version.
> On Windows: check the box that says **"Add Python to PATH"** during install.
> It's easy to miss, and things won't work without it.

**Step 3 — Open a terminal**
The terminal is the text window where you type commands to run the game.
- **Windows:** search *PowerShell* in the Start menu
- **Mac:** search *Terminal* in Spotlight
- **VS Code:** press `` Ctrl + ` ``

Once all three are ready, run the steps below.

---

## Windows Quickstart

Copy each block into PowerShell, one after the other.

**1. Clone the repo**

```powershell
git clone https://github.com/michaelnocito/nexus-sql-mystery.git C:\Projects\nexus-sql-mystery
cd C:\Projects\nexus-sql-mystery
```

> **Why `C:\Projects\` instead of Desktop or Documents?**
> Desktop and Documents usually sync to OneDrive automatically. OneDrive
> can show a file as present before it's fully downloaded — and when
> Python tries to open it, you get a confusing error even though the
> file looks right there. `C:\Projects\` is local-only and always reachable.

**2. Install requirements**

```powershell
pip install -r requirements.txt
```

**3. Play**

```powershell
python main.py
```

The game starts. You're Alex Chen. Day one. Good luck.

> The game auto-saves your progress. Type `reset` in the game to start fresh.

---

## Mac / Linux Setup

```bash
git clone https://github.com/michaelnocito/nexus-sql-mystery.git ~/Projects/nexus-sql-mystery
cd ~/Projects/nexus-sql-mystery
pip install -r requirements.txt
python main.py
```

> **Platform note:** NEXUS is built and tested on Windows. Audio cues use
> `winsound` which is Windows-only — the game runs fine without them on
> Mac/Linux, you just won't hear the beeps. If something trips you up,
> an issue or PR is welcome.

---

## What You'll Learn

Season 1 teaches SQL fundamentals through 13 guided objectives across 6 scenes.
By the end, you'll have used every one of these in a real investigation:

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
| Primary / foreign keys | How tables relate | Understanding why `vendor_id` matters |

You don't memorize syntax. You use it to catch a thief.

> **📘 Want a standalone reference?** The **[SQL Foundations Guide](docs/sql-foundations.md)**
> covers every concept above with detailed explanations, syntax examples,
> a quick reference card, 16 practice exercises, and a full glossary.
> Works on its own even if you don't play the game.

---

## Features

- **Real SQL execution** — your queries run against a live SQLite database
- **13 guided objectives** across 6 investigation scenes
- **Concept cards** — unlock SQL reference cards as you progress
- **The Analyst's Field Guide** — collectible documents that recap each chapter
- **SQL autocomplete** — Tab-completion for keywords, tables, and columns
- **Progressive hints** — story-style nudges that escalate to full solutions
- **Story So Far** — every concept card shows a running recap of your investigation
- **Celebrations** — toast banners, particle effects, and career motivation messages
- **Cliffhanger endings** — each episode ends with a dramatic teaser
- **Spirit guide** — Sam drops contextual tips when you're stuck
- **Auto-save** — pick up where you left off
- **Keyboard shortcuts** — Ctrl+Enter run, Ctrl+H hint, Ctrl+S solution, Ctrl+D copy
- **[SQL Foundations Guide](docs/sql-foundations.md)** — standalone reference doc with exercises to reinforce what you learned

---

## Seasons Roadmap

NEXUS is one game built in seasons — each season adds new skills,
new story, and a new collectible document. All seasons ship in this repo.

| Season | Title | Skills | Story | Status |
|--------|-------|--------|-------|--------|
| 1 | **The Audit** | SQL fundamentals | Corporate fraud, $1.87M embezzlement scheme | **Available now** |
| 2 | **The Ghost in the Machine** | Python basics + SQL | Supernatural twist — server room anomalies, data that shouldn't exist | Planned |
| 3 | **The Network** | Advanced SQL + pandas | Cross-company investigation, connected conspiracies | Planned |
| 4 | **The Reveal** | Advanced Python + SQL | Grand conspiracy, full supernatural reveal | Planned |

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
- **QPainter** — vector scene illustrations (no image assets needed)

---

## Project Structure

```text
nexus/
├── main.py                          <- launch the game
├── requirements.txt                 <- pip install -r requirements.txt
├── core/
│   ├── game.py                      <- game state, objectives, hints, save/load
│   ├── db.py                        <- SQLite interface + seed data
│   ├── scenes.py                    <- story text, step guidance, cliffhangers
│   ├── codex.py                     <- SQL concept definitions
│   └── collectibles.py             <- Field Guide page content
├── ui/
│   ├── main_window.py               <- app shell, wires everything together
│   ├── cmd_panel.py                 <- narrative output + SQL editor
│   ├── scene_view.py                <- QPainter scene illustrations + clue sidebar
│   ├── sql_editor.py                <- autocomplete SQL editor widget
│   ├── concept_popup.py             <- concept card dialog
│   ├── hud.py                       <- top bar (scene, progress, feature buttons)
│   ├── codex_panel.py               <- browsable concept reference
│   ├── collectibles_panel.py        <- Field Guide document viewer
│   └── celebrations.py             <- toast banners, particles, screen flash
├── data/
│   └── world.db                     <- generated at runtime (auto-seeded)
├── docs/
│   └── sql-foundations.md           <- SQL reference guide + practice exercises
└── README.md                        <- you are here
```

---

## Contributing

Found a bug? Have an idea? Open an issue or send a pull request —
every experience level is welcome.

---

## More Tools

**[Spreadsheet Cleaner](https://github.com/michaelnocito/spreadsheet-cleaner)** —
A Python learning project where you build a real data-cleaning tool in three layers.
Pairs well with NEXUS if you're learning both SQL and Python. Start with NEXUS for
SQL, then move to Spreadsheet Cleaner for Python — or the other way around.

**[RecordForge](https://github.com/michaelnocito/recordforge)** —
Generate fictional PDFs, Word docs, HTML files, and Excel datasets for testing, QA, and demos.
Free Windows app, no Python required.

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
