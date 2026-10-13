"""Fail-closed historical promotion gate for V1.2 Advanced.

A true original-V1.2 comparison requires frozen V1.2 predictions for every
evaluation game. Generic historical targets and alternate model baselines do
not substitute for original V1.2 out-of-time predictions.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import pandas as pd

REQUIRED = {"season","gameId","actualTotal","frozenV12Total"}

def historical_baseline_gate(historical, baseline, years=(2024,2025)):
    missing = REQUIRED - set(baseline)
    if missing: raise ValueError(f"Baseline required fields absent: {sorted(missing)}")
    if not {"season","gameId"}.issubset(historical): raise ValueError("Historical IDs missing")
    keys=["season","gameId"]
    if baseline.duplicated(keys).any(): raise ValueError("Duplicate original baseline game identity")
    history=historical[keys].drop_duplicates().copy()
    joined=history.merge(baseline[list(REQUIRED)],on=keys,how="left",validate="one_to_one")
    by_year={}
    for year in years:
        subset=joined[joined.season==year]
        verified=subset[["actualTotal","frozenV12Total"]].notna().all(axis=1)
        by_year[str(year)]={"games":int(len(subset)),"verified_baselines":int(verified.sum()),
                             "missing":int((~verified).sum())}
    passed=all(r["games"]>0 and r["missing"]==0 for r in by_year.values())
    return {"years":by_year,"cross_season_v12_comparison_ready":passed,
            "status":"PASS" if passed else "BLOCKED_MISSING_TRUE_FROZEN_V12_BASELINES",
            "fallback":"Independent challenger-vs-challenger cross-year analysis is possible, but must not be labeled V1.2 superiority."}

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--history",required=True)
    p.add_argument("--baseline",required=True)
    p.add_argument("--output",default="advanced_historical_baseline_gate.json")
    args=p.parse_args()
    h=pd.read_parquet(args.history) if args.history.endswith(".parquet") else pd.read_csv(args.history)
    b=pd.read_csv(args.baseline)
    report=historical_baseline_gate(h,b)
    Path(args.output).write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))
    if not report["cross_season_v12_comparison_ready"]:
        raise SystemExit(2)
