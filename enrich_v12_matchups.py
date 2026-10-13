"""Attach league-wide pregame advanced matchup evidence to frozen predictions.

Inputs:
  --predictions: existing V1.2 Streamlit prediction CSV
  --snapshots: pregame team-game features produced by ingest_cfbd.py
Output: enriched matchup CSV. Does NOT modify original scores or claim retraining.
"""
import argparse
from pathlib import Path
import pandas as pd
from advanced_features import build_matchup_features, build_current_team_features, METRICS

PAIRINGS = {
  "rush_success": ("rushSuccessRate", "defRushSuccessRateAllowed"),
  "pass_success": ("passSuccessRate", "defPassSuccessRateAllowed"),
  "standard_down_success": ("standardDownSuccess", "defStandardDownSuccessAllowed"),
  "passing_down_success": ("passingDownSuccess", "defPassingDownSuccessAllowed"),
  "rush_ppa": ("rushPPA", "defRushPPAAllowed"),
  "pass_ppa": ("passPPA", "defPassPPAAllowed"),
  "standard_down_ppa": ("standardDownPPA", "defStandardDownPPAAllowed"),
  "passing_down_ppa": ("passingDownPPA", "defPassingDownPPAAllowed"),
  "line_yards": ("lineYards", "defLineYardsAllowed"),
  "stuff_rate": ("stuffRateAllowed", "defStuffRateCreated"),
  "havoc": ("havocAllowed", "defHavocCreated"),
  "explosiveness": ("offExplosiveness", "defExplosivenessAllowed"),
}

def enrich(predictions: pd.DataFrame, snapshots: pd.DataFrame, min_coverage=.90):
    required={"season","week","gameId","teamA","teamB","predictedTotal","predictedMargin"}
    absent=sorted(required-set(predictions))
    if absent: raise ValueError(f"Prediction file missing {absent}")
    if predictions.duplicated(["season","gameId"]).any(): raise ValueError("Duplicate predictions")
    schedule=predictions[["season","week","gameId","teamA","teamB"]].rename(
        columns={"teamA":"homeTeam","teamB":"awayTeam"})
    # Snapshot generator uses case-sensitive provider team names; do not fuzzy join.
    merged=build_matchup_features(schedule,snapshots)
    original=predictions.merge(merged.drop(columns=["week","homeTeam","awayTeam"]),
        on=["season","gameId"],how="left",validate="one_to_one")
    evidence=[]
    for label,(off,defense) in PAIRINGS.items():
        for n in (3,5,10):
            h=f"home_adv_{off}_last{n}"
            a=f"away_adv_{defense}_last{n}"
            ah=f"away_adv_{off}_last{n}"
            hd=f"home_adv_{defense}_last{n}"
            if {h,a,ah,hd}.issubset(original):
                # Positive value means higher offense metric relative to opposing defense.
                # For stuff and havoc, directional interpretation may differ; raw gap only.
                for side,of,de in [("home",h,a),("away",ah,hd)]:
                    original[f"{side}_{label}_offMinusOppDef_last{n}"] = original[of]-original[de]
                evidence.append(label)
    if not evidence: raise ValueError("No available matchup-pair statistics")
    present=original.filter(regex=r"^(home|away)_.*_offMinusOppDef_last5$")
    row_fraction=present.notna().mean(axis=1)
    original["advancedCoverageFraction"]=row_fraction
    original["advancedDataReady"]=row_fraction>=min_coverage
    original["advancedMatchupStatus"]=original["advancedDataReady"].map(
        {True:"ADVANCED EVIDENCE AVAILABLE - NO RETRAINED SCORES",
         False:"INSUFFICIENT ADVANCED COVERAGE - FROZEN SCORES"})
    original["advancedFeaturePairsAvailable"]=len(set(evidence))
    # Score columns left untouched.
    return original

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--predictions",required=True)
    source=p.add_mutually_exclusive_group(required=True)
    source.add_argument("--snapshots",help="Snapshots already containing the scheduled games")
    source.add_argument("--team-games",help="Completed raw team-games; construct strictly pregame snapshots")
    p.add_argument("--out",default="local_advanced_data/advanced_matchups.csv")
    args=p.parse_args()
    predictions=pd.read_csv(args.predictions)
    if args.snapshots:
        snapshots=pd.read_csv(args.snapshots)
    else:
        games=pd.read_csv(args.team_games)
        from ingest_cfbd import ADV_FIELDS, HAVOC_FIELDS
        for metric in list(ADV_FIELDS)+list(HAVOC_FIELDS):
            if metric not in METRICS: METRICS.append(metric)
        schedule=predictions[["season","week","gameId","teamA","teamB"]]
        home=schedule.rename(columns={"teamA":"team","teamB":"opponent"})
        away=schedule.rename(columns={"teamB":"team","teamA":"opponent"})
        upcoming=pd.concat([home,away],ignore_index=True)
        snapshots=build_current_team_features(games,upcoming)
    result=enrich(predictions,snapshots)
    out=Path(args.out);out.parent.mkdir(parents=True,exist_ok=True)
    result.to_csv(out,index=False)
    print(f"{len(result)} games; {int(result.advancedDataReady.sum())} evidence-ready; output {out}")
if __name__=="__main__":main()
