"""
score_surveys.py — MARS & SUS scoring with robust CSV loading
Inputs
  surveys/mars.csv  # headers: E1..E5,F1..F4,A1..A3,I1..I4,S1  (1–5 Likert)
  surveys/sus.csv   # headers: Q1..Q10                       (1–5 Likert)
Outputs
  charts/P5_mars.png   # MARS subscales bar chart
  charts/P6_sus.png    # SUS histogram
Console
  Prints sample size and means. Gracefully warns if files/headers missing.
"""

import os, numpy as np, pandas as pd, matplotlib.pyplot as plt

os.makedirs("charts", exist_ok=True)

MARS_PATH = "surveys/mars.csv"
SUS_PATH  = "surveys/sus.csv"

def read_csv_robust(path: str) -> pd.DataFrame:
    """Load CSV with best-effort encoding/delimiter handling and clean headers."""
    for enc in ("utf-8-sig", "utf-8", "cp1252", "gbk"):
        try:
            df = pd.read_csv(path, sep=None, engine="python", encoding=enc)
            # strip whitespace/BOM, uppercase headers (accept e1/E1 etc.)
            df.columns = [str(c).strip().replace("\ufeff", "").upper() for c in df.columns]
            # coerce all cells to numeric where possible
            for c in df.columns:
                df[c] = pd.to_numeric(df[c], errors="coerce")
            return df
        except Exception:
            continue
    raise SystemExit(f"[error] Failed to read CSV: {path}")

made_any = False

# --------- MARS ----------
if os.path.exists(MARS_PATH):
    mars = read_csv_robust(MARS_PATH)
    need = set(["E1","E2","E3","E4","E5","F1","F2","F3","F4","A1","A2","A3","I1","I2","I3","I4","S1"])
    if need.issubset(set(mars.columns)):
        def mean_cols(cols): 
            return float(mars[cols].mean(axis=1).mean())
        E = mean_cols(["E1","E2","E3","E4","E5"])
        F = mean_cols(["F1","F2","F3","F4"])
        A = mean_cols(["A1","A2","A3"])
        I = mean_cols(["I1","I2","I3","I4"])
        Overall = float(mars["S1"].mean())

        plt.figure()
        plt.bar(["Engagement","Functionality","Aesthetics","Information","Overall"],
                [E, F, A, I, Overall])
        plt.ylim(0, 5)
        plt.ylabel("Mean (1–5)")
        plt.title("P5 MARS subscales")
        plt.savefig("charts/P5_mars.png", bbox_inches="tight")
        plt.close()
        print(f"[MARS] n={len(mars)}  E={E:.2f} F={F:.2f} A={A:.2f} I={I:.2f} Overall={Overall:.2f}")
        made_any = True
    else:
        print("[warn] mars.csv missing headers. Got:", list(mars.columns))
else:
    print("[info] surveys/mars.csv not found (skip MARS).")

# --------- SUS ----------
if os.path.exists(SUS_PATH):
    sus = read_csv_robust(SUS_PATH)
    need = set([f"Q{i}" for i in range(1,11)])
    if need.issubset(set(sus.columns)):
        scores = []
        for _, r in sus.iterrows():
            odd  = sum(max(0, min(4, (r[q] or 0) - 1))   for q in ["Q1","Q3","Q5","Q7","Q9"])
            even = sum(max(0, min(4, 5 - (r[q] or 0)))  for q in ["Q2","Q4","Q6","Q8","Q10"])
            scores.append((odd + even) * 2.5)
        mean_sus = float(np.mean(scores)) if scores else float("nan")

        plt.figure()
        plt.hist(scores, bins=5)
        plt.xlabel("SUS score (0–100)")
        plt.title("P6 SUS distribution")
        plt.savefig("charts/P6_sus.png", bbox_inches="tight")
        plt.close()
        print(f"[SUS] n={len(scores)}  mean={mean_sus:.1f}")
        made_any = True
    else:
        print("[warn] sus.csv missing headers. Got:", list(sus.columns))
else:
    print("[info] surveys/sus.csv not found (skip SUS).")

print("Charts saved -> ./charts" if made_any else
      "No survey figures generated. Please check CSV paths/headers.")
