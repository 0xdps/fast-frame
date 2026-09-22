# ADR 0007: Server-Side Rendering for Admin (v0.3)

## Status

Accepted

## Context

FastFrame v0.3 aims to provide a Django-admin-like interface. Must decide between:
- **SSR (Server-Side Rendering)**: Jinja2 templates, traditional request/response
- **CSR (Client-Side Rendering)**: React/Vue SPA, API-driven

Django admin's major pain points:
- N+1 queries, unbound FK selects, poor mobile UX, no real-time updates
- But also: dated UI, hard to customize, performance traps

## Decision

**v0.3 will use Server-Side Rendering (SSR)** with progressive enhancement via htmx + Alpine.js.

**Stack:**
- FastAPI (async Python)
- Jinja2 templates
- htmx (12KB) for partial updates without page reloads
- Alpine.js (15KB) for client-side interactivity
- Tailwind CSS for styling

**NOT building:**
- Mobile-responsive admin (admin is a power-user desktop tool)
- Full SPA (React/Vue)
- Offline/PWA capabilities

## Rationale

**1. Faster Time to Market**
- No build toolchain (Webpack, Vite, npm)
- Jinja2 already planned for v0.5 (templates/static)
- Can reuse Django admin HTML structure as starting point

**2. Performance for Typical Usage**
```
Admin list view (50 rows):
- SSR: Server renders in ~50ms, browser displays immediately (15KB HTML)
- CSR: ~2s first load (500KB JS bundle), then fast after

For occasional admin use (not 8hrs/day), SSR is faster.
```

**3. Security & Compliance**
- No client-side state management complexity
- CSRF/sessions work naturally
- Easier to audit (no XSS from client rendering)

**4. Django-Like DX**
- Users expect Django admin = SSR
- Familiar form submit → validate → re-render pattern

**5. Progressive Enhancement**
```html
<!-- Works without JS, enhanced with htmx -->
<input hx-get="/admin/api/search" hx-trigger="keyup delay:300ms">
```
- Autocomplete, inline editing, bulk actions via htmx
- Falls back to full page loads if JS disabled

## Consequences

**Positive:**
- Simpler to build and maintain
- Better first-page performance
- Works in restricted environments (corporate proxies)
- No JS dependency hell

**Negative:**
- Real-time collaboration harder (need SSE/polling vs WebSockets)
- Heavy admin users may want SPA eventually
- Some interactions require server roundtrips

**Mitigation:**
- v0.4+ can offer optional `fastframe-admin-spa` package
- Power users can build custom views with FastAPI + React
- htmx reduces "feel" of server roundtrips (partial updates)

## Alternatives Considered

**React Admin / Vue Admin:**
- Rejected for v0.3 due to complexity and build time
- May revisit as optional package in v0.4+

**No admin at all:**
- Rejected - admin is a core Django feature users expect
- Third-party tools (Retool, Forest) don't match Django's ease

## Related Decisions

- ADR 0003: Thin ORM (admin needs field introspection)
- Upcoming: Field API design (admin auto-generates forms from it)
- v0.5: Templates/static (admin is the first Jinja2 consumer)
