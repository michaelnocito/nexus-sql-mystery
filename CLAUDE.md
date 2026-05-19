# NEXUS — Developer Reference

## Running the Game

```
python main.py
```

Run from project root. The SQLite database (`data/world.db`) is auto-created and seeded on first launch. Type `reset` in the game terminal to wipe save state and start over.

---

## File Structure

```
core/
  game.py               GameState class — the single source of truth for all runtime state
  db.py                 DatabaseInterface — SQLite connection, query execution, seed data
  scenes.py             Season 1: OBJECTIVES list, S1_YOUR_MOVE, S1_HINTS, S1_RECALL_CHALLENGES,
                        S1_SCENE_WHY, S1_RESULT_REACTION, S1_OBJECTIVE_FOCUS, scene constants
  season2_game.py       Season 2: same structure as scenes.py for S2 content
  season2_scenes.py     Season 2: S2_SCENES dict (scene metadata, intros, ambient lines)
  season2_data.py       Season 2: DB seed rows (server_logs, deleted_records, backup_snapshots)
  codex.py              Season 1 SQL concept definitions (shown in ◆ Concepts panel)
  season2_codex.py      Season 2 SQL concept definitions
  collectibles.py       Season 1 Field Guide pages
  season2_collectibles.py  Season 2 Field Guide pages

ui/
  main_window.py        App shell — creates all panels, wires GameState callbacks,
                        triggers concept flash and post-load scene check
  cmd_panel.py          3-column layout: left=dialogue thread, center=terminal widget,
                        right=investigation log. Owns hint system, error routing,
                        recall gate intercept, dialogue bubble rendering.
  terminal_widget.py    Cartoon cel-shaded CRT monitor widget — SQL input/output centerpiece
  hud.py                Top bar: scene title, progress bar, HUD buttons including
                        "◆ Concepts" (flashes green on concept unlock)
  portraits.py          Character portrait QPainter rendering (Diana, Sam, narrator aliases)
  scene_view.py         QPainter scene illustrations (desk, server room, etc.)
  sql_editor.py         CodeEditor with Tab autocomplete for SQL keywords/tables/columns
  concept_popup.py      Concept card dialog with Matrix rain → Morpheus message → card reveal
  codex_panel.py        Browsable concept reference (all unlocked cards)
  collectibles_panel.py Field Guide document viewer
  celebrations.py       Toast banners, particle effects, screen flash

data/
  world.db              Auto-seeded SQLite DB (gitignored)
```

---

## Key Systems

### GameState (`core/game.py`)

Central state object. Constructed once in `MainWindow`, never replaced.

- `self.scene` — current scene id string
- `self.completed` — list of completed objective ids (append-only, drives all unlock logic)
- `self.current_season` — 1 or 2
- `self._recall_pending` — active recall gate challenge dict, or None
- `self._recall_done` — set of scene ids whose exit recall gate has been cleared
- `self.clues` — list of discovered clue strings

**Callbacks (set by MainWindow after construction):**

| Callback | Fires when |
|----------|-----------|
| `on_scene_change(scene_id)` | Player moves to a new scene |
| `on_story(kind, text)` | STORY beat — kind is `why`, `beat`, or `recall` |
| `on_briefing(goal, move)` | New objective briefing |
| `on_progress(objective_id)` | Objective completed |
| `on_status(label, value)` | HUD stat update |
| `on_season_change(season)` | Season 1 → Season 2 transition |

**Key methods:**

- `on_query(sql, result)` — called by DatabaseInterface after every query; runs validator chain
- `on_exec(code, output)` — called for Python execution results
- `_check_scene_unlock()` — advances scene when all objectives done; inserts recall gate if needed
- `_handle_recall(sql)` — validates recall gate answer from SQL text (keyword match, no DB exec)
- `get_recall_challenge()` — returns the challenge dict for the most recently completed concept
- `emit_scene_state()` — re-emits WHY + briefing (called on load and scene change)
- `_save()` / `_load()` — SQLite persistence including `recall_done` column migration

### DatabaseInterface (`core/db.py`)

- `query(sql)` → list of Row objects; calls `game.on_query(sql, result)` after execution
- `exec_python(code)` → string output; calls `game.on_exec(code, output)`
- Seeds Season 1 tables on first connect; seeds Season 2 tables when `transition_to_season2()` is called

### Scene / Objective Flow

1. `game.scene` determines which objectives are active (filtered from OBJECTIVES by scene id)
2. Player types SQL → `db.query()` → `game.on_query()` → validators run in order
3. First passing validator marks that objective complete, fires `on_progress`, emits story beat
4. `_check_scene_unlock()` runs — if all scene objectives done, either:
   - Inserts a recall gate (`_recall_pending` set, `on_story("recall", ...)` fires), or
   - Advances to next scene (`_advance_to_scene()`)
5. At end of Season 1: `transition_to_season2()` → seeds S2 DB, loads S2 first scene

### Hint System (2-click, `ui/cmd_panel.py`)

- Click 1: Sam tip — first hint string from `S1_HINTS[obj_id]` (or S2), shown as Sam dialogue bubble
- Click 2: Full answer card — `_make_answer_card(answer)` widget with copy button
- Special case: if `_recall_pending` is active, skip straight to the answer card (player is already at a gate)

### Recall Gate

Between-scene SQL quiz. Uses hypothetical tables (e.g. `logs`, `sales`) that don't exist in the game DB.

**Critical:** `cmd_panel.py` intercepts the submit path before any DB call:
```python
if self._game._recall_pending is not None:
    self._game._handle_recall(raw)
    return   # never execute the fake-table SQL
```

`_handle_recall` does keyword matching on the raw SQL text. 2 misses → reveal + auto-pass.
The scene whose exit gate cleared is recorded in `_recall_done` (persisted).

### Concept Unlock + ◆ Concepts Flash

When an objective with a new `concept` id completes:
1. `concept_popup.py` plays Matrix rain → Morpheus message → concept card
2. `main_window.py` calls `hud.flash_concepts_button()` — green pulse animation on the HUD button
3. HUD button label is "◆ Concepts" (renamed from "Codex" in this session)

### Error Routing

All SQL and Python errors route to the terminal widget (`terminal_widget.py`) only.
They are never appended to the left-panel dialogue thread.

---

## Adding a New Scene (Season 1 example)

1. Add a scene constant to `core/scenes.py` (e.g. `SCENE_NEW_PLACE = "new_place"`)
2. Add objective dicts to `OBJECTIVES` in `core/game.py` with `"scene": SCENE_NEW_PLACE`
3. Add narrative content to `scenes.py`: `S1_YOUR_MOVE`, `S1_HINTS`, `S1_RECALL_CHALLENGES`,
   `S1_SCENE_WHY`, `S1_RESULT_REACTION`, `S1_OBJECTIVE_FOCUS`
4. Add the scene to `S1_SCENE_ORDER` list in `core/game.py` (controls advancement order)
5. Add a scene dict to `SCENES` in `core/scenes.py` (title, art_key, intro, objectives, ambient, exits)
6. Add art key to `ui/scene_view.py` painter dispatch if needed

For Season 2, follow the same pattern in `season2_game.py` and `season2_scenes.py`.

---

## Season 2 Notes

Season 2 shares `game.py`'s unified flow (same `_check_scene_unlock`, same recall gate logic,
same `_recall_done` persistence). It does NOT have its own separate game engine.

`game._content()` switches season data sources:
```python
if self.current_season == 2:
    from core import season2_game as M
    ...
```

Season 2 DB tables: `server_logs`, `deleted_records`, `backup_snapshots` — seeded in `db.py`
when `transition_to_season2()` is called.

Season 2 recall challenges also use hypothetical tables (`logs`, `sales`, etc.) — already
covered by the same `cmd_panel.py` intercept as Season 1.

---

## Spec Files

The `SPEC_*.md` files in the project root are design documents from development.
They are not part of the game runtime and can be archived or deleted once the feature ships.
