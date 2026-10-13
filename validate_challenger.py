"""Offline promotion gate for advanced V1.2 challenger research.

Usage:
 python validate_challenger.py --baseline baseline.csv --challenger challenger.csv

Each CSV: gameId,season,actualTotal,predictedTotal
Optional: actualMargin,predictedMargin.
No data is uploaded to GitHub.
"""
import argparse
import numpy as np
import pandas as pd

def evaluate(baseline, challenger, min_gain=0.10):
    keys=["season","gameId"]
    for name,df in [("baseline",baseline),("challenger",challenger)]:
        missing=set(keys+["actualTotal","predictedTotal"])-set(df.columns)
        if missing: raise ValueError(f"{name} missing columns: {sorted(missing)}")
        if df.duplicated(keys).any(): raise ValueError(f"{name} duplicate games")
    a=baseline[keys+["actualTotal","predictedTotal"]].rename(columns={"actualTotal":"baseActual","predictedTotal":"basePred"})
    b=challenger[keys+["actualTotal","predictedTotal"]].rename(columns={"actualTotal":"newActual","predictedTotal":"newPred"})
    m=a.merge(b,on=keys,how="outer",indicator=True,validate="one_to_one")
    if not (m["_merge"]=="both").all():
        raise ValueError("Different game coverage: compare exactly the same held-out games")
    for c in ["baseActual","newActual","basePred","newPred"]:
        m[c]=pd.to_numeric(m[c],errors="raise")
        if not np.isfinite(m[c]).all(): raise ValueError(f"Invalid values in {c}")
    if not np.allclose(m.baseActual,m.newActual,atol=0,rtol=0):
        raise ValueError("The actual outcomes disagree")
    rows=[]
    for season,g in m.groupby("season"):
        frozen=np.mean(abs(g.basePred-g.baseActual))
        challenger_mae=np.mean(abs(g.newPred-g.newActual))
        gain=frozen-challenger_mae
        rows.append({"season":season,"games":len(g),"frozen_total_mae":frozen,
                     "challenger_total_mae":challenger_mae,"improvement":gain,
                     "passes_min_gain":bool(gain>=min_gain)})
    return pd.DataFrame(rows)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--baseline",required=True)
    p.add_argument("--challenger",required=True)
    p.add_argument("--min-gain",type=float,default=.10)
    p.add_argument("--require-season",type=int,default=2025)
    args=p.parse_args()
    r=evaluate(pd.read_csv(args.baseline),pd.read_csv(args.challenger),args.min_gain)
    print(r.to_string(index=False,float_format=lambda x:f"{x:.5f}"))
    selected=r.loc[r.season==args.require_season]
    if selected.empty:
        raise SystemExit("FAILED: required untouched season missing")
    if not selected.passes_min_gain.all():
        raise SystemExit("RESEARCH ONLY: challenger fails minimum improvement")
    print("PASSED MINIMUM TOTAL-MAE THRESHOLD (not sufficient alone to promote).")

if __name__=="__main__":main()
