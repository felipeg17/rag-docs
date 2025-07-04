import os
import requests
import base64
import dotenv
import time

from pathlib import Path
import streamlit as st

# Cargar variables de entorno
dotenv.load_dotenv()


def show():
  st.title("Cargar documento PDF")
  pdf_file = st.file_uploader("Cargar archivo PDF", type="pdf")
  if pdf_file:
    pdf_bytes = pdf_file.read()
    document_title = st.text_input("Titulo del documento")
    document_type = "documento-pdf"
    
    if st.button("Cargar documento", key="procesar"): 
      url = f"http://{os.getenv('API_HOST')}:{os.getenv('API_PORT')}/"
      endpoint = "rag-docs/api/v1/documento"
      with st.spinner("Procesando documento..."):
        payload = {
          "title": document_title,
          "document_type": document_type,
          # "document_bytes": pdf_bytes.hex()
          "document_bytes": base64.b64encode(pdf_bytes).decode('utf-8')
        }

        headers = {"Content-Type": "application/json"}
        
        response = requests.post(
          url + endpoint,
          json=payload,
          headers=headers
        )
      
      if response.status_code in [200, 201]:
        st.success(f"Request exitoso- {response.status_code}")
        for key, value in response.json().items():
          st.write(f"{key}: {value}")
      else:
        st.error(
          f"Request fallido con status code {response.status_code}: {response.text}"
        )

