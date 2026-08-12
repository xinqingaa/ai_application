BEGIN;

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS review_assistant.rag_chunk_embeddings (
    chunk_id TEXT NOT NULL REFERENCES review_assistant.rag_chunks(chunk_id)
        ON DELETE CASCADE,
    embedding_space_ref TEXT NOT NULL,
    embedding_provider TEXT NOT NULL,
    embedding_config_ref TEXT NOT NULL,
    embedding_model TEXT NOT NULL,
    embedding_dimensions INTEGER NOT NULL CHECK (embedding_dimensions > 0),
    preprocessing_version TEXT NOT NULL,
    embedding VECTOR NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (chunk_id, embedding_space_ref),
    CHECK (vector_dims(embedding) = embedding_dimensions)
);

CREATE INDEX IF NOT EXISTS rag_chunk_embeddings_space_idx
    ON review_assistant.rag_chunk_embeddings (embedding_space_ref);

COMMIT;
