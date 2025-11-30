import logging
import os
import pdb

import chromadb
import dotenv


# Cargar variables de entorno
dotenv.load_dotenv()

# Configuracion de logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

#! IMPORTANTE: ultima version de chromadb http - api/v2 unicamente

# Parametros
db_host = os.getenv("CHROMADB_HOST")
db_port = os.getenv("CHROMADB_PORT")
tenant = "dev"
database = "rag-database"
collection_name = "rag-docs"

settings = chromadb.Settings(
    chroma_api_impl="chromadb.api.fastapi.FastAPI",
    chroma_server_host=f"http://{db_host}:{db_port}",
    chroma_server_http_port=db_port,
    allow_reset=True,
)

#  admin
admin_client = chromadb.AdminClient(settings=settings)

try:
    # Creacion tenant
    admin_client.create_tenant(name=tenant)
    logging.info(f"Tenant '{tenant}' created successfully.")

    # Creacion database
    admin_client.create_database(tenant=tenant, name=database)
    logging.info(f"Database '{database}' created successfully.")

except Exception as e:
    logging.error(f"Error creating tenant or database: {e}")


# Revisar tenant y database
tenant_name = admin_client.get_tenant(name=tenant)
database_name = admin_client.get_database(tenant=tenant, name=database)
logging.info(f"Tenant: {tenant_name}, Database: {database_name}")
pdb.set_trace()

# Crear cliente
chroma_client = chromadb.HttpClient(
    host=f"http://{db_host}:{db_port}",
    tenant=tenant,
    database=database,
)


# Crear coleccion
collection = chroma_client.create_collection(name=collection_name)
logging.info(f"Collections: {chroma_client.list_collections()}")
pdb.set_trace()
