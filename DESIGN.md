---
version: alpha
colors:
  background: "#101827"
  text: "#e8edf5"
  muted: "#98a3b7"
  line: "#303b4e"
  error: "#fb716d"
typography:
  sans:
    fontFamily: "system-ui, -apple-system, 'PingFang SC', sans-serif"
  data:
    fontFamily: "system-ui, -apple-system, 'PingFang SC', sans-serif"
rounded:
  panel: "14px"
  control: "9px"
  pill: "999px"
spacing:
  panel: "24px"
components:
  panel:
    backgroundColor: "{colors.background}"
    textColor: "{colors.text}"
    rounded: "{rounded.panel}"
    padding: "{spacing.panel}"
---

## Overview

The original Financial Freedom workspace is the canonical design and interaction source. Reuse its page modules, shared UI helpers, and stylesheet in `ui/original`; preserve their structure, labels, states, charts and controls. DSH owns the conversation shell and high-frequency entries. The embedded workspace omits its duplicate sidebar and uses a small return-to-chat control plus a compact workspace-tools rail that expands over the content on hover or keyboard focus.

## Colors

`ui/original/styles.css` owns the original dark financial workspace palette and market-direction convention. `ui/original/dsh-embed.css` maps the workspace tokens to a light palette. Users choose light or dark with the persistent control above the embedded workspace; this is independent of the A-share / US market color convention. DSH owns the surrounding shell. Financial values must retain their source and freshness; cached prices are not presented as live prices.

## Typography

The original workspace stylesheet and shared numeric formatting own typography and the Chinese locale. The DSH shell uses its own font.

## Layout

The original content header, page structure, scrolling, and optional utility rail remain intact. DSH navigation supplies high-frequency entry points; additional tools appear in the workspace left icon rail, expanding on hover or keyboard focus. Embedded content adapts to the remaining viewport without duplicating the original navigation sidebar.

## Elevation & Depth

Reuse the original panel, header and chart styles. Avoid adding a second design system around source page content.

## Shapes

Original workspace component styles own borders, spacing and control shapes.

## Components

Use the copied original page modules and `ui.js` for workspace components. Adapt API contracts in `ui/original/dsh-api.js`; report unavailable capabilities rather than inventing data. Preserve keyboard and loading/error behavior.

## Do's and Don'ts

- Match the original page first; preserve DSH navigation and sessions.
- Keep original market source and time labels, including stale-cache disclosure.
- Clearly identify operations whose backend is not yet available.
- Do not reintroduce the former agent as the DSH agent.

## Workspace mark

The workspace rail uses an original geometric F and rising line in `ui/original/finfreedom-mark.svg`, designed for legibility at 24 px against the DSH rail. This artwork has not been cleared by a trademark search.
