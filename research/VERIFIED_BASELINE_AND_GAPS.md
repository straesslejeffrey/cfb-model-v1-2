# Independently reproduced 2025 advanced scoring benchmark

Source: user's original saved Drive file `V1_2_ADVANCED_SCORING_2025_BACKTEST.csv` (762 games).
Recomputed from actualTotal, frozenV12Total, and advancedChallengerTotal.

| Metric | Frozen V1.2 | Advanced challenger | Change |
|---|---:|---:|---:|
| Total MAE | 13.082629 | 12.992434 | 0.090195 lower |
| Total RMSE | 16.128711 | 16.024325 | 0.104386 lower |
| Signed error (predicted minus actual) | +2.619633 | +2.333730 | 0.285903 closer to zero |

**Production promotion: NOT approved.** Historical MAE gain 0.090195 is
below the frozen 0.10 minimum threshold. Do not rewrite production
predictions on this evidence.

Feature-contract audit of the exact stored 1,011-feature list:
- PPA: 105 matching names
- Success rate: 117
- Drive metrics: 549
- Scoring opportunity references: 216
- Explosive drive references: 105
- Turnover references: 105
- No exact-name match for havoc, line yards, stuff rate, pressure rate,
  red-zone, field position, or quarterback availability.

These counts **overlap** and do not add up to 1,011. The absence of a
keyword in the 1,011 candidate names does not prove the frozen V1.2 or
underlying V1.3 datasets lacked that metric. It flags areas for precise
source-column inspection.

## Reproduce
```bash
python audit_archived_2025.py \
  --backtest V1_2_ADVANCED_SCORING_2025_BACKTEST.csv
```

Saved raw 2025 file belongs in protected data storage; do not commit
13.5 MB of game rows containing over 1000 features to the app repo.

## Next experiment
Recover earlier-year train/validation rows (2018-2024) from the existing
Parquet research set and model artifacts, build an incremental missing-
metric challenger, then evaluate 2025 **without fitting anything on 2025**.
Promote only following threshold, temporal, and prospective 2026 validation.
