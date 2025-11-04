import os

import dotenv
import requests
import streamlit as st


# Cargar variables de entorno
dotenv.load_dotenv()


def show():
    st.title("Chabot")

    document_title = st.text_input("Titulo del documento")
    document_type = "documento-pdf"
    query_text = st.text_input("Ingrese la pregunta al documento")

    if st.button("Preguntar al PDF", key="procesar"):
        url = f"http://{os.getenv('API_HOST')}:{os.getenv('API_PORT')}/"
        endpoint = "rag-docs/api/v1/cadena_rankeada"
        with st.spinner("Procesando pregunta..."):
            payload = {
                "title": document_title,
                "document_type": document_type,
                "query": query_text,
            }

            headers = {"Content-Type": "application/json"}

            response = requests.post(url + endpoint, json=payload, headers=headers)

        if response.status_code in [200, 201]:
            st.success(f"Request exitoso- {response.status_code}")
            for key, value in response.json().items():
                st.write(f"{key}: {value}")
        else:
            st.error(f"Request fallido con status code {response.status_code}: {response.text}")

    # response_container = st.container()
    # container = st.container()

    # with container:
    #   with st.form(key='my_form', clear_on_submit=True):
    #       user_input = st.text_input("Query:", placeholder="Talk to PDF data 🧮", key='input')
    #       submit_button = st.form_submit_button(label='Send')

    #   if submit_button and user_input:
    #     output = conversational_chat(user_input)
    #     st.session_state['past'].append(user_input)
    #     st.session_state['generated'].append(output)
