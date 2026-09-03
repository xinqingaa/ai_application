# Fireworks Route

Read this reference only when the user explicitly selects Fireworks IR, “高级版”, “路线二”, or GIF, or when a completed SVG needs a Fireworks-backed export.

## Ownership boundary

The editorial skill remains responsible for the figure claim, audience, abstraction, composition, series contract, and final visual review. Fireworks is a subordinate backend for Diagram IR, routing, SVG rendering, automated checks, and supported exports.

Do not let a Fireworks style silently replace the visual system in `visual-system.md`. Map its IR and style overrides to the project contract where possible. If the renderer cannot express an essential orientation zone, takeaway, boundary, or annotation without weakening the lesson, use Route 1 instead unless the user insists on Route 2.

## Route selection

- Explicit Fireworks, Fireworks IR, “高级版”, or “路线二”: use Route 2.
- Explicit GIF: use Route 2 and verify that the requested topology satisfies a supported Fireworks motion contract.
- PNG or offline HTML without another trigger: keep the already selected authoring route and use Fireworks only for export.
- No explicit trigger: use Route 1.

Never silently switch routes after the user selected one. If the user explicitly permits “路线二不可用就走路线一”, that permission applies only to that request.

## Resolve the backend

Use the bundled bridge; it performs no network access and never installs software:

```bash
python3 skills/editorial-system-diagrams/scripts/fireworks_bridge.py detect
```

A complete backend contains at least `SKILL.md`, `scripts/fireworks.py`, `schemas/diagram-v1.schema.json`, and `references/composition-quality-contract.md`. The bridge checks an explicit `FIREWORKS_SKILL_ROOT`, then Codex skill locations under `CODEX_HOME`, `~/.codex/skills`, and `~/.agents/skills`.

When the backend is missing:

- Route 1: continue only if the bridge's local XML and marker-reference checks pass, perform the ordinary rendered visual review, and report `fireworks_validation: skipped (not installed)`.
- Route 2: stop and report that Fireworks must be installed. Do not auto-install, use `npx`, or run downloaded GitHub scripts. Installation requires an explicit user request.
- An explicit user-approved fallback may switch Route 2 to Route 1; otherwise do not substitute output.

## Author with Diagram IR

After `detect` succeeds, read the installed Fireworks `SKILL.md` and only the Fireworks references required by the selected diagram type and output. Preserve the editorial brief and visual contract already established here.

Create a versioned `.diagram.json` with stable node and edge ids. Prefer source and target ids plus ports over coordinate-only edges. Save the layout report beside the SVG.

```bash
python3 skills/editorial-system-diagrams/scripts/fireworks_bridge.py render-ir \
  architecture diagram.diagram.json diagram.svg \
  --report diagram.layout.json
```

`render-ir` validates the IR before rendering. Do not edit the generated SVG as the primary way to change topology; update the IR and regenerate. A small final SVG correction is acceptable only when it is recorded and does not make regeneration discard the fix.

## Validate every SVG

Run this after either authoring route:

```bash
python3 skills/editorial-system-diagrams/scripts/fireworks_bridge.py check-svg diagram.svg
```

For Route 2, add `--require-fireworks` when checking separately. Fireworks checks XML, marker integrity, component collisions, geometry, and composition. These checks do not replace the editorial rubric or rendered image inspection.

Route 1 SVGs without Fireworks `data-graph-role` metadata receive less semantic coverage. They may gradually add invisible node, edge, container, label, and reserved-region metadata without changing their rendered appearance.

## Derived exports

Offline HTML can wrap the final SVG from either route:

```bash
python3 skills/editorial-system-diagrams/scripts/fireworks_bridge.py export-html \
  diagram.svg diagram.html --title "Diagram title"
```

PNG can be exported from either route when CairoSVG or `rsvg-convert` is available:

```bash
python3 skills/editorial-system-diagrams/scripts/fireworks_bridge.py export-png \
  diagram.svg --type architecture --width 1920
```

GIF is Route 2 only. It requires a Fireworks-generated semantic SVG, a supported motion contract, Puppeteer, and an encoder such as FFmpeg. Run `doctor` first and fail visibly when the required runtime is absent:

```bash
python3 skills/editorial-system-diagrams/scripts/fireworks_bridge.py doctor
python3 skills/editorial-system-diagrams/scripts/fireworks_bridge.py animate diagram.svg diagram.gif
```

Always retain a static SVG fallback for HTML and GIF delivery. Report which artifacts were actually generated and which optional exports were skipped.
