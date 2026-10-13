# Experimental Advanced FBS Feature Builder

**Status: feature engineering only — NOT a trained or deployed prediction upgrade.**

The production Streamlit application currently reads frozen prediction CSVs.
This branch preserves V1.2 and V1.3, adds an independent pregame feature
builder, and DOES NOT change any published score or total.

## Goal
Apply the same structured, timestamp-safe advanced metrics to **every team**,
not hand-picked Twitter/X figures for a single matchup.

## Input schema
One row per **completed team-game**. Required columns:
`season,week,gameId,team,opponent`. Each game needs reciprocal home/opponent
rows. Optional numeric metric names are in `advanced_features.py:METRICS`.

Metric values must be **postgame observations for that exact game**, never
season-ending averages or ranks scraped after the target game. Harmonize
provider definitions before importing; no values are silently imputed.

Supported families include EPA, success rates, early/passing downs,
explosive runs and passes, line yards, stuff/power rate, havoc and pressure,
yards before contact, missed tackles, receiving routes, drive efficiency,
starting field position, third downs, and neutral pace.

**Not currently available in this repository:** complete league-wide
historical play-by-play, provider API credentials, QB/injury history, and the
training pipeline/model artifacts that consume the 282-feature V1.2 contract.

## Usage
```python
import pandas as pd
from advanced_features import (build_pregame_team_features,
    build_matchup_features, build_current_team_features, coverage_report)

games = pd.read_csv("completed_team_games.csv")
pregame = build_pregame_team_features(games)
schedule = pd.read_csv("historical_schedule.csv")
matchups = build_matchup_features(schedule, pregame)
matchups.to_csv("historical_advanced_matchups.csv", index=False)

upcoming = pd.read_csv("upcoming_team_rows.csv")
future = build_current_team_features(games, upcoming)
print(coverage_report(future).to_string(index=False))
```

For future games, pass `future` to `build_matchup_features` with the
upcoming game schedule. Matchups include each team's lagged metrics, valid
observation counts, and home-minus-away differentials.

## Validation requirements before production
1. Audit V1.2's existing 282-feature contract: remove redundant feature families.
2. Ingest licensed/reliable per-game historical values for the entire FBS.
3. Align school IDs, season/week conventions, postponements, and neutral sites.
4. Audit which metric definitions include garbage time and sack handling.
5. Assert feature timestamps precede kickoff; week-level cutoff is conservative.
6. Train challenger on earlier seasons, test on untouched later seasons.
7. Compare winner accuracy, margin/total MAE, calibration and missingness.
8. Promote only if performance improves. Never overwrite frozen V1.2.

Twitter/X visualizations are leads for metrics, not training data by themselves.
