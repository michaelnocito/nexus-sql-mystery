# SPEC: Narrative Separation + Story-Code Fusion
# Status: DRAFT — needs go/no-go on the layout (Section 3) before build
# Stage: 2 (Spec Writing)
# This is the core-value spec: "learn SQL by solving a mystery" only
# works if the SQL and the story are the SAME act, not adjacent ones.

---

## 1. The problem (from playtest)

- Narration lives in the same scrolling feed as query-result tables and
  mechanical messages. A result table shoves the story off-screen; the
  player loses the thread and has to scroll up to find it.
- The story reads as "bare bones." The SQL doesn't feel like it *did*
  anything — run query, get a table, get a generic ✓. No payoff beat.
- The player cannot always see, large and unmissable: WHY they're here,
  WHAT they're accomplishing, HOW to proceed.
- Mandate: we TEACH SQL. We do not obscure the path for "mystery." The
  path must be clear; the *story* supplies motivation, not obfuscation.

---

## 2. Design principle

One investigative act, three fused parts:
**story problem → the query is your move → the rows ARE the revelation.**

The query result must be narratively acknowledged: a per-objective
**result-reaction** beat that reflects what the correct query exposed and
pushes the plot one step. Mechanics are taught *through* the
investigation, never in a box beside it.

---

## 3. Layout re-architecture  (DECISION NEEDED — go/no-go)

Three permanently-distinct regions. Narration NEVER appears in the feed.

### A. STORY panel — new, prominent, top of the centre column
- Fixed/large, never scrolled away by query output.
- Holds: the scene's WHY (premise/stakes) and the **current story beat**.
- After a correct query, its content updates to the **result-reaction**
  beat (the revelation). This is where the SQL "lands."
- Visually: distinct ground, generous type, the emotional centre.

### B. BRIEFING — the left panel (evolve what exists)
- Always visible. The player's compass:
  - **GOAL** — what you're accomplishing, in-story (1 line)
  - **YOUR MOVE** — the clear path / approach (HOW), plain language
  - Progress + clue checklist (keep)
- Scene art stays a small thumbnail (already done).

### C. CONSOLE — the existing scroll feed, mechanical ONLY
- Query echo, result tables, success/fail, hints, concept cards.
- No narration, no story beats. This is the "doing" surface.

Editor stays at the bottom.

---

## 4. Content model (per objective)

Each of the 12 S2 objectives gets three authored pieces:

1. **Setup beat** (STORY panel) — the in-world situation that creates a
   question only the database can answer. Ends pointing at the question.
2. **Your move** (BRIEFING) — plain-language path: what to ask the data
   and the SQL idea to reach for. Teaches the concept *as the method of
   investigation*, not "in Season 1 you learned…".
3. **Result-reaction** (STORY panel, fires after correct query) — reacts
   to exactly what the correct query reveals; advances the plot; sets up
   the next setup beat. This is the payoff that makes the SQL feel
   impactful.

Tone target: tight, noir, specific. No filler. Every beat earns its line.

---

## 5. Scope

### In
- `cmd_panel.py` / `main_window.py`: split STORY panel out of the feed;
  feed becomes mechanical-only; wire setup/reaction into STORY panel.
- New game callbacks/flow: deliver setup beat on objective focus, and a
  result-reaction beat on objective completion (engine already completes
  objectives — add the reaction emission).
- `season2_game.py` content: rewrite step text → "your move" briefing;
  add a `S2_RESULT_REACTION` map (per-objective revelation beat); rewrite
  scene intros as punchy WHY/setup. Same SQL, same concepts, same 12
  objectives — only the writing + delivery change.
- Left panel: GOAL + YOUR MOVE always-visible treatment.

### Out / untouched
- SQL ladder, validators, objective IDs, progression logic (just fixed)
- Season 1 content (S1 may adopt this later — separate pass)
- Portraits, codex, collectibles, scene art
- The Phase-2 click-to-advance pacing (still later)

---

## 6. Acceptance criteria

- [ ] AC1: Narration/story never renders in the scroll feed; it lives only in the STORY panel
- [ ] AC2: A large query-result table never pushes story off-screen — WHY/beat stays visible
- [ ] AC3: At all times the player can see, without scrolling: WHY (story panel), GOAL + YOUR MOVE (briefing)
- [ ] AC4: After each correct query, a result-reaction beat fires that references what the data showed and advances the plot
- [ ] AC5: A first-time player can state, at any point, "I'm here because X, I need to find Y, I do that by Z" — purely from on-screen text
- [ ] AC6: No mechanics-first phrasing ("in Season 1 you used…"); motivation is in-world
- [ ] AC7: Full S2 SQL playthrough: every objective has setup + your-move + reaction; no dead air, no generic ✓-only
- [ ] AC8: No regression in progression, portraits, concept card, codex

---

## 7. Open questions

**Q1: Result-reaction authoring — static or data-driven?**
Static per-objective text written to reflect what the *correct* query
exposes (e.g. "Fourteen rows. All 03:03:00. User: [SYSTEM]."). Simple,
reliable, authorable now. Data-driven (interpolate real result values) is
more magical but fragile across query variants.
→ Recommend: **static, specific**. Revisit data-driven later if wanted.

**Q2: Briefing — evolve left panel, or new band under STORY panel?**
Left panel already shows objective/progress/log and the user said it
"looks good." → Recommend: **evolve the left panel** (add GOAL + YOUR
MOVE prominently), keep one mental location for "the compass."

(Both recommendations are low-risk; treating as decided unless redirected.)

---

## 7b. Repetition via VARIED PRACTICE (ADDED 2026-05-17 — user requirement)

PRIMARY mechanism (user's exact ask): "repetition of using the same skill
to solve slightly different things." Each core SQL skill is reused across
2–3 slightly varied problems before it's considered learned — not used
once and abandoned.

**Content-model change — supersedes the one-shot ladder:**
The SQL-core ladder is currently 12 objectives = 12 brand-new concepts,
each used once. CHANGE IT: introduce ~6–7 core skills only; each recurs
2–3 times across the 12 objectives in a *slightly different* investigative
context (different column, pattern, combination, or question) and
escalating difficulty. Fewer concepts, deeper grooves. This also satisfies
the earlier "day-one, smaller chunks" instinct. Resolve the exact
skill→objective mapping at build time (keep the 12 story beats; remap
which skill each one practices). Same SQL engine, validators adjust.

Supporting mechanisms (secondary):

- **Interleaving (authoring only):** later objectives' reference queries
  must reuse an earlier concept while introducing the new one (e.g. a
  later scene query uses LIKE + strftime while teaching HAVING). Frame
  as the case escalating, not drilling. Bake into the §4 content rewrite.
- **Recall gates (wire existing system):** `get_recall_challenge()` +
  `S2_RECALL_CHALLENGES` already exist but are not surfaced in the new
  flow. Add a short, in-world, ONE-question retrieval prompt between
  scenes (delivered via STORY panel + answered in the editor) before the
  next scene unlocks. Keep it fast; story-framed, not quiz-framed.
- Mini-game: explicitly DEFERRED — fits the future opt-in Pro-Panel
  side-quest spec, not this one. Interleaving + recall gates first.

New acceptance criteria:
- [ ] AC9: At least the back-half S2 objectives require combining a new
  concept with a previously-learned one (verified interleaving)
- [ ] AC10: A one-question recall gate fires between scenes using the
  existing recall-challenge data, story-framed, and gates progression

## 8. Implementation order

1. Layout: extract STORY panel from the feed; feed = mechanical only (AC1–AC3)
2. Engine: emit setup beat on objective focus; emit result-reaction on completion (AC4)
3. Content: rewrite S2 scene intros → WHY/setup; step text → "your move"; add S2_RESULT_REACTION (AC5–AC7)
4. Left panel: GOAL + YOUR MOVE always-visible
5. Full SQL playthrough regression (AC8) — yours

---

*Spec written: 2026-05-17*
*Author: Mike + Claude*
