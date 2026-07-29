# UI specification

Companion to `MASTER_PROMPT.md` and `ARCHITECTURE.md`. This is the frontend contract: every screen, its layout regions, its states, and the design system behind it. Treat every decision here as settled, not a suggestion — if something needed here isn't specified, that's a gap to flag back, not a gap to fill in with a guess.

## Design system

Dark-mode first — this is a developer control panel read for hours at a stretch, not a marketing page, and most of what fills the screen is code, diffs, and logs. Light mode is a later toggle, not a v1 requirement.

**Color** (hex values are the actual tokens, not placeholders):
- Background: `#0E0F12`
- Surface (cards, panels): `#17191D`
- Border / divider: `#2A2D33`
- Text primary: `#E8E9EB`
- Text secondary: `#9A9DA6`
- Accent (primary actions, links, focus rings): `#6366F1`
- Status – in progress: `#3B82F6`
- Status – success / passed / healthy: `#22C55E`
- Status – needs attention: `#F59E0B`
- Status – failed / blocked: `#EF4444`

Status colors are reserved for status — never reuse them for decoration. If it's not communicating running/passed/warning/failed, it doesn't get one of these four colors.

**Typography:**
- UI text: Inter. Chosen for legibility at small sizes across a dense dashboard, not for personality — this interface has a lot of small labels and status text competing for space, and that's the wrong place to spend a distinctive type choice.
- Code, diffs, logs: JetBrains Mono. Chosen specifically because it visually distinguishes `0`/`O` and `1`/`l`/`I` — reading a diff wrong because of font ambiguity is a real failure mode here.
- Scale: 12 / 14 / 16 / 20 / 24 / 32px. Body text is 14px. Never go below 12px.

**Icons:** Lucide, outline style, 1.5px stroke. 20px in the nav rail and tab bars, 16px inline with text, 14px in dense table rows. Icons are navigation and action affordances only — never decorative, never standalone without a text label the first time a user sees them.

**Spacing:** 4px base unit. Scale: 4 / 8 / 12 / 16 / 24 / 32 / 48px. Card padding is 16px. Section gaps are 24px.

**Writing in the UI:**
- Name things by what the person controls, not how the system is built. "Notifications," not "webhook config."
- Buttons name the action and keep that name through the whole flow: a button that says "Deploy" produces a status that says "Deployed," never "Submitted" or "Success."
- Errors state what happened and what to do next, in plain language, never apologize, never say just "Something went wrong."
- Empty states are an invitation to act, not a blank space: "No projects yet — describe what you want to build" with the primary action right there, not a gray placeholder icon alone.

## Desktop app — screens

The desktop app is the full control surface. Persistent left nav rail (72px wide, icon + label, collapsible to icon-only at 56px): Home, Settings.

### 1. Home
- Top bar: page title "Projects," search input (right-aligned), primary button "New project" (top-right, accent color) — opens a small menu with three entry points: **Describe an idea** (screen 2), **Import from GitHub**, **Import a local folder** (both screen 7)
- Main area: card grid, 3 columns at desktop width, 1 column below 768px. Each card: project name, phase badge (one of the six phase names, colored by status not by phase), status text, thin progress bar, "updated Xm ago"
- Empty state (zero projects): centered, single column — one line of text, the "New project" button, nothing else on the page

### 2. New project (idea intake)
- Centered single column, max-width 640px, generous vertical whitespace — this is a blank-page moment
- Large multi-line text area, placeholder text shows a realistic example idea, not "Lorem ipsum"
- Secondary, less prominent: "Attach reference files" (optional file drop)
- Primary button: "Analyze" — disabled until the text area has content
- Submitting transitions to screen 3, replacing this view (not a new page)

### 3. Clarifying questions
- Single column, max-width 640px
- Two sections, always both visible:
  - **"Needs your input"** — every blocking question, expanded by default, required before continuing. Each: question text, one-line "why this matters," and an input control matched to the question type (short text / single-select / toggle — never a free-text box for something that's actually a choice between two options)
  - **"Filled in automatically"** — collapsed by default, one line each showing the assumption made, with a visible "Edit" link per item. Expanding one reveals the same input control as a blocking question, pre-filled with the default
- Bottom bar, sticky: "Start building" — disabled until every blocking question has an answer

### 4. Project workspace
This is the main screen and the most complex one — a person will live here.
- Top bar: project name (click to rename inline), current phase as a stepper across the top (twelve phases per `MASTER_PROMPT.md`, current one highlighted, completed ones checked — shown grouped into the same four bands as the phase stepper's tooltip, since twelve raw dots is too dense to scan at a glance), a **Checkpoints** icon button (small clock/history glyph) next to pause/resume, and the pause/resume control itself
- Checkpoints: opens a small list, one entry per major build milestone (auto-created at each phase's DoD and after any accepted diff), each with a timestamp and one-line description, and a "Restore" action. This is build-state rollback — undoing a bad direction mid-build — and is distinct from the Deploy tab's rollback, which is about live, already-shipped environments. Restoring a checkpoint is itself a confirmable action (a plain "this will discard everything after this point, continue?" prompt), not a silent revert.
- Below the top bar: six tabs — **Activity**, **Preview**, **Diffs**, **Tests**, **Cost**, **Deploy**

**Activity tab** (default tab):
- Live-updating vertical log stream, newest at bottom, auto-scrolling unless the user has scrolled up
- Each entry: timestamp, a small colored dot for which role produced it (generator / critic / verifier / blind tester — four distinct but muted colors, not the four status colors, so they're never confused with pass/fail state), one line of what happened
- Filter chips above the stream: All, Generator, Critic, Verifier, Blind tester
- Sticky input at the bottom of this tab only: "Direct the build" — free-text, for mid-build natural-language redirection ("use Postgres instead of SQLite," "hold off on the payments task"). This is distinct from Diffs-tab approvals: it's steering, not a checkpoint response, and it queues as a new high-priority task rather than blocking the current one

**Preview tab:**
- A live rendering of the app as it's actually being built, in an embedded frame — not a description of it, the running thing, refreshing as tasks complete. Empty/loading state before anything is renderable yet: "Nothing to preview until the first task completes," not a blank frame.
- A toggle in the tab's top-right: **Visual edit mode**. On: click any element in the preview to select it, a small side panel offers spacing/color/typography/layout controls scoped to that element. Changes here don't touch code directly — they queue as a task the same way the "Direct the build" input does, so they go through the same generate/verify loop as everything else rather than silently patching the DOM. Off by default; this is a deliberate choice on the person's part, not the default interaction mode.

**Diffs tab:**
- Two-pane: file tree on the left (240px), diff viewer on the right, monospace, standard red/green line highlighting using the status colors above
- Diffs are grouped by task, collapsible per task
- Where a checkpoint needs human sign-off: an inline banner above that diff, "Review needed before continuing," with Approve / Request changes buttons — never silently auto-advances past a flagged checkpoint

**Tests tab:**
- Summary row at top: five counts (Acceptance, Differential, Property-based, Mutation, Blind-adversarial), pass/fail as colored numbers
- Below: a table, one row per test — name, discipline, status, and for tests with history, a small sparkline of pass/fail over recent runs plus a flakiness score
- Failed tests expand inline to show the failure detail, not a separate page

**Cost tab:**
- A horizontal bar: spend so far vs. cap, colored by how close to the cap (green under 70%, amber 70-90%, red above 90%)
- Breakdown below: spend by tier (fast / mid / frontier), as a simple horizontal bar per tier
- "Forecasted total" as a single line, with the basis for the estimate (e.g., "based on remaining task count")

**Deploy tab:**
- Environment cards (Staging, Production side by side): current version, status, and for production, canary percentage if a rollout is in progress
- "Roll back" button — only enabled when a previous stable version exists to roll back to, disabled with a tooltip explaining why otherwise
- Custom domain row under the Production card: connected domain name if one exists, else a "Connect a domain" action. Status shown plainly — "Pending DNS," "Connected," "Certificate error" — this is a common enough failure point (DNS propagation, misconfigured records) that a vague "connecting..." spinner isn't good enough

### 5. Escalation banner (not a separate page)
- Appears as a persistent, non-dismissible banner at the top of the workspace when something is blocked — a cost cap hit, a high-stakes ambiguity, a repeated failure past the retry cap
- Plain-language statement of what's blocked and why, then explicit action buttons for the actual decision (e.g., "Raise cap by $20" / "Pause here"), never just a free-text box when the decision is really a choice between known options

### 6. Settings
Six sections in a single scrollable page, not sub-tabs (grouped, but still short enough not to need them):
- **Model routing** — a three-row table, one per tier (fast / mid / frontier), each with a provider dropdown and a model field
- **API keys** — one row per provider, key input is write-only (never redisplays a saved key, shows only "Connected" + a Rotate action)
- **Cost caps** — default cap per project, editable
- **Notifications** — toggle list: build complete, blocked/needs input, deployment failed, cost cap approaching
- **Integrations** — GitHub: "Connect" button if not linked, else the connected account name + "Disconnect." Once connected, repos become pickable from screen 7.
- **Billing** — current plan name, usage this period against plan limits (a bar, same visual language as the Cost tab), payment method (masked, "Update" action), a link to invoice history. Nothing here is load-bearing until there's more than one paying account — see `API_SPEC.md`'s billing section for the same caveat.

### 7. Import project
Reached from Home's "New project" menu, two entry paths on one screen (tabs or a toggle, not separate pages):
- **From GitHub**: list of repos from the connected account (search/filter above the list), each row shows name, visibility (public/private), last updated. Selecting one moves straight to screen 3 (clarifying questions) — the "idea" in this case is inferred from the repo itself rather than typed.
- **From a local folder**: a native folder picker (desktop only; this path doesn't exist on mobile — mobile shows GitHub only, with local folders deep-linking to "Continue on desktop"). Once picked, same as above: straight to screen 3.
- If GitHub isn't connected yet, the GitHub tab shows the same "Connect" action as Settings, inline, so this isn't a dead end.

## Mobile app — screens

Thin client only. No diff viewer, no log stream, no test table — those stay on desktop. If a screen below would need any of those to be useful, it links out to "Continue on desktop" instead of trying to fit them on a phone.

### 1. Home
- Simple vertical list, one row per project: name, phase badge, status dot. Tap opens screen 5.
- Floating action button, bottom-right: new project

### 2. New idea (mobile)
- Same as desktop screen 2, single text area, plus a microphone icon inside the input for voice capture — tap to record, transcribed text appears in the field, editable before submitting
- Same "Analyze" button behavior

### 3. Clarifying questions (mobile)
- One question per screen, not a scrolling list — swipe or tap "Next" to advance
- Same blocking/auto-filled distinction as desktop, auto-filled questions shown after all blocking ones, with the same edit affordance
- Progress dots at the top showing position in the question set

### 4. Notifications
- Standard system push notifications: build complete, blocked, deployment status. Tapping one deep-links to screen 5 or directly to an approval action

### 5. Project status (read-only summary)
- Phase stepper (same states as desktop), current activity as a single line of text (not the full log), test pass count, cost spent vs. cap as a single bar
- If something needs approval: the same plain-language escalation content as the desktop banner, with the same explicit action buttons, full-width on this screen
- "Open on desktop" link at the bottom for anything needing the diff viewer or full logs

### 6. Settings (mobile)
- Notification toggles only (same list as desktop). Everything else — model routing, API keys, cost caps, integrations, billing — shows as read-only with "Edit on desktop."
