# 13.4 independent Devices and Grid review

Reviewed 2026-10-11. **ACCEPT bounded software/reference closure.** No
remaining demonstrated P0/P1 in the reviewed changes. This reviewer changed no
13.4 application code and launched no connected tests during the parent run.

Inspected the actual native `13-4-reference-grid.png` first. The restrained node
rows show admitted health/pairing and reveal details on demand. The shared Orb
remains compact. A real isolated reference Desktop-origin task is visible, with
its private request replaced by `Private OSCAR interaction`; it is not physical
Desktop-to-phone acceptance. That Desktop advertises no executor capabilities,
and the UI says so. A task associated with both source Desktop and target Cloud
is labelled associated work, not two executing Workers. No power/wake control
or available Home Node is fabricated.

Read the Devices composition, Core task origin fields, client/session identity,
state sanitation, reference network control and native regression. Task origin
comes from canonical surface associations. Shared task metadata does not transfer
private prompt, response or approval inheritance. Network loss withdraws snapshot,
approval and connected identity; reconnect obtains current authoritative readback.
Local disconnect deletes credentials and clearly preserves the separate remote
revocation obligation. Remote node revocation is unsupported by this Mobile API
and requires trusted Core administration; the UI does not substitute local
deletion for that capability.

Initial P2 findings corrected: `This phone` now requires both matched session
identity and admitted Mobile role; source/target task counts say associated active
tasks instead of implying executor ownership. Future Cloud/Edge nodes appear only
when configured. The unsupported Home Node text is explanatory, not a fake node.

Parent final results: targeted native scenario PASS in 29 seconds; Core 56 PASS;
JVM app 16 + expression 5 PASS. Inspected the native scenario's Desktop origin,
private-data negative, actual isolated HTTP acceptor loss/reconnect and credential
deletion assertions. The reference service's network control is a fixture-only
administrative action, not a product power API. These runs are separately
attributed; this reviewer did not independently execute them. Earlier 13.1–13.3
independent security checks remain recorded in their stage reports.

Not checked: physical cross-device networking, real phone/OEM, remote revocation
or power management. Remaining risk: small-display/large-font detail density and
final owner judgement belong to 13.8 and consolidated device acceptance.
