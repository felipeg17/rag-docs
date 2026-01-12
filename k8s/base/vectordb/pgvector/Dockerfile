FROM pgvector/pgvector:pg16

# Copy schema initialization scripts
COPY init-scripts/ /docker-entrypoint-initdb.d/
RUN chmod -R 755 /docker-entrypoint-initdb.d/