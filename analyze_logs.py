"""
Outputs:
  - P1_startup.png    (cold vs warm, median)
  - P2_tts.png        (TTS start latency by step, median)
  - P3_reroute.png    (Reroute latency histogram)
  - P4_battery.png    (optional; session battery start/end)
  - P7_prewarm.png    (optional; TTS prewarm histogram)
  - Prints per-session medians
  - Prints latest-session robust stats (median, IQR, 95% CI)
  - Prints A/B analysis for TTS prewarm (ON vs OFF)
  - Saves CSV summaries in charts/
"""

import os, glob
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

os.makedirs("charts", exist_ok=True)

# ---------- Config ----------
USE_LATEST_ONLY = True    # True: analyze only the latest session for charts & robust stats
N_BOOT = 2000             # bootstrap iterations for 95% CI
RNG = np.random.default_rng(42)
# ----------------------------

# Load logs
files = sorted(glob.glob("logs/run_*.csv"))
if not files:
    raise SystemExit("No logs found. Run main.py first.")

def load_sessions(files_list):
    dfs = []
    for f in files_list:
        try:
            d = pd.read_csv(f)
            d["session"] = os.path.basename(f)
            dfs.append(d)
        except Exception as e:
            print(f"[warn] skip {f}: {e}")
    if not dfs:
        raise SystemExit("No readable logs.")
    return pd.concat(dfs, ignore_index=True)

df_all = load_sessions(files)

# Per-session medians (for quick sanity check)
def per_session_median(evt):
    d = df_all[df_all["type"] == evt]
    if d.empty: 
        return pd.Series(dtype=float)
    return d.groupby("session")["value_ms"].median()

table = pd.concat([
    per_session_median("cold_start_ms").rename("cold_start_ms"),
    per_session_median("warm_start_ms").rename("warm_start_ms"),
    per_session_median("tts_start_latency_ms").rename("tts_start_latency_ms"),
    per_session_median("reroute_latency_ms").rename("reroute_latency_ms"),
], axis=1)

print("=== Per-session medians (ms) ===")
print(table.fillna("—"))

# Choose dataset for charts & robust stats
if USE_LATEST_ONLY:
    latest = files[-1]
    print(f"\n[info] Using latest session for charts & robust stats: {os.path.basename(latest)}")
    df = pd.read_csv(latest)
else:
    df = df_all.copy()

# ---------- Helper stats ----------
def robust_stats(series: pd.Series, n_boot=N_BOOT):
    s = pd.to_numeric(series, errors="coerce").dropna()
    if s.empty:
        return np.nan, np.nan, (np.nan, np.nan), 0
    med = float(np.median(s))
    iqr = float(np.percentile(s, 75) - np.percentile(s, 25))
    boots = [np.median(RNG.choice(s, size=len(s), replace=True)) for _ in range(n_boot)]
    ci = (float(np.percentile(boots, 2.5)), float(np.percentile(boots, 97.5)))
    return med, iqr, ci, len(s)

def save_summary_row(rows, name, series):
    med, iqr, ci, n = robust_stats(series)
    rows.append({
        "metric": name,
        "median_ms": med,
        "IQR_ms": iqr,
        "CI95_low_ms": ci[0],
        "CI95_high_ms": ci[1],
        "n": n
    })

# ---------- Charts P1–P4, P7 ----------
# P1: cold vs warm
cold = df[df["type"]=="cold_start_ms"]["value_ms"]
warm = df[df["type"]=="warm_start_ms"]["value_ms"]
cold_med = np.median(cold) if not cold.empty else np.nan
warm_med = np.median(warm) if not warm.empty else np.nan

plt.figure()
plt.bar(["cold","warm"], [cold_med, warm_med])
plt.title("P1 Cold vs Warm (median ms)")
plt.ylabel("ms")
plt.savefig("charts/P1_startup.png", bbox_inches="tight")
plt.close()

# P2: TTS start by step (median)
tts = df[df["type"]=="tts_start_latency_ms"]
if not tts.empty:
    g = tts.groupby("label")["value_ms"].median().sort_values()
    plt.figure()
    g.plot(kind="bar")
    plt.title("P2 TTS Start Latency by Step (median ms)")
    plt.ylabel("ms")
    plt.savefig("charts/P2_tts.png", bbox_inches="tight")
    plt.close()

# P3: reroute histogram
rr = df[df["type"]=="reroute_latency_ms"]
if not rr.empty:
    plt.figure()
    rr["value_ms"].plot(kind="hist", bins=10)
    plt.title("P3 Reroute Latency Distribution")
    plt.xlabel("ms")
    plt.savefig("charts/P3_reroute.png", bbox_inches="tight")
    plt.close()

# P4: battery (optional)
bs = df[df["type"]=="battery_start_pct"]["value_ms"]
be = df[df["type"]=="battery_end_pct"]["value_ms"]
if not bs.empty and not be.empty:
    s = pd.Series({"start(%)": bs.iloc[-1], "end(%)": be.iloc[-1]})
    plt.figure()
    s.plot(kind="bar")
    plt.ylim(0, 100)
    plt.title("P4 Battery % (session)")
    plt.savefig("charts/P4_battery.png", bbox_inches="tight")
    plt.close()

# P7: prewarm histogram (optional)
pre = df[df["type"]=="tts_prewarm_ms"]["value_ms"]
if not pre.empty:
    plt.figure()
    pre.plot(kind="hist", bins=10)
    plt.title("P7 TTS Prewarm (ms)")
    plt.savefig("charts/P7_prewarm.png", bbox_inches="tight")
    plt.close()

# ---------- Robust stats (latest or all, depending on USE_LATEST_ONLY) ----------
rows = []
save_summary_row(rows, "cold_start_ms", cold)
save_summary_row(rows, "warm_start_ms", warm)
save_summary_row(rows, "tts_start_latency_ms", tts["value_ms"])
save_summary_row(rows, "reroute_latency_ms", rr["value_ms"])
summary_df = pd.DataFrame(rows)
summary_df.to_csv("charts/summary_metrics.csv", index=False)

print("\n=== Enhanced stats (median / IQR / 95% CI) ===")
print(summary_df.fillna("—"))

# ---------- A/B: Prewarm ON vs OFF over sessions ----------
def session_has_prewarm(path):
    try:
        d = pd.read_csv(path)
        return (d["type"]=="tts_prewarm_ms").any()
    except Exception:
        return False

ab_rows = []
for f in files:
    d = pd.read_csv(f)
    cond = "ON" if session_has_prewarm(f) else "OFF"
    s = d[d["type"]=="tts_start_latency_ms"]["value_ms"]
    if not s.empty:
        ab_rows.append({
            "session": os.path.basename(f),
            "cond": cond,
            "tts_start_median": float(np.median(s))
        })

ab = pd.DataFrame(ab_rows)
if ab.empty or ab["cond"].nunique() < 2:
    print("\n[info] A/B prewarm: need sessions with both ON and OFF to compare.")
else:
    print("\n=== A/B Prewarm (per-session median of TTS start latency) ===")
    print(ab.pivot_table(index="cond", values="tts_start_median", aggfunc="median"))

    on  = ab[ab["cond"]=="ON"]["tts_start_median"].to_numpy()
    off = ab[ab["cond"]=="OFF"]["tts_start_median"].to_numpy()

    # Group-median difference (ON - OFF) with bootstrap CI over sessions
    def boot_ab(n_boot=N_BOOT):
        diffs = []
        for _ in range(n_boot):
            bo = RNG.choice(on,  size=len(on),  replace=True)
            bf = RNG.choice(off, size=len(off), replace=True)
            diffs.append(np.median(bo) - np.median(bf))
        return np.array(diffs)

    diffs = boot_ab()
    diff_med = float(np.median(diffs))
    ci_low, ci_high = float(np.percentile(diffs, 2.5)), float(np.percentile(diffs, 97.5))
    rel_change = (np.median(on)/np.median(off) - 1.0) * 100.0

    ab_out = pd.DataFrame({
        "cond": ["ON_median", "OFF_median", "ON-OFF_median", "ON_vs_OFF_%change", "CI95_low", "CI95_high"],
        "value": [np.median(on), np.median(off), diff_med, rel_change, ci_low, ci_high]
    })
    ab_out.to_csv("charts/ab_prewarm_summary.csv", index=False)

    print(f"Median difference (ON - OFF): {diff_med:.1f} ms  [95% CI {ci_low:.1f}, {ci_high:.1f}]")
    print(f"Relative change: {rel_change:+.1f}%  (negative is better)")
    print("Saved A/B summary -> charts/ab_prewarm_summary.csv")

print("\nCharts saved -> ./charts")
