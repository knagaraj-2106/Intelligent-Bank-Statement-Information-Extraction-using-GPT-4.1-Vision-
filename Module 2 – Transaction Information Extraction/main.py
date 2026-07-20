import streamlit as st
import pdfplumber
import json
import mysql.connector
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage
from datetime import datetime

# -------------------------------
# GPT MODEL
# -------------------------------

llm = ChatOpenAI(
    model="gpt-4.1",
    temperature=0
)

# -------------------------------
# MYSQL CONNECTION
# -------------------------------

def get_connection():

    try:

        connection = mysql.connector.connect(
            host="127.0.0.1",
            user="root",
            password="Salaar@2106",
            database="bank_ai"
        )

        return connection

    except Exception as e:

        st.error(
            f"Database Connection Error: {e}"
        )

        raise

def get_all_statements():

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""
        SELECT id, bank_name
        FROM basic_details
        ORDER BY id
    """)

    records = cursor.fetchall()

    cursor.close()
    connection.close()

    return records

# -------------------------------
# PDF TEXT EXTRACTION
# -------------------------------

def extract_pdf_text(pdf_file):

    text = ""

    with pdfplumber.open(pdf_file) as pdf:

        for page in pdf.pages:

            page_text = page.extract_text()

            if page_text:
                text += page_text + "\n"

    return text

# -------------------------------
# CLEAN GPT RESPONSE
# -------------------------------

def clean_json_response(content):

    content = content.strip()

    if content.startswith("```json"):
        content = content.replace("```json", "")

    if content.startswith("```"):
        content = content.replace("```", "")

    if content.endswith("```"):
        content = content.replace("```", "")

    return content.strip()

# -------------------------------
# LLM EXTRACTION
# -------------------------------

def extract_transaction_details(statement_text):

    prompt = f"""
You are a bank statement extraction system.

Extract ALL transactions from the bank statement.

Return ONLY valid JSON.

Rules:
1. Return JSON array only.
2. No explanations.
3. No markdown.
4. No comments.
5. No extra text.
6. Return every transaction found.
7. Do not return samples.
8. Do not truncate.
9. Do not summarize.
10. Return all transactions.
11. transaction_date MUST be returned in YYYY-MM-DD format.
12. Never return DD/MM/YYYY.

Example:

[
  {{
    "transaction_date": "2023-07-01",
    "description": "ATM Withdrawal",
    "transaction_no": "N/A",
    "cheque_no": "N/A",
    "debit_amount": 1000,
    "credit_amount": null,
    "balance_amount": 9000
  }}
]

Bank Statement:

{statement_text}
"""

    try:

        response = llm.invoke(
            [HumanMessage(content=prompt)]
        )

        raw_content = response.content

        st.subheader("Raw LLM Output")
        st.text(raw_content)

        cleaned_content = clean_json_response(
            raw_content
        )

        data = json.loads(
            cleaned_content
        )

        if not isinstance(data, list):

            st.error(
                "LLM did not return a JSON array."
            )

            return []

        return data

    except json.JSONDecodeError as e:
    
        st.error(
            f"JSON Parsing Error: {e}"
        )
    
        st.download_button(
            label="Download Raw GPT Response",
            data=raw_content,
            file_name="gpt_response.txt",
            mime="text/plain"
        )
    
        return []

    except Exception as e:

        st.error(
            f"LLM Error: {e}"
        )

        return []

def convert_date(date_value):

    if not date_value:
        return None

    formats = [
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%Y-%m-%d",
        "%d %b %Y",
        "%d %B %Y"
    ]

    for fmt in formats:

        try:

            return datetime.strptime(
                str(date_value).strip(),
                fmt
            ).strftime("%Y-%m-%d")

        except:

            pass

    return None

# -------------------------------
# SAVE TO DATABASE
# -------------------------------

def save_to_database(transactions, statement_id):

    if len(transactions) == 0:
        return 0

    connection = get_connection()

    cursor = connection.cursor()

    sql = """
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

    inserted_count = 0

    try:

        for transaction in transactions:

            formatted_date = convert_date(
                transaction.get("transaction_date")
            )
            
            values = (
                statement_id,
                formatted_date,
                transaction.get("description"),
                transaction.get("transaction_no"),
                transaction.get("cheque_no"),
                transaction.get("debit_amount"),
                transaction.get("credit_amount"),
                transaction.get("balance_amount")
            )

            cursor.execute(
                sql,
                values
            )

            inserted_count += 1

        connection.commit()

    except Exception as e:

        connection.rollback()

        st.error(
            f"Database Error: {e}"
        )

    finally:

        cursor.close()
        connection.close()

    return inserted_count

# -------------------------------
# STREAMLIT UI
# -------------------------------

st.set_page_config(
    page_title="Bank Statement Extractor",
    layout="wide"
)

st.title("Bank Statement Extractor")

statements = get_all_statements()

if not statements:

    st.error(
        "No records found in basic_details table."
    )

    st.stop()

selected_statement = st.selectbox(
    "Select Statement ID",
    statements,
    format_func=lambda x: f"ID {x[0]} - {x[1]}"
)

uploaded_file = st.file_uploader(
    "Upload Bank Statement PDF",
    type=["pdf"]
)

if uploaded_file:

    with st.spinner(
        "Reading PDF..."
    ):

        statement_text = extract_pdf_text(
            uploaded_file
        )

    st.success(
        "PDF Read Successfully"
    )

    if st.button(
        "Extract Transactions"
    ):

        all_transactions = []

        with pdfplumber.open(uploaded_file) as pdf:

            total_pages = len(pdf.pages)

            for page_number, page in enumerate(pdf.pages, start=1):

                st.write(
                    f"Processing Page {page_number} of {total_pages}"
                )

                page_text = page.extract_text()

                if page_text:

                    page_transactions = extract_transaction_details(
                        page_text
                    )

                    if page_transactions:

                        all_transactions.extend(
                            page_transactions
                        )

        transactions = all_transactions

        st.subheader(
            "Extracted Transactions"
        )

        st.json(
            transactions
        )

        st.write(
            "Transaction Count:",
            len(transactions)
        )

        if len(transactions) > 0:

            # Get selected ID from dropdown
            statement_id = selected_statement[0]
        
            st.success(
                f"Using Statement ID: {statement_id}"
            )
        
            rows_inserted = save_to_database(
                transactions,
                statement_id
            )
        
            st.success(
                f"{rows_inserted} Transactions Saved Successfully"
            )
        
        else:
        
            st.warning(
                "No transactions found."
            )
