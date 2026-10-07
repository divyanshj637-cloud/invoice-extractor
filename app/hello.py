import os
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel
from app.schema import Invoice

load_dotenv()

client= OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1",

)



text="""
ACME STATIONERY PVT LTD
Invoice #1042      Date: 12 Sep 2026
Notebook *10 ........... 500.00 GBP
GST 18% ................ 90.00 GBP
Pen *5  ................ 100 GBP
GST 18% ...............  18 GBP
SUB TOTAL:600
TAX: 108
TOTAL: 708.00 GBP
"""

resp= client.chat.completions.parse(
    model="openai/gpt-oss-20b",
    messages=[
        {
            "role": "system",
            "content": """Extract invoice fields using ONLY values explicitly written in the text. Do not calculate, infer, guess, or correct any values.

CRITICAL FOR TOTALS AND MATH:
- Documents may contain printing or arithmetic errors.
- Extract the exact number printed next to 'TOTAL', even if it mathematically contradicts the subtotal or tax.
- NEVER recalculate or 'fix' the grand total.

FORMAT RULES:
- If a value is missing, return null.
- Invoice number: omit any '#' symbol.
- Dates: format as YYYY-MM-DD.
- Currency: must be one of INR, USD or EUR otherwise null."""
        },
        {"role": "user", "content": text},
    ],
    response_format=Invoice,

)

print(resp.choices[0].message.parsed)