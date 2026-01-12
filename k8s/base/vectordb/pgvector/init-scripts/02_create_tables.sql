-- Create tables for RAG application persistent data layer
-- This script runs after schemas are created (01_create_schemas.sql)

-- Set search path to app schema
SET search_path TO app;

-- Table: documents
-- Stores document metadata with content-based deduplication via hash
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(1000) NOT NULL,
    document_type VARCHAR(200) NOT NULL,
    file_size_bytes INTEGER,
    page_count INTEGER,
    content_hash VARCHAR(64) NOT NULL UNIQUE,
    status VARCHAR(50) NOT NULL DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Indexes for documents
-- CREATE INDEX IF NOT EXISTS idx_documents_title ON documents(title);
-- CREATE INDEX IF NOT EXISTS idx_documents_content_hash ON documents(content_hash);

-- Table: search_interactions
-- Stores search query logs with execution metrics
CREATE TABLE IF NOT EXISTS search_interactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL,
    query_text TEXT NOT NULL,
    k_results INTEGER,
    results_count INTEGER,
    avg_similarity_score DOUBLE PRECISION,
    execution_time_ms INTEGER,
    session_id UUID,
    user_id VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Indexes for search_interactions
-- CREATE INDEX IF NOT EXISTS idx_search_interactions_document_id ON search_interactions(document_id);
-- CREATE INDEX IF NOT EXISTS idx_search_interactions_session_id ON search_interactions(session_id);

-- Table: qa_interactions
-- Stores question/answer logs with LLM metrics
CREATE TABLE IF NOT EXISTS qa_interactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    strategy VARCHAR(50),
    k_results INTEGER,
    llm_model VARCHAR(100),
    embedding_model VARCHAR(100),
    execution_time_ms INTEGER,
    tokens_used INTEGER,
    session_id UUID,
    user_id VARCHAR(255),
    feedback_text TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Indexes for qa_interactions
-- CREATE INDEX IF NOT EXISTS idx_qa_interactions_document_id ON qa_interactions(document_id);
-- CREATE INDEX IF NOT EXISTS idx_qa_interactions_session_id ON qa_interactions(session_id);

-- Trigger function to auto-update updated_at timestamp
-- CREATE OR REPLACE FUNCTION update_updated_at_column()
-- RETURNS TRIGGER AS $$
-- BEGIN
--     NEW.updated_at = NOW();
--     RETURN NEW;
-- END;
-- $$ LANGUAGE plpgsql;

-- -- Attach triggers to tables
-- DROP TRIGGER IF EXISTS update_documents_updated_at ON documents;
-- CREATE TRIGGER update_documents_updated_at
--     BEFORE UPDATE ON documents
--     FOR EACH ROW
--     EXECUTE FUNCTION update_updated_at_column();

-- DROP TRIGGER IF EXISTS update_search_interactions_updated_at ON search_interactions;
-- CREATE TRIGGER update_search_interactions_updated_at
--     BEFORE UPDATE ON search_interactions
--     FOR EACH ROW
--     EXECUTE FUNCTION update_updated_at_column();

-- DROP TRIGGER IF EXISTS update_qa_interactions_updated_at ON qa_interactions;
-- CREATE TRIGGER update_qa_interactions_updated_at
--     BEFORE UPDATE ON qa_interactions
--     FOR EACH ROW
--     EXECUTE FUNCTION update_updated_at_column();

-- Grant permissions to langchain user
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA app TO langchain;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA app TO langchain;

-- Log completion
DO $$
BEGIN
    RAISE NOTICE 'Tables initialized: documents, search_interactions, qa_interactions';
END $$;
