# SPEC: Season 1 — Narrative Fusion + Varied Practice
# Status: DRAFT — needs go/no-go before build
# Mirrors SPEC_NARRATIVE_FUSION.md (S2), applied to Season 1 ("The Audit").
# Lands in v2.0.0 via normal merge season2-dev -> master (NEVER overwrite;
# v1.0.0 stays as a historical release/tag).

---

## 1. Goal

Bring Season 1 up to the same standard as the reworked Season 2:
- 3-region UI (STORY panel / BRIEFING / mechanical CONSOLE)
- Per-objective SETUP → YOUR MOVE → RESULT-REACTION fusion
- VARIED PRACTICE: all 8 S1 skills, each practiced **twice** in a
  slightly different context with escalating difficulty (~16 objectives)
- Direction text at the recall-gate clarity bar (feedback_nexus_clarity)
- Between-scene recall gates (non-punishing)

Story unchanged: "The Audit" — $1.87M fraud, Marcus Webb, Apex + Pinnacle.

---

## 2. The 8 skills × 2 reps (grounded in real S1 seed data)

Tables: employees(10) · departments(6) · vendors(8) · transactions(~28).

| Skill | Rep A (context) | Rep B (varied context) |
|-------|-----------------|------------------------|
| SELECT/FROM | list the tables / `SELECT * FROM employees` | `SELECT name,salary FROM employees` (specific cols) |
| WHERE | `vendors WHERE verified = 0` (the two shells) | `employees WHERE id = 4` (lookup Webb — diff col/type) |
| COUNT | `COUNT(*) FROM employees` (headcount) | `COUNT(*) ... WHERE vendor_id = 4` (count Apex payments) |
| SUM | `SUM(amount) WHERE vendor_id = 4` (Apex total) | `SUM(amount) WHERE department='Special Projects'` |
| GROUP BY | `vendor_id, SUM(amount) GROUP BY vendor_id` | `approved_by, COUNT(*) GROUP BY approved_by` (→ Webb) |
| JOIN | `transactions JOIN vendors ON vendor_id=id` | `transactions JOIN employees ON approved_by=id` |
| ORDER BY | `departments ORDER BY budget DESC` (Special Proj top) | `... WHERE vendor_id=4 ORDER BY date` (escalation) |
| IN | `transactions WHERE vendor_id IN (4,7)` | `employees WHERE department IN ('Finance','Executive')` |

16 objectives. Each skill's card shows on Rep A only; Rep B is silent
varied practice ("you've done this — here's the twist"). Every objective
verified solvable against the seed data before coding (AC, like S2).

---

## 3. Scene distribution (keep the existing 6 scenes — no new art/story)

~2–3 objectives per scene, mapped to the existing fraud beats:

- **your_desk** (onboarding): SELECT/FROM·A, SELECT/FROM·B, COUNT·A
- **db_terminal** (the log): GROUP BY·A, WHERE·A, JOIN·A
- **hr_files**: WHERE·B (Webb), GROUP BY·B (approver), ORDER BY·A (budgets)
- **cfo_dept**: SUM·A (Apex), COUNT·B (Apex count), ORDER BY·B (escalation)
- **audit_trail**: IN·A (4,7), SUM·B (Special Projects), JOIN·B (approver)
- **confrontation**: IN·B, final synthesis beat

Existing S1 scene art is reused unchanged. 6 scenes, 16 objectives.

---

## 4. Engine/UI scope — unify, don't fork

The STORY/BRIEFING/recall system already exists but is currently
S2-only; S1 still runs the old single-feed path (game.py has
`if current_season == 1:` legacy branches in `_advance_to_scene`,
`_render_current_scene`, `_emit_scene_state`, `_check_scene_unlock`
recall, plus old console `on_output(style="scene"/"guidance")`).

Plan: **generalise the season-2 narrative flow to be season-agnostic**
so both seasons use STORY/BRIEFING/recall/concept-dedupe. Concretely:
- `game.py`: make `_emit_scene_state`, `_emit_completion_story`, the
  recall gate, concept-dedupe, and `_advance_to_scene` work for S1 too
  (read from S1_* maps when season==1, S2_* when season==2). Remove the
  S1 console-narration legacy path.
- New content module additions: `S1_SCENE_WHY`, `S1_SETUP`,
  `S1_YOUR_MOVE`, `S1_RESULT_REACTION`, `S1_RECALL_CHALLENGES`,
  `S1_OBJECTIVE_FOCUS`, rebuilt `OBJECTIVES` (16, skill-tagged) — in
  `core/game.py` or a new `core/season1_content.py` (cleaner; decide at
  build).
- `core/codex.py`: 8 skill cards (replace the current S1 concept set).
- `main_window.py`: drop the S1-specific `_sync_side_panel`/console
  intro/guidance branch; S1 uses `emit_scene_state()` like S2.
- `scene_view.py`: already season-agnostic (GOAL/YOUR MOVE) — no change.

### Out / untouched
- S1 scene art, story premise, the fraud plot, collectibles narrative
- Season 2 (done)
- Phase-2 click-to-advance pacing (still later)

---

## 5. Acceptance criteria

- [ ] AC1: All 16 S1 objectives solvable vs seed data (reference query each)
- [ ] AC2: Each of the 8 skills appears exactly twice; card once (Rep A)
- [ ] AC3: 3-region layout active in S1 (narration only in STORY panel)
- [ ] AC4: Every objective has SETUP + YOUR MOVE + RESULT-REACTION
- [ ] AC5: YOUR MOVE / SETUP closers at the recall-gate clarity bar
- [ ] AC6: Between-scene recall gates fire, non-punishing
- [ ] AC7: Full S1 progression drives 16/16, no stuck, ending → S1→S2 transition still works
- [ ] AC8: S2 unaffected (regression); concept dedupe still 6/6 in S2
- [ ] AC9: Programmatic verification battery green (mirror S2's _verify_all)

---

## 6. Open questions (low-risk defaults)

- Q1: Content location — extend `game.py` vs new `core/season1_content.py`.
  → Recommend new module (game.py is already large; S2 set the pattern).
- Q2: 16 objectives across 6 scenes means 2–3/scene (S2 was 2/scene).
  → Fine; scene art/story unchanged, only objective count per scene grows.

---

## 7. Implementation order

1. Design + verify the 16 reference queries vs seed data (AC1) — before code
2. New S1 content module: scene WHY, setup, your-move, reaction, recall, focus
3. codex.py → 8 skill cards
4. game.py: generalise narrative flow season-agnostic; rebuild OBJECTIVES(16)
5. main_window.py: remove S1 legacy console branch
6. Full verification battery (AC7–AC9) + S1→S2 transition
7. Playthrough sign-off → then v2.0.0 merge + tag + Release

---

*Spec written: 2026-05-18*
*Author: Mike + Claude*
