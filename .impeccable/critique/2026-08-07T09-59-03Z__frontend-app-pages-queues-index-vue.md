---
target: queues screen (frontend/app/pages/queues/index.vue)
total_score: 16
max_score: 40
na_heuristics: 
p0_count: 2
p1_count: 2
timestamp: 2026-08-07T09-59-03Z
slug: frontend-app-pages-queues-index-vue
---
### Design Health Score

| # | Heuristic | Score | Key Issue |
|---|-----------|-------|-----------|
| 1 | Visibility of System Status | 2 | "Connected" pill + "Sampled" timestamp exist, but no distinction between "genuinely zero queues" and "poll degraded," and no visible cue when the 10s auto-refresh actually lands |
| 2 | Match System / Real World | 2 | "Workload," "Tracked," "Tier" assume Celery fluency with no glossary; color-to-urgency mapping is inverted (see P1) |
| 3 | User Control and Freedom | 2 | URL-synced filter/sort is genuinely good, but there are zero write actions and no way to pause auto-refresh |
| 4 | Consistency and Standards | 2 | Native unstyled `<select>`s sit next to a fully-styled shadcn `Button`; the bar's color coding isn't reused in the Tier cards showing the same two numbers |
| 5 | Error Prevention | 3 | Read-only surface; divide-by-zero guarded in the width math; Tier block cleanly no-ops when no queue has a tier |
| 6 | Recognition Rather Than Recall | 1 | No baseline/threshold/trend — user must recall "normal" load per queue from memory; legend disappears below `sm` |
| 7 | Flexibility and Efficiency | 1 | No click-to-sort headers despite the table visually inviting it, no saved views, no density control, no shortcuts |
| 8 | Aesthetic and Minimalist Design | 2 | Calm and uncluttered, but in the "empty template" sense — nothing visually separates a healthy queue from one in trouble |
| 9 | Error Recovery | 1 | Raw `err.response.data.detail` string dumped in red, no icon, no cause hint, no inline retry |
| 10 | Help and Documentation | 0 | Zero in-context help: no tooltips on Tier/Workload/Tracked, no doc link from the empty state |
| **Total** | | **16/40** | **Poor — significant UX overhaul needed before this earns Kanchi's "enjoyable" claim** |

### Design Specificity Verdict

**LLM assessment**: No. This is a generic filterable admin CRUD screen — search box + two native `<select>`s + three stat cards + an optional summary grid + a bordered `<table>` — structurally identical to the sibling Workers page. It contains zero Celery-specific *action*: no retry, purge, requeue, pause-consumption, or orphan-flag anywhere on the screen. The only per-row control is a link that navigates away. It embodies neither half of Kanchi's stated differentiation from Flower: it isn't distinctively "enjoyable," and it exposes none of the "active management" depth the product claims to have over Flower.

**Deterministic scan**: The static CLI scan of the source file itself (`detect.mjs`) came back clean — 0 findings, exit code 0. The live browser-injected scan on the rendered DOM found 6 rule hits instead: `overused-font` (single font family, 100% of text), `gradient-text`, `layout-transition`, `pulsing-dot` (`animate-ping` on the nav's "Connected" indicator), `marquee` (`animate-shimmer` loop), and `codex-grid-background` (tiled hairline background). All six attach to shared app-shell chrome — the nav bar, the global background texture, a shimmer skeleton component — not to anything this screen's own template authors. That's a notable split: the *chrome* carries the app's only motion/texture personality, while the *content area* (the part a design-specificity verdict actually judges) is the plain, uninflected part. This corroborates rather than contradicts the "generic" verdict above — the boldness Kanchi does have lives everywhere except where the Celery-specific work would need to show up. No CLI false positives to flag since the static pass returned nothing; the `overused-font` live finding is the one worth taking seriously as a symptom, not a nag — it's consistent with A's point that the table has no typographic hierarchy to separate signal from noise.

**Visual overlays**: Not left running — the live-server instance used for injection was started and stopped within Assessment B for evidence-gathering only; no persistent `[Human]`-tab overlay was requested or left behind for this run. The 6 findings above are the full console output captured during that pass.

### Overall Impression

This screen works — it fetches queue metrics, filters, sorts, tiers, auto-refreshes, and syncs state to the URL — but it reads as the *table you'd build first*, not the table Kanchi ships. For a product whose entire pitch against Flower is "materially better UX + materially deeper management," this specific screen currently offers neither: no action beyond a single "Open In Dashboard" escape hatch, and no visual language that makes a backed-up queue *feel* different from a quiet one. The single biggest opportunity: this is the screen an on-call engineer opens first during a real incident, and right now it can't even show them whether one queue is broken or the whole system is — because the bar chart scales to today's own worst offender instead of any fixed reference.

### What's Working

1. **Default sort is Workload, descending.** The one moment the screen anticipates triage before the user asks for it — the busiest, likely-most-concerning queue surfaces first with zero configuration required.
2. **URL-synced filter/sort state.** Shareable, bookmarkable, back/forward-safe filtered views (`useUrlQuerySync`) — a real efficiency win most admin tables skip entirely.
3. **Clean structural degradation.** The Priority Tiers block fully disappears via `hasTieredQueues` rather than rendering an empty grid, and the width math for the stacked bar is guarded against divide-by-zero. Small, but it's the kind of care that avoids embarrassing edge-case breakage.

### Priority Issues

- **[P0] The bar chart's scale has no fixed floor — it normalizes to today's own worst queue.** `getRunningWidth`/`getScheduledWidth` divide by `maxVisibleWorkload`, the largest workload among the *currently filtered* rows.
  **Why it matters**: In a system-wide outage where every queue is equally backed up, the worst queue simply defines "100%" and every other bar looks proportionally normal — the exact scenario this screen exists to catch becomes invisible. This is the opposite of what a monitoring screen should do under stress.
  **Fix**: Add an absolute reference — fixed threshold bands (healthy/elevated/critical), a per-queue historical baseline, or a min/max sparkline — instead of pure relative-max normalization.
  **Suggested command**: `/impeccable overdrive` (this is a data-encoding problem, not a polish problem — needs a genuinely different visual model for the load bar).

- **[P0] Zero active-management action exists on this screen.** The only per-row control is a plain link to the main dashboard; there is no retry, purge, pause-consumption, or orphan-flag affordance anywhere.
  **Why it matters**: Active management beyond passive monitoring is literally half of Kanchi's stated differentiation from Flower. This is exactly the screen where an operator would expect to act on a queue that's in trouble, and instead it's read-only telemetry with an exit door — Flower with nicer chrome.
  **Fix**: Add at least one inline action per row (pause consumption, purge scheduled tasks, flag as orphaned) surfaced contextually when a queue crosses a load threshold.
  **Suggested command**: `/impeccable shape` (this is a scope/capability decision before it's a visual one — worth planning what the action set should be).

- **[P1] Color semantics are inverted for urgency.** The stacked bar maps `bg-status-warning` (amber/caution) to *Running* — the healthy, being-worked-on state — and `bg-status-info` (calm blue) to *Scheduled* — the backlog metric that should actually worry someone as it grows.
  **Why it matters**: This actively trains the eye toward the wrong signal at the exact moment color-coding is supposed to help fast scanning during triage.
  **Fix**: Remap Running to a neutral/positive token; reserve warning/error tokens for backlog size crossing a defined threshold, not for the state that means "work is happening."
  **Suggested command**: `/impeccable colorize`

- **[P1] Mobile loses both the numeric data and the only call-to-action with zero affordance.** Measured directly: the table's scroll width is 795px against a 356px visible viewport at 390px width — Running, Scheduled, Tracked, and "Open In Dashboard" are all off-screen with no scroll shadow or indicator that more content exists. The Running/Scheduled color legend is `hidden sm:flex`, so below that breakpoint the color-coded bar has no key at all — meaning is color-only on mobile.
  **Why it matters**: The product's own stated audience includes non-Celery-expert support staff, who are more likely to be checking status from a phone. This is a WCAG 1.4.1 (use of color) failure on top of a pure usability one.
  **Fix**: Responsive card layout for narrow viewports instead of a raw horizontally-scrolling table; keep the legend visible at every breakpoint.
  **Suggested command**: `/impeccable adapt`

- **[P2] Empty and error states read as unfinished, not intentional.** The empty state has no icon distinguishing "genuinely idle" from "broker not connected," and no next step. The error state dumps the raw backend string (`err.response.data.detail`) in red with no inline retry — recovery requires a visual trip back to the top-right Refresh button.
  **Why it matters**: This directly contradicts one of the product's own stated principles — that the default, no-auth, no-data state should feel like a complete product, not a half-configured one. This is the state most first-time viewers and support staff will actually see.
  **Fix**: Author a real empty state (icon, likely-cause line, inline retry, link to broker setup docs); move the retry action next to the error text itself.
  **Suggested command**: `/impeccable onboard`

### Persona Red Flags

**Alex (power user, mid-triage)**: During a simulated backup, the relative-max bar scaling means Alex can't tell "one queue is bad" from "everything is bad" at a glance — the chart is mathematically incapable of showing a system-wide event. No delta/trend indicator exists between the 10-second refreshes, so Alex must manually hold two snapshots in memory to tell whether a growing `scheduled_tasks` count is a live crisis or already draining. The only action available — `Open In Dashboard` — means Alex has to leave this screen entirely to do anything about what they just saw. And mid-incident, checking from a phone, the numeric columns and the one action link are scrolled off-screen with no visible cue that they exist (confirmed: 795px content vs. 356px viewport).

**Sam (accessibility)**: The Running/Scheduled legend is `hidden sm:flex` — on mobile, the bar's meaning is conveyed by color alone with no textual fallback, a direct WCAG 1.4.1 violation at that breakpoint. The three filter `<label>` elements have no `for` attribute and their `<input>`/`<select>` counterparts have no `id` — association is purely visual, so a screen reader gets no programmatic name for "Filter Queues," "Sort By," or "Order." The table's `<th>` cells have no `scope="col"` and there's no `<caption>`, so assistive tech gets no explicit header association for a 7-column data table.

### Minor Observations

- "Tracked Tasks" is never defined on-screen — cumulative? A superset of running+scheduled? A rolling window? No non-expert viewer can infer this.
- The Tier caption has a singular/plural bug: `tier.queueCount` renders as "1 queues" when the count is 1.
- Large numbers render with no thousands separators (`98213`, `500000`), which hurts exactly the fast scanning a triage screen needs.
- Long queue names have no truncation or `title` attribute and will distort the table's row rhythm.
- The Tier column shows "Fast/Medium/Slow" as plain text with no color chip, despite the section literally being titled "Priority Tiers" — an unused, obvious opportunity for a scannable visual cue that's already half-built (the tier concept exists, just not the visual encoding).

### Questions to Consider

- If active management is half of Kanchi's promised differentiation from Flower, why does this screen's only per-row control navigate *away* instead of letting the user *do* something — where does that promised capability actually live, if not here?
- The bar is scaled to today's max, not an absolute threshold — is this screen meant to answer "which queue is worst relative to its peers" or "which queue is in absolute trouble"? It can currently only answer the first, and that's the wrong question during a systemic outage.
- Given the product explicitly serves non-Celery-expert support staff, has "Tracked Tasks," "Tier," or "Workload (Running + Scheduled)" ever been tested on someone who doesn't already speak Celery?
