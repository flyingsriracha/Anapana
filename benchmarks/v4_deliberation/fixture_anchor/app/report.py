"""Builds the customer report. This is what /report calls."""
from db.pool import POOL
from app.rates import get_exchange_rate


def build_report():
    """Fetch line items and convert each to USD.

    Single request, single DB connection. The conversion calls the FX
    provider once per line item.
    """
    with POOL.acquire() as conn:
        rows = conn.fetch_rows()

    report = []
    for row in rows:
        rate = get_exchange_rate(row["currency"])
        report.append(
            {
                "id": row["id"],
                "currency": row["currency"],
                "amount_usd": round(row["amount"] * rate, 2),
            }
        )
    return report
