import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKER_ROOT = ROOT / "services" / "worker"
if str(WORKER_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKER_ROOT))

from worker.jobs.process_weather import clamp_date_range


def test_clamp_date_range_future_end_date():
    start = date(2025, 11, 17)
    end = date(2026, 2, 8)
    today = date(2026, 2, 5)

    start_out, end_out, did_clamp = clamp_date_range(start, end, today=today)

    assert start_out == start
    assert end_out == today
    assert did_clamp is True


def test_clamp_date_range_start_after_end():
    start = date(2026, 2, 6)
    end = date(2026, 2, 5)

    start_out, end_out, did_clamp = clamp_date_range(start, end, today=date(2026, 2, 5))

    assert start_out == end
    assert end_out == end
    assert did_clamp is True
