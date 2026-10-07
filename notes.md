# Phase 1 notes: hello-world extraction

Setup: Groq API, model openai/gpt-oss-20b, Pydantic schema, structured output via `.parse`.

## Experiments

**Exp 1/2: removed the TOTAL line, then made `total` optional**
- Happened: the model still returned 590 by adding 500 + 90.
- Learned: making a field optional only allows None; it doesn't stop the model from calculating a value.

**Exp 3: added `invoice_number`**
- Happened: returned `1042` without the "#".
- Learned: output format varies unless the prompt specifies it.

**Exp 4: added `phone`, which isn't in the text**
- `phone: str` -> returned `''` (empty string, looks like real data).
- `phone: str | None = None` -> returned `None` (honest "not found").
- Learned: use optional fields for anything that might be missing.

## Fix
Added to the system prompt: "do not calculate, infer or guess; return null if not written."

Result: `total=None`, `invoice_number='1042'`, `phone=None`.


# Phase 2 notes: real schema and validation

Built `app/schema.py` with `LineItem` and `Invoice` (Pydantic): optional fields default to None, `ge=0` blocks negatives, `Literal` limits currency to INR/USD/EUR, `date` rejects impossible dates, and a `model_validator` checks subtotal + tax = total (tolerance 0.01).

## Schema tests (`try_schema.py`, no API calls)
- Good invoice accepted; invoice with no tax accepted (tax stays None, validator skips its check).
- Rejected as expected: bad currency, negative amount, totals that don't add up, impossible date (2026-13-45).
- Learned: `default=0` on tax would have wrongly rejected invoices with no tax stated, so missing fields use None.

## Experiments with the model (`hello.py`)

**Messier invoice (date "12 Sep 2026", line items, GBP)**
- Date converted to a real date object (2026-09-12).
- Invoice number returned without "#", as the prompt asked.
- Currency GBP is not in the allowed list -> returned None instead of forcing a wrong value.
- Unit prices not written in the text -> returned None (no calculating).
- Problem: the "GST 18%" rows were extracted as line items. Tax rows are not products. Needs a prompt rule.

**Model misread the total**
- The model returned 600 (the SUB TOTAL line) as the grand total.
- The validator caught it: "subtotal + tax (708.0) does not match total (600.0)".
- Fix: prompt now says to use the exact number printed next to TOTAL and never recalculate.

**Deliberately wrong total (70887.00)**
- Model extracted 70887 faithfully, as the prompt instructs.
- Validator rejected it: "subtotal + tax (708.0) does not match total (70887.0)".
- The script crashes because nothing handles the error yet. Phase 4 retry loop will.

