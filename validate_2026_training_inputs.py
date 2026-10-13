"""Validate current-season advanced matchup inputs before model inference.

Inputs contain V1.2 frozen score estimates and trailing 2026 team form.
This validator does NOT train, fit, or alter predictions.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import pandas as pd

REQUIRED = ["season","week","gameId","teamA","teamB","predictedTotal","predictedMargin",
            "teamA_priorGameCount","teamB_priorGameCount",
            "teamA_lastHistoricalWeek","teamB_lastHistoricalWeek"]
METRICS = ["offPointsPerDrive","defPointsPerDriveAllowed","offPPAperPlay",
           "defPPAperPlayAllowed","offSuccessRate","defSuccessRateAllowed",
           "offScoringOpportunityRate","defScoringOpportunityRateAllowed",
           "offExplosiveDriveRate","defExplosiveDriveRateAllowed",
           "offTurnoverDriveRate","defTurnoverDriveRateForced",
           "offPointsPerScoringOpportunity","defPointsPerScoringOpportunityAllowed"]

def validate(df):
    missing=sorted(set(REQUIRED)-set(df.columns))
    if missing: raise ValueError(f"Required fields missing: {missing}")
    if df.duplicated(["season","gameId"]).any(): raise ValueError("Duplicate game keys")
    for side in ("teamA","teamB"):
        if not (pd.to_numeric(df[side+"_priorGameCount"],errors="coerce") >= 3).all():
            raise ValueError(side+" has fewer than three previous games")
        if not (pd.to_numeric(df[side+"_lastHistoricalWeek"],errors="coerce") <
                pd.to_numeric(df["week"],errors="coerce")).all():
            raise ValueError(side+" has historical week >= target week")
        for metric in METRICS:
            for window in (3,5):
                col=f"{side}_2026_{metric}_last{window}"
                if col not in df: raise ValueError("Missing "+col)
    expected=[f"{side}_2026_{m}_last{w}" for side in ("teamA","teamB")
              for m in METRICS for w in (3,5)]
    coverage=df[expected].apply(pd.to_numeric,errors="coerce").notna().mean(axis=1)
    return {"games":int(len(df)),"identity_unique":True,
            "both_teams_at_least_three_prior_games":True,
            "every_history_precedes_prediction_week":True,
            "advanced_feature_count":len(expected),
            "rows_at_least_80pct_coverage":int((coverage>=.8).sum()),
            "minimum_coverage":round(float(coverage.min()),4),
            "maximum_coverage":round(float(coverage.max()),4),
            "status":"RESEARCH_INPUT_VALIDATED_NOT_RETRAINED"}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",required=True)
    p.add_argument("--report",default="advanced_2026_validation.json")
    args=p.parse_args()
    report=validate(pd.read_csv(args.input))
    Path(args.report).write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))
if __name__=="__main__":main()
