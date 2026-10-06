import os
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel

load_dotenv()

client= OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1",

)

class Invoice(BaseModel):
    vendor: str
    total: float | None=None
    invoice_number: str
    phone: str | None=None

text="""
ACME STATIONERY PVT LTD
Invoice #1042      Date:12/09/2026
Notebook *10 ........... 500.00
GST 18% ................ 90.00
TOTAL: 590.00
"""

resp= client.chat.completions.parse(
    model="openai/gpt-oss-20b",
    messages=[
        {"role": "system", "content": "Extract invoice fields."},
        {"role": "user", "content": text},
    ],
    response_format=Invoice,

)

print(resp.choices[0].message.parsed)