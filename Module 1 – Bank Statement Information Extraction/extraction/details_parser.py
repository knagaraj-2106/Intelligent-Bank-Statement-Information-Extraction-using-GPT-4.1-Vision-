import json
from openai import OpenAI
from config import OPENAI_API_KEY


client = OpenAI(
    api_key=OPENAI_API_KEY
)


def extract_basic_details(text):

    prompt = f"""
You are a bank statement extraction system.

Extract the following fields from the bank statement text.

Return ONLY valid JSON.

Required fields:

bank_name
bank_branch
ifsc_code
micr_no
bank_id
account_number
account_address
account_open_date
account_type
cif_no
nominee_exist
mobile_no
email_id
statement_date
from_date
to_date
customer_id

Rules:

1. Return null if value not available.
2. Do not explain anything.
3. Return only JSON.
4. Do not add markdown.
5. Output must be valid JSON.

Bank Statement Text:

{text}
"""

    try:

        response = client.chat.completions.create(

            model="gpt-4o-mini",

            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],

            temperature=0
        )

        result = response.choices[0].message.content.strip()

        details = json.loads(result)

        return details


    except Exception as e:

        return {

            "bank_name": None,
            "bank_branch": None,
            "ifsc_code": None,
            "micr_no": None,
            "bank_id": None,
            "account_number": None,
            "account_address": None,
            "account_open_date": None,
            "account_type": None,
            "cif_no": None,
            "nominee_exist": None,
            "mobile_no": None,
            "email_id": None,
            "statement_date": None,
            "from_date": None,
            "to_date": None,
            "customer_id": None,
            "error": str(e)
        }
