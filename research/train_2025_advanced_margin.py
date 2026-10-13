"""2025 chronological orientation-safe margin residual experiment; research only."""
import argparse,json
from pathlib import Path
import numpy as np,pandas as pd
from sklearn.pipeline import make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge
from train_advanced_totals_research import symmetric_features

def margin_features(df):
    x=symmetric_features(df,True).replace([np.inf,-np.inf],np.nan)
    x["abs_frozen_margin"]=pd.to_numeric(df.frozenV12Margin,errors="raise").abs()
    return x

def evaluate(df):
    need={"frozenV12Margin","actualMarginTeamA","actualTeamAPoints",
          "actualTeamBPoints","week_base"}
    if missing:=need-set(df):raise ValueError(f"Missing fields: {sorted(missing)}")
    if (df.actualTeamAPoints-df.actualTeamBPoints-df.actualMarginTeamA).abs().max()>1e-8:
        raise ValueError("Invalid margin orientation/target")
    x=margin_features(df)
    base=pd.to_numeric(df.frozenV12Margin,errors="raise")
    truth=pd.to_numeric(df.actualMarginTeamA,errors="raise")
    signs=np.where(base>=0,1.,-1.)
    residual=(truth-base)*signs
    w=pd.to_numeric(df.week_base,errors="raise")
    train=w<=8; tune=w.between(9,11);holdout=w.between(12,14)
    if min(train.sum(),tune.sum(),holdout.sum())<40:
        raise ValueError("Insufficient chronological splits")
    def model(alpha):
        return make_pipeline(SimpleImputer(strategy="median"),
                             StandardScaler(),Ridge(alpha=alpha))
    trials={}
    for alpha in (10,100,1000,10000):
        m=model(alpha).fit(x.loc[train],residual.loc[train])
        pred=base.loc[tune]+signs[tune]*m.predict(x.loc[tune])
        trials[alpha]=float(np.mean(abs(pred-truth.loc[tune])))
    alpha=min(trials,key=trials.get)
    m=model(alpha).fit(x.loc[train],residual.loc[train])
    pred=base.loc[holdout]+signs[holdout]*m.predict(x.loc[holdout])
    actual=truth.loc[holdout]
    baseline_mae=float(abs(base.loc[holdout]-actual).mean())
    candidate_mae=float(abs(pred-actual).mean())
    return dict(train_games=int(train.sum()),tune_games=int(tune.sum()),
                holdout_games=int(holdout.sum()),features=len(x.columns),
                alpha=alpha,baseline_margin_mae=baseline_mae,
                advanced_margin_mae=candidate_mae,
                improvement=baseline_mae-candidate_mae,
                baseline_winner_accuracy=float((np.sign(base.loc[holdout])==np.sign(actual)).mean()),
                advanced_winner_accuracy=float((np.sign(pred)==np.sign(actual)).mean()),
                status="RESEARCH_ONLY_DO_NOT_PROMOTE")
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--historical",required=True);p.add_argument("--output",required=True)
    args=p.parse_args()
    result=evaluate(pd.read_csv(args.historical,low_memory=False))
    Path(args.output).write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))
