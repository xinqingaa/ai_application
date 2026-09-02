# Review Rubric

Use this rubric for an existing diagram or a final rendered figure. Report the highest-impact findings first.

## P0 — Semantic correctness

- Does every boundary include the responsibilities required by its definition?
- Do arrow directions match the real data, control, or validation flow?
- Are offline preparation and per-request runtime distinguished correctly?
- Does the figure invent, omit, or overstate a relationship?
- Does a success state claim more than the mechanism actually verifies?

Any P0 issue requires structural correction before visual polish.

## P1 — Narrative and scope

- Can the figure's one-sentence claim be stated without using “and” repeatedly?
- Does the figure match the intended lesson or section rather than consume adjacent topics?
- Are prerequisite, extension, and future concepts visually subordinate?
- Would splitting overview and detail improve comprehension?
- Does each branch contribute to the main claim?

## P1 — Abstraction quality

- Are durable concepts more prominent than mechanisms?
- Are implementation types, parameters, vendors, and error codes dominating the main labels?
- Can repeated technical objects be replaced by representative tokens or plain-language actions?
- Does the diagram teach a mental model before exposing plumbing?

## P1 — Visual hierarchy

- Is the title the first reading entry?
- Is the main path visible before labels are read?
- Are primary, secondary, and annotation levels visually distinct?
- Is there enough quiet space around the focal relationship?
- Does every status or note clearly belong to a stage?

## P2 — Layout and connectors

- Are equivalent stages aligned and consistently sized?
- Are there avoidable crossings, long perimeter lines, or ambiguous arrowheads?
- Does every dashed line have one consistent meaning?
- Are branches labeled where necessary?
- Are auxiliary bands separated from the main flow?

## P2 — Series consistency

- Does the figure use the shared canvas, margins, title zone, type scale, spacing, and card families?
- Do colors preserve the same semantics across the series?
- Are icon family, stroke weight, and takeaway treatment consistent?
- Does this figure feel like a chapter in the same publication without copying another figure's layout?

## P2 — Typography and terminology

- Is the smallest text readable at embedded size?
- Are bilingual labels used selectively?
- Are naming styles consistent?
- Can code identifiers move into prose or a detail figure?
- Are labels concise enough to scan rather than read as paragraphs?

## P3 — Polish and accessibility

- Are contrast and grayscale differentiation adequate?
- Is meaning preserved without color?
- Are gradients, shadows, nested cards, and decorative icons serving information?
- Are exports crisp, unclipped, and free of tiny text?
- Is editable source preserved?

## Review output

Summarize:

1. the diagram's intended claim;
2. what already works;
3. P0 and P1 issues;
4. series-level inconsistencies;
5. a concrete restructure direction;
6. what should move to prose, an experiment, or a detail figure.

Avoid vague feedback such as “make it cleaner.” Name the competing claims, incorrect boundaries, unnecessary labels, and specific hierarchy changes.
