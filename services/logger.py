"""
CSV event logger.

- Creates logs/run_YYYYmmdd_HHMMSS.csv on import.
- log(type, label="", value_ms="") appends a row:
    ts | type | label | value_ms
- APP_T0 captures process start for cold-start measurements.
"""

import os, csv, time
from datetime import datetime

os.makedirs("logs", exist_ok=True)
LOG_PATH = os.path.join("logs", f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")

with open(LOG_PATH, "w", newline="", encoding="utf-8") as f:
    csv.writer(f).writerow(["ts", "type", "label", "value_ms"])

def log(evt_type, label="", value_ms=""):
    with open(LOG_PATH, "a", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow([datetime.now().isoformat(), evt_type, label, value_ms])

APP_T0 = time.perf_counter()
