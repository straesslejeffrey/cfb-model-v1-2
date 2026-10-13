"""Join saved V1.3 *pregame* 2026 matchup evidence to frozen V1.2 games.

Use the already computed 2026 V1.3 game-level matrix from Drive.
This is an advanced explanatory feature bridge, NOT a new trained score model.
Input files may be parquet or csv. Never replace frozen V1.2 predictions.
"""
import argparse
from pathlib import Path
import pandas as pd

FAMILIES = (
    "pregame",
)
UNSAFE = ("actual", "final", "target", "label", "postgame", "result")
JOIN = ["season", "gameId"]
IDENTITY = ["season", "week", "gameId"]
NAME_MAP = {"teamA": "homeTeam", "teamB": "awayTeam"}

def read_table(path):
    return pd.read_parquet(path) if str(path).lower().endswith((".parquet", ".pq")) else pd.read_csv(path)

def add_advanced_context(predictions, matrix, min_coverage=0.65):
    predictions = predictions.copy()
    matrix = matrix.copy()
    needed = set(IDENTITY + ["teamA", "teamB", "predictedTotal", "predictedMargin"])
    if needed-set(predictions):
        raise ValueError(f"Frozen prediction fields missing: {sorted(needed-set(predictions))}")
    required_matrix = set(IDENTITY + ["homeTeam", "awayTeam"])
    if required_matrix-set(matrix):
        raise ValueError(f"Historical matrix identity missing: {sorted(required_matrix-set(matrix))}")
    for df, label in [(predictions, "predictions"), (matrix, "matrix")]:
        for name in ("season", "week", "gameId"):
            df[name] = pd.to_numeric(df[name], errors="raise").astype("int64")
        if df.duplicated(JOIN).any():
            raise ValueError(f"Duplicate {label} season-game IDs")
    eligible = [c for c in matrix if (
        any(prefix in c for prefix in FAMILIES)
        and not any(bad in c.lower() for bad in UNSAFE)
        and pd.api.types.is_numeric_dtype(matrix[c])
    )]
    if not eligible:
        raise ValueError("No explicitly pregame numeric features in matrix")
    # Pre-existing matrices can contain game-performance fields such as
    # home_offPointsPerDrive. These are excluded: only pregame-qualified
    # feature names are eligible for this bridge.
    eligible = [c for c in eligible if (
        c.startswith(("home_pregame_", "away_pregame_", "home_opp_pregame_",
                      "away_opp_pregame_"))
    )]
    if not eligible: raise ValueError("No supported pregame-qualified fields")
    incoming = matrix[IDENTITY + ["homeTeam", "awayTeam"] + eligible].copy()
    incoming = incoming.rename(columns={x: "advanced_" + x for x in eligible})
    result = predictions.merge(incoming, on=JOIN, how="left", validate="one_to_one", suffixes=("", "_source"))
    # TeamA is not guaranteed to mean home in all exports. Require exact orientation.
    match = (result["week"] == result["week_source"])
    match &= (result.teamA == result.homeTeam) & (result.teamB == result.awayTeam)
    evidence_cols = ["advanced_" + c for c in eligible]
    for col in evidence_cols:
        result.loc[~match, col] = float("nan")
    result["advanced2026IdentityMatch"] = match.fillna(False)
    result["advanced2026FeatureCoverage"] = result[evidence_cols].notna().mean(axis=1)
    result["advanced2026Ready"] = result.advanced2026IdentityMatch & (
        result.advanced2026FeatureCoverage >= min_coverage)
    result["advanced2026SelectionPolicy"] = "STRICT_PREGAME_PREFIX_ONLY"
    result["advanced2026Source"] = "V1_3_GAME_LEVEL_MATCHUP_MATRIX_2026 - PREGAME ONLY"
    result["advanced2026Status"] = result.advanced2026Ready.map({
        True: "PREGAME ADVANCED EVIDENCE - NOT YET IN V1.2 SCORING",
        False: "INSUFFICIENT DATA - FROZEN V1.2 SCORES",
    })
    result = result.drop(columns=["week_source", "homeTeam", "awayTeam"])
    return result

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--predictions",required=True)
    p.add_argument("--matrix",required=True)
    p.add_argument("--out",default="local_advanced_data/v12_week7_2026_pregame_context.csv")
    p.add_argument("--minimum-coverage",default=.65,type=float)
    args=p.parse_args()
    if not 0 <= args.minimum_coverage <= 1: p.error("coverage must be from 0 to 1")
    pred=read_table(args.predictions)
    out=add_advanced_context(pred,read_table(args.matrix),args.minimum_coverage)
    if not out.predictedTotal.equals(pred.predictedTotal) or not out.predictedMargin.equals(pred.predictedMargin):
        raise RuntimeError("Frozen predictions unexpectedly changed")
    dst=Path(args.out); dst.parent.mkdir(parents=True,exist_ok=True)
    out.to_csv(dst,index=False)
    print(f"Rows={len(out)} | matched={int(out.advanced2026IdentityMatch.sum())} "
          f"| evidence_ready={int(out.advanced2026Ready.sum())} | "
          f"added_columns={sum(c.startswith('advanced_') for c in out)} | {dst}")
if __name__=="__main__": main()
