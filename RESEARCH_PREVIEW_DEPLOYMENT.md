# V1.2 Advanced — Streamlit research-preview release

## Release identity
- Repository: `straesslejeffrey/cfb-model-v1-2`
- Branch: `feature/advanced-fbs-features`
- Entry point: `app.py`
- Suggested separate Streamlit app name: `cfb-v12-advanced-research`
- **Do not change the existing production app's GitHub branch or redeploy its main branch.**

## Publish as a new Streamlit Community Cloud app
1. Sign into [Streamlit Community Cloud](https://share.streamlit.io/).
2. Select **Create app → Deploy a public app from GitHub**.
3. Select repository `straesslejeffrey/cfb-model-v1-2`.
4. Select branch `feature/advanced-fbs-features`.
5. Set main file path to `app.py`.
6. Choose a separate app URL/name, such as `cfb-v12-advanced-research`.
7. Deploy the **new app**, leaving existing V1.2 and V1.3 applications untouched.
8. In the sidebar, select **V1.2 Advanced (research preview)**, choose Season 2026 and Week 7, and open its experimental totals.

## What this release contains
- All 58 Week 7 matchups with 2026 rolling advanced statistics.
- A research-only experimental 2025-trained total-score adjustment.
- Original V1.2 spreads, winners, and scoring output preserved; V1.3 is not embedded as a separately selectable model in this branch.
- No verified 2018–2024 frozen V1.2 baseline; cross-season superiority not proven.
- Do not label advanced totals as production-certified or use as a betting recommendation.

## Promotion restrictions
- Holdout total-score error improved by about 0.20 points on 185 late-2025 games, but its bootstrap interval includes zero, and Week 14 got worse.
- Advanced margin experiments did not meaningfully improve MAE or winner accuracy.
- Deployment as a clearly labeled **research preview** is acceptable after smoke testing; production replacement remains blocked.

## Audit
Use GitHub Actions on the feature branch to verify tests before and after release.
