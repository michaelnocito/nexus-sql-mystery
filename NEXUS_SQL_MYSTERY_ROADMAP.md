# NEXUS SQL Mystery Roadmap

Local: C:\Users\Mike\Projects\nexus-sql-mystery

This file was created to hold the dev-cockpit item below. The rest of this
app's roadmap goes here as it takes shape.

---

## Dev cockpit (not started)

**Every new app starts with one now.** This one does not have one yet, so it is owed.

The dev cockpit is the instrument panel that makes it possible to exercise one piece of the
app repeatedly without working through everything around it. The canon — the full control
list, the reasoning behind each control, and the app-applicable translation of each — is
`BUILD_PILLARS.md`, section **"A. The dev cockpit"**, in `C:\Users\Mike\Projects\play-area`.
The implementation is already written: `play-area/dev-cockpit.js` plus
`play-area/harness-lib.js` for the headless half. Copy them in; declare this app's own knobs.

What that means here:

- **Jump straight to one screen, one state, one record** — no clicking through a flow to
  reach the thing being worked on
- **Bypass auth, quotas, rate limits and paywalls** while testing (the no-fail toggle)
- **Freeze and single-step** any animation, timer, queue or polling loop
- **Slow-motion** on transitions and network timing, so what the eye missed becomes visible
- **A latency readout** — time to first paint, time to a response landing
- **Instant reset to a known seeded state**, in one keystroke
- **Layout, focus-order and hit-target overlays**
- **Every timing, threshold and limit the app's feel depends on, on a live slider**
- **A numbers dump** — one keypress writes a pasteable line plus a `<app>-tuning.txt` file.
  That file is the handoff to the next session; without it the tuning dies with the tab.
- **A headless harness** (`node <app>-harness.js`) so an agent can prove a change without
  asking a human to click

Gated behind `?dev=1` (auto-on for localhost), wrapped in `DEV:BEGIN` / `DEV:END` strip
markers, and nothing inside it load-bearing: delete the block and the app runs identically.
