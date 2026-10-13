"""Explicit historical-to-current pregame feature alignment.

No predictions are generated here. Historical HOME/AWAY alignment must be
verified using homeTeam/awayTeam identifiers; teamA/teamB are not assumed home.
"""
import pandas as pd
from validate_2026_training_inputs import METRICS

def feature_contract():
    return [(side,metric,window) for side in ("home","away")
            for metric in METRICS for window in (3,5)]

def historical_features(frame):
    names={f"{side}_pregame_{metric}_L{window}":
           f"{side}_{metric}_last{window}"
           for side,metric,window in feature_contract()}
    missing=sorted(set(names)-set(frame))
    if missing: raise ValueError(f"Missing historical features: {missing[:12]}")
    if not {"homeTeam","awayTeam","season","week"}.issubset(frame):
        raise ValueError("Missing historical game/team identities")
    return frame[list(names)].rename(columns=names)

def current_features(frame):
    needed={"teamA","teamB","season","week","homeTeam","awayTeam"}
    if not needed.issubset(frame):
        raise ValueError("Must provide explicit homeTeam and awayTeam mapping; cannot infer teamA is home")
    normal=(frame.teamA==frame.homeTeam)&(frame.teamB==frame.awayTeam)
    reversed_=(frame.teamB==frame.homeTeam)&(frame.teamA==frame.awayTeam)
    if not (normal|reversed_).all():
        raise ValueError("TeamA/teamB and home/away identities disagree")
    output=pd.DataFrame(index=frame.index)
    for side,metric,window in feature_contract():
        a=f"teamA_2026_{metric}_last{window}"
        b=f"teamB_2026_{metric}_last{window}"
        if not {a,b}.issubset(frame): raise ValueError(f"Missing current features {a}, {b}")
        src_normal=a if side=="home" else b
        src_reverse=b if side=="home" else a
        output[f"{side}_{metric}_last{window}"]=pd.to_numeric(frame[src_normal].where(normal,frame[src_reverse]),errors="coerce")
    return output

if __name__=="__main__":
    print("Common feature contract:",len(feature_contract()))
