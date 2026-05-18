# SPEC: Message Panel Redesign — Phase 1 (Visual Differentiation + Portraits + Chunking)
# Status: DRAFT — needs one decision (OQ1) before build
# Stage: 2 (Spec Writing)
# Phase 2 (segmenting / click-to-advance pacing) is a SEPARATE later spec.

---

## 1. Goal

Turn the undifferentiated purple wall of text into a WoW-style typed
message area where every message category is visually unmistakable, NPC
speech reads as coming from a distinct character (90s-X-Men-cartoon-style
portrait + name), and text is chunked per documented ADHD/attention and
multimedia-learning research.

Phase 1 = the visible win. Pacing/segmenting = Phase 2.

---

## 2. Discovery findings (current state)

- All narrative flows through ONE callback: `GameState.on_output(text, style)`
  → `MainWindow._on_output` → `CmdPanel.append_output(text, style)`.
- Rendering target is a single `QTextEdit#narrative` with a `STYLES` dict
  of `QTextCharFormat`s: scene, guidance, normal, dim, warning, success,
  error, input, output, spirit.
- **No NPC-dialogue concept exists.** NPC speech is either plain quoted
  prose inside `style="scene"` blocks, or Sam via `style="spirit"`.
- Current `scene` style: purple, bold, 16px, heavy top/bottom block
  margins → the "everything looks the same, double-spaced" problem.
- Research brief (sourced, on file in session) prescribes: ~45–60 chars/
  line for novices, ~150% line-height (NOT double), 2–3 sentence blocks,
  signaling via color/icon/header, separate bounded region for query
  output, name-tag + portrait + tinted box for NPC dialogue.

---

## 3. Message-type system (the core deliverable)

Replace the single rich-text flow with a **scrollable list of typed
message widgets** (`QScrollArea` + vertical layout of message widgets).
Rationale: true visual bounding (speech boxes, bordered output panels,
portraits) is not achievable cleanly in one QTextEdit flow, and a widget
list is the natural substrate for Phase 2 segmenting (each segment = a
widget revealed on click). This architecture choice is made; not an open
question.

Message types and their treatment:

| Type | Visual treatment |
|------|------------------|
| `narration` | Plain block, neutral ink (#1f2328), no portrait, ~150% leading, 2–3 sentence chunks, gap between chunks |
| `dialogue` | NPC portrait (left) + name tag + tinted speech box keyed to that NPC's color. Visually distinct from narration. |
| `system` | Boxed, neutral accent, small icon (e.g. ⚙). Scene transitions, season cards. |
| `tutorial` | Boxed, blue accent, numbered/iconized step. (Phase 2 makes these click-advance.) |
| `hint` | On-demand collapsed element, amber. Already partially exists. |
| `success` | Green icon + short confirmation line. |
| `failure` | Red/amber icon + corrective line. |
| `query_output` | Monospace, bordered/ground-tinted panel — its own walled region (WoW combat-log model). |

Color mapping (from WoW contextual model + existing palette):
success=#1a7f37, failure=#cf222e, system=neutral #57606a accent,
tutorial=#0969da, NPC=per-character.

---

## 4. NPC portrait system

Style: **90s X-Men: The Animated Series** — angular, sharp cel-shaded,
bold ink outlines, flat shadow planes, slightly heroic proportions. NOT
rubber-hose/Roger Rabbit. Drawn with QPainter (consistent with the
game's existing no-image-assets vector approach), rendered to a small
QPixmap (e.g. 48–56px) cached per NPC.

Per-NPC spec (S1+S2 speakers identified from content — to be finalized
in build step 1):
- **Sam** — spirit guide; ghostly cool palette, slightly translucent
- **Diana** — manager; warm, sharp blazer silhouette
- **Rachel Kim** — COO; composed, authoritative
- **Vanessa** — HR; approachable
- (Villains/others as content requires)

Each NPC: one portrait + a signature accent color used for their speech
box border/name tag. A generic fallback portrait covers any
unattributed speaker so nothing crashes.

---

## 5. Chunking rules (research-backed, applied globally)

- Wrap/measure narration to ~45–60 characters per line (novice optimum).
- Line-height ≈ 150% (replace current ~200% double-spacing).
- Hard cap narration blocks at 2–3 sentences; insert a real inter-chunk
  gap (margin) between blocks, not blank lines.
- Signaling: every message type carries a consistent icon + color so the
  player parses *type* before reading *content*.

(Segmenting — splitting tutorial text into click-advanced steps — is the
single highest-impact intervention but is explicitly **Phase 2**.)

---

## 6. Scope

### In (Phase 1):
- New widget-list message area replacing the QTextEdit narrative flow
- 8 message types with distinct visual treatment
- `on_dialogue(speaker, text)` callback + `CmdPanel` rendering of speech
  boxes with portraits
- QPainter NPC portrait set + per-NPC color registry
- Chunking/line-length/leading applied to narration & system text
- Content re-tagging per OQ1 decision

### Out (later phases / untouched):
- Click-to-advance segmenting & typewriter (Phase 2 spec)
- Any gameplay/objective/validator logic
- Scene art panel, HUD, codex/collectibles panels
- Season 1/2 content *meaning* (only message *attribution* changes)

---

## 7. Acceptance criteria

- [ ] AC1: Each of the 8 message types is visually distinguishable at a glance without reading the text
- [ ] AC2: NPC dialogue shows the correct portrait + name + per-NPC colored box; unattributed speaker falls back gracefully
- [ ] AC3: Query output is in its own bounded region, never blended into narration
- [ ] AC4: Narration is ≤60 char/line, ~150% leading, ≤3-sentence chunks with inter-chunk gaps
- [ ] AC5: A first-time player can tell "someone is speaking to me" vs "this is narration" vs "this is a system event" instantly
- [ ] AC6: No regression — full S1 + S2 SQL playthrough renders correctly, nothing crashes on any existing on_output call
- [ ] AC7: Portraits render crisply at the chosen size and match the 90s-X-Men cel-shaded brief

---

## 8. OPEN QUESTION (decide before build) — the scope driver

**OQ1: How much existing content gets re-tagged as dialogue?**

The visual system is identical regardless. The cost variable is content.
Options:

- **(a) Full re-tag.** Audit every S1+S2 scene intro / cliffhanger /
  step text, split narration vs each NPC line, emit via `on_dialogue`.
  Best player experience, highest effort, touches all content files.
- **(b) Hybrid (recommended).** New `dialogue` channel + portrait system
  built fully. Re-tag only: (i) Sam (already isolated via spirit), (ii)
  clearly-attributed speaker lines in scene intros where a named NPC
  speaks in quotes (Diana/Rachel/Vanessa), (iii) all *new* content tagged
  going forward. Leaves ambiguous narration as narration. ~80% of the
  felt benefit, ~30% of the effort.
- **(c) System only.** Build the visual system + portraits, retag only
  Sam. Cheapest, proves the system, but most NPC speech stays as
  narration until a later content pass.

Recommendation: **(b) Hybrid.** Captures the "a distinct entity is
talking to me" goal everywhere it matters without a full content rewrite,
and is independently shippable.

---

## 9. Implementation order (once OQ1 decided)

1. Enumerate all speaking NPCs across S1+S2 content (grep + read)
2. Build QPainter portrait set + per-NPC color registry (AC7)
3. Build widget-list message area + 8 message-type widgets (AC1,AC3,AC4)
4. Add `on_dialogue(speaker, text)` callback (game.py → main_window → cmd_panel)
5. Re-tag content per OQ1 (AC2,AC5)
6. Full S1+S2 render regression pass (AC6) — live playthrough (yours)

---

*Spec written: 2026-05-17*
*Author: Mike + Claude*
*Research brief: in-session (Cowan; Mayer segmenting/signaling; line-length
lit review; WoW chat model; visual-novel portrait conventions) — sourced.*
