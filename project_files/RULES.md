# Rules

Read this before `MASTER_PROMPT.md`, before anything else. These aren't style preferences. Every one of them exists because it already went wrong once, for real, on this exact project.

## 1. Never modify a test to make it pass
A failing test means the code is wrong until proven otherwise — not the test. If you genuinely believe a specific test is written incorrectly, stop, say exactly why in plain language, and wait for confirmation before touching it. Weakening an assertion, deleting a case, or loosening a tolerance so broken code passes is the same category of problem as reporting a fake result directly. There is no version of this that's a minor judgment call.

## 2. Never return fake or example data where a real implementation belongs
If something isn't built yet, it returns an explicit error or a clearly labeled "not implemented" — never a plausible-looking placeholder someone could mistake for real output. This already happened: a project-summary endpoint once returned a hardcoded fake project with a made-up cost figure, and two security scanners once returned "passed" without scanning anything at all.

## 3. Never mock the exact dependency a test exists to verify
Mocking something unrelated to isolate a test is normal and fine. Mocking the model router in a test that exists specifically to prove a real model call works, or mocking the sandbox in a test that exists specifically to prove real sandboxed execution works, isn't testing — it's manufacturing the appearance of a test. This already happened, on this project's Phase 1 test, on the two things its own DoD said had to be real.

## 4. Nothing is "done" without real, pasted evidence
Writing the code isn't done. Importing without errors isn't done. Done means: run for real, against the real dependency, with the actual output pasted as evidence. "It should work" and "I ran it and here's what happened" are different claims. Only make the second one, and only when it's true.

## 5. When something is ambiguous, stop and ask — don't guess
Everything load-bearing is supposed to already be in `MASTER_PROMPT.md`, `ARCHITECTURE.md`, `UI_SPEC.md`, or `API_SPEC.md`. If something isn't covered and the answer would actually change what gets built, say precisely what's missing and wait. Don't pick a reasonable-sounding default and move on silently — an unstated assumption is indistinguishable from a mistake until someone finds it.

## 6. When something is broken or blocked, say so immediately, in plain language, in the first sentence
Not as a footnote after a bigger claim of success. Not softened to sound smaller than it is. Worth saying plainly: this already went right once on this project — Docker being unreachable got reported honestly instead of worked around or hidden. That's the standard. Keep hitting it.

## 7. No silent substitutes
If the spec calls for real sandboxed execution and Docker isn't available, the answer is "blocked, here's exactly why" — not quietly running the code unsandboxed and calling it close enough. If a spec'd tool isn't installed, the answer is "blocked" — not a stub faking that tool's output so the pipeline looks green.

## 8. Before writing "complete," "done," "✅," or "verified" anywhere, check yourself against this
- Did I run this for real, against the real dependency, not a mock of it?
- Did I paste the actual output, not a description of what the output would probably look like?
- If a skeptical second engineer read only this claim and the evidence next to it, would they be convinced, or would they have follow-up questions?

If the honest answer to any of those is no, the correct status is "not yet," "partial," or "blocked" — say which, and say why, in `VERIFICATION_CHECKLIST.md` terms.

## If you break one of these
Say so the moment you notice, in exactly those words — "I broke rule [n]: [what happened]" — then correct it. Catching your own violation and flagging it is not a failure and won't be treated as one. Getting caught in one without having flagged it first is the only actual failure these rules exist to prevent.
