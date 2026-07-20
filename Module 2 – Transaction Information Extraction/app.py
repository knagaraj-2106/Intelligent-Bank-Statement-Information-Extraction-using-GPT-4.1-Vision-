BSExtractorProject2-Part2/app.py:

import streamlit as st

from pdf_reader import extract_text_from_pdf
from llm_extractor import extract_transactions
from db_insert import insert_transactions

st.set_page_config(
    page_title="Bank Transaction Extractor",
    layout="wide"
)

st.title("Bank Statement Transaction Extractor")

statement_id = st.number_input(
    "Statement ID",
    min_value=1,
    step=1
)

uploaded_file = st.file_uploader(
    "Upload Bank Statement PDF",
    type=["pdf"]
)

if st.button("Extract Transactions"):

    if uploaded_file is None:
        st.error("Please upload a PDF")
        st.stop()

    try:

        with st.spinner("Reading PDF..."):
            statement_text = extract_text_from_pdf(
                uploaded_file
            )

        st.success("PDF Read Successfully")

        st.write(
            "Characters Extracted:",
            len(statement_text)
        )

        with st.spinner("Extracting Transactions..."):
            transactions = extract_transactions(
                statement_text,
                statement_id
            )

        st.success(
            f"{len(transactions)} Transactions Extracted"
        )

        st.write(
            "Transactions Found:",
            len(transactions)
        )

        if len(transactions) > 0:

            st.dataframe(
                transactions,
                use_container_width=True
            )

        else:

            st.warning(
                "No Transactions Found"
            )

            st.stop()

        with st.spinner(
            "Saving Transactions To Database..."
        ):
            insert_transactions(
                transactions
            )

        st.success(
            "Transactions Stored Successfully"
        )

    except Exception as e:

        st.error(
            f"Application Error: {str(e)}"
        )

BSExtractorProject2-Part2/db_connection.py:

import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    connection = mysql.connector.connect(
        host = os.getenv("DB_HOST"),
        user = os.getenv("DB_USER"),
        password = os.getenv("DB_PASSWORD"),
        database = os.getenv('DB_NAME')
    )
    return connection

BSExtractorProject2-Part2/db_insert.py:

from db_connection import get_connection
def insert_transactions(transaction_list):

    connection = get_connection()

    cursor = connection.cursor()

    query = """
    INSERT INTO transaction_details
    (
        statement_id,
        transaction_date,
        description,
        transaction_no,
        cheque_no,
        debit_amount,
        credit_amount,
        balance_amount
    )
    VALUES
    (
        %s,%s,%s,%s,%s,%s,%s,%s
    )
    """

    for row in transaction_list:

        values = (
            row.get("statement_id"),
            row.get("transaction_date"),
            row.get("description"),
            row.get("transaction_no"),
            row.get("cheque_no"),
            row.get("debit_amount"),
            row.get("credit_amount"),
            row.get("balance_amount")
        )

        cursor.execute(query, values)

    connection.commit()

    cursor.close()
    connection.close()

BSExtractorProject2-Part2/llm_extractor.py:

import json
from os import getenv
from langchain.text_splitter import RecursiveCharacterTextSplitter
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()

llm = ChatOpenAI(
    model='gpt-4o-mini',
    temperature=0,
    api_key=getenv('OPENAI_API_KEY')
)

def extract_transactions(statement_text, statement_id):

    prompt = f"""
    You are an expert bank statement analyzer.

    Extract all the transactions from the uploaded bank statement.

    Return ONLY valid JSON.

    JSON Format.

    [
    {{
        "statement_id": {statement_id},
        "transaction_date": "YYYY-MM-DD",
        "description": "",
        "transaction_no": "",
        "cheque_no": "",
        "debit_amount": 0,
        "credit_amount": 0,
        "balance_amount": 0
    }}
    ]

    Rules:
    1. Extract every transaction that are available in tabular format. each row belongs one transaction.import
    2. In some of the uploaded bank statements Description column name mentioned as Description,TRANSACTION 			    PARTICULARS,Details,Narration all these can consider under column "description".
    3. Possible scenarios the debit column named as Withdrawal and credit column named as Deposit consider it as Withdrawal=debit_amount, Deposit=credit_amount.
    4. Keep null values as empty string.
    5. Convert dates into YYYY-MM-DD format.
    6. No Explanation.

    Bank Statement:
    {statement_text}
    """
    print(f"Total Characters Received: {len(statement_text)}")
    print("Calling GPT...")
    
    response = llm.invoke(prompt)

    print("\n")
    print("=" * 100)
    print("RAW GPT RESPONSE")
    print("=" * 100)
    
    print(repr(response.content))
    
    print("=" * 100)
    print("END GPT RESPONSE")
    print("=" * 100)
    
    return []
