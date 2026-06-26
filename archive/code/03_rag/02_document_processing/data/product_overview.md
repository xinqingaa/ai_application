# Product Overview

The support assistant answers questions about onboarding, deployment, and daily operations.
It does not browse the web and should rely on approved internal documents.

## Ingestion Policy

Markdown and text files are the first supported input formats in this phase.
We keep the loader simple so the learning focus stays on document flow, chunk design, and metadata.

## Chunking Notes

Small chunks are easier to retrieve precisely, but they can lose surrounding context.
Large chunks preserve context, but they may include too much unrelated text.
Overlap is used so important sentences are less likely to be split across chunk boundaries.

## Metadata Rules

Every chunk should keep a stable source path, filename, suffix, and chunk index.
Later phases will reuse these fields for citation, filtering, and debugging.
