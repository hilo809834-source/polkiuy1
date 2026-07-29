# API specification

Companion to `MASTER_PROMPT.md`, `ARCHITECTURE.md`, and `UI_SPEC.md`. This is the backend contract every screen in `UI_SPEC.md` is built against. REST over HTTPS, JSON bodies, except where a screen needs a live stream (noted explicitly below).

## Conventions

- Base path: `/api/v1`
- Auth: bearer token in the `Authorization` header. Token issuance/login flow is intentionally out of scope for Phase 1-2 — single-user local use doesn't need it yet; add it as its own spec before Phase 6 multi-user work starts, don't guess a scheme now and lock it in early.
- All timestamps: ISO 8601, UTC.
- All IDs: strings (UUIDv4).
- Standard error shape, every non-2xx response:
```json
{
  "error": {
    "code": "cost_cap_exceeded",
    "message": "This project hit its $20 cost cap for the Quality phase.",
    "details": {}
  }
}
```
`code` is a stable, machine-readable snake_case string. `message` is the plain-language version shown directly in the UI where relevant — write it the way `UI_SPEC.md`'s writing rules describe, since it may be shown verbatim.

## Core data models

```
Project {
  id: string
  name: string
  phase: "foundation" | "core_loop" | "quality" | "hardening" | "existing_codebases" | "access_layer"
  status: "intake" | "questions_pending" | "building" | "testing" | "blocked" | "deployed" | "failed" | "paused"
  created_at: string
  updated_at: string
  cost_spent_usd: number
  cost_cap_usd: number
}

Question {
  id: string
  project_id: string
  text: string
  why_it_matters: string
  tier: "blocking" | "auto_filled"
  input_type: "text" | "select" | "toggle"
  options: string[] | null       // present when input_type = "select"
  answer: string | null
  default_value: string | null   // set when tier = "auto_filled"
  confidence: number | null      // 0-1, only meaningful when auto_filled
  reversibility: "low" | "medium" | "high"
}

Task {
  id: string
  project_id: string
  description: string
  status: "pending" | "generating" | "reviewing" | "verifying" | "blind_testing" | "done" | "failed"
  depends_on: string[]            // other task ids
  needs_review: boolean           // true if this task's diff is a required human checkpoint
}

ActivityEntry {
  id: string
  project_id: string
  task_id: string | null
  role: "generator" | "critic" | "verifier" | "blind_tester" | "orchestrator"
  message: string
  created_at: string
}

TestResult {
  id: string
  project_id: string
  task_id: string
  discipline: "acceptance" | "differential" | "property_based" | "mutation" | "blind_adversarial"
  status: "passed" | "failed"
  detail: string
  flaky_score: number | null      // 0-1, only present for tests with repeat history
}

Deployment {
  id: string
  project_id: string
  environment: "staging" | "production"
  version: string
  canary_percent: number | null
  status: "deploying" | "healthy" | "rolled_back" | "failed"
  created_at: string
}

Escalation {
  id: string
  project_id: string
  reason_code: "cost_cap" | "ambiguous_decision" | "repeated_failure"
  message: string
  actions: { label: string, action_id: string }[]
  resolved: boolean
}

Integration {
  provider: "github"
  connected: boolean
  account_name: string | null
}

Repo {
  id: string
  name: string
  visibility: "public" | "private"
  updated_at: string
}

Subscription {
  plan: string
  usage_current_period: number
  usage_limit: number
  renews_at: string
}

Invoice {
  id: string
  amount_usd: number
  issued_at: string
  status: "paid" | "open" | "failed"
}

Checkpoint {
  id: string
  project_id: string
  created_at: string
  description: string
  trigger: "phase_dod" | "diff_approved"
}
```

## Endpoints

### Projects
| Method | Path | Body | Returns | Notes |
|---|---|---|---|---|
| POST | `/projects` | `{ idea_text: string, reference_files?: string[] }` | `Project` | Kicks off intent understanding async; project starts in `intake` |
| GET | `/projects` | — | `Project[]` | Powers the Home screen |
| GET | `/projects/{id}` | — | `Project` | |
| PATCH | `/projects/{id}` | `{ name?: string, status?: "paused" \| "building" }` | `Project` | Used for rename and pause/resume |
| DELETE | `/projects/{id}` | — | `204` | |

### Intake and questions
| Method | Path | Body | Returns | Notes |
|---|---|---|---|---|
| GET | `/projects/{id}/questions` | — | `Question[]` | Powers screen 3 in `UI_SPEC.md` |
| POST | `/projects/{id}/questions/{qid}/answer` | `{ answer: string }` | `Question` | Also valid for editing an auto-filled default |
| POST | `/projects/{id}/spec/confirm` | — | `Project` | Errors with `code: "blocking_questions_unanswered"` if any blocking question lacks an answer; moves project to `building` |

### Build and orchestration
| Method | Path | Body | Returns | Notes |
|---|---|---|---|---|
| GET | `/projects/{id}/tasks` | — | `Task[]` | |
| GET | `/projects/{id}/activity` | — | `ActivityEntry[]` | Initial load |
| GET | `/projects/{id}/activity/stream` | — | Server-sent events, `ActivityEntry` per message | Powers the live Activity tab; use SSE, not polling |
| GET | `/projects/{id}/diffs` | — | `{ task_id: string, files: { path: string, diff: string }[] }[]` | |
| POST | `/projects/{id}/diffs/{task_id}/approve` | `{ comment?: string }` | `Task` | Required before a `needs_review: true` task continues |
| POST | `/projects/{id}/diffs/{task_id}/request_changes` | `{ comment: string }` | `Task` | Sends the task back to the generator with the comment as context |

### Testing
| Method | Path | Body | Returns | Notes |
|---|---|---|---|---|
| GET | `/projects/{id}/tests` | — | `TestResult[]` | |
| GET | `/projects/{id}/tests/flaky` | — | `TestResult[]` | Filtered to `flaky_score` above a threshold; powers the flaky list |

### Cost
| Method | Path | Body | Returns | Notes |
|---|---|---|---|---|
| GET | `/projects/{id}/cost` | — | `{ spent_usd: number, cap_usd: number, forecast_usd: number, by_tier: { fast: number, mid: number, frontier: number } }` | |
| PATCH | `/projects/{id}/cost` | `{ cap_usd: number }` | Updated cost object | The action behind "Raise cap" on the escalation banner |

### Checkpoints
| Method | Path | Body | Returns | Notes |
|---|---|---|---|---|
| GET | `/projects/{id}/checkpoints` | — | `Checkpoint[]` | Auto-created at each phase's DoD and after any accepted diff — not user-created |
| POST | `/projects/{id}/checkpoints/{checkpoint_id}/restore` | — | `Project` | Discards build state after the checkpoint. This is build-state rollback, separate from deployment rollback below |

### Deployment
| Method | Path | Body | Returns | Notes |
|---|---|---|---|---|
| GET | `/projects/{id}/deployments` | — | `Deployment[]` | |
| POST | `/projects/{id}/deployments` | `{ environment: "staging" \| "production" }` | `Deployment` | |
| POST | `/projects/{id}/deployments/{deployment_id}/rollback` | — | `Deployment` | Errors with `code: "no_rollback_target"` if there's nothing stable to roll back to — this is what disables the button in `UI_SPEC.md` |
| GET | `/projects/{id}/deployments/{deployment_id}/domain` | — | `{ domain: string \| null, status: "pending_dns" \| "connected" \| "certificate_error" }` | |
| POST | `/projects/{id}/deployments/{deployment_id}/domain` | `{ domain: string }` | Same shape as GET | |

### Escalations
| Method | Path | Body | Returns | Notes |
|---|---|---|---|---|
| GET | `/projects/{id}/escalations?resolved=false` | — | `Escalation[]` | Powers the escalation banner on both desktop and mobile |
| POST | `/projects/{id}/escalations/{id}/resolve` | `{ action_id: string }` | `Escalation` | `action_id` must match one of the `actions` offered on that escalation — no free-text resolution path |

### Build direction
| Method | Path | Body | Returns | Notes |
|---|---|---|---|---|
| POST | `/projects/{id}/direct` | `{ message: string }` | `Task` | Powers the "Direct the build" input in `UI_SPEC.md`. Creates a new high-priority task from free text rather than blocking the current one — this is steering, not an approval |

### Integrations
| Method | Path | Body | Returns | Notes |
|---|---|---|---|---|
| GET | `/integrations/github` | — | `Integration` | |
| POST | `/integrations/github/connect` | — | Redirect to GitHub OAuth | Standard OAuth code exchange; store only the resulting token, never credentials |
| POST | `/integrations/github/disconnect` | — | `Integration` | |
| GET | `/integrations/github/repos` | — | `Repo[]` | Powers screen 7's "From GitHub" list |
| POST | `/projects` (extended) | `{ source: { type: "idea", idea_text: string } \| { type: "github_repo", repo_id: string } \| { type: "local_folder", path: string } }` | `Project` | Supersedes the simpler body in the Projects section above — a project now starts from one of three sources, not idea text alone |

### Billing
| Method | Path | Body | Returns | Notes |
|---|---|---|---|---|
| GET | `/billing/subscription` | — | `Subscription` | |
| GET | `/billing/invoices` | — | `Invoice[]` | |
| POST | `/billing/payment-method` | `{ token: string }` | `{ status: "updated" }` | `token` comes from the payment processor's client-side tokenization, never a raw card number |

Billing is single-account scoped for now — it tracks usage and payment for whoever's running this instance, not a multi-tenant permission system. Don't build org/team billing until there's an actual second paying account to design it against.

### Settings
| Method | Path | Body | Returns | Notes |
|---|---|---|---|---|
| GET | `/settings/models` | — | `{ tier: string, provider: string, model: string }[]` | |
| PATCH | `/settings/models` | Same shape as GET | Updated list | |
| POST | `/settings/keys` | `{ provider: string, api_key: string }` | `{ provider: string, connected: true }` | Never returns the key itself, matching the write-only field in `UI_SPEC.md` |
| GET | `/settings/notifications` | — | `{ event: string, enabled: boolean }[]` | |
| PATCH | `/settings/notifications` | Same shape as GET | Updated list | |

## What's intentionally not specified here

Multi-user auth/permissions and team/org management — those belong to a later, genuinely multi-tenant phase in `ARCHITECTURE.md` subsystem G, not the core loop. Billing above is scoped to a single account on purpose, for the same reason. Specify multi-user auth separately once this has actually passed its own DoD for real and there's a second real account to design against; locking in a permissions model now, before Phase 1 has run once, is exactly the kind of guess this document exists to avoid.
