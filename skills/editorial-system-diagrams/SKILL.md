---
name: editorial-system-diagrams
description: Design, review, or rework publication-quality technical diagrams—such as system architecture, process, lifecycle, course concept, and mechanism diagrams—when editorial hierarchy, conceptual clarity, or series consistency matters. Do not use for quantitative data charts, freeform illustration, or decorative imagery.
---

# Editorial System Diagrams

Create diagrams that teach one important relationship at a glance. Treat the diagram as an editorial explanation, not an inventory of implementation objects.

## Establish the diagram brief

Before drawing, identify:

- the one sentence the reader should understand;
- the audience and what they already know;
- the relationship to show: sequence, boundary, hierarchy, comparison, convergence, filtering, state change, or feedback;
- whether this is a standalone figure or part of a series;
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

For a series, freeze the shared visual contract before producing individual figures: canvas ratio, title zone, type scale, spacing unit, card families, connector rules, color roles, icon family, and takeaway treatment. Vary the composition when the subject requires it, but preserve the contract.

## Select a rendering route

- Use Mermaid when labeled nodes and edges fully communicate the structure and editorial layout is secondary.
- Use SVG or HTML when precise hierarchy, repeated geometry, custom annotations, or responsive editorial composition matters.
- Use the native document or presentation format when the diagram must remain editable inside that artifact.
- Do not use image generation for diagrams whose labels, topology, or editability must be exact.

Keep the editable source whenever the renderer supports it. A raster export alone is not a maintainable diagram source.

## Render and inspect

Inspect the actual rendered result, not only its source. Check it at intended display size and at a reduced size representative of the final reading context.

Read [review-rubric.md](references/review-rubric.md) for a formal review or before final delivery. Fix issues in this order:

1. semantic correctness and boundaries;
2. course or narrative sequencing;
3. hierarchy and density;
4. connector clarity and label precision;
5. visual consistency and polish.

Do not polish a diagram that still teaches the wrong boundary.

## Non-negotiable quality rules

- Give every figure a clear title and, when needed, one short orienting sentence.
- Limit the main figure to one claim and usually three to six primary stages or groups.
- Make the central path recognizable before the reader parses the labels.
- Use color by semantic role, not merely to distinguish adjacent boxes.
- Give dashed lines one documented meaning per figure.
- Connect status, diagnostics, and exceptions to the stage they describe; do not leave them as visual islands.
- Use consistent shapes for equivalent objects and visibly different shapes only for meaningful differences.
- Avoid repeated decorative icons, nested cards, gradients, glow, and shadow when they do not encode information.
- Do not encode meaning by color alone.
- Deliver concise notes about intentional omissions or unresolved source ambiguity when relevant.
