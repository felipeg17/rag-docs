-- Create schemas for RAG application

-- Application schema: stores document metadata and interaction logs
CREATE SCHEMA IF NOT EXISTS app;

-- Vector schema: stores pgvector embeddings for RAG
CREATE SCHEMA IF NOT EXISTS vector;

-- Grant full permissions to langchain user
GRANT ALL ON SCHEMA app TO langchain;
GRANT ALL ON SCHEMA vector TO langchain;
GRANT ALL on SCHEMA public TO langchain;

-- Log completion
DO $$
BEGIN
    RAISE NOTICE 'Schemas initialized: app, vector';
END $$;