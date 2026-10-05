# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Kanchi is used by a broader team than backend engineers alone: platform/backend engineers who own the Celery-based services, plus product and support staff who need to check on task/job status without deep Celery expertise. Usage spans both routine day-to-day monitoring/debugging and higher-pressure moments (failures, backed-up queues, misbehaving workers) — the interface needs to serve calm exploration and urgent triage equally well, and stay legible to non-specialist viewers.

## Product Purpose

Kanchi is a real-time Celery task monitoring and management system. It ingests Celery events (via a broker — RabbitMQ or Redis) and gives visibility into task execution, worker health, and task statistics as they happen, over REST + WebSocket. Success means someone can see what's running, what failed, and what needs attention, and act on it (retry, inspect, automate) without digging through raw broker/worker logs.

## Positioning

Kanchi's differentiation vs. the standard tool in this space (Flower) is twofold and both halves matter equally:

- **UX**: a modern, real-time, "enjoyable" interface — not a utilitarian admin table dump.
- **Capability depth**: goes beyond passive monitoring into active task management — retry tracking, orphan detection, task retry chains, and workflow automation — which Flower does not offer at this depth.

Neither alone is the pitch; it's the combination of a materially better interface plus materially deeper management capability.

## Operating Context

- Self-hosted, run by the team that owns the Celery workload (Docker Compose or local dev via `make dev`); not a SaaS product, so no multi-tenant chrome (billing, org switching) belongs here.
- Backend: FastAPI + SQLAlchemy + Alembic (`agent/`). Frontend: Nuxt 4 + Vue 3 + TypeScript + Pinia (`frontend/`), shadcn-vue/reka-ui component layer.
- Core surfaces: dashboard/overview, task list + task detail, worker health, queues, concurrency, workflow automation (create/edit/view), settings/workspace, login.
- Auth is opt-in and off by default (`AUTH_ENABLED=false`). When disabled, anyone reaching the backend can read metrics and connect over WebSockets — the UI must look and function complete with no logged-in identity present, not just tolerate that state.
- Data defaults to SQLite; PostgreSQL/MySQL supported via `DATABASE_URL`.

## Capabilities and Constraints

- Real-time task monitoring via WebSocket; task filtering/search (date range, status, name, worker, full-text); task retry tracking and orphan detection; daily task statistics/history; worker health monitoring; workflow automation.
- Optional auth: HTTP Basic or OAuth (Google, GitHub), with email-pattern allowlisting — all opt-in, disabled by default.
- Pickle-serialized broker payloads are rejected by default for safety (`ENABLE_PICKLE_SERIALIZATION` opt-in).

## Brand Commitments

Project name is "Kanchi." No dedicated logo/wordmark asset exists yet beyond the default Nuxt favicon — future design work should not assume an established mark is in place. MIT licensed, open-source, with a public Discord community. No other confirmed brand/voice commitments.

## Evidence on Hand

Real product screenshots exist at `.github/images/`: dashboard overview, failed tasks table, task detail panel, workflow automation, task retry chain, retry task modal. These reflect the actual incumbent UI and should be treated as ground truth for current visual maturity, not aspirational references. No testimonials, case studies, or customer evidence exist — do not fabricate any.

## Product Principles

- Serve both calm day-to-day monitoring and urgent triage without the interface changing character between them.
- Stay legible to non-specialist viewers (product/support) while still giving engineers the depth they need — don't gate comprehension behind Celery jargon alone.
- Earn the "enjoyable interface" claim: the UI is a stated differentiator, not an afterthought to the data.
- Default (no-auth) state must feel like a complete, intentional product, not a stripped-down or half-configured one.
- Prefer real task/worker/queue data and states over decorative chrome — this is an operational tool first.

## Accessibility & Inclusion

No project-specific accessibility requirement has been established beyond standard web accessibility practice.
