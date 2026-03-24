# Action Log Template

Use or copy this format when documenting a browser run.

```markdown
## Step 1
- Goal: Open the sign-in form
- Inspected evidence:
  - Snapshot ref: [e12]
  - Role/name: button "Sign in"
  - Extra inspection: selector `button[data-test="signin"]` matched 1 element
- Action:
  - click [e12]
- Verification:
  - New snapshot shows dialog "Sign in"
  - URL unchanged
  - Email field present

## Step 2
- Goal: Fill email
- Inspected evidence:
  - Snapshot ref: [e4]
  - Role/name: textbox "Email"
- Action:
  - fill [e4] with `user@example.com`
- Verification:
  - New snapshot shows textbox value populated
```

## Minimum fields

- Step number
- Goal
- Inspected evidence
- Exactly one action
- Verification result

If refs go stale, start a new step with the new snapshot evidence instead of reusing the old line.
