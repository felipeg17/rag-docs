import streamlit as st
from pathlib import Path

from components import qa_pdf, chatbot

PATH = Path(__file__).resolve().parent

def main():
  st.sidebar.subheader("Funcionalidades")
  page = st.sidebar.radio(
    "Seleccione funcionalidad",
    ["Documento", "Chatbot"]
  )
  
  if page == "Documento":
    qa_pdf.show()
  elif page == "Chatbot":
    chatbot.show()

if __name__ == "__main__":
  main()