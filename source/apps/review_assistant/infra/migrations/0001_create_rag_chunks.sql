BEGIN;

CREATE SCHEMA IF NOT EXISTS review_assistant;

CREATE TABLE IF NOT EXISTS review_assistant.rag_chunks (
    chunk_id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL,
    document_version TEXT NOT NULL,
    parent_chunk_id TEXT,
    original_filename TEXT NOT NULL,
    file_format TEXT NOT NULL,
    chunk_kind TEXT NOT NULL,
    ordinal INTEGER NOT NULL CHECK (ordinal > 0),
    token_count INTEGER NOT NULL CHECK (token_count > 0),
    source_role TEXT NOT NULL CHECK (
        source_role IN ('reference_knowledge', 'historical_material')
    ),
    evidence_eligibility TEXT NOT NULL CHECK (
        evidence_eligibility IN (
            'current_evidence',
            'historical_context',
            'ineligible'
        )
    ),
    content TEXT NOT NULL CHECK (length(btrim(content)) > 0),
    source_spans JSONB NOT NULL DEFAULT '[]'::jsonb,
    business_metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    lexical_text TEXT NOT NULL CHECK (length(btrim(lexical_text)) > 0),
    lexical_config_ref TEXT NOT NULL,
    search_vector TSVECTOR GENERATED ALWAYS AS (
        to_tsvector('pg_catalog.simple', lexical_text)
    ) STORED,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS rag_chunks_search_vector_gin_idx
    ON review_assistant.rag_chunks USING GIN (search_vector);

CREATE INDEX IF NOT EXISTS rag_chunks_document_version_idx
    ON review_assistant.rag_chunks (document_id, document_version);

CREATE INDEX IF NOT EXISTS rag_chunks_lexical_config_idx
    ON review_assistant.rag_chunks (lexical_config_ref);

COMMIT;
