def total_with_tax(cents: int, rate_bps: int) -> int:
    """Return the total in cents including tax.

    cents:    pre-tax amount, in cents.
    rate_bps: tax rate in basis points (1 bps = 0.01%, so 825 bps = 8.25%).
    """
    tax = cents * rate_bps // 10000
    return cents + tax
