"""Leakage-safe league-wide advanced feature engineering.

Input: completed TEAM-GAME rows, one per team per game, with season, week, gameId,
team, opponent, and optional numeric postgame metrics listed in METRICS.
Output: pregame team snapshots and matchup-differential features.
This module intentionally does not retrain or modify frozen V1.2.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

KEYS = ["season", "week", "gameId", "team", "opponent"]

# Numeric game-level inputs. All are optional individually; only present metrics
# are transformed. Data collection must harmonize metric definitions first.
METRICS = [
    "offEPA", "defEPAAllowed", "rushEPA", "passEPA",
    "defRushEPAAllowed", "defPassEPAAllowed",
    "offSuccessRate", "defSuccessRateAllowed",
    "standardDownSuccess", "passingDownSuccess",
    "defStandardDownSuccessAllowed", "defPassingDownSuccessAllowed",
    "rushExplosiveRate", "passExplosiveRate",
    "defRushExplosiveRateAllowed", "defPassExplosiveRateAllowed",
    "lineYards", "defLineYardsAllowed", "stuffRateAllowed",
    "defStuffRateCreated", "powerSuccess", "defPowerSuccessAllowed",
    "havocAllowed", "defHavocCreated", "frontSevenHavoc",
    "pressureRateAllowed", "defPressureRate", "pressureToSackRate",
    "yardsBeforeContact", "missedTacklesForced", "missedTackleRateAllowed",
    "pointsPerDrive", "pointsPerOpportunity", "opportunitiesPerDrive",
    "defPointsPerDriveAllowed", "defPointsPerOpportunityAllowed",
    "defOpportunitiesPerDriveAllowed", "threeAndOutRate",
    "avgStartingFieldPosition", "neutralSecondsPerPlay",
    "passYardsPerRoute", "thirdDownConversion", "defThirdDownConversionAllowed",
]

def _validate_games(games: pd.DataFrame) -> pd.DataFrame:
    missing = sorted(set(KEYS) - set(games.columns))
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    if games[KEYS].isna().any().any():
        raise ValueError("Required keys must not be missing")
    df = games.copy()
    df["season"] = pd.to_numeric(df["season"], errors="raise").astype(int)
    df["week"] = pd.to_numeric(df["week"], errors="raise").astype(int)
    if (df["week"] < 1).any():
        raise ValueError("week must be at least 1")
    if df.duplicated(["season", "gameId", "team"]).any():
        raise ValueError("Duplicate team-game rows")
    # A completed game has exactly two opposing team rows. Require mutual identity.
    for _, g in df.groupby(["season", "gameId"], sort=False):
        if len(g) != 2 or set(g["team"]) != set(g["opponent"]) or g["team"].nunique() != 2:
            raise ValueError("Each completed game needs exactly two reciprocal team rows")
        if g["week"].nunique() != 1:
            raise ValueError("The two game rows disagree on week")
    return df

def build_pregame_team_features(
    completed_games: pd.DataFrame,
    windows=(3, 5, 10),
) -> pd.DataFrame:
    """Pregame snapshots for completed games, using strictly EARLIER WEEKS.

    One row per team-game; same-week doubleheaders cannot contaminate each other.
    The first game of a season has NaNs and priorGames=0 (no fake zeros).
    By default, the history resets every season. For preseason priors, provide
    a separately timestamped source and validate its cutoff independently.
    """
    df = _validate_games(completed_games)
    present = [m for m in METRICS if m in df.columns]
    if not present:
        raise ValueError("No recognized numeric metric columns")
    for m in present:
        df[m] = pd.to_numeric(df[m], errors="coerce")
        if np.isinf(df[m].to_numpy(dtype=float)).any():
            raise ValueError(f"Infinite values in {m}")
    windows = tuple(sorted(set(int(w) for w in windows)))
    if not windows or min(windows) < 1:
        raise ValueError("windows must contain positive integers")
    df = df.sort_values(["season", "team", "week", "gameId"]).reset_index(drop=True)
    results = []
    for (season, team), g in df.groupby(["season", "team"], sort=False):
        previous = g.iloc[0:0]
        for week, group in g.groupby("week", sort=True):
            for _, match in group.iterrows():
                record = {k: match[k] for k in KEYS}
                record["priorGames"] = len(previous)
                for metric in present:
                    for n in windows:
                        vals = previous[metric].tail(n).dropna()
                        record[f"adv_{metric}_last{n}"] = float(vals.mean()) if len(vals) else np.nan
                        record[f"adv_{metric}_n_last{n}"] = int(len(vals))
                results.append(record)
            previous = pd.concat([previous, group], ignore_index=True)
    return pd.DataFrame(results)

def build_matchup_features(
    schedule: pd.DataFrame,
    team_snapshots: pd.DataFrame,
) -> pd.DataFrame:
    """Join home/away team snapshots to a scheduled game's pregame features.

    schedule columns: season, week, gameId, homeTeam, awayTeam.
    Both snapshots must be supplied for the same game. For FUTURE scheduled
    games, build_current_team_features must be used instead.
    """
    required = ["season", "week", "gameId", "homeTeam", "awayTeam"]
    if not set(required).issubset(schedule.columns):
        raise ValueError(f"Missing schedule columns: {sorted(set(required)-set(schedule.columns))}")
    if schedule.duplicated(["season", "gameId"]).any():
        raise ValueError("Duplicate schedule game IDs")
    if (schedule.homeTeam == schedule.awayTeam).any():
        raise ValueError("Identical home and away teams")
    keys = ["season", "week", "gameId"]
    features = [c for c in team_snapshots if c.startswith("adv_") or c == "priorGames"]
    side = team_snapshots[keys+["team"]+features]
    result = schedule.copy()
    for slot, side_name in [("homeTeam", "home"), ("awayTeam", "away")]:
        incoming = side.rename(columns={"team": slot, **{c:f"{side_name}_{c}" for c in features}})
        result = result.merge(incoming, on=keys+[slot], how="left", validate="one_to_one", indicator=True)
        if (result["_merge"] != "both").any():
            raise ValueError(f"Missing {side_name} pregame snapshot for one or more games")
        result = result.drop(columns="_merge")
    for col in features:
        if col.startswith("adv_") and not "_n_last" in col:
            result["diff_"+col] = result["home_"+col] - result["away_"+col]
    return result

def build_current_team_features(
    completed_games: pd.DataFrame,
    upcoming: pd.DataFrame,
    windows=(3,5,10),
) -> pd.DataFrame:
    """Build team snapshots for a future schedule (not yet in completed_games).

    Upcoming requires season, week, gameId, team, opponent. Only games from
    strictly earlier weeks contribute. Supports all FBS teams provided in data.
    """
    history = _validate_games(completed_games)
    missing = sorted(set(KEYS)-set(upcoming.columns))
    if missing:
        raise ValueError(f"Missing upcoming columns: {missing}")
    if upcoming.duplicated(["season","gameId","team"]).any():
        raise ValueError("Duplicate upcoming teams")
    upcoming = upcoming[KEYS].copy()
    if ((upcoming[["season","gameId"]].apply(tuple,axis=1)).isin(
        history[["season","gameId"]].apply(tuple,axis=1))).any():
        raise ValueError("Upcoming schedule overlaps completed games")
    fake = upcoming.copy()
    for metric in [m for m in METRICS if m in history.columns]:
        fake[metric] = np.nan
    out = build_pregame_team_features(pd.concat([history,fake],ignore_index=True), windows)
    return upcoming.merge(out, on=KEYS, how="left", validate="one_to_one")

def coverage_report(features: pd.DataFrame) -> pd.DataFrame:
    cols = [c for c in features if c.startswith("adv_") and "_n_last" not in c]
    return pd.DataFrame({
        "feature": cols,
        "non_null_rows": [int(features[c].notna().sum()) for c in cols],
        "coverage_pct": [round(100*features[c].notna().mean(),2) for c in cols],
    })
