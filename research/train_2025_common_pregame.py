"""Research-only chronological benchmark; does not produce 2026 predictions."""
import json
import pandas as pd
import numpy as np
from sklearn.pipeline import make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge
import argparse

METRICS = ["offPointsPerDrive", "defPointsPerDriveAllowed", "offPPAperPlay",
           "defPPAperPlayAllowed", "offSuccessRate", "defSuccessRateAllowed",
           "offScoringOpportunityRate", "defScoringOpportunityRateAllowed",
           "offExplosiveDriveRate", "defExplosiveDriveRateAllowed",
           "offTurnoverDriveRate", "defTurnoverDriveRateForced",
           "offPointsPerScoringOpportunity", "defPointsPerScoringOpportunityAllowed"]

def evaluate(df):
    cols=[f"home_pregame_{metric}_{window}"
          for metric in METRICS for window in ("L3","L5")]
    if not set(cols).issubset(df):
        raise ValueError("Historical feature contract mismatch")
    if not {"week_base","actualTotal","frozenV12Total"}.issubset(df):
        raise ValueError("Missing targets or frozen baseline")
    x=df[cols].apply(pd.to_numeric, errors="coerce").replace([np.inf,-np.inf],np.nan)
    residual=df.actualTotal-df.frozenV12Total
    train=df.week_base<=8
    tune=df.week_base.between(9,11)
    test=df.week_base.between(12,14)
    if min(train.sum(),tune.sum(),test.sum())<10:
        raise ValueError("Insufficient independent chronological splits")
    def model(alpha):
        m=make_pipeline(SimpleImputer(strategy="median",keep_empty_features=True),
                        StandardScaler(),Ridge(alpha=alpha))
        m.fit(x.loc[train],residual.loc[train])
        return m
    scores={}
    for a in (10,100,1000,10000):
        adjustment=model(a).predict(x.loc[tune])
        scores[a]=float(np.mean(abs(residual.loc[tune]-adjustment)))
    best=min(scores,key=scores.get)
    adjustment=model(best).predict(x.loc[test])
    frozen=float(np.mean(abs(residual.loc[test])))
    challenger=float(np.mean(abs(residual.loc[test]-adjustment)))
    return {"training_games":int(train.sum()),"tuning_games":int(tune.sum()),
            "test_games":int(test.sum()),"selected_alpha":best,
            "feature_count":len(cols),"validation_mae_by_alpha":scores,
            "frozen_total_mae":frozen,"research_total_mae":challenger,
            "research_gain":frozen-challenger,
            "status":"RESEARCH_ONLY_NOT_DEPLOYABLE",
            "caveat":"Home-side historical features only. 2026 teamA/teamB orientation not validated. Not cross-season tested."}
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--backtest",required=True)
    p.add_argument("--report",required=True)
    a=p.parse_args()
    result=evaluate(pd.read_csv(a.backtest,low_memory=False))
    with open(a.report,"w") as f:json.dump(result,f,indent=2)
    print(json.dumps(result,indent=2))
