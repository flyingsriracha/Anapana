from pricing import total_with_tax


def test_zero_rate():
    # No tax: total equals the pre-tax amount.
    assert total_with_tax(5000, 0) == 5000


def test_total_with_tax():
    # $100.00 at 8.25% tax should be $108.25.
    assert total_with_tax(10000, 825) == 10800
