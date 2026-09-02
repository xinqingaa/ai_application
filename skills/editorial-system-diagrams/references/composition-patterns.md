# Composition Patterns

Select the pattern from the relationship the reader needs to understand. Do not choose a layout because it looks impressive.

## Linear pipeline

**Use for:** a stable sequence with one dominant start and end.

Structure the figure around three to six aligned stages and one clear arrow spine. Put prerequisites or cross-cutting support in a subordinate band.

**Avoid when:** several stages operate in parallel or the main lesson is a boundary rather than a sequence.

## Offline / online bands

**Use for:** systems with preparation or indexing before a runtime request, such as ingestion and retrieval.

Place the offline band above or below the online band. Show the shared store or handoff explicitly. Keep the user request and final response within the online band.

**Avoid:** drawing preparation as if it happens on every request, or defining the runtime system as only its final two nodes.

## Layered architecture

**Use for:** ownership, trust boundaries, control planes, capability layers, or cross-cutting services.

Give each layer a short role statement. Show only relationships that cross or organize layers; omit ordinary internal plumbing.

**Avoid:** using layers merely to group boxes by color or team when that grouping does not explain behavior.

## Parallel comparison

**Use for:** two or three routes applied to the same input, such as lexical versus semantic retrieval.

Align equivalent steps and outputs. Keep shared inputs and comparison criteria visible. Use consistent geometry so differences reflect meaning rather than styling.

**Avoid:** combining several lessons' internal implementation details merely because the routes are adjacent.

## Converge and fuse

**Use for:** several ranked lists, signals, or evidence streams joining into one result.

Show representative tokens moving from each route into the merge. Make the fusion rule the focal transformation and keep route-local scores subordinate.

**Avoid:** leaving empty, failed, or unavailable route states in an unrelated legend. Attach them to their source routes or move them to a separate detail figure.

## Candidates through gates

**Use for:** filtering, thresholds, policy checks, eligibility, or diagnostic pipelines.

Represent one or two named candidates and visibly track them through consecutive gates. Mark the exact gate where an item is removed and state why.

**Avoid:** replacing the candidates with a row of function names. The reader should see what changes, not only which functions execute.

## Lifecycle or loop

**Use for:** iteration, feedback, learning, recovery, or repeated operation.

Keep the forward path dominant. Draw the feedback edge from a specific output to a specific earlier decision and label the trigger. Put persistent state or governance in a supporting band when it affects the entire loop.

**Avoid:** a vague arrow returning to the beginning without explaining what changes.

## Boundary map

**Use for:** explaining what belongs inside a concept or system and what remains outside.

Draw the boundary first, then place internal responsibilities and external actors. If offline and online responsibilities differ, combine the boundary with bands rather than shrinking the boundary around the most visible runtime component.

**Avoid:** treating the visually central node as the entire system when required upstream responsibilities belong inside the definition.

## Context assembly

**Use for:** turning a candidate collection into a constrained package, prompt, evidence set, or delivery object.

Use four moves: candidates, selection or budgeting, assembled container, permitted outputs. Make exclusions subordinate and state the invariant linking inclusion to permission.

**Avoid:** drawing every internal field, report object, and historical partition in the overview. Use a separate implementation figure when those details are the subject.

## Validation with outcomes

**Use for:** parsing and local checks that produce success, warning, refusal, or failure.

Keep the successful path straight. Branch failures directly from the check that discovers them. Name outcomes in reader language; place exact error codes in a detail layer when needed.

**Avoid:** treating a successful syntax or membership check as proof of semantic support. Use a takeaway statement to declare what the check does not establish.
