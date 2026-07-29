# Backlog

Real items, deliberately not in the current build. Each one gets pulled in when its trigger condition is actually true — not before, and not all at once on spec. Adding any of these before its trigger is true means designing for a problem that doesn't exist yet, at the cost of the one that does.

## Trigger: once phases 1-4 pass their DoD for real
Nothing new needed here — this is the actual current gate. Everything below waits for this regardless of how it's organized.

## Trigger: once there's a second real paying account
- Multi-tenant architecture (isolation beyond what `ARCHITECTURE.md` subsystem G already scopes for a single account)
- Team/org billing and permissions (see `API_SPEC.md`'s note on this — deliberately deferred there too)
- API versioning
- Rate limiting and quotas per account
- Approval workflows for multi-person teams (distinct from the single-user diff approval already specced)

## Trigger: once it's actually deployed and carrying real traffic
- Monitoring dashboards (beyond the Cost/Deploy tabs already specced)
- Error reporting and incident management
- Analytics and telemetry
- Performance budgets
- Cache invalidation strategy
- Backup and restore
- Disaster recovery runbooks
- Offline behavior, if the mobile client needs it once real usage shows whether it does

## Trigger: once there's real design work to formalize, not invent
- A full design token system and component library doc (the design system in `UI_SPEC.md` is real but lightweight on purpose)
- A formal accessibility requirements document (axe-core scanning already runs — this is the policy layer on top of it)
- Internationalization readiness

## Trigger: once real concurrency or scale makes it necessary
- Formal background job queue infrastructure (the task graph and async execution already specced cover this until real load says otherwise)
- Build reproducibility guarantees
- Formal per-agent-step observability (the activity log and audit trail already cover this at the level currently needed)

## Ongoing practice, not a one-time document
- CI/CD pipelines and release gates
- Prompt versioning
- Model evaluation and benchmarking (the internal eval set in `MASTER_PROMPT.md` is the seed of this — it grows with real usage, it isn't written once)
- Data retention policy
- Plugin/extension architecture (only worth designing once there's a real second thing wanting to extend it)

## Explicitly not planned regardless of trigger
- Anything from `ARCHITECTURE.md`'s "Out of scope" list — the organizational-learning layer, autonomous product council, AI-operating-system abstraction, research function, multi-org federation. Those aren't deferred, they're excluded.
