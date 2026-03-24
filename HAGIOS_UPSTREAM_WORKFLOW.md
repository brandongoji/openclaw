# Hagios Upstream Overlay Workflow (Hagios 1 + Hagios 2)

## Purpose
Maintain custom Hagios features while staying compatible with upstream OpenClaw updates.

## Roles
- **Hagios 2 (backup/fixer):** update gate, validation, rollback prep, recovery actions.
- **Hagios 1 (active):** daily runtime with approved custom overlays.

## Rules
1. Prefer skills/plugins/overlay before core edits.
2. If core edits are unavoidable, keep them minimal, isolated, and documented.
3. Never merge upstream directly into production runtime without gate validation.

## Branch Model
- `upstream/main` (read-only reference)
- `hagios/base-sync` (clean sync branch)
- `hagios/custom` (your feature branch)
- Optional release branches: `release/YYYY-MM-DD`

## Update Cycle
1. Fetch upstream OpenClaw changes.
2. Update `hagios/base-sync` from upstream.
3. Rebase/merge `hagios/custom` onto new base.
4. Resolve conflicts, favoring original-source behavior unless custom behavior is intentional.
5. Build and smoke-test on Hagios 2.
6. Run regression checklist (below).
7. Promote to Hagios 1 only after pass.

## Regression Checklist (Gate on Hagios 2)
- Core UI loads and nav/session switching works.
- Chat send/receive works.
- Attach/upload flow works.
- Skills still trigger and behave as expected.
- Messaging channels still function (at minimum configured critical channels).
- Cron jobs and automation still run.
- No unexpected config migration or doctor errors remain unresolved.

## Custom Surface Map (keep updated)
Track every non-upstream customization:
- File/path
- Why it exists
- Risk level
- Owner
- Replacement plan (move to skill/plugin?)

## Rollback Plan
- Keep last known-good release artifact/config snapshot.
- If post-update checks fail on Hagios 1:
  1. Stop promotion
  2. Revert to last known-good
  3. Re-run failed checks on Hagios 2
  4. Patch in `hagios/custom`, then retry gate

## Cross-Instance Delegation Standard
For Hagios 1 -> Hagios 2 handoffs, include:
- `From: Hagios 1`
- `To: Hagios 2`
- Objective, constraints, deliverable, minimal context only

## Success Criteria
- Upstream updates stay regular.
- Custom features survive updates with low conflict overhead.
- Hagios 2 can always recover/repair Hagios 1.
