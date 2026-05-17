# SPEC: Season 2 — SQL-Core Redesign
# Status: DRAFT
# Stage: 2 (Spec Writing) — ladder proposed, open questions pending
# Supersedes the Python-primary design of season2_game.py

---

## 1. Goal

Make Season 2's main path **100% SQL** — intermediate SQL that makes a
beginner feel like a real analyst by the end. Python becomes an **optional
side quest** per scene (reusing the 12 Python objectives already built).
Tableau is explicitly OUT — deferred to a future Season 4 spec.

North star: a player who only ever touches SQL finishes Season 2 feeling
like a SQL pro and never feels they skipped required content.

---

## 2. Design principles (locked)

- **Side quests are enrichment, never homework.** Skippable, opt-in, no
  progression penalty, no "you missed this" framing.
- **One concept per objective**, taught in 3 layers:
  1. What it is (one sentence, anchored to a Season 1 SQL concept)
  2. Why this scene needs it (story motivation)
  3. Exact minimal example to type, then the fuller form
- **Story unchanged.** "The Ghost in the Machine" — phantom 3:03am queries,
  the revenant employee record, the dead man's switch. Same beats, solved
  with SQL instead of Python.
- **No Season 3 collision.** S2 stays intermediate. CTEs and window
  functions remain Season 3 territory.

---

## 3. The intermediate-SQL ladder (proposed)

Season 1 taught: SELECT, WHERE, COUNT, SUM, GROUP BY, JOIN, ORDER BY, IN.

Season 2 teaches the natural next tier, one rung per objective:

| Scene | Obj | SQL concept (one per objective) | Story beat it cracks |
|-------|-----|--------------------------------|----------------------|
| 1 Server Logs | s2a | `LIKE` pattern matching | Find the phantom entries by timestamp pattern |
| 1 | s2b | Date/time filtering (`strftime` / `time` slice) | Prove they cluster at 3:03am |
| 2 Ghost Records | s2c | Subquery in `WHERE` | Find deleted_records IDs not in employees |
| 2 | s2d | `HAVING` (filter an aggregate) | The record restored > 10 times |
| 3 Timestamp Analysis | s2e | `GROUP BY` + `HAVING COUNT` | 3:03 is no coincidence — count proves it |
| 3 | s2f | `CASE WHEN` (label rows) | Tag each entry NORMAL vs ANOMALY |
| 4 Archive | s2g | Subquery in `FROM` (derived table) | Compare two backup snapshots |
| 4 | s2h | `IS NULL` / `COALESCE` | Spot the rows tampering left blank |
| 5 Pattern Decoder | s2i | `SUBSTR` / string functions | Extract first letter of each action |
| 5 | s2j | `GROUP_CONCAT` (assemble the message) | Reveal the hidden confession |
| 6 The Signal | s2k | Combine subquery + CASE + date filter | The capstone query |
| 6 | s2l | (no new concept) narrative payoff | "You did this with SQL alone." |

12 SQL objectives, 6 scenes, 2 each — same shape as the current file, so
the integration we already shipped (routing, save, scene art, codex,
collectibles) is REUSED, not rebuilt.

---

## 4. Python side quests

The 12 Python objectives in `season2_game.py` are **not deleted** — they
are demoted to one opt-in side quest per scene, surfaced in the **Pro Panel**
(the feature from the bonus-challenge discussion). Framing: *"A data analyst
would also automate this in Python — want to see how? Optional."*

Reuses existing Python step-text/hints/validators with light edits to the
intro framing only.

---

## 5. Scope

### Changes (content + light wiring):
- `core/season2_game.py` — rewrite S2_OBJECTIVES (SQL validators), all
  S2_STEP_TEXT, S2_HINTS, S2_OBJECTIVE_FOCUS, S2_RECALL_CHALLENGES to the
  SQL ladder + 3-layer model
- `core/season2_codex.py` — replace Python concept cards with SQL concept
  cards (LIKE, subquery, HAVING, CASE, date functions, etc.)
- New: side-quest data structure (Python objectives moved here) + Pro Panel
  UI (separate sub-spec / later task)
- `core/season2_data.py` — verify seed data supports every SQL objective
  (timestamps, NULLs, action strings must make the queries solvable)

### Does NOT change:
- The Season 2 integration plumbing (game.py routing, db seeding, scene
  art, save/load) — already shipped on season2-dev, reused as-is
- The story / scene intros / cliffhangers / collectible narrative
- Season 1
- Season 3/4 plans

---

## 6. Acceptance criteria

- [ ] AC1: Every main-path objective is solvable with SQL only — no Python required
- [ ] AC2: Each objective teaches exactly ONE new SQL concept, 3-layer scaffolded
- [ ] AC3: Seed data in season2_data.py makes all 12 SQL objectives solvable (verified by writing a reference solution per objective)
- [ ] AC4: A player using zero side quests reaches the finale with no blocked progression and no "missed content" messaging
- [ ] AC5: Each scene exposes exactly one optional Python side quest in the Pro Panel; skipping has zero gameplay effect
- [ ] AC6: SQL concept cards appear in the Codex; Python side-quest completion grants a distinct Pro badge
- [ ] AC7: Difficulty curve verified — no objective introduces more than one new concept beyond the previous

---

## 7. Open questions (decide before build)

**Q1: SQLite function coverage.** The engine runs SQLite. `strftime`,
`SUBSTR`, `GROUP_CONCAT`, `COALESCE` are all native SQLite — confirmed
available. But does the current `season2_data.py` timestamp format support
`strftime`? (Needs `'YYYY-MM-DD HH:MM:SS'` text — verify.)
→ Must check season2_data.py before finalizing the ladder.

**Q2: Is `GROUP_CONCAT` (s2j) too clever for intermediate?** Alternative:
keep the message-decoding as the Python side quest only, and make s2j a
simpler aggregate. → Recommend: keep GROUP_CONCAT but make it the gentlest
possible form; it's a satisfying "whoa" moment that sells SQL power.

**Q3: Pro Panel — build now or stub now?** The SQL rewrite and the Pro
Panel are separable. → Recommend: ship SQL-core first (its own spec/PR),
then Pro Panel + side quests as a second spec. Keeps each change reviewable.

---

## 8. Implementation order (once Q1–Q3 resolved)

1. Resolve Q1 — audit season2_data.py for SQL solvability + timestamp format
2. Write one reference SQL solution per objective (proves AC3 before coding)
3. Rewrite season2_game.py: validators → step text → hints → focus → recall
4. Rewrite season2_codex.py: SQL concept cards
5. Verify AC1–AC4 by playthrough (SQL-only path)
6. (Second spec) Pro Panel + Python side quests + AC5/AC6

---

*Spec written: 2026-05-17*
*Author: Mike + Claude*
