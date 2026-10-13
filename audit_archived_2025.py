"""Audit archived V1.2 vs advanced 2025 challenger predictions (not a retrain)."""
import argparse
import json
import numpy as np
import pandas as pd

def evaluate(df, min_gain=0.10):
    required={"gameId","season","week","actualTotal","frozenV12Total","advancedChallengerTotal"}
    if required-set(df.columns):
        raise ValueError("Missing fields: "+str(sorted(required-set(df.columns))))
    if df.duplicated(["season","gameId"]).any():raise ValueError("Duplicate games")
    for c in ["actualTotal","frozenV12Total","advancedChallengerTotal"]:
        df[c]=pd.to_numeric(df[c],errors="raise")
        if not np.isfinite(df[c]).all(): raise ValueError("Nonfinite "+c)
    def metrics(g):
        a=(g.frozenV12Total-g.actualTotal).to_numpy()
        b=(g.advancedChallengerTotal-g.actualTotal).to_numpy()
        return dict(games=len(g),frozenMAE=round(float(np.abs(a).mean()),6),
                    advancedMAE=round(float(np.abs(b).mean()),6),
                    improvement=round(float(np.abs(a).mean()-np.abs(b).mean()),6),
                    frozenRMSE=round(float(np.sqrt(np.mean(a*a))),6),
                    advancedRMSE=round(float(np.sqrt(np.mean(b*b))),6))
    overall=metrics(df)
    overall["passesMinimumImprovement"]=bool(overall["improvement"]>=min_gain)
    by_week=[dict(week=int(w),**metrics(g)) for w,g in df.groupby("week",sort=True)]
    return dict(overall=overall,by_week=by_week,
                caution="Historical 2025 evaluation; not prospective 2026 validation")
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--backtest",required=True)
    p.add_argument("--output",default="saved_2025_advanced_audit.json")
    a=p.parse_args()
    r=evaluate(pd.read_csv(a.backtest))
    with open(a.output,"w") as f:json.dump(r,f,indent=2)
    print(json.dumps(r["overall"],indent=2))
