## Summary

<!-- What does this change do? -->

## Slice / scope

<!-- Which OSCAR slice or sub-slice does this belong to? -->

- Slice:
- Scope:

## Why this path

<!-- Why is this the simplest suitable implementation/delegation approach? Mention alternatives considered when relevant. -->

## Completion condition

<!-- What observable state proves the scoped objective is complete? -->

## Engineering review

- [ ] Scope is the smallest coherent solution; no speculative framework/abstraction added
- [ ] Responsibilities/boundaries are clear and coupling is intentional
- [ ] Shared behavior is reused without premature abstraction
- [ ] External/cross-component contracts are typed/validated where relevant
- [ ] Authoritative state ownership is clear
- [ ] Timeout/retry/reconnect/cancellation/idempotency behavior considered where relevant
- [ ] New dependency justified and isolated appropriately
- [ ] Security/permission checks live at authoritative execution boundaries
- [ ] Critical-path performance measured or budgeted where relevant
- [ ] Tool/Worker/model success reports are not treated as verified completion without evidence

## Test checklist

- [ ] Core behavior tested
- [ ] Failure/error path tested
- [ ] Disconnect/offline behavior tested where relevant
- [ ] Cancellation/retry/concurrency behavior tested where relevant
- [ ] Safety/security implications reviewed where relevant
- [ ] Hardware verified on-device where relevant
- [ ] UI visually verified where relevant

## Verification evidence

<!-- Distinguish execution success from objective verification. Link/describe authoritative evidence. -->

- Verification state: `verified | partially_verified | blocked | failed | unknown`
- [ ] Resulting repository/runtime/device/API state inspected after execution
- [ ] Independent verification used where practical
- [ ] Unverified surfaces/limitations listed below

Evidence:

- Add evidence here.

## Documentation

- [ ] `README.md` status/current position updated if needed
- [ ] `docs/ROADMAP.md` updated if needed
- [ ] Relevant domain docs updated
- [ ] `docs/DECISIONS.md` updated for architectural changes
- [ ] `ENGINEERING.md` updated if a durable engineering rule changes
- [ ] `CHANGELOG.md` updated for a milestone/user-visible change
- [ ] Updated canonical docs were re-read/checked before claiming propagation is complete

## Limitations / follow-ups

<!-- Be explicit. Do not hide unfinished or unverified behavior behind demo/success states. -->
