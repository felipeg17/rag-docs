import os
import logging
import pdb
import dotenv
import base64

from pathlib import Path
from typing import Optional
from binascii import unhexlify

# Langchain controls
# from langchain.globals import set_debug

# llm model
from langchain_openai import ChatOpenAI
from langchain_aws import ChatBedrockConverse

# Vector database
from langchain_chroma import Chroma
import chromadb

# Embeddings
from langchain_openai import OpenAIEmbeddings

# Prompts and messages
from langchain.prompts import (
  PromptTemplate, ChatPromptTemplate, MessagesPlaceholder
)

# Documents processing
import fitz
from langchain.schema import Document

# Splitters
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_experimental.text_splitter import SemanticChunker

# Parsers and runnables
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableParallel

# Chains
from langchain.chains.retrieval_qa.base import RetrievalQA

# Reranking
from langchain.retrievers.contextual_compression import (
  ContextualCompressionRetriever
)
from langchain_cohere import CohereRerank

# Tracing
from langsmith import traceable

# Cargar variables de entorno
dotenv.load_dotenv()
# Modo debug verbose para langchain
# set_debug(False)

# Configuracion de logging
logging.basicConfig(
  level=logging.INFO, 
  format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class ProcessDocument():
  def __init__(
    self,
    query_id: str = None,
    document_bytes: bytes = None,
    document_title: str = None,
    document_type: str = "documento-pdf",
  ) -> None:
    self._query_id: str = query_id
    self._document_bytes = document_bytes
    self._document_title = document_title
    self._document_type = document_type
    self._collection_name: str = "rag-docs"
    self._embeddings_model_name: str = "text-embedding-ada-002"
    
  def load_services(self) -> None:
    self._llm_gpt = self._load_llm_model()
    logging.info("LLM cargado")
    self._load_embeddings_service(
      embeddings_model=self._embeddings_model_name
    )
    logging.info(f"Servicio de embeddings {self._embeddings_model_name} cargado")
    self._chroma_http_client = self._load_chroma_client()
    if self._chroma_http_client.heartbeat():
      logging.info("Cliente chroma en linea")
    self._chroma_vdb = self._load_chroma_vbd(collection_name=self._collection_name)
    logging.info("Chroma vdb cargada")
    
  def load_document(self) -> None:
    #* Convertir hex_string a bytes
    # self._document_bytes = unhexlify(self._document_bytes)

    #* Convertir de base64 a bytes
    self._document_bytes = base64.b64decode(self._document_bytes)

    #* Cargar documento pdf con normalidad
    self._document_pdf = fitz.open(
      stream=self._document_bytes,
      filetype="pdf"
    )
    
  def process_document(
    self, 
    splitter_params: dict=None, 
    splitting_method="recursive",
  ) -> bool:
    # Revisar si el documento ya esta en la base de datos
    if self.check_document_in_vdb(title=self._document_title):
      logging.info(f"Documento {self._document_title} ya existe vdb")
      return False
    
    if splitting_method == "semantic":
      self._text_splitter = SemanticChunker(
        embeddings=self._embeddings_service,
        breakpoint_threshold_type="gradient"
      )
    else:
      #* Parametros para el splitter
      splitter_params = splitter_params or {
        "chunk_size": 800,
        "chunk_overlap": 50
      }
      self._text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=splitter_params["chunk_size"],
        chunk_overlap=splitter_params["chunk_overlap"]
      )
      
    # Transformar el documento_pdf a un documento con metadata
    self._document_with_metadata = self._transform_doc_with_metadata()
    
    # Dividir el documento en chunks
    self._document_splitted = self._text_splitter.split_documents(
      documents=self._document_with_metadata
    )
    
    # Ingestar el documento en la base de datos vectorial
    self._chroma_vdb.add_documents(documents=self._document_splitted)
    logging.info(f"{self._document_title} ingestado en vdb")
    return True
  
  def get_results_from_vdb_search(
    self, 
    query: str=None, 
    k_results: int=4,
    metadata_filter: dict={}
  ) -> list:
    results = []
    if not query:
      query = """
      Describe the main idea of the document
      """
    
    if not metadata_filter:
      metadata_filter = {
        "tipo-documento": self._document_type
      }

    results = self._chroma_vdb.similarity_search_with_score(
      query=query,
      k=k_results,
      filter=metadata_filter,
      where_document={"$contains": " "}
    )
    # pdb.set_trace()
    return results
  
  @traceable
  def get_answer_from_rag_qa(
    self,
    query: str="", 
    k_results: int=4
  ) -> dict:
    
    if not query:
      query = """
      Describe the main idea of the document
      """
    
    #* Creacion del retriever
    self._retriever = self._chroma_vdb.as_retriever(
      search_type="similarity",
      search_kwargs={
        "k": k_results,
        "filter": {
          "tipo-documento": {"$eq": self._document_type},
        },
        "where_document": {"$contains": " "}
      }
    )
    
    #* Prompt de la cadena qa (es el que usa el llm para responder la pregunta)
    prompt_text = """
    You are an assistant specialized in answering questions about documents.
    Your task is to use the information provided in the context to answer
    the question.
    Instructions: 
      1. Answer the following question based on the information
      2. Do not include unsolicited information, do not make up data, do not 
      include recommendations outside of the provided context.
      3. Be very concise in your answer, do not include unnecessary information.

    Context:
    {context}
    Question:
    {question}
    """
    qa_prompt = PromptTemplate.from_template(template=prompt_text)
    
    #* Cadena qa
    qa_chain = RetrievalQA.from_chain_type(
      llm = self._llm_gpt,
      retriever=self._retriever,
      return_source_documents=True,
      chain_type="stuff",
      chain_type_kwargs={"prompt": qa_prompt}
    )
    
    #* Se usa este prompt para la busqueda en la vdb
    answer = qa_chain.invoke(
      {"query": query}
    )
    
    return answer
  
  @traceable
  def get_reranked_results(self, query: str="", k_results: int=4) -> str:
    if not query:
      query = """
      Describe the main idea of the document
      """
    
    self._retriever = self._chroma_vdb.as_retriever(
      search_type="similarity",
      search_kwargs={
        "k": k_results,
        "filter": {
          "tipo-documento": {"$eq": self._document_type},
        },
        "where_document": {"$contains": " "}
      }
    )
    
    compressor = CohereRerank(
      top_n=3,
      model="rerank-v3.5"
    )
    
    compression_retriever = ContextualCompressionRetriever(
      base_compressor=compressor, 
      base_retriever=self._retriever
    )
    
    prompt_text = """
    You are an assistant specialized in answering questions about documents.
    Your task is to use the information provided in the context to answer
    the question.
    Instructions: 
      1. Answer the following question based on the information
      2. Do not include unsolicited information, do not make up data, do not 
      include recommendations outside of the provided context.
      3. Be very concise in your answer, do not include unnecessary information.

    Context:
    {context}
    Question:
    {question}
    """
    
    qa_prompt = ChatPromptTemplate.from_template(template=prompt_text)
    
    setup_and_retrieval = RunnableParallel(
      {
        "question": RunnablePassthrough(), 
        "context": compression_retriever 
      }
    )
    
    compressor_retrieval_chain = \
      setup_and_retrieval | qa_prompt | self._llm_gpt | StrOutputParser()
    answer = compressor_retrieval_chain.invoke(query)
    
    return answer
  
  def check_document_in_vdb(self, title: str) -> bool:
    if not title:
      return False
    
    document_results = self._chroma_vdb.get(
      where={
        "titulo": {"$eq": title}
      },
    )
    return bool(document_results.get("ids"))
  
  def delete_document_from_vdb(self, title: str) -> bool:
    if not title:
      logging.error("Titulo no proporcionado")
      return False
    document_results = self._chroma_vdb.get(
      where={
        "titulo": {"$eq": title}
      },
      # include=["ids"]
    )
    if document_results.get("ids"):
      self._chroma_vdb.delete(
        ids=document_results.get("ids")
      )
      logging.info(f"Documento {title} eliminado de vdb")
      return True
    logging.info(f"Documento {title} no encontrado en vdb")
    return False
  
  def _transform_doc_with_metadata(self) -> list[Document]:
    documents: list = []
    for page_number in range(self._document_pdf.page_count):
      logging.info(f"Procesando pagina {page_number+1}")
      page = self._document_pdf.load_page(page_number)
      page_text = page.get_text("text")
        
      documents.append(
        Document(
          page_content=page_text,
          metadata={
            "titulo": self._document_title,
            "tipo-documento": self._document_type,
            "pagina": page_number, 
          }
        )
      )
    
    logging.info(f"{self._document_title} transformado a documento con metadata")
    return documents
  
  def _load_llm_model(
    self, 
    modelo: str="gpt-4o-mini", 
    model_params: dict=None, 
  ):
    # model_params = model_params or {
    #   "model_name": "gpt-4o-mini",
    #   "api_version": "2023-05-15",
    #   "temperature": 0.05, 
    #   "max_tokens": 4000,
    #   "top_p": 0.95,
    # }
    
    # return ChatOpenAI(
    #   model=modelo,
    #   api_key=os.environ.get('OPENAI_API_KEY'),
    #   temperature=model_params["temperature"],
    #   max_tokens=model_params["max_tokens"],
    #   top_p=model_params["top_p"]
    # )
    #! Cuando se isa el arn del modelo es necesario agregar el provider
    #! revisar la seccion de cross-inference region y obtener el profile ARN
    return ChatBedrockConverse(
      model_id="arn:aws:bedrock:us-east-1:008319781255:inference-profile/us.anthropic.claude-3-5-haiku-20241022-v1:0",
      provider="anthropic",
      temperature=0.1,
      top_p=0.9,
      max_tokens=4000,
      aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
      aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
      region_name=os.environ.get('AWS_REGION', 'us-west-1')
    )
    
  def _load_embeddings_service(
    self, 
    embeddings_model: str="text-embedding-ada-002"
  ) -> None:
    if embeddings_model == "text-embedding-ada-002":
      self._embeddings_service = OpenAIEmbeddings(
        model=embeddings_model,
        api_key=os.environ.get('OPENAI_API_KEY')
      )
      
  def _load_chroma_client(
    self, 
    tenant: str="dev", 
    database: str="rag-database"
  ) -> chromadb.HttpClient: 
    #* Es necesario verificar si el tenant y la base de datos existen
    db_host = os.getenv("CHROMADB_HOST")
    db_port = os.getenv("CHROMADB_PORT")
    return chromadb.HttpClient(
      host=f"http://{db_host}:{db_port}",
      tenant=tenant,
      database=database
    )
    
  def _load_chroma_vbd(self, collection_name: str="rag-docs") -> Chroma:
    #* En caso que no exista la coleccion, se crea
    # if collection_name not in self._chroma_http_client.list_collections():
    #   self._chroma_http_client.create_collection(name=collection_name)
    try:
      self._chroma_http_client.get_collection(name=collection_name)
      logging.info(f"Coleccion {collection_name} existente")
    except Exception as e:
      logging.error(f"Coleccion no existente {collection_name}:::{e}")
      self._chroma_http_client.create_collection(name=collection_name)
      logging.info(f"Coleccion {collection_name} creada")
    return Chroma(
      collection_name=collection_name,
      embedding_function=self._embeddings_service,
      client=self._chroma_http_client
    )
    
if __name__ == "__main__":
  DOCS_PATH = Path(__file__).parent 
  folder_path = DOCS_PATH / "documents"
  file_name = "fl-taxes.pdf"
  document_title = "Business Owners Taxes in Florida"
  file_path = str(folder_path / file_name)
  
  try:
    with open(file_path, 'rb') as file:
      pdf_bytes = file.read()
  except Exception as e:
    logging.error(f"Error al cargar el archivo {file_path}:::{e}")
  
  doc = ProcessDocument(
    query_id="1",
    document_bytes=base64.b64encode(pdf_bytes).decode('utf-8'),
    # document_bytes=pdf_bytes.hex(),
    document_title=document_title
  )
  
  #* Cargar servicios
  logging.info("Cargando servicios")
  doc.load_services()
  
  pdb.set_trace()

  #* Procesar documento
  # logging.info("Procesando documento")
  # doc.load_document()
  # doc.process_document()

  # pdb.set_trace()
  

  # * Buscar en la vdb
  query = """
  What are communication service tax rates?
  """
  # results = doc.get_results_from_vdb_search(
  #   query=query,
  #   k_results=4
  # )
  # for result in results:
  #   print(f"Score:::{result[1]}")
  #   print(f"Metadata:::{result[0].metadata}")
  #   print(f"Texto:::{result[0].page_content}")
  #   print("-"*50)
  #   print("\n\n")
  
  # pdb.set_trace()
  
  #* Respuesta por RAG con cadena de QA sin salida estructurada
  # query = """
  # How AI is going to affect claims?
  # """
  # answer_qa = doc.get_answer_from_rag_qa(
  #   query=query,
  #   k_results=4
  # )
  # for key, value in answer_qa.items():
  #   print("-"*50)
  #   print(f"{key}:::{value}")
    
  # pdb.set_trace()
  
  #* Respuesta por RAG con reranking sin salida estructurada
  answer_re = doc.get_reranked_results(
    query=query,
    k_results=2
  )
  print(f"Answer:::{answer_re}")
  
  
  
  
  