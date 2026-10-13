# Opponent-specific margin experiment — 2025 research only

Evaluated 185 untouched games from Weeks 12–14. Fit Weeks 1–8, selected regularization using Weeks 9–11. Source is the archived true-V1.2 2025 backtest.

| Model | Holdout margin MAE | Winner accuracy |
|---|---:|---:|
| Frozen V1.2 | 12.916132776 | 73.5135% |
| Previous 57-feature candidate | 12.895704159 | 73.5135% |
| Matched offense-opponent-defense challenger (43 features) | 12.893618756 | 73.5135% |
| Extended matched interactions (99 features) | 12.894657947 | 73.5135% |

The challenger constructed pregame offensive-vs-opponent-defense matched advantages using home/away rolling last-3 and last-5 efficiencies, including PPA, success rate, explosiveness, drive scoring and turnovers. It then used orientation-invariant sums, absolute differences and products, with a signed residual relative to the baseline V1.2 margin. Ridge regularization was selected on Weeks 9–11 (alpha 100000).

**Decision: reject promotion.** Improvement of 0.022514 margin points/game is below the existing 0.10 gate, and winner accuracy is unchanged. This is only one held-out portion of one season and cannot demonstrate cross-season superiority. The experimental Streamlit views and original V1.2/V1.3 production scores must remain separate.
