from pydantic import ValidationError
from app.schema import Invoice

good = {"vendor": "ACME", "currency":"INR", "subtotal":500, "tax":90, "total":590}
print("good ->", Invoice(**good)) # Invoice(**good) is the key trick. The ** unpacks the dictionary into named fields, so it behaves as if you'd written

no_tax = {"subtotal":500, "total":590} # This tests that a missing tax is allowed. The validator skips its check because one of the three numbers is None, and return self still hands the invoice back.
print("no tax -->", Invoice(**no_tax))

bad_tests = {
    "bad currency": {"currency": "Rupees"},
    "negative ammount": {"total": -5},
    "totals dont add up": {"subtotal": 500, "tax":90, "total":999},
    "impossible date": {"invoice_date": "2026-13-45"},
}

#.items() gives you each label and its data as a pair, one at a time. So name is the label, and data is the bad invoice.
# The loop runs the same code four times, once per bad case, so you don't repeat it.
for name, data in bad_tests.items(): 
    try:
        Invoice(**data)
        print(name, "-> unexpectedly passed")
    except ValidationError as e:
        print(name, "-> rejected", e.errors()[0]["msg"])