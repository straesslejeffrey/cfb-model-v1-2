# 2025 advanced challenger: game-level independent replication

Verified October 13, 2026 from the original 762-row archived CSV:
`V1_2_ADVANCED_SCORING_2025_BACKTEST.csv` downloaded from the
original Google Drive project. This is an ARCHIVED backtest, not a new model.

| Measure | Result |
|---|---:|
| Games | 762 |
| Frozen V1.2 total MAE | 13.082629 |
| Advanced total MAE | 12.992434 |
| MAE difference | +0.090195 |
| Games where advanced abs error smaller | 58.136% |
| Median game-level absolute-error improvement | +0.102906 |
| 10,000 bootstrap 95% CI for mean game-level difference | [+0.04915, +0.13137] |
| Bootstrap share with positive mean | 100% |
| 2025 weeks with positive average gain | 16/16 |
| Promotion MAE threshold | +0.10 |
| Decision | **KEEP FROZEN V1.2** |

Computed using game-level `abs(frozenV12Total - actualTotal)` minus
`abs(advancedChallengerTotal - actualTotal)`, random seed 4526.
Bootstrap resamples games as though independent; it does NOT reflect
model selection uncertainty, temporal correlation, or future data drift.
The original experiment explored candidate architectures on historical
data. Therefore the above confidence interval should not be interpreted
as proof of prospective performance.

Week-by-week MAE improvement (positive means advanced performs better):

| Week | Games | Improvement |
|---|---:|---:|
| 1 | 48 | .038 |
| 2 | 50 | .021 |
| 3 | 47 | .153 |
| 4 | 50 | .130 |
| 5 | 51 | .137 |
| 6 | 50 | .080 |
| 7 | 56 | .173 |
| 8 | 59 | .046 |
| 9 | 53 | .043 |
| 10 | 52 | .051 |
| 11 | 51 | .184 |
| 12 | 58 | .103 |
| 13 | 60 | .092 |
| 14 | 67 | .010 |
| 15 | 9 | .158 |
| 16 | 1 | .908 |

Note Week 16 has one game and is not a stable comparison.

Next promotion work is **prospective/strictly out-of-time 2026 evaluation**,
including independent margin and winner accuracy, and finding reliable
new feature families not already in the 1,011 research candidates.
Never tune to 2025 and then report the same 2025 as an untouched test.
