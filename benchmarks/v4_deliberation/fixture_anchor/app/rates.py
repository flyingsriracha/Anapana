"""Currency conversion. Each call hits a slow external FX provider."""
import time

call_count = 0


def get_exchange_rate(currency: str) -> float:
    """Look up USD exchange rate for `currency`.

    Hits a remote FX API: ~0.4s per call. Uncached.  # TODO: cache this?
    """
    global call_count
    call_count += 1
    time.sleep(0.4)  # network round-trip to the FX provider
    return {"EUR": 1.08, "GBP": 1.27, "JPY": 0.0067}[currency]
