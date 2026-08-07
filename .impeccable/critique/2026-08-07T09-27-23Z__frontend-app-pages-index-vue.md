---
target: Dashboard / overview (frontend/app/pages/index.vue)
total_score: 25
max_score: 40
na_heuristics: 
p0_count: 1
p1_count: 2
timestamp: 2026-08-07T09-27-23Z
slug: frontend-app-pages-index-vue
---
Method: dual-agent (A: design-review subagent · B: detector-scan subagent)

## Design Health Score

| # | Heuristic | Score | Key Issue |
|---|-----------|-------|-----------|
| 1 | Visibility of System Status | 3 | `secondsSinceUpdate` is computed and passed to `DataTable` but never rendered anywhere — the "is this feed actually live" signal is fully wired and fully invisible |
| 2 | Match System / Real World | 4 | Solid — vocabulary ("orphaned," "retry chain," "routing key") matches Celery's own mental model without dumbing down |
| 3 | User Control and Freedom | 2 | `TimeRangeFilter`'s trigger looks disabled during live mode but its click handler still force-disables live mode as a side effect — a "disabled" control silently mutating state |
| 4 | Consistency and Standards | 2 | Live-mode toggle is a clickable `Badge` (inert everywhere else on the page); pagination copy differs between components ("entries" vs "tasks") |
| 5 | Error Prevention | 3 | Retry/Cancel confirmations use specific, plain-language consequence copy; Resolve/Unresolve has none (acceptable given low stakes) |
| 6 | Recognition Rather Than Recall | 2 | `SearchInput` implies a `field:operator:value` query DSL with zero inline teaching; Cmd+K's existence is never hinted at in the visible UI |
| 7 | Flexibility and Efficiency | 3 | URL-synced filter/sort/page/time-range state and a command palette exist, but the palette only supports 2 actions — underbuilt relative to the shell around it |
| 8 | Aesthetic and Minimalist Design | 2 | No page heading; three status accordions + full toolbar + 6-column table land with equal visual weight on first paint; unclipped full hostnames repeat every row |
| 9 | Error Recovery | 3 | Inline exception text, retry-chain visualization, resolve/unresolve workflow; but CommandPalette failures only `console.error` — a broken call and "no task found" look identical to the user |
| 10 | Help and Documentation | 1 | Nothing on the page — no tooltip, no "?", no onboarding — teaches a non-specialist what "orphaned" or the filter syntax mean, despite the product explicitly targeting non-Celery-expert users |
| **Total** | | **25/40** | **Acceptable — significant improvements needed before non-specialist users are comfortable** |

## Design Specificity Verdict

**LLM assessment**: Split cleanly along data vs. chrome. The data model and workflows are genuinely Celery-specific — orphan detection with copy like "Waiting for worker '{hostname}' to acknowledge this task," retry chains, routing keys, live WebSocket updates. No generic admin template ships that domain logic. But the visual/interaction chrome — a search bar + time-range popover + sortable paginated table + Cmd+K palette + mouse-following glow-on-hover cards — is largely interchangeable with any dark-mode SaaS admin dashboard. The two elements that gesture at bespoke design investment (the `.glow-border` mouse-follow effect and the command palette) are both generic "enjoyable-SaaS" tropes, not something that reads as *for Celery specifically*. PRODUCT.md stakes the pitch on "not a utilitarian admin table dump" plus deeper capability — the capability half is earned here; the visual half currently reads as competent-generic rather than distinctive.

**Deterministic scan**: Clean. `detect.mjs --json` against `index.vue` and its seven directly-used components (`data-table.vue`, `WorkerStatusSummary.vue`, `CommandPalette.vue`, `TaskIssueSummary.vue`, `RetryTaskConfirmDialog.vue`, `TimeDisplay.vue`, `TimeRangeFilter.vue`) returned exit code 0 and zero findings on both runs, verified as a genuine clean result (no `DESIGN.md` or ignore config exists to suppress rules, no inline ignore comments in the scanned files). Notably, the detector's pattern-matching couldn't catch — and the LLM review did — a real functional bug (hardcoded API URL, see P0) and a semantic color-token collision (failed/orphaned sharing a class string): both require cross-file, meaning-level reasoning a regex-based scanner isn't built for. No disagreement between assessments; the detector's silence here is a scope limitation, not a contradiction.

**Visual overlays**: Not available this session — no browser automation tool is exposed and the Nuxt dev server isn't running. Assessment A worked from source plus the real `dashboard-overview.png` screenshot as ground truth instead.

## Overall Impression

The dashboard's substance is ahead of its surface. Orphan detection, retry chains, and consequence-aware confirmation dialogs genuinely deliver on Kanchi's "deeper than Flower" half of its positioning — that's real, working differentiation. But the page you land on doesn't announce any of that: no heading, three status widgets with identical visual weight regardless of whether everything's fine or on fire, and a color system that quietly conflates "orphaned" and "failed" — the exact distinction this product's whole pitch rests on being able to see at a glance. The single biggest opportunity: make the page's *visual* hierarchy match the *informational* hierarchy it already computes (freshness, severity, orphan-vs-failed) instead of leaving that signal computed-but-unrendered or rendered-but-indistinguishable.

## What's Working

1. **Progressive disclosure matched to the dual-mode brief.** Collapsed-by-default accordions with inline counts let a calm-monitoring user get "we're fine" in one glance, while inline row expansion (no page nav) into exception text/retry chains serves urgent triage without a context switch — a real embodiment of "serve calm and urgent without changing character."
2. **Consequence-aware confirmation copy** on Retry/Cancel is specific and plain-language ("re-queued and executed again," "SIGTERM... cannot be undone"), not generic "Are you sure?" — this is the part of the page that most concretely earns the "materially deeper management capability" claim over Flower.
3. **Orphan detection made legible** ("Waiting for worker X to acknowledge this task") turns a normally invisible Celery failure mode into readable, first-class UI — directly useful to the non-specialist persona who wouldn't otherwise know what "orphaned" means in raw broker terms.

## Priority Issues

**[P0] Command palette task lookup hardcodes `http://localhost:8765`**
- **Why it matters**: `CommandPalette.vue` line 181 calls `fetch('http://localhost:8765/api/events/recent?limit=1000')` directly instead of going through the app's shared `apiClient`. On any self-hosted deployment that isn't literally `localhost:8765` — custom ports, reverse proxy, Docker Compose service names, i.e. most real installs per PRODUCT.md's self-hosted operating context — Cmd+K → "Rerun Task…" silently finds nothing and shows a plausible "No task found with ID X," which reads as user error rather than a broken feature.
- **Fix**: Route this call through the shared `apiClient` service already used everywhere else on the page.
- **Suggested command**: `/impeccable harden`

**[P1] "Failed" and "Orphaned" status pills are visually identical**
- **Why it matters**: `frontend/app/components/ui/badge/index.ts` gives `failed` and `orphaned` the exact same class string (`border-status-error-border bg-status-error-bg text-status-error hover:bg-status-error-hover`), while `useTaskStatus.ts`'s own `getStatusColor` map treats `orphaned` as `status-neutral` — the two color systems disagree with each other. Color is this product's primary at-a-glance triage signal, and orphan-vs-failed is exactly the distinction Kanchi's differentiation claim depends on surfacing quickly. Collapsing them to one hue forces label-by-label reading precisely when speed matters most, and removes the only differentiating channel for colorblind users.
- **Fix**: Give `orphaned` its own token consistent with `useTaskStatus.ts`'s neutral treatment, and reconcile the two disagreeing color systems.
- **Suggested command**: `/impeccable colorize`

**[P1] No page-level heading or orientation on landing**
- **Why it matters**: `index.vue` drops straight into three equal-weight status accordions with no H1, no title, no framing text — unlike the Task Registry surface ("Task Registry" + "Monitor and manage your Celery tasks"). For a non-specialist landing here without daily familiarity, an unlabeled stack of status bars undercuts the product principle that the default state should "feel like a complete, intentional product."
- **Fix**: Add a lightweight heading/summary line consistent with how other core surfaces introduce themselves.
- **Suggested command**: `/impeccable layout`

**[P2] Disabled-looking controls that aren't actually inert**
- **Why it matters**: `TimeRangeFilter`'s trigger visually reads as disabled during live mode, but its click handler still fires and silently force-disables live mode as a side effect (`handleButtonClick`) — breaking the basic "disabled means inert" contract. Separately, the Live-mode toggle is implemented as a clickable `Badge`, a component that's inert everywhere else on the page, so its interactivity isn't discoverable by pattern-matching against the rest of the UI.
- **Fix**: Use a real toggle/switch for Live Mode; make the time-range trigger either truly inert during live mode or visually communicate "click to exit live mode."
- **Suggested command**: `/impeccable audit`

**[P2] Freshness signal computed but never shown**
- **Why it matters**: `secondsSinceUpdate` is computed in `index.vue` and passed into `DataTable`, but never rendered in its template. For a real-time monitoring tool, "is this actually live right now" is core visibility-of-system-status territory that a power user needs during an incident — and the data is already there, just not surfaced.
- **Fix**: Surface it next to the Live badge, e.g. "Live · updated 4s ago."
- **Suggested command**: `/impeccable polish`

## Persona Red Flags

**Alex (Power User)**: Cmd+K's flagship efficiency feature (rerun-by-ID) is broken on any non-`localhost:8765` deployment (P0) — the one part of the UI built specifically for Alex is also its most fragile. No visible freshness indicator despite the plumbing existing, so Alex must trust "Live" blindly. The palette does only 2 things (toggle-live, rerun-by-ID) — no jump-to-task/worker/queue — underscoped for someone who reaches for Cmd+K expecting broad control.

**Jordan (First-Timer / product-support staff)**: Zero orientation copy on landing (P1) — nothing explains what "Orphaned tasks — 7 detected" means practically before Jordan already knows the domain vocabulary. The free-text search bar implies a query DSL (`state:is:failed`) with no inline teaching anywhere in the toolbar. The Failed/Orphaned color collision (P1) hits Jordan hardest — the persona least likely to read every label carefully is exactly the one most likely to misjudge severity at a glance.

**Sam (Accessibility-Dependent)**: Table rows expand via a plain `@click` on the whole `<TableRow>` with no `tabindex`, `role="button"`, or keydown handler — the only way to see exception text or retry chains is mouse-only. The decorative mouse-following glow effect (`handleMouseMove`) queries and mutates styles document-wide on every mouse move with no `prefers-reduced-motion` guard and no keyboard/touch equivalent. Combined with the Failed/Orphaned color collision, a colorblind user loses the one differentiating channel entirely and has no keyboard path to the detail that would compensate.

## Minor Observations

- Pagination copy differs between `data-table.vue` ("...of Z entries") and `TaskIssueSummary.vue` ("...of Z tasks"/"...of Z entries" mixed) — reads as two different builders.
- Worker hostnames render unclipped in every row (e.g. `prod-worker-maint-01.company.com`) with no truncation/tooltip pattern, unlike `TimeDisplay`, which already does hover-title truncation elsewhere.
- Several handlers (`handleRerunTask`, `confirmRetry`, `handleResolveAction`, the environment-change watcher) surface failures only via `console.error`/`console.log` — invisible to the actual user, visible only in devtools.
- Worth checking: does the environment/workspace dropdown + avatar shown above this page (likely layout-level chrome) imply a logged-in identity even when `AUTH_ENABLED=false`? That would cut against the "no-auth state must feel complete, not half-configured" product principle.
- `TaskIssueSummary`'s own lookback tabs (12h/24h/48h/72h) and `DataTable`'s independent calendar-based `TimeRangeFilter` are two different UI patterns for the same "time window" concept on one page.

## Questions to Consider

- If orphaned and failed tasks are meant to be triaged differently — per the product's own differentiation claim — why do they currently render in the identical shade of red? Is color actually load-bearing here, or is text secretly the only real channel?
- What is this dashboard's actual "peak" moment — reopening the tab mid-incident? If so, why does the failure-count widget carry identical visual weight to "3 workers online" instead of escalating?
- The command palette is the clearest "materially better UI" gesture on the page — why does it do only two things the toolbar already exposes? What would it take to make Cmd+K the fast path to everything (jump to task/worker/queue, saved filters, navigation)?
- Given "auth is off by default and the UI must still feel complete," does the environment-switcher-plus-avatar chrome above this page silently imply a logged-in identity that doesn't exist when auth is disabled?
- If a non-specialist landed on this page with zero context, what's the one thing they're supposed to understand first — and does anything on the page currently say that out loud?
