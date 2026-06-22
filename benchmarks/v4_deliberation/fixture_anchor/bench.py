"""Reproduce the slow /report. Run: python bench.py"""
import time
from app import rates
from app.report import build_report
from db.pool import POOL


def main():
    rates.call_count = 0
    t0 = time.perf_counter()
    report = build_report()
    elapsed = time.perf_counter() - t0
    print(f"rows in report:        {len(report)}")
    print(f"elapsed:               {elapsed:.2f}s")
    print(f"FX provider calls:     {rates.call_count}")
    print(f"max pool conns in use: {POOL.max_in_use}")


if __name__ == "__main__":
    main()
