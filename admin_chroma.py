import chromadb
import pdb
import dotenv
import logging
import os

# Cargar variables de entorno
dotenv.load_dotenv()

# Configuracion de logging
logging.basicConfig(
  level=logging.INFO, 
  format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


# Parametros
db_host = os.getenv("HOST")
db_port = os.getenv("CHROMADB_PORT")
tenant = "dev"
database = "rag-database"
collection_name = "rag-docs"


settings = chromadb.Settings(
  chroma_api_impl="chromadb.api.fastapi.FastAPI",
  chroma_server_host=f"http://{db_host}:{db_port}",
  chroma_server_http_port=db_port,
  allow_reset = True
)

#admin
admin_client = chromadb.AdminClient(settings=settings)

try:
  # admin_client.create_tenant(name=tenant)
  admin_client.create_database(tenant=tenant, name=database)	
except Exception as e:
  print(e)
  pass
pdb.set_trace()

# tenant_name = admin_client.get_tenant(name=tenant)
# database_name = admin_client.get_database(tenant=tenant, name=database)
# pdb.set_trace()

# cliente
chroma_client = chromadb.HttpClient(
  host=f"http://{db_host}:{db_port}",
  tenant=tenant,
  database=database,
)
pdb.set_trace()

# chroma_client.list_collections()

collection = chroma_client.create_collection(name=collection_name)
pdb.set_trace()
