## Summary

<!-- What does this change do? -->

## Slice / scope

<!-- Which OSCAR slice or sub-slice does this belong to? -->

- Slice:
- Scope:

## Why this path

<!-- Why is this the simplest suitable implementation/delegation approach? Mention alternatives considered when relevant. -->

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

## Test checklist

- [ ] Core behavior tested
- [ ] Failure/error path tested
- [ ] Disconnect/offline behavior tested where relevant
- [ ] Cancellation/retry/concurrency behavior tested where relevant
- [ ] Safety/security implications reviewed where relevant
- [ ] Hardware verified on-device where relevant
- [ ] UI visually verified where relevant

## Documentation

- [ ] `README.md` status/current position updated if needed
- [ ] `docs/ROADMAP.md` updated if needed
- [ ] Relevant domain docs updated
- [ ] `docs/DECISIONS.md` updated for architectural changes
- [ ] `ENGINEERING.md` updated if a durable engineering rule changes
- [ ] `CHANGELOG.md` updated for a milestone/user-visible change

## Limitations / follow-ups

<!-- Be explicit. Do not hide unfinished behavior behind demo states. -->
