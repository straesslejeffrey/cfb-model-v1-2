# Original Colab notebook discovery — 2026-10-13

The original `CFB_Model_Main_ipynb_2_0 (1).ipynb` was provided for audit.
It contains **1,659 code cells**, and **already implements a substantially
larger advanced-data research pipeline** than the newly added generic
`advanced_features.py` scaffold.

## Confirmed from notebook (not a claim that files are in GitHub)

- Frozen production V1.2 feature contract: **282 features**.
- Advanced scoring research: **1,011 candidate advanced features**.
- Research/common-game matrix: **5,701 historical games**, with 89.93%
  reported feature coverage.
- Research champion: **150 selected features**, advanced residual architecture,
  residual alpha 0.5.
- 2025 untouched evaluation: frozen total MAE **13.0826**, advanced total MAE
  **12.9924**, improvement **0.0902**; 2025 team-points MAE **9.1889** vs
  **9.1511** (improvement 0.0378).
- Formal promotion decision: **KEEP FROZEN V1.2**, advanced challenger
  research-only, **5/6** promotion criteria passed; a separate provisional
  promotion check also failed.
- Another scoring-environment research decision: KEEP_FROZEN_V1_2,
  prospective forward validation required.

Relevant notebook cells by zero-based index:
- 63: Advanced scoring challenger train, validation, 2025 championship.
- 65: Historical advanced feature contract and common-game intersection.
- 62: Advanced final robustness championship and promotion decision.
- 11: Scoring-environment final production decision.
- 70: Team-scoring challenger rejected.
- 75–78: Week 7 V1.2 export, 282-feature bridge, update.
- 1367: Prior CFBD credential reference via Colab Secrets.
- 1433: Historical pregame dataset export.

## Existing Google Drive paths, inferred from notebook code

- `/content/google_drive/MyDrive/CFB_Model/v1_2/scoring_data_upgrade/`
- `/content/google_drive/MyDrive/CFB_Model/v1_2/audit/`
- Original model paths under `CFB_Model/v1_2/` and archived V1.1 model
  artifacts (search notebook for `CFB_V1_1_PHASE_3A_BEST_CANDIDATE.joblib`
  and `CFB_V1_1_PHASE_4B_TOTAL_MODEL_282.joblib`).
- The actual CSV/parquet/joblib files are referenced **in the notebook** but
  have not yet been made available via GitHub or an accessible mounted Drive.

## Corrected development direction

Do NOT automatically download all years and train a second independent feature
pipeline. First recover and compare the existing 1,011-feature contract and
saved challenger against the newly proposed input features.

Next tasks: audit advanced source field completeness; identify uniquely missing
signals (e.g. verified QB availability); validate cutoff timestamps; test
incremental advanced features out of sample and prospectively; preserve the
frozen production model unless a reliable improvement is demonstrated.

The experimental ingestion and feature-scaffold files on this branch are
**provisional only**, not production-approved and not yet run against live CFBD
response schemas. This discovery supersedes the earlier premise that no
historical advanced challenger existed.
