# Step Protocol

Use this checklist for every browser step.

## One-step loop

1. Snapshot first.
   - Prefer aria refs or role/name refs.
   - Record the current URL/state if it matters.
2. Confirm the target.
   - Match ref, role, accessible name, label, or stable selector.
   - If uncertain, inspect with evaluate or selector queries.
3. Perform one action only.
4. Re-snapshot.
5. Verify the expected result before continuing.

## Evidence to look for

- Snapshot ref for the element
- Accessible name / role
- Stable selector or DOM attribute
- URL change
- Dialog/modal presence
- Text appearing or disappearing
- Form value updated
- Disabled/enabled state changed

## Avoid

- Blind repeated clicks
- Acting on stale refs after a page update
- Combining multiple actions before verification
- Guessing from visuals when a deterministic ref exists

## Fallback when verification fails

1. Stop.
2. Snapshot again.
3. Re-inspect the DOM/selector state.
4. Explain what changed.
5. Choose the next single action from the new evidence.

## Destructive actions

Before delete/submit/publish/purchase/account-setting changes:
- confirm intent if not already explicit
- inspect the exact control one more time
- perform the single destructive action
- re-snapshot and verify outcome
