"""Download and normalize CFBD game-level advanced data for league-wide feature engineering.

Requires CFBD_API_KEY in the environment. Never commit your key.
Calls documented /stats/game/advanced and /stats/game/havoc endpoints.
Exports ONLY metrics directly supported by the returned game-level schema.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import pandas as pd

from advanced_features import build_pregame_team_features, coverage_report

BASE = "https://api.collegefootballdata.com"

# Explicit mappings avoid confusing EPA with CFBD's expected-points-added
# derivative PPA. Field names offEPA/rushEPA in the feature builder are generic;
# this adapter uses dedicated PPA-named fields until definitions are reconciled.
ADV_FIELDS = {
    "offPPA": ("offense", "ppa"),
    "defPPAAllowed": ("defense", "ppa"),
    "rushPPA": ("offense", "rushingPlays", "ppa"),
    "passPPA": ("offense", "passingPlays", "ppa"),
    "defRushPPAAllowed": ("defense", "rushingPlays", "ppa"),
    "defPassPPAAllowed": ("defense", "passingPlays", "ppa"),
    "offSuccessRate": ("offense", "successRate"),
    "defSuccessRateAllowed": ("defense", "successRate"),
    "standardDownSuccess": ("offense", "standardDowns", "successRate"),
    "passingDownSuccess": ("offense", "passingDowns", "successRate"),
    "defStandardDownSuccessAllowed": ("defense", "standardDowns", "successRate"),
    "defPassingDownSuccessAllowed": ("defense", "passingDowns", "successRate"),
    "rushSuccessRate": ("offense", "rushingPlays", "successRate"),
    "passSuccessRate": ("offense", "passingPlays", "successRate"),
    "defRushSuccessRateAllowed": ("defense", "rushingPlays", "successRate"),
    "defPassSuccessRateAllowed": ("defense", "passingPlays", "successRate"),
    "standardDownPPA": ("offense", "standardDowns", "ppa"),
    "passingDownPPA": ("offense", "passingDowns", "ppa"),
    "defStandardDownPPAAllowed": ("defense", "standardDowns", "ppa"),
    "defPassingDownPPAAllowed": ("defense", "passingDowns", "ppa"),
    "rushExplosiveness": ("offense", "rushingPlays", "explosiveness"),
    "passExplosiveness": ("offense", "passingPlays", "explosiveness"),
    "defRushExplosivenessAllowed": ("defense", "rushingPlays", "explosiveness"),
    "defPassExplosivenessAllowed": ("defense", "passingPlays", "explosiveness"),
    "lineYards": ("offense", "lineYards"),
    "defLineYardsAllowed": ("defense", "lineYards"),
    "stuffRateAllowed": ("offense", "stuffRate"),
    "defStuffRateCreated": ("defense", "stuffRate"),
    "powerSuccess": ("offense", "powerSuccess"),
    "defExplosivenessAllowed": ("defense", "explosiveness"),
    "offExplosiveness": ("offense", "explosiveness"),
    "secondLevelYards": ("offense", "secondLevelYards"),
    "defSecondLevelYardsAllowed": ("defense", "secondLevelYards"),
    "openFieldYards": ("offense", "openFieldYards"),
    "defOpenFieldYardsAllowed": ("defense", "openFieldYards"),
    "defPowerSuccessAllowed": ("defense", "powerSuccess"),
}
HAVOC_FIELDS = {
    "havocAllowed": ("offense", "havocRate"),
    "defHavocCreated": ("defense", "havocRate"),
    "frontSevenHavoc": ("defense", "frontSevenHavocRate"),
    "defensiveBackHavoc": ("defense", "dbHavocRate"),
}

def _nested(obj, path):
    for k in path:
        if not isinstance(obj, dict):
            return None
        obj = obj.get(k)
    if obj is None:
        return None
    try:
        return float(obj)
    except (ValueError, TypeError):
        return None

def fetch_endpoint(path, year, key, exclude_garbage_time=False):
    params = {"year": int(year), "seasonType": "regular"}
    if path.endswith("/advanced"):
        params["excludeGarbageTime"] = str(bool(exclude_garbage_time)).lower()
    url = BASE + path + "?" + urlencode(params)
    request = Request(url, headers={
        "Authorization": "Bearer " + key,
        "Accept": "application/json",
        "User-Agent": "cfb-v1.2-advanced-feature-audit/0.1",
    })
    try:
        with urlopen(request, timeout=60) as response:
            result = json.load(response)
    except HTTPError as exc:
        raise RuntimeError(f"CFBD API returned HTTP {exc.code} for {path}; check key, quota and API tier") from exc
    if not isinstance(result, list):
        raise ValueError(f"Unexpected {path} response; expected list")
    return result

def normalize_rows(advanced, havoc):
    rows = {}
    for payload, mapping in [(advanced, ADV_FIELDS), (havoc, HAVOC_FIELDS)]:
        for item in payload:
            required = ["season", "week", "gameId", "team", "opponent"]
            if any(item.get(c) is None for c in required):
                raise ValueError("API row missing identity fields")
            key = (int(item["season"]), int(item["week"]), str(item["gameId"]), item["team"], item["opponent"])
            existing = rows.setdefault(key, dict(zip(required, key)))
            for feature, path in mapping.items():
                value = _nested(item, path)
                if value is not None:
                    existing[feature] = value
    if not rows:
        raise ValueError("No rows returned. Data unavailable or incorrect entitlement.")
    if not advanced:
        raise ValueError("Advanced stats are required; havoc-only rows are not sufficient.")
    result = pd.DataFrame(list(rows.values()))
    # Reject partial matchup records explicitly: the feature builder requires
    # reciprocal game rows and must not silently fabricate missing teams.
    pairs = result.groupby(["season", "gameId"])
    for _, group in pairs:
        if len(group) != 2 or set(group.team) != set(group.opponent):
            raise ValueError("API lacks reciprocal rows for one or more games")
        if group.week.nunique() != 1:
            raise ValueError("Inconsistent week on paired rows")
    if not set(ADV_FIELDS).intersection(result.columns):
        raise ValueError("Advanced endpoint did not yield mapped metrics")
    return result.sort_values(["season", "week", "gameId", "team"]).reset_index(drop=True)

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--start-year", type=int, required=True)
    p.add_argument("--end-year", type=int, required=True)
    p.add_argument("--output-dir", default="local_advanced_data")
    p.add_argument("--exclude-garbage-time", action="store_true")
    args = p.parse_args()
    key = os.getenv("CFBD_API_KEY")
    if not key:
        raise SystemExit("CFBD_API_KEY environment variable is required")
    if args.start_year > args.end_year:
        raise SystemExit("start-year must be <= end-year")
    all_rows = []
    for year in range(args.start_year, args.end_year+1):
        adv = fetch_endpoint("/stats/game/advanced", year, key, args.exclude_garbage_time)
        havoc = fetch_endpoint("/stats/game/havoc", year, key)
        normalized = normalize_rows(adv, havoc)
        all_rows.append(normalized)
        print(f"{year}: {len(normalized)} completed team-game rows")
    games = pd.concat(all_rows, ignore_index=True)
    # Import feature registry here to preserve separate PPA vs EPA names.
    from advanced_features import METRICS
    metric_names = list(ADV_FIELDS)+list(HAVOC_FIELDS)
    for metric in metric_names:
        if metric not in METRICS:
            METRICS.append(metric)
    features = build_pregame_team_features(games)
    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    games.to_csv(out/"cfbd_team_games.csv", index=False)
    features.to_csv(out/"cfbd_pregame_advanced.csv", index=False)
    coverage_report(features).to_csv(out/"coverage_report.csv", index=False)
    print(f"Wrote datasets to {out.resolve()}")

if __name__ == "__main__":
    main()
