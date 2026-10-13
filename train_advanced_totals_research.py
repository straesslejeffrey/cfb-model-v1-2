"""Research-only 2025 -> 2026 advanced total-score challenger.

Fits on 2025 games, evaluates late 2025 weeks and exports an experimental 2026
total only. The A/B orientation is made irrelevant using symmetric features.
Do not promote or use in production without cross-season validation.
"""
import argparse, json
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from sklearn.pipeline import make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge

PAIR_METRICS = (
    "offPointsPerDrive","defPointsPerDriveAllowed",
    "offPPAperPlay","defPPAperPlayAllowed",
    "offSuccessRate","defSuccessRateAllowed",
    "offScoringOpportunityRate","defScoringOpportunityRateAllowed",
    "offExplosiveDriveRate","defExplosiveDriveRateAllowed",
    "offTurnoverDriveRate","defTurnoverDriveRateForced",
    "offPointsPerScoringOpportunity","defPointsPerScoringOpportunityAllowed",
)
WINDOWS=(3,5)

def symmetric_features(df, historical):
    features={}
    for metric in PAIR_METRICS:
        for n in WINDOWS:
            if historical:
                left=f"home_pregame_{metric}_L{n}"
                right=f"away_pregame_{metric}_L{n}"
            else:
                left=f"teamA_2026_{metric}_last{n}"
                right=f"teamB_2026_{metric}_last{n}"
            if left not in df or right not in df:
                raise ValueError(f"Missing compatible feature pair: {left} / {right}")
            a=pd.to_numeric(df[left],errors="coerce")
            b=pd.to_numeric(df[right],errors="coerce")
            prefix=f"{metric}_{n}"
            features[prefix+"_sum"]=a+b
            features[prefix+"_absdiff"]=(a-b).abs()
    return pd.DataFrame(features,index=df.index)

def train_and_evaluate(historical, current, output):
    if len(historical)==0 or len(current)==0:
        raise ValueError("Empty input datasets")
    hist=historical.copy()
    week=pd.to_numeric(hist["week_base"],errors="raise")
    # Weeks 1-8 training, 9-11 hyperparameter selection, 12-14 final research evaluation
    train=week<=8
    tune=(week>=9)&(week<=11)
    test=(week>=12)&(week<=14)
    if min(train.sum(),tune.sum(),test.sum())<40:
        raise ValueError("Insufficient chronological train/tune/test rows")
    X=symmetric_features(hist,True)
    y=pd.to_numeric(hist["actualTotal"],errors="raise")-pd.to_numeric(hist["frozenV12Total"],errors="raise")
    baseline=pd.to_numeric(hist["frozenV12Total"],errors="raise")
    alphas=[10.0,100.0,1000.0,10000.0]
    candidate=[]
    for alpha in alphas:
        m=make_pipeline(SimpleImputer(strategy="median",add_indicator=False),
                        StandardScaler(),Ridge(alpha=alpha))
        m.fit(X.loc[train],y.loc[train])
        val=baseline.loc[tune]+m.predict(X.loc[tune])
        mae=float(np.mean(np.abs(val-hist.loc[tune,"actualTotal"])))
        candidate.append((mae,alpha))
    selected=min(candidate)[1]
    model=make_pipeline(SimpleImputer(strategy="median"),
                        StandardScaler(),Ridge(alpha=selected))
    model.fit(X.loc[train],y.loc[train])
    challenger=baseline.loc[test]+model.predict(X.loc[test])
    truth=pd.to_numeric(hist.loc[test,"actualTotal"],errors="raise")
    baseline_mae=float(np.mean(np.abs(baseline.loc[test]-truth)))
    advanced_mae=float(np.mean(np.abs(challenger-truth)))
    # Final model retrains on every available completed 2025 game. The held-out
    # research metric above MUST NOT be confused with this final fit's performance.
    final=make_pipeline(SimpleImputer(strategy="median"),
                        StandardScaler(),Ridge(alpha=selected))
    final.fit(X,y)
    live=symmetric_features(current,False)
    current_predictions=current[["season","week","gameId","teamA","teamB","predictedTotal"]].copy()
    current_predictions["researchAdvancedTotal"]=pd.to_numeric(current["predictedTotal"],errors="raise")+final.predict(live)
    current_predictions["status"]="EXPERIMENTAL_RESEARCH_ONLY_NOT_PROMOTED"
    out=Path(output);out.mkdir(parents=True,exist_ok=True)
    report={"train_count":int(train.sum()),"tune_count":int(tune.sum()),"test_count":int(test.sum()),
            "alpha":selected,"features":int(X.shape[1]),"frozen_holdout_mae":baseline_mae,
            "challenger_holdout_mae":advanced_mae,
            "improvement":baseline_mae-advanced_mae,
            "2026_rows":len(current_predictions),
            "warning":"2025-only research; no cross-season validation; no production promotion"}
    (out/"research_evaluation.json").write_text(json.dumps(report,indent=2))
    current_predictions.to_csv(out/"research_advanced_2026_totals.csv",index=False)
    joblib.dump(final,out/"research_advanced_totals_2025.joblib")
    print(json.dumps(report,indent=2))
    return report

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--historical-2025",required=True)
    p.add_argument("--current-2026",required=True)
    p.add_argument("--output-dir",required=True)
    a=p.parse_args()
    train_and_evaluate(pd.read_csv(a.historical_2025),
                       pd.read_csv(a.current_2026),a.output_dir)
if __name__=="__main__":main()
