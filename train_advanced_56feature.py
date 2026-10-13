"""Leakage-guarded research training for common home/away rolling features.

Fit candidate on one set of seasons; select alpha on a later season; evaluate
on a never-used final year. Requires the same 56-feature contract in inference.
Does NOT promote or deploy automatically.
"""
import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd
from align_advanced_feature_contract import historical_features, current_features, feature_contract

FEATURE_NAMES=[f"{s}_{m}_last{w}" for s,m,w in feature_contract()]

def _model(alpha):
    from sklearn.impute import SimpleImputer
    from sklearn.preprocessing import StandardScaler
    from sklearn.linear_model import Ridge
    from sklearn.pipeline import make_pipeline
    return make_pipeline(SimpleImputer(strategy="median",add_indicator=False),
                         StandardScaler(),Ridge(alpha=alpha))

def train(historical, current, destination, train_end=2023, validation_year=2024, test_year=2025):
    required=["season","week","actualTotal","frozenV12Total"]
    for col in required:
        if col not in historical: raise ValueError(f"Historical target missing: {col}")
    if not train_end < validation_year < test_year:
        raise ValueError("Chronological split required")
    hx=historical_features(historical).replace([np.inf,-np.inf],np.nan).astype(float)
    if list(hx.columns)!=FEATURE_NAMES: raise ValueError("Feature order drift")
    residual=pd.to_numeric(historical.actualTotal)-pd.to_numeric(historical.frozenV12Total)
    seasons=pd.to_numeric(historical.season)
    train_mask=seasons<=train_end
    valid_mask=seasons==validation_year
    test_mask=seasons==test_year
    sizes=[int(m.sum()) for m in (train_mask,valid_mask,test_mask)]
    if min(sizes)<50: raise ValueError(f"Insufficient split sizes: {sizes}")
    if hx.loc[train_mask].notna().mean().min()<.35:
        raise ValueError("Training feature missingness too high")
    scores={}
    for a in (10.,100.,1000.,10000.):
        model=_model(a).fit(hx.loc[train_mask],residual.loc[train_mask])
        predicted=model.predict(hx.loc[valid_mask])
        scores[a]=float(np.mean(np.abs(residual.loc[valid_mask]-predicted)))
    alpha=min(scores,key=scores.get)
    final=_model(alpha).fit(hx.loc[train_mask|valid_mask],residual.loc[train_mask|valid_mask])
    holdout=final.predict(hx.loc[test_mask])
    frozen_mae=float(np.abs(residual.loc[test_mask]).mean())
    candidate_mae=float(np.mean(np.abs(residual.loc[test_mask]-holdout)))
    current_x=current_features(current).replace([np.inf,-np.inf],np.nan).astype(float)
    if list(current_x.columns)!=FEATURE_NAMES:raise ValueError("Inference feature order drift")
    if current_x.isna().mean().max()>.1:raise ValueError("Insufficient current inference features")
    # Predictions deliberately not exported before a promotion decision.
    destination=Path(destination);destination.mkdir(parents=True,exist_ok=True)
    report=dict(train_games=sizes[0],validation_games=sizes[1],test_games=sizes[2],
                selected_alpha=alpha,feature_count=len(FEATURE_NAMES),
                frozen_2025_total_mae=frozen_mae,challenger_2025_total_mae=candidate_mae,
                gain=frozen_mae-candidate_mae,validation_scores=scores,
                inference_rows=len(current),inference_feature_coverage=float(current_x.notna().mean().mean()),
                status="RESEARCH_ONLY_NOT_DEPLOYED")
    (destination/"advanced_56feature_holdout_report.json").write_text(json.dumps(report,indent=2))
    if candidate_mae < frozen_mae-0.10:
        from joblib import dump
        dump({"pipeline":final,"features":FEATURE_NAMES,"test_year":test_year,
              "model_version":"V1.2_ADVANCED_CANDIDATE"},destination/"advanced_56feature_candidate.joblib")
        report["candidate_saved"]=True
    else:
        report["candidate_saved"]=False
    (destination/"advanced_56feature_holdout_report.json").write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))
    return report

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--historical",required=True)
    p.add_argument("--current",required=True)
    p.add_argument("--schedule",required=True,help="Verified 2026 schedule CSV with season,gameId,homeTeam,awayTeam")
    p.add_argument("--output",required=True)
    a=p.parse_args()
    h=pd.read_parquet(a.historical) if a.historical.endswith(".parquet") else pd.read_csv(a.historical)
    c=pd.read_csv(a.current)
    schedule=pd.read_csv(a.schedule)
    keys=["season","gameId"]
    needed=set(keys+["homeTeam","awayTeam"])
    if not needed.issubset(schedule):
        raise ValueError("Verified 2026 home/away schedule fields missing")
    if schedule.duplicated(keys).any():
        raise ValueError("Duplicate verified 2026 schedule game IDs")
    for key in keys:
        c[key]=pd.to_numeric(c[key],errors="raise")
        schedule[key]=pd.to_numeric(schedule[key],errors="raise")
    c=c.merge(schedule[keys+["homeTeam","awayTeam"]],on=keys,how="left",validate="one_to_one")
    if c[["homeTeam","awayTeam"]].isna().any().any():
        raise ValueError("Missing verified home-away game orientation")
    train(h,c,a.output)
