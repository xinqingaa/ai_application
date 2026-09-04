# Visual System

Use this reference to establish a publishable diagram style and keep a series coherent. These values are defaults, not a mandate to copy one specific layout.

## 1. Canvas and embedding mode

Choose the page structure from how the figure will be read.

- **Inline explanatory figure** — appears directly under a section that has already established the question. It normally has no visible figure title, subtitle, lesson badge, or footer takeaway. Use the available canvas for the relationship itself; put a necessary caveat next to the stage it qualifies.
- **Standalone or reusable figure** — may be opened, exported, or reused without its surrounding article. It may use an orientation zone with a visible title and one short claim. Add a footer takeaway only when it carries a boundary that cannot be attached clearly to one stage.
- **Section or series opener** — may include a lesson identifier when identity and navigation are part of the artifact. Do not repeat that identifier on ordinary inline figures in the same article.

The default course teaching canvas is `1600 × 900` with a `viewBox="0 0 1600 900"`. Treat it as a starting size, not a page template. Short pipelines and handoff diagrams may use a shallower canvas; dense comparisons may need more height. Choose dimensions after the composition is known, and never preserve 16:9 by shrinking type or adding empty orientation and takeaway zones.

## 2. Hierarchy

Use no more than five visible levels. For an inline figure, the first visible level is usually the stage, object, or relation that starts the diagram; for a standalone figure, it may be the figure title. Stage titles should be about 1.25–1.45 times the body size. If a visible figure title is warranted, make it about 2.2–2.8 times the body size. Annotations may be smaller but must remain readable at the final display size.

Use weight and whitespace before adding more borders or colors. Reserve the heaviest weight for the actual reading entry, not automatically for a page title.

## 3. Typography and terminology

- Use one primary sans-serif family and at most one monospace family for literal code.
- Keep line length inside cards short; prefer two short lines to a compressed paragraph.
- Use sentence case or a consistent Chinese title style. Do not mix title conventions arbitrarily.
- Use bilingual labels only when the second language establishes an important technical term. Do not translate every ordinary process label.
- Keep `CamelCase`, `snake_case`, parameter names, and error codes out of overview figures unless they are the explicit lesson.
- Prefer concise nouns for stages and short verbs for connectors or transitions.

## 4. Default color roles

Start with a quiet light canvas and a dark ink color. A reusable default palette is:

| Role | Default | Use |
|---|---|---|
| Canvas | `#F7F9FC` | page background |
| Ink | `#102A56` | titles, primary text, structural strokes |
| Primary | `#1557B0` | main flow and active structure |
| Evidence / data | `#0F7C83` | knowledge, retrieval, evidence, data movement |
| Model / reasoning | `#5B45C6` | model or reasoning stages only |
| Boundary / caution | `#C76B00` | exclusions, prerequisites, unverified states |
| Failure | `#C43D3D` | confirmed failure only |
| Neutral border | `#AFC3E3` | secondary containers and separators |

Treat these as semantic roles. Do not recolor each neighboring box for variety. Use pale tints for group surfaces and reserve saturated fills for at most one or two focal elements.

Avoid gradients, glow, and strong shadows by default. If a gradient is retained as a brand motif, restrict it to one focal node and keep all other surfaces quiet.

## 5. Geometry and spacing

Adopt an 8-unit spacing system. Prefer gaps and padding drawn from 8, 16, 24, 32, and 48 units rather than arbitrary values.

- Use one or two card families, not a different container for every concept.
- Keep equivalent stages equal in height and visually aligned.
- Use restrained corner radii; nested rounded rectangles quickly create a UI-dashboard appearance.
- Use a consistent border weight. Increase weight only for a real boundary or focal path.
- Give the main flow generous surrounding whitespace. Empty space is part of the explanation.

### Collision-safe layout

- Judge spacing from the rendered glyphs and strokes, not only from source coordinates or nominal text boxes.
- Keep text inside a card's safe area with visible padding on every side. If a label approaches a border, widen the card, shorten or wrap the label, or change the composition; do not solve it with cramped typography.
- Do not allow non-semantic overlap among text, connector labels, arrow shafts, arrowheads, card borders, section borders, or neighboring containers.
- A connector may touch a node border only at its deliberate entry or exit point. Stop the arrowhead at the border and keep it outside the node's text safe area.
- When a connector crosses a band or system boundary, route it through a clear corridor, cross the boundary cleanly, and keep the route away from the boundary title and orientation copy.
- Place connector labels beside a line with clear separation, or interrupt the line behind the label. Never place readable text directly on top of a stroke.

## 6. Connectors

- Establish one dominant spine before adding branches.
- Prefer short horizontal or vertical connectors over long perimeter routes.
- Label decision branches, transformations, and feedback triggers when their meaning is not self-evident.
- Use solid lines for the main flow.
- Keep arrowheads subordinate to the nodes and labels. As a starting point, use an arrowhead length around 1.5–2 times the connector stroke width, then inspect it at the final embedded size.
- Assign dashed lines one secondary meaning, such as diagnostics, optional paths, or feedback. Never use the same dash style for several meanings.
- Attach failures, statuses, and notes to the stage that emits them.
- Avoid crossings. When crossings are unavoidable, reconsider grouping or split the figure.
- Distinguish data movement from control or validation only when the distinction matters to the teaching claim.

## 7. Icons and illustration

Icons are anchors, not content.

- Use one coherent icon family and stroke weight.
- Prefer one icon per major stage; do not add an icon to every small candidate or row.
- Do not repeat several icons to communicate quantity when simple labels such as A and B are clearer.
- Never let an icon occupy more visual weight than its stage title.
- Use diagrams and text, not decorative AI imagery, when topology and terminology must be exact.

## 8. Density budget

A useful default for a primary teaching figure is:

- zero visible titles for an inline figure, or one for a standalone figure;
- at most one orienting sentence when the surrounding prose cannot provide it;
- three to six primary stages or groups;
- at most one secondary band or branch;
- at most one takeaway statement;
- no more than two short explanatory lines per main card.

If the content exceeds this budget, choose among:

1. split overview and detail;
2. split consecutive lessons;
3. move implementation names into prose;
4. convert a secondary object into a short annotation;
5. show one representative item rather than the full inventory.

Do not respond by reducing the type size below the established series scale.

## 9. Series contract

Freeze these decisions before producing a set:

- canvas sizing policy and safe margins;
- when visible titles, lesson identifiers, and orienting sentences are allowed;
- type family, sizes, and weights;
- spacing unit and card padding;
- primary card families;
- connector weight, arrowhead, and dash semantics;
- semantic color roles;
- icon family and icon size;
- takeaway or boundary treatment;
- export sizes and file naming.

Keep the contract stable even when individual diagrams use different composition patterns or canvas heights. A series is unified by typography, spacing, connector behavior, color semantics, and shape grammar—not by cloning the same header, badge, footer, or number of boxes.

## 10. Accessibility and export

- Maintain readable contrast for text, strokes, and pale tints.
- Do not encode state by color alone; pair color with a label, shape, or icon.
- Verify the smallest text at the final embedded size, not only on the source canvas.
- Inspect both full-size and reduced-size exports for clipping, blur, crowded labels, overly thin lines, and every text/connector/border collision.
- Preserve editable source and export a deterministic SVG or high-resolution PNG when possible.
