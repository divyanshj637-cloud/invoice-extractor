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