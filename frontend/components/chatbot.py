import requests
import streamlit as st

from utils.utils import load_backend_config


def show():
    st.title("Chabot")

    document_title = st.text_input("Titulo del documento")
    question_text = st.text_input("Ingrese la pregunta al documento")

    if st.button("Preguntar al PDF", key="procesar"):
        url = load_backend_config()
        endpoint = f"api/v1/documents/{document_title}/ask"
        with st.spinner("Procesando pregunta..."):
            payload = {
                "question": question_text,
                "strategy": "rerank",
                "k_results": 4,
                "metadata_filter": {},
            }

            headers = {"Content-Type": "application/json"}

            response = requests.post(url + endpoint, json=payload, headers=headers)

        if response.status_code in [200]:
            st.success(f"Request exitoso- {response.status_code}")
            for key, value in response.json().items():
                st.write(f"{key}: {value}")
        else:
            st.error(f"Request fallido con status code {response.status_code}: {response.text}")
