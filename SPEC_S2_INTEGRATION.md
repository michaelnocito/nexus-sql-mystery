# SPEC: Season 2 Integration — "The Ghost in the Machine"
# Status: DRAFT
# Stage: Ready to implement

---

## 1. Goal

Wire the existing Season 2 files into the running NEXUS app so that after
completing Season 1, the player transitions into Season 2 seamlessly.

Season 2 content is fully written. This spec covers integration only —
no new story, objectives, or data.

---

## 2. What exists (Discovery findings)

### Already done — do not rewrite:
- `core/season2_game.py`      — 12 objectives, validators, hints, step text, focus commands, recall challenges, cliffhangers
- `core/season2_scenes.py`    — 6 scenes (server_logs → ghost_records → timestamp → archive → pattern_decoder → the_signal)
- `core/season2_data.py`      — seed function `seed_season2(conn)` adds 3 tables: server_logs, deleted_records, backup_snapshots
- `core/season2_codex.py`     — Python concept cards (variables, loops, list comprehensions, functions, string methods, dicts)
- `core/season2_collectibles.py` — "The Python Codex" (5 pages, one per scene)

### Needs to change:
- `core/game.py`              — currently Season 1 only; needs to know about Season 2 objectives and season state
- `core/db.py`                — needs to call `seed_season2()` when Season 2 begins
- `ui/main_window.py`         — imports only Season 1 assets; needs Season 2 scenes, codex, collectibles
- `core/scenes.py`            — Season 1 scenes only; Season 2 scenes need to be accessible to the router

---

## 3. Integration design

### Season progression model
- A `current_season` field (int: 1 or 2) lives in `save_state`
- Season 1 end = after completing the final Season 1 objective (`confrontation` scene complete)
- Transition trigger: display Season 1 cliffhanger → show "Season 2 begins" card → seed S2 data → load first S2 scene
- No going back to Season 1 after transition (save_state locks it)

### Routing
- `SCENES` dict in `main_window.py` (or a new `ALL_SCENES`) merges S1 + S2 scenes
- `GameState` uses `current_season` to know which objectives/hints/step_text to reference
- Scene art keys already defined in S2 scenes (`server_room`, `desk`, `archive`, `server_room_night`, `coo_office`) — `scene_view.py` needs to paint these if not already

### Codex
- Season 2 concept cards use different IDs (`s2_variables`, `s2_for_loops`, etc.)
- `CodexPanel` needs to display both S1 and S2 unlocked concepts
- `get_concept()` in `core/codex.py` needs to check both S1 and S2 concept sets

### Collectibles
- Season 2 collectible = "The Python Codex" (already in `season2_collectibles.py`)
- `CollectiblesPanel` needs to load the correct collectible based on current season

---

## 4. Acceptance criteria

These are the testable conditions that define "done." Each must pass before
the spec is considered complete.

- [ ] AC1: Running `python main.py` after Season 1 completion shows the Season 2 intro scene (server room, 3:03am logs)
- [ ] AC2: Player can submit Python code (not SQL) in the editor and it executes correctly against `db.query()`
- [ ] AC3: Completing all 2 objectives in Scene 1 (store_result, loop_records) triggers the cliffhanger card and advances to Scene 2
- [ ] AC4: Season 2 codex cards (variables, loops, etc.) appear in the Codex panel after being unlocked
- [ ] AC5: "The Python Codex" collectible pages unlock one per scene in the Collectibles panel
- [ ] AC6: Save/load preserves Season 2 progress — reopening the app resumes the correct S2 scene
- [ ] AC7: Season 1 save data is not corrupted by the Season 2 migration

---

## 5. Constraints (do not touch)

- Do NOT rewrite Season 2 content files — they are correct as-is
- Do NOT change the Season 1 gameplay or objectives
- Do NOT change the UI layout, color palette, or celebration effects
- Do NOT change `world.db` schema — `seed_season2()` already handles safe migration
- Do NOT add a season-select menu — progression is linear

---

## 6. Open questions (decide before coding)

These need answers before implementation starts. Each is a real decision,
not a to-do item.

**Q1: How does the app detect "Season 1 is complete"?**
Options:
  a) Check that all S1 objectives are in the completed list in save_state
  b) Check that the player reached the `confrontation` scene
  → Recommend: (a) — more robust, doesn't depend on scene order

**Q2: Does the Python editor need to change, or does it already accept multi-line Python?**
  - `sql_editor.py` is named for SQL but may already support arbitrary text
  - Need to verify: does `cmd_panel.py` pass input through `exec()` sandbox or SQL parser?
  → Must check before writing any integration code

**Q3: What scene art keys does Season 2 use, and do they exist in `scene_view.py`?**
  - S2 scenes reference: `server_room`, `desk`, `archive`, `server_room_night`, `coo_office`
  - `server_room` and `desk` likely exist from S1; `archive`, `server_room_night`, `coo_office` may not
  → Check `scene_view.py` paint methods before assuming art is ready

---

## 7. Implementation order

Once open questions are resolved, build in this sequence:

1. Answer Q2 (editor mode) — determines how much cmd_panel.py changes
2. Answer Q3 (scene art) — determines if new QPainter scenes need to be drawn
3. Add `current_season` to save_state in `game.py`
4. Merge S1 + S2 scene/objective routing in `game.py` and `main_window.py`
5. Wire `seed_season2()` into `db.py` on season transition
6. Update `CodexPanel` and `CollectiblesPanel` for dual-season content
7. Test AC1 → AC7 in order

---

*Spec written: 2026-05-17*
*Author: Mike + Claude*
