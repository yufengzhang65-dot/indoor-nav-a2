"""
Acceptance thresholds checker.

- Loads the most recent logs/run_*.csv
- Computes medians for key metrics and checks against targets:
    cold_start_ms      <= 1500
    warm_start_ms      <= 800
    tts_start_latency  <= 500
    reroute_latency    <= 1000
- Prints pass/fail summary.

Tip: This script looks at the latest session only.
"""

import glob, pandas as pd, json

TARGETS = {
    "cold_start_ms": 1500,
    "warm_start_ms": 800,
    "tts_start_latency_ms": 500,
    "reroute_latency_ms": 1000
}

files = sorted(glob.glob("logs/*.csv"))
if not files: raise SystemExit("No logs found.")
df = pd.read_csv(files[-1])

def med(evt):
    d = df[df.type==evt]
    return float('nan') if d.empty else d.value_ms.median()

summary = {k: med(k) for k in TARGETS}
print("=== Medians (ms) ==="); print(pd.Series(summary))

verdict = {k: (summary[k] <= TARGETS[k]) for k in TARGETS if pd.notna(summary[k])}
print("=== Threshold Check ==="); print(verdict)

ok_ratio = sum(verdict.values())/len(verdict) if verdict else 0
print(f"Acceptance: {ok_ratio:.0%} of targets met")
