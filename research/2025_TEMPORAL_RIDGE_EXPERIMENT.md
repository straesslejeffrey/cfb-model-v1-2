# Advanced residual research: strict within-2025 chronological split

Research-only experiment using the existing saved 2025 advanced backtest (762 games).

- Input: V1_2_ADVANCED_SCORING_2025_BACKTEST.csv from Google Drive
- Model: Median imputation + standard scaling + Ridge regression of actualTotal minus frozenV12Total
- Features: 80 selected deterministically by pregame-oriented names (gameDiff, gameAdjDiff, gameMatchupAdvantage; recent L3 and L5 efficiency/drive/PPA signals)
- Train Weeks 1-8 (411 games)
- Choose regularization on Weeks 9-11 (156 games); alpha 100 selected from 10,100,1000,10000
- Final evaluation Weeks 12-14 (185 games) not used for the Ridge fit or alpha selection
- Frozen total MAE: 13.055643308
- Challenger total MAE: 12.934682239
- MAE improvement: 0.120961069 points/game

WARNING: This is **not** a cross-season backtest, not an untouched multi-year prospective comparison, not an audit of every original feature's pregame cutoff, and not validation of 2026 deployment. Do not swap V1.2 scores based on these numbers. The 2026 matchup matrix is separately available in the user's Google Drive, but still requires authentic Parquet execution and its coverage audit.

Three remaining launch stages: (1) execute, verify and connect current 2026 game-level inputs; (2) backtest/retrain independent 2018-2025 years and 2026 outcomes, and pass promotion rules; (3) wire validated predictor into Streamlit, test and deploy.
