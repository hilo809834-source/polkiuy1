# Master build prompt — autonomous software engineering platform

**How to use this:** read `RULES.md` first — before this file, before anything else. Then paste this whole file as your first message to Claude Code, Cursor, Jules, or another coding agent, along with `ARCHITECTURE.md`, `UI_SPEC.md`, and `API_SPEC.md`. Together these five files are the complete spec — the operating rules, system design, every screen and layout decision, and every endpoint and data shape. Where any of them gives an answer, that answer is settled: implement it as written rather than choosing a reasonable-sounding alternative. Where something genuinely isn't covered, say so explicitly instead of filling the gap silently — an unstated assumption is exactly what this spec exists to prevent.

## What you're building

A platform where a person describes a software idea in their own words. The system asks a small number of targeted clarifying questions — not a fixed checklist, only the questions where the answer actually changes the build — and fills in the rest itself, logging every assumption it makes. It then autonomously writes, tests, and ships production-ready code for that idea, with no human touching the code in between.

"Tested" is the whole point of this project. It means a generator/critic/verifier loop where no single agent grades its own homework, plus a separate blind agent that drives the finished app the way an adversarial human tester would and has never seen the implementation — not just unit tests the generator wrote for itself.

This tool builds one project at a time for one user or small team. It is not a company, a research lab, or a network of AI organizations managing each other. That line is deliberate — see "Out of scope" below.

## Verification standard

`RULES.md` covers this in full — read it first. Short version: a phase's DoD is not met by this agent's own claim that it's met. Real dependency, real output pasted as evidence, every time.

## Autonomous loop protocol

Once Phase 1's DoD has been reported back and confirmed, run continuously. Don't stop to ask permission at every small step — that's not what these checkpoints are for.

- **Within a phase:** iterate generate → verify → fix as many times as it takes, without asking for confirmation on each individual attempt.
- **Between phases:** when a phase's DoD is met with real evidence, record that evidence directly in `VERIFICATION_CHECKLIST.md` — don't just assert it in chat — then move straight into the next phase. No need to wait for a "go ahead" on every single transition; the go-ahead is already given by this document.
- **Stop and report immediately, before finishing the rest of that phase, only when:**
  - something is genuinely blocked and a real, evidenced attempt hasn't resolved it (not just "this is hard")
  - meeting a phase's DoD would require an assumption not covered anywhere in the spec
  - cost or usage is approaching a level worth a real decision before continuing
  - all twelve phases are done
- Default behavior is to keep working through the phases in order, with real evidence logged at each one. Silence from the user is permission to keep building exactly as specced — it is never permission to skip the evidence.

## Build order

**On timeline:** this assumes one person or a couple people driving Claude Code or Cursor hard, not a large team. Phases 1 through 6 are the fast part — that's the actual "it just built something end to end" moment, and it's realistically days to a couple weeks away if you focus there first instead of trying to do all twelve at once. Phases 7 through 12 are what make the result trustworthy enough to actually rely on rather than a demo, and honestly, that's months of work for one person even with heavy AI-agent help — blind-testing infrastructure, deployment automation, and a repo-graph engine are each real subsystems, not add-ons. Ship through phase 6, start using what you get, then keep going. Don't wait for phase 12 to have something real in hand.

Each phase has a definition of done (DoD). Don't move to the next phase until the current one's DoD is actually true, verified by running it — not by inspection.

### 1 — Scaffolding & secrets
Repo structure with clear service boundaries (see `ARCHITECTURE.md`). Secrets manager: nothing hardcoded, nothing logged in plaintext.

**DoD:** a deliberately planted fake secret in a source file gets caught by a real check before it would reach a commit or a log line — not just "the secrets manager class exists."

### 2 — Model router
Config-driven, multi-provider, pinned model versions, capped retries. Hugging Face's hosted Inference API is one of the providers, wired in the same way as the others — see `ARCHITECTURE.md`'s note on it.

**DoD:** a real call succeeds against two different real providers, with the actual response text from each pasted as evidence.

### 3 — Sandbox execution
Containerized, isolated per task, resource-limited.

**DoD:** a deliberately runaway script actually gets killed by the timeout/memory limit. A normal script running successfully is not sufficient evidence — the limit itself has to be shown working.

### 4 — Minimal orchestrator
Wires 1 through 3 together: a task goes in, real sandboxed output comes back.

**DoD:** a hardcoded "hello world" task goes from a text prompt to a running process inside the sandbox, end to end, through the router.

### 5 — Intake & specification
Intent understanding, contradiction/gap detection, clarifying questions tiered by reversibility × blast radius × confidence, specification compiler.

**DoD:** a real free-text idea produces a real structured spec and real tiered questions from an actual model call — not a hardcoded example response.

### 6 — Core build loop
A separate agent generates the definition of done as executable acceptance criteria before code exists. Task decomposition into a dependency graph. Generate → test → retry with capped retries.

**DoD:** given a simple greenfield spec, the system produces working code that passes acceptance criteria it did not write itself, end to end, with no human editing code.

### 7 — Quality loop
Generator/critic/verifier split into distinct roles. A blind adversarial tester (Playwright, spec-only, never the implementation). Differential, property-based, and mutation testing alongside the acceptance tests. A self-healing debugger that does real root-cause analysis. Flakiness detection from failure-rate history.

**DoD:** on a real test project, the blind tester catches at least one class of bug that the generator's own acceptance tests missed.

### 8 — Security, compliance & tool connections
Security, license, and accessibility scanning wired in as real callable tools with real output — not a hardcoded pass. External integrations (GitHub first) go through MCP as the general connector mechanism rather than a one-off bespoke integration per service — that's where the rest of the industry converged (both Claude Code and GitHub Copilot use it this way), and it means the next integration after GitHub is a new MCP server, not new core code. Enforcement points — run a scan after any dependency change, redact secrets before any outbound log — are explicit hooks at defined lifecycle events, not buried inside a big function where they're easy to silently skip.

**DoD:** real scan output with real findings against a real target, and a real GitHub repo import working end to end through the MCP connection.

### 9 — Delivery & cost guardrails
Canary release, feature flags, automatic rollback on failed health checks. Cost and token budget guardrails with a real escalation UX. Custom domain connection at deploy time.

**DoD:** a generated app deploys to a real staging environment, a forced health-check failure triggers an actual rollback, and a real cost cap actually halts a runaway loop instead of letting it keep spending.

### 10 — Existing codebases
Repository intelligence as a queryable graph. Change-impact analysis and a safe-edit planner. Multi-agent write-conflict handling.

**DoD:** given a real, existing open-source repo the system did not generate, it makes a small, correct, tested change without breaking existing behavior that nothing in the repo's own test suite previously caught.

### 11 — Desktop app
The full control surface from `UI_SPEC.md`: diff review, the live activity log, a live preview pane of the running app as it's built (not just logs — watch it develop), a visual point-and-click edit mode for layout/spacing/color tweaks that doesn't require a code round-trip, a build checkpoint/rollback system distinct from deployment rollback (undo a bad direction mid-build, not just a bad deploy), and the GitHub/local-folder import from screen 7.

**DoD:** a real person completes a real build, start to finish, without touching anything outside the desktop app.

### 12 — Mobile app & session persistence
Thin client only. Don't build a separate native codebase for this — no AI app builder in this space produces native iOS/Android binaries directly; the standard, proven pattern is a thin native shell (Capacitor or equivalent) around the same web surface the desktop app already has, and there's no reason to be the exception here. Push notifications, voice capture, approve/reject. A long-running build survives the app closing or a network drop and resumes correctly.

**DoD:** a build started from the mobile app can be reviewed and approved from the desktop app, and survives closing both apps mid-run.

## Out of scope — do not build these

Earlier drafts of this spec ballooned into 258 "components" across nine layers by the end — the last of which described an autonomous product-management council, a research lab that runs its own experiments, and a self-governing federation of AI organizations with a written constitution. None of that is this product. Specifically, do not build:

- An organizational-learning layer that gives the platform its own long-term "memory," "reputation," or evolving institutional identity — that's a research problem, not a product requirement.
- An autonomous business or product-management layer — market intelligence, roadmap generation, a "product council" that makes prioritization calls. The human is the product manager. The system builds what it's told.
- A general "AI operating system" abstraction — global scheduler, event bus, speculative or branching execution across hypothetical futures. A task queue and a worker pool are enough at this scale.
- An autonomous research function — hypothesis generation, experiment design, peer review, patent search. This system builds software. It doesn't discover science.
- Any multi-organization federation, marketplace, or governance layer between separate autonomous AI companies.

If a future revision of this spec starts drifting back toward any of these, that's the signal to stop and cut it, not to keep building.

## Working constraints

- Models are accessed via API from existing providers — this project is not training or hosting its own foundation model. Keep the provider layer abstracted so swapping or adding a provider doesn't touch calling code.
- Respect the license of everything pulled in. Default to MIT/Apache-2.0-licensed dependencies. Specific recommended tools and their licenses are in `ARCHITECTURE.md` — follow that rather than picking the first popular library for a given job.
- Pin model versions explicitly and keep a deprecation watch. Providers retire specific model versions on their own schedule, and a saved config silently breaking on that is a real failure mode here, not a hypothetical one.
- Build an internal evaluation set from real specs run through this system, and track real resolution rate. Don't lean on public benchmarks like SWE-bench as a substitute for that — they're contaminated by memorization and don't reflect messy real codebases.

## Where the rest of the detail lives

- `RULES.md` — the operating rules. Read first, not last.
- `ARCHITECTURE.md` — the full subsystem breakdown, two data flow diagrams, the tech stack and license table, and the model routing strategy.
- `UI_SPEC.md` — every screen, its layout regions and states, navigation, and the full design system (colors, type, icons, spacing, UI writing rules) for both the desktop and mobile apps.
- `API_SPEC.md` — every endpoint, request and response shape, the core data models, and error format the frontend is built against.
- `VERIFICATION_CHECKLIST.md` — what to actually check before trusting any phase's "done" status. Use this every time, not just once.
- `BACKLOG.md` — real production concerns deliberately not in this build yet, sorted by when each one actually becomes relevant. Not a signal to build early.

Treat all six as the living source of truth while building — update them when the design changes, and don't let this prompt drift out of sync with them.
