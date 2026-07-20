import streamlit as st
import os

from extraction.pdf_extractor import extract_text
from extraction.details_parser import extract_basic_details
from database.insert_data import save_basic_details
from llm.llm_process import process_with_llm

st.title("Bank Statement Extractor")

uploaded_file = st.file_uploader(
    "Upload Statement",
    type=['pdf']
)

if uploaded_file:
    path = os.path.join('uploads',uploaded_file.name)

    with open(path,'wb') as f:
        f.write(uploaded_file.getbuffer())
    st.success('File uploaded')

    text = extract_text(path)
    data = extract_basic_details(text)
    st.subheader("Structured Details")
    st.json(data)

    if st.button('Store and Process'):
        inserted_id=save_basic_details(data)
        st.success(f"Stored Successfully ID={inserted_id}")
        # llm_output = process_with_llm(data)
        # st.subheader('LLM Output')
        # st.write(llm_output)
