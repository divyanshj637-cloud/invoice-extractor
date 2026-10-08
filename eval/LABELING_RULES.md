# Labeling rules

How each label file in `eval/labels/` was filled. Follow these so every label is consistent.
Labels are the ground truth for `evaluate.py`. Wrong label = wrong accuracy number.

## General
1. Fill only what is printed on the receipt. If a field is not printed, use `null`.
2. Never calculate a value yourself (no total minus tax to get a subtotal).
3. Numbers are unquoted (`108.5`, not `"108.5"`). Dates are `YYYY-MM-DD`, day-first.
4. `line_items` is `null` for now (not labeled).
5. Never edit `_sroie_hint`. It is only for cross-checking vendor, date and total.
6. `_note` is free text. Use `""` when there is nothing to say (never `null`).

## Fields:

**vendor**
- Use the registered company name if printed (SDN BHD / S/B / BHD / Pvt Ltd / registered business name).
- Otherwise use the shop name at the top.
- Leave out the registration number in brackets, e.g. `(139386 X)`.
- If the OCR text has a typo but the hint shows the real name, use the real name and say so in `_note` (doc_014).

**invoice_number**
- The number next to Invoice No / Invoice # / Bill No / Receipt No / Inv No.
- Also counts: Sales No, Slip No, Doc No, a `BILL ...` line, a line labeled only `NO :`.
- Keep leading zeros. Drop `#`.
- Table, order and vehicle numbers are not invoice numbers.
- Unlabeled codes (e.g. `T1 R000418193`) do not count. No number means `null`.

**invoice_date**
- Always `YYYY-MM-DD`. Dates on the receipts are day-first: `04/12/2017` = 4 Dec 2017 = `2017-12-04`.

**currency**
- `INR` for Rs / ₹ / INR. `MYR` for RM. `USD`, `EUR` when printed.
- `(RM)` in a column header counts as RM.
- `$` alone, `DH`, or no symbol: `null`.

**subtotal**
- Only if a line is printed: Subtotal / Taxable Value / Taxable Amount / Total (Excl. GST) / Total Sales Amount.
- If a printed "Subtotal" already includes tax, use the excl-GST line instead. If none exists, `null` and explain in `_note`.
- Figures that appear only in the GST summary table: `null`.
- Labels like "Plan Charges" or a bare "TOTAL" are not subtotal labels: `null`.

**tax**
- Only if one combined amount is printed (IGST, Total GST, GST line, single-rate GST summary figure).
- A printed `0.00` is `0.0`, not `null`.
- CGST + SGST printed separately with no combined figure: `null`, `_note` = `split GST`.
- Per-item tax only: `null`, `_note` = `per-item tax only`.
- No GST shown at all: `null`.

**total**
- The final amount to pay, after discount and round-off.
- If the receipt prints "inclusive" and "after rounding" totals, use the after-rounding one.

## When the receipt's own math does not add up
Copy the printed numbers anyway. Put the exact phrase `math inconsistent` in `_note`, then the reason.
The checker skips the totals-mismatch error only when `_note` contains `math inconsistent`.

Examples used so far:
- doc_003: `math inconsistent: rounding adjustment 0.02`
- doc_007: `math inconsistent: 10% service charge 8.78 not in subtotal+tax`
- doc_031: `math inconsistent: rounding 0.01`
- doc_040: `split GST; math inconsistent: 1650+148.50+148.50=1947, printed total 1950`

## Judgment calls already made (stay consistent)
- doc_017: `BILL 1856 - 608 - 9161 - 2806180322` is the invoice number.
- doc_030: number labeled only `NO :` is the invoice number.
- doc_027: business name used as vendor (matches the hint); no GST printed so tax is `null`.
- doc_044: "Plan Charges" is not a subtotal label, so subtotal is `null`.
- doc_047: vendor keeps `(Dealer)` because it is not a registration number.
- doc_029 / doc_032: supplies split 0% and 6%, so no single subtotal; tax is the one `GST:` figure.
- Unihakka receipts (011-013, 022, 024, 026): prices in `$` with no RM, so currency is `null`.
