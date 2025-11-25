# import base64
# import logging
# import os
# from pathlib import Path
# import pdb

# import dotenv
# import requests


# # Cargar variables de entorno
# dotenv.load_dotenv()

# # Configuracion de logging
# logging.basicConfig(
#     level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
# )

# DOCS_PATH = Path(__file__).parent

# if __name__ == "__main__":
#     # save_data_from_json_to_db()
#     folder_path = DOCS_PATH
#     file_name = "Prueba_tecnica.pdf"
#     file_path = str(folder_path / file_name)
#     try:
#         with open(file_path, "rb") as file:
#             pdf_bytes = file.read()
#             # Encode to base64 string as expected by the API
#             pdf_base64 = base64.b64encode(pdf_bytes).decode("utf-8")
#     except Exception as e:
#         logging.error(f"Error al cargar el archivo {file_path}:::{e}")

#     url = f"http://{os.getenv('HOST')}:8106/"
#     endpoint = "rag-docs/api/v1/documento"

#     payload = {
#         "title": "Prueba_tecnica",
#         "document_type": "documento-pdf",
#         "document_bytes": pdf_base64,
#     }

#     headers = {"Content-Type": "application/json"}
#     pdb.set_trace()

#     response = requests.post(url + endpoint, json=payload, headers=headers)

#     if response.status_code in [200, 201]:
#         logging.info(f"Request exitoso- {response.status_code}")
#         logging.info(f"{response.text}")
#         pdb.set_trace()
#     else:
#         logging.error(f"Request fallido con status code {response.status_code}: {response.text}")
