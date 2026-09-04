---
name: editorial-system-diagrams
description: Design, review, or rework publication-quality technical diagrams when editorial hierarchy, conceptual clarity, or series consistency matters. In this repository, orchestrate both the default direct-SVG route and an explicitly requested Fireworks IR route. Do not use for quantitative data charts, freeform illustration, or decorative imagery.
---

# Editorial System Diagrams

Create diagrams that teach one important relationship at a glance. Treat the diagram as an editorial explanation, not an inventory of implementation objects.

## Course-article integration

When this skill is invoked while creating or substantially rewriting a course article, edit the prose and the figure as one explanation. Place the figure where the relationship first becomes necessary. Remove only ASCII flows, lists, or sentences that repeat the figure item by item without adding causes, examples, constraints, or boundaries. A figure does not replace prerequisite recall, narrative reasoning, worked examples, or failure analysis.

Do not trigger a retroactive illustration pass merely because a completed article contains drawable relationships. Typo fixes, factual corrections, link repairs, path migrations, and small wording changes do not require new figures unless the user explicitly requests them.

All course article types may use diagrams. Use them for sequence, state, boundary, hierarchy, comparison, convergence, filtering, feedback, or multi-object handoff when the visual materially reduces explanation cost. Keep exact code, JSON, logs, formulas, and verbatim examples in prose when their exact form is the lesson.

For this repository, the default teaching canvas is `1600 × 900`. Adjust the ratio or height only when the relationship or reading medium requires it; never solve excess scope with smaller type. Store editable course SVGs directly in `course/assets/` as `<three-digit-lesson>.<lesson-slug>.<figure-slug>.svg`. Use matching `prerequisite.` or `reference.` prefixes for unnumbered course material. Derived exports do not replace the SVG source.

## Establish the diagram brief

Before drawing, identify:

- the one sentence the reader should understand;
- the audience and what they already know;
- the relationship to show: sequence, boundary, hierarchy, comparison, convergence, filtering, state change, or feedback;
- the embedding context: the surrounding section heading, what prose has established before the figure, and what prose will explain after it;
- whether this is an inline explanatory figure, a standalone figure, or a reusable figure in a series;
- whether a visible title or lesson identifier adds information that the surrounding article does not already provide;
- the required delivery format and whether editable source is needed.

If the source material supports multiple independent claims, split the figure. Do not solve excess scope by shrinking text or adding nested cards.

## Edit the content before styling

Classify candidate labels into three levels:

1. **Concepts** — durable terms the reader should remember.
2. **Mechanisms** — actions or relationships that explain the concept.
3. **Implementation details** — class names, field names, parameter names, vendors, error codes, and experiment diagnostics.

Use concepts as primary labels and mechanisms as short supporting text. Move implementation details to the surrounding prose, a caption, an experiment, or a separate detail figure unless the implementation itself is the lesson.

Prefer natural-language states such as “structure cannot be parsed” over identifiers such as `structured_output_invalid`. Preserve exact code identifiers only when the user is learning or debugging that identifier.

## Choose a composition

Read [composition-patterns.md](references/composition-patterns.md) when selecting or changing the layout. Choose the smallest pattern that makes the intended relationship obvious without a legend.

Use one dominant reading direction. Keep auxiliary information in a clearly subordinate band, inset, or takeaway—not as an unconnected island beside the main flow.

## Apply the visual system

Read [visual-system.md](references/visual-system.md) when creating a new figure, defining a series, or materially restyling an existing diagram.

For a series, freeze the shared visual contract before producing individual figures: canvas policy, visible-title policy, type scale, spacing unit, card families, connector rules, color roles, icon family, and annotation treatment. Vary the composition when the subject or embedding context requires it, but preserve the visual grammar.

## Select the authoring route

This skill is the only top-level diagram authoring workflow for this repository. Select exactly one authoring route after the brief, content, composition, and visual contract are established.

### Route 1 — direct SVG (default)

Use the existing direct-SVG workflow unless the user explicitly requests Fireworks, Fireworks IR, “高级版”, “路线二”, or a GIF. Preserve the current editorial freedom: write and refine SVG directly when precise hierarchy, custom annotations, takeaway zones, or non-regular composition matters. Keep the SVG as the editable source.

Do not reinterpret a request for PNG or offline HTML as a request for Route 2. Those are export choices applied after the SVG is complete.

### Route 2 — Fireworks IR (explicit only)

Use Route 2 only for an explicit trigger above. A direct GIF request also selects Route 2 because Fireworks motion requires a generated semantic SVG with a supported motion contract. Read [fireworks-route.md](references/fireworks-route.md) before using this route or a Fireworks export.

Route 2 keeps the editorial decisions already made by this skill. Fireworks supplies Diagram IR, routing, rendering, executable geometry checks, and supported exports; its default content hierarchy, visual theme, and palette must not silently replace this project's visual contract. Keep both the `.diagram.json` source and generated `.svg`.

Fireworks is a pinned shared backend dependency. On the first functional call, the bundled bridge searches supported user locations and installs the pinned source into `~/.local/share/agent-skills/fireworks-tech-graph` only when no complete installation exists. Do not invoke `npx`, follow mutable `main`, or copy Fireworks into this repository. If bootstrap fails, stop and report the installation error; use the basic structural fallback only when the user explicitly requests it for that run.

PNG, offline HTML, and GIF are derived artifacts, never the maintainable source. Do not use image generation for diagrams whose labels, topology, or editability must be exact.

## Render and inspect

Inspect the actual rendered result, not only its source. Check it at intended display size and at a reduced size representative of the final reading context.

After either route produces SVG, run `scripts/fireworks_bridge.py check-svg <file.svg>`. The bridge bootstraps Fireworks when needed, then runs XML, marker, collision, geometry, and composition checks. A failed check or bootstrap requires correction and rerun; it is not an unavailable-backend fallback. Route 2 always requires Fireworks. Route 1 may use `--allow-basic-fallback` only when the user explicitly requests an emergency offline fallback, and the delivery must say that Fireworks validation was skipped.

Run a dedicated collision pass after rendering. Text, connector labels, arrow shafts, arrowheads, node borders, and section boundaries must not overlap unless the contact is the intentional endpoint of a connector. Cross-boundary routes need a visible corridor and must stay clear of section titles and explanatory text.

Read [review-rubric.md](references/review-rubric.md) for a formal review or before final delivery. Fix issues in this order:

1. semantic correctness and boundaries;
2. course or narrative sequencing;
3. hierarchy and density;
4. connector clarity and label precision;
5. visual consistency and polish.

Do not polish a diagram that still teaches the wrong boundary.

## Non-negotiable quality rules

- Give every SVG an accessible `<title>` and `<desc>`. Show a title inside the artwork only when the figure must orient readers without the surrounding article or when it adds a distinct claim.
- Inline figures should normally enter the relationship directly. Do not add a lesson badge, subtitle, or takeaway strip merely to fill a familiar template.
- Limit the main figure to one claim and usually three to six primary stages or groups.
- Make the central path recognizable before the reader parses the labels.
- Keep rendered text and connector labels inside their visual safe areas; do not let glyphs touch borders, arrows, or neighboring containers.
- Terminate connectors at explicit node edges. Arrowheads must not intrude into a card's text area, and connector routes must not run through labels or section headings.
- Use color by semantic role, not merely to distinguish adjacent boxes.
- Give dashed lines one documented meaning per figure.
- Connect status, diagnostics, and exceptions to the stage they describe; do not leave them as visual islands.
- Use consistent shapes for equivalent objects and visibly different shapes only for meaningful differences.
- Avoid repeated decorative icons, nested cards, gradients, glow, and shadow when they do not encode information.
- Do not encode meaning by color alone.
- Deliver concise notes about intentional omissions or unresolved source ambiguity when relevant.
