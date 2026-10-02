# ADR 0011: Admin sidebar stays expanded

## Status

Accepted

## Context

The admin lists every registered model in a sidebar. An earlier version of that sidebar could collapse to a 64px rail of icons.

Every model used the same list icon. Collapsed, Users and Groups (and any other model) looked identical. The name was only available as a tooltip, which does not work when you are scanning the rail. The collapse control existed to save horizontal space, and it removed the only thing that distinguished one model from another.

App groups inside the sidebar are a different control. Collapsing a group hides that group's models, and opening it shows their names again.

## Decision

The admin sidebar does not collapse. It stays at its open width and shows each model's name. There is no collapse control in the top bar.

The FastFrame header at the top of the sidebar links to the dashboard (Overview).

App groups in the sidebar can still be collapsed. Sidebar search remains the way to jump to a model when the list is long.

## Consequences

- A project with many models uses sidebar search and collapsible app groups, not an icon rail.
- Admin UIs copied with `startadmin` should keep this. A collapsed rail needs a distinct icon per model, and that change needs a superseding ADR.
