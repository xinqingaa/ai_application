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

Use the bundled bridge. `detect` is read-only; `ensure` and every functional command install the pinned backend on first use when no complete installation exists:

```bash
python3 skills/editorial-system-diagrams/scripts/fireworks_bridge.py detect
python3 skills/editorial-system-diagrams/scripts/fireworks_bridge.py ensure
```

When another script needs the absolute backend path, use the locator/bootstrap wrapper:

```bash
skills/editorial-system-diagrams/scripts/find_fireworks.sh
```

A complete backend contains at least `SKILL.md`, `scripts/fireworks.py`, `schemas/diagram-v1.schema.json`, and `references/composition-quality-contract.md`. The bridge and locator check an explicit `FIREWORKS_SKILL_ROOT`, then the standard per-user skill locations for Codex, shared agents, Claude, and Cursor, followed by `~/.local/share/agent-skills/fireworks-tech-graph`. The bridge also honors `CODEX_HOME` before these per-user locations.

When the backend is missing:

- The bootstrapper downloads the commit pinned in `fireworks-source.lock.json` with Git, validates the expected source tree, and atomically installs it into the shared user path. It never follows mutable `main`, invokes `npx`, or executes remote Fireworks scripts during installation.
- Concurrent first calls share an installation lock so they cannot expose a partial backend.
- If installation fails, both routes stop with the underlying network, Git, permission, or integrity error.
- Route 1 may use `check-svg --allow-basic-fallback` only after the user explicitly requests an emergency offline fallback. Route 2 never uses the basic fallback.
- `FIREWORKS_SKILL_ROOT` remains the explicit location override. Updates require changing the pinned commit and validating it; normal calls never auto-upgrade.

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
