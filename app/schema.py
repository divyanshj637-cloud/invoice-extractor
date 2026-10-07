from datetime import date  # real date type: 2026-09-12 is stored as a date, not loose text
from typing import Literal  # lets you say "only these exact values are allowed"

from pydantic import BaseModel, Field, model_validator  # schema base, per-field rules, whole-model rules


class LineItem(BaseModel):  # One row on the invoice, like "Notebook, 10 pieces, 50 each, 500 total."
    description: str  # what was sold, e.g. "Notebook" (required)
    quantity: float | None = Field(default=None, ge=0)    # how many, e.g. 10
    unit_price: float | None = Field(default=None, ge=0)  # price of one, e.g. 50
    amount: float | None = Field(default=None, ge=0)      # row total, e.g. 500


# The whole invoice: header details, money totals, and the list of rows.
# Every field can be None, because a missing value must stay missing, not be guessed.
class Invoice(BaseModel):
    vendor: str | None = None
    invoice_number: str | None = None
    invoice_date: date | None = None
    currency: Literal["INR", "USD", "EUR"] | None = None  # only these codes, otherwise None
    subtotal: float | None = Field(default=None, ge=0)    # before tax, e.g. 500
    tax: float | None = Field(default=None, ge=0)         # e.g. 90
    total: float | None = Field(default=None, ge=0)       # final amount, e.g. 590
    line_items: list[LineItem] = []

    # Our own rule: if subtotal, tax, and total are all present, they must add up.
    @model_validator(mode="after")  # runs after all fields are filled in
    def check_totals(self):
        # Only check when all three exist; if one is missing there's nothing to compare.
        if None not in (self.subtotal, self.tax, self.total):
            # Allow a 0.01 difference for rounding.
            if abs(self.subtotal + self.tax - self.total) > 0.01:
                raise ValueError(
                    f"subtotal + tax ({self.subtotal + self.tax}) "
                    f"does not match total ({self.total})"
                )
        return self  # hand the invoice back unchanged if it passed




