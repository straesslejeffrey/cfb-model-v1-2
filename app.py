
from pathlib import Path
import pandas as pd
import numpy as np
import streamlit as st

# ==================================================================================================
# PAGE CONFIG
# ==================================================================================================

st.set_page_config(
    page_title="CFB Model V1.2",
    layout="wide",
)

st.title("CFB Model V1.2")

st.caption(
    "Frozen V1.2 production predictions with Week 7 betting calibration overlay"
)

# ==================================================================================================
# PATHS
# ==================================================================================================

APP_DIR = Path(__file__).resolve().parent

BASE_DATA_PATH = (
    APP_DIR /
    "v1_2" /
    "data" /
    "streamlit_predictions_2026.csv"
)

OVERLAY_DATA_PATH = (
    APP_DIR /
    "v1_2" /
    "data" /
    "streamlit_betting_overlay_week7.csv"
)

# ==================================================================================================
# LOAD DATA
# ==================================================================================================

@st.cache_data(ttl=60)
def load_base_predictions():

    df = pd.read_csv(
        BASE_DATA_PATH,
        low_memory=False,
    )

    required = [
        "gameId",
        "season",
        "week",
        "teamA",
        "teamB",
        "predictedTotal",
        "predictedMarginTeamA",
        "projectedTeamAScore",
        "projectedTeamBScore",
        "projectedWinner",
        "projectedWinningMargin",
        "displayScore",
    ]

    missing = [
        c
        for c in required
        if c not in df.columns
    ]

    if missing:
        raise RuntimeError(
            f"Base prediction file missing columns: {missing}"
        )

    return df


@st.cache_data(ttl=60)
def load_betting_overlay():

    if not OVERLAY_DATA_PATH.exists():
        return pd.DataFrame()

    return pd.read_csv(
        OVERLAY_DATA_PATH,
        low_memory=False,
    )


base = load_base_predictions()
overlay = load_betting_overlay()

# ==================================================================================================
# SIDEBAR FILTERS
# ==================================================================================================

st.sidebar.header("Filters")

# --------------------------------------------------------------------------------------------------
# SEASON
# --------------------------------------------------------------------------------------------------

season_options = sorted(
    pd.to_numeric(
        base["season"],
        errors="coerce",
    )
    .dropna()
    .astype(int)
    .unique()
    .tolist(),
    reverse=True,
)

selected_season = st.sidebar.selectbox(
    "Season",
    season_options,
    index=0,
)

season_df = base[
    pd.to_numeric(
        base["season"],
        errors="coerce",
    )
    ==
    selected_season
].copy()

# --------------------------------------------------------------------------------------------------
# WEEK
# --------------------------------------------------------------------------------------------------

week_options = sorted(
    pd.to_numeric(
        season_df["week"],
        errors="coerce",
    )
    .dropna()
    .astype(int)
    .unique()
    .tolist(),
    reverse=True,
)

selected_week = st.sidebar.selectbox(
    "Week",
    week_options,
    index=0,
)

week_df = season_df[
    pd.to_numeric(
        season_df["week"],
        errors="coerce",
    )
    ==
    selected_week
].copy()

week_game_count = len(
    week_df
)

# --------------------------------------------------------------------------------------------------
# GAME SELECTOR
# --------------------------------------------------------------------------------------------------

week_df["gameLabel"] = (
    week_df["teamA"].astype(str)
    +
    " vs "
    +
    week_df["teamB"].astype(str)
)

game_options = (
    week_df[
        "gameLabel"
    ]
    .sort_values()
    .tolist()
)

selected_game = st.sidebar.selectbox(
    "Game",
    game_options,
    index=0,
)

selected_df = week_df[
    week_df["gameLabel"]
    ==
    selected_game
].copy()

if len(selected_df) != 1:

    raise RuntimeError(
        f"Expected exactly one selected game, found {len(selected_df)}."
    )

# ==================================================================================================
# MERGE BETTING OVERLAY FOR SELECTED GAME
# ==================================================================================================

if not overlay.empty:

    overlay_week = overlay[
        (
            pd.to_numeric(
                overlay["season"],
                errors="coerce",
            )
            ==
            selected_season
        )
        &
        (
            pd.to_numeric(
                overlay["week"],
                errors="coerce",
            )
            ==
            selected_week
        )
    ].copy()

    if not overlay_week.empty:

        overlay_keep = [
            "gameId",
            "calibratedTeamAScore",
            "calibratedTeamBScore",
            "calibratedTotal",
            "teamAWinProbability",
            "teamBWinProbability",
            "marketHomeSpread",
            "marketTotal",
            "teamAML",
            "teamBML",
            "spreadEdgeA",
            "modelSpreadPlay",
            "calibratedTotalEdge",
            "totalSide",
            "moneylineEdgeSide",
            "moneylineProbabilityEdge",
            "moneylineEVPercent",
            "injuryRiskDisplay",
            "injuryReviewFlag",
            "dataThroughWeek",
        ]

        overlay_keep = [
            c
            for c in overlay_keep
            if c in overlay_week.columns
        ]

        selected_df = selected_df.merge(
            overlay_week[
                overlay_keep
            ],
            on="gameId",
            how="left",
            validate="one_to_one",
        )

# ==================================================================================================
# PAGE HEADER
# ==================================================================================================

st.subheader(
    f"{selected_season} — Week {selected_week}"
)

st.write(
    f"{week_game_count} games available"
)

overlay_available = (
    "calibratedTotal"
    in selected_df.columns
    and
    selected_df["calibratedTotal"]
    .notna()
    .any()
)

if overlay_available:

    st.success(
        "Betting calibration overlay is active for this week."
    )

else:

    st.info(
        "Base V1.2 production predictions are shown. "
        "No betting calibration overlay is available for this matchup."
    )

# ==================================================================================================
# SELECTED GAME
# ==================================================================================================

row = selected_df.iloc[0]

team_a = str(
    row["teamA"]
)

team_b = str(
    row["teamB"]
)

st.markdown("---")

st.markdown(
    f"## {team_a} vs {team_b}"
)

# ==================================================================================================
# BASE V1.2 OUTPUT
# ==================================================================================================

col1, col2, col3, col4 = st.columns(4)

with col1:

    st.metric(
        "V1.2 Projected Score",
        (
            f"{row['projectedTeamAScore']:.1f} - "
            f"{row['projectedTeamBScore']:.1f}"
        ),
    )

    st.caption(
        f"{team_a} vs {team_b}"
    )

with col2:

    margin = float(
        row[
            "predictedMarginTeamA"
        ]
    )

    if margin >= 0:

        margin_text = (
            f"{team_a} by {margin:.1f}"
        )

    else:

        margin_text = (
            f"{team_b} by {abs(margin):.1f}"
        )

    st.markdown("**V1.2 Margin**")

    st.markdown(
        f"### {margin_text}"
    )

with col3:

    st.metric(
        "Raw V1.2 Total",
        f"{row['predictedTotal']:.1f}",
    )

with col4:

    st.metric(
        "Projected Winner",
        str(
            row[
                "projectedWinner"
            ]
        ),
    )

# ==================================================================================================
# BETTING CALIBRATION OVERLAY
# ==================================================================================================

if (
    overlay_available
    and
    pd.notna(
        row.get(
            "calibratedTotal",
            np.nan,
        )
    )
):

    st.markdown(
        "### Betting Calibration Overlay"
    )

    c1, c2, c3, c4 = st.columns(4)

    # ----------------------------------------------------------------------------------------------
    # CALIBRATED TOTAL
    # ----------------------------------------------------------------------------------------------

    with c1:

        st.metric(
            "Calibrated Total",
            f"{row['calibratedTotal']:.1f}",
            delta=(
                f"{row['calibratedTotal'] - row['predictedTotal']:+.1f}"
                " vs raw"
            ),
        )

    # ----------------------------------------------------------------------------------------------
    # WIN PROBABILITY
    # ----------------------------------------------------------------------------------------------

    with c2:

        p_a = float(
            row[
                "teamAWinProbability"
            ]
        )

        p_b = float(
            row[
                "teamBWinProbability"
            ]
        )

        if p_a >= p_b:

            win_team = team_a
            win_prob = p_a

        else:

            win_team = team_b
            win_prob = p_b

        st.markdown("**Model Win Probability**")

        st.markdown(
            f"### {win_team}"
        )

        st.markdown(
            f"## {win_prob:.1%}"
        )

    # ----------------------------------------------------------------------------------------------
    # ATS SIDE
    # ----------------------------------------------------------------------------------------------

    with c3:

        spread_play = row.get(
            "modelSpreadPlay",
            "",
        )

        if (
            pd.isna(spread_play)
            or
            str(spread_play).strip()
            ==
            ""
        ):

            spread_play = (
                "No market line"
            )

        st.metric(
            "Model ATS Side",
            spread_play,
        )

    # ----------------------------------------------------------------------------------------------
    # TOTAL EDGE
    # ----------------------------------------------------------------------------------------------

    with c4:

        total_side = row.get(
            "totalSide",
            "",
        )

        total_edge = row.get(
            "calibratedTotalEdge",
            np.nan,
        )

        if pd.notna(
            total_edge
        ):

            total_text = (
                f"{total_side} "
                f"{abs(float(total_edge)):.1f} pts"
            )

        else:

            total_text = (
                "No market line"
            )

        st.metric(
            "Total Edge",
            total_text,
        )

    # ==================================================================================================
    # CALIBRATED SCORE
    # ==================================================================================================

    if (
        pd.notna(
            row.get(
                "calibratedTeamAScore",
                np.nan,
            )
        )
        and
        pd.notna(
            row.get(
                "calibratedTeamBScore",
                np.nan,
            )
        )
    ):

        st.write(
            "**Calibrated projected score:** "
            f"{team_a} {row['calibratedTeamAScore']:.1f} — "
            f"{team_b} {row['calibratedTeamBScore']:.1f}"
        )

    # ==================================================================================================
    # MARKET COMPARISON
    # ==================================================================================================

    st.markdown(
        "#### Market Comparison"
    )

    market_cols = st.columns(4)

    with market_cols[0]:

        spread = row.get(
            "marketHomeSpread",
            np.nan,
        )

        if pd.notna(spread):

            st.write(
                f"**{team_a} spread:** "
                f"{float(spread):+.1f}"
            )

        else:

            st.write(
                "**Spread:** unavailable"
            )

    with market_cols[1]:

        market_total = row.get(
            "marketTotal",
            np.nan,
        )

        if pd.notna(
            market_total
        ):

            st.write(
                f"**Market total:** "
                f"{float(market_total):.1f}"
            )

        else:

            st.write(
                "**Market total:** unavailable"
            )

    with market_cols[2]:

        team_a_ml = row.get(
            "teamAML",
            np.nan,
        )

        if pd.notna(
            team_a_ml
        ):

            st.write(
                f"**{team_a} ML:** "
                f"{float(team_a_ml):+.0f}"
            )

        else:

            st.write(
                f"**{team_a} ML:** unavailable"
            )

    with market_cols[3]:

        team_b_ml = row.get(
            "teamBML",
            np.nan,
        )

        if pd.notna(
            team_b_ml
        ):

            st.write(
                f"**{team_b} ML:** "
                f"{float(team_b_ml):+.0f}"
            )

        else:

            st.write(
                f"**{team_b} ML:** unavailable"
            )

    # ==================================================================================================
    # MONEYLINE EDGE
    # ==================================================================================================

    ml_side = row.get(
        "moneylineEdgeSide",
        "",
    )

    ml_edge = row.get(
        "moneylineProbabilityEdge",
        np.nan,
    )

    ml_ev = row.get(
        "moneylineEVPercent",
        np.nan,
    )

    if (
        pd.notna(
            ml_edge
        )
        and
        str(
            ml_side
        ).strip()
        !=
        ""
    ):

        st.write(
            f"**Moneyline model edge:** "
            f"{ml_side} | "
            f"{float(ml_edge):+.1%} probability edge | "
            f"{float(ml_ev):+.1f}% model EV"
        )

    # ==================================================================================================
    # INJURY FLAG
    # ==================================================================================================

    injury_flag = row.get(
        "injuryReviewFlag",
        False,
    )

    if isinstance(
        injury_flag,
        str,
    ):

        injury_flag = (
            injury_flag
            .strip()
            .lower()
            in [
                "true",
                "1",
                "yes",
            ]
        )

    if bool(
        injury_flag
    ):

        st.warning(
            "Injury review recommended before using this matchup."
        )

    st.caption(
        "Betting overlay is a model-vs-market comparison tool, "
        "not a guarantee of a winning wager."
    )


# ==================================================================================================
# ADVANCED MATCHUP EVIDENCE (2025 SEASON PRIORS, NOT CURRENT 2026 STATS)
# Separate research view: never change the frozen score / margin calculations.
# ==================================================================================================
ADVANCED_PRIORS_PATH = APP_DIR / "research" / "2026_week7_advanced_preseason_matchups.csv"

@st.cache_data(ttl=60)
def load_advanced_priors():
    if not ADVANCED_PRIORS_PATH.exists():
        return pd.DataFrame()
    return pd.read_csv(ADVANCED_PRIORS_PATH, low_memory=False)

with st.expander("Advanced matchup research — 2025 season priors (not part of score prediction)", expanded=False):
    st.caption(
        "These are 2025 season-average offensive/defensive statistics attached to 2026 "
        "games as preseason context. They are NOT Week 7 live form, and the V1.2 predicted "
        "scores above do not incorporate them."
    )
    prior_data = load_advanced_priors()
    prior_row = prior_data[
        (pd.to_numeric(prior_data.get("season", pd.Series(dtype=float)), errors="coerce") == selected_season)
        & (pd.to_numeric(prior_data.get("week", pd.Series(dtype=float)), errors="coerce") == selected_week)
        & (prior_data.get("teamA", pd.Series(dtype=str)) == team_a)
        & (prior_data.get("teamB", pd.Series(dtype=str)) == team_b)
    ] if not prior_data.empty else pd.DataFrame()

    if prior_row.empty:
        st.info("No saved advanced preseason data for this matchup.")
    else:
        p = prior_row.iloc[0]
        available_a = int(p.get("teamAAdvancedPriorAvailable", 0)) == 1
        available_b = int(p.get("teamBAdvancedPriorAvailable", 0)) == 1
        if not (available_a and available_b):
            missing_teams = [name for name, ok in [(team_a, available_a), (team_b, available_b)] if not ok]
            st.warning("Historical advanced statistics unavailable for: " + ", ".join(missing_teams))
        else:
            matchup_pairs = [
                ("Overall PPA", "offPPA", "defPPAAllowed"),
                ("Rushing success rate", "rushSuccessRate", "defRushSuccessRateAllowed"),
                ("Passing success rate", "passSuccessRate", "defPassSuccessRateAllowed"),
                ("Standard-down PPA", "standardDownPPA", None),
                ("Passing-down PPA", "passingDownPPA", None),
                ("Rushing PPA", "rushPPA", "defRushPPAAllowed"),
                ("Passing PPA", "passPPA", "defPassPPAAllowed"),
                ("Offensive line yards", "lineYards", "defLineYardsAllowed"),
                ("Havoc", "havocAllowed", "defHavocCreated"),
            ]
            records = []
            for label, offense, defense in matchup_pairs:
                a = pd.to_numeric(p.get("teamA_" + offense), errors="coerce")
                b = pd.to_numeric(p.get("teamB_" + offense), errors="coerce")
                opp_b = pd.to_numeric(p.get("teamB_" + defense), errors="coerce") if defense else np.nan
                opp_a = pd.to_numeric(p.get("teamA_" + defense), errors="coerce") if defense else np.nan
                records.append({
                    "Metric": label,
                    f"{team_a} 2025 offense": a,
                    f"{team_b} 2025 offense": b,
                    f"{team_a} vs {team_b} defense": a - opp_b if defense else np.nan,
                    f"{team_b} vs {team_a} defense": b - opp_a if defense else np.nan,
                })
            st.dataframe(
                pd.DataFrame(records).round(3),
                hide_index=True,
                use_container_width=True,
            )
            st.caption(
                "The offense-minus-defense columns are raw descriptive differences, "
                "NOT calibrated matchup advantages or point adjustments. "
                "Their direction and importance depend on each statistic's definition."
            )

# --------------------------------------------------------------------------
# V1.2 Advanced — current-season research evidence (not a trained score)
# --------------------------------------------------------------------------
CURRENT_ADVANCED_PATH = APP_DIR / "v1_2" / "data" / "advanced_2026_week7_research_inputs.csv"
@st.cache_data(ttl=60)
def load_current_advanced():
    if not CURRENT_ADVANCED_PATH.exists():
        return pd.DataFrame()
    return pd.read_csv(CURRENT_ADVANCED_PATH, low_memory=False)

with st.expander("V1.2 Advanced | Verified 2026 team trends (research)", expanded=False):
    st.caption("Current 2026 prior games: last 3 and last 5 completed games. "
               "These metrics are NOT yet used to modify V1.2 score predictions.")
    advanced = load_current_advanced()
    selected = advanced.loc[
        (advanced["gameId"].astype(str) == str(row["gameId"])) &
        (advanced["season"] == selected_season) &
        (advanced["week"] == selected_week)
    ] if not advanced.empty else pd.DataFrame()
    if len(selected) != 1:
        st.info("Current-season advanced statistics unavailable for this game.")
    else:
        ar = selected.iloc[0]
        metrics = [
            ("Points per drive", "offPointsPerDrive"),
            ("PPA per play", "offPPAperPlay"),
            ("Success rate", "offSuccessRate"),
            ("Scoring opportunity rate", "offScoringOpportunityRate"),
            ("Explosive drive rate", "offExplosiveDriveRate"),
            ("Defensive PPA allowed", "defPPAperPlayAllowed"),
            ("Defensive success allowed", "defSuccessRateAllowed"),
        ]
        view = []
        for label, metric in metrics:
            rec = {"Measure": label}
            for side, team in [("teamA",team_a),("teamB",team_b)]:
                rec[f"{team} L3"] = ar.get(f"{side}_2026_{metric}_last3")
                rec[f"{team} L5"] = ar.get(f"{side}_2026_{metric}_last5")
            view.append(rec)
        st.dataframe(pd.DataFrame(view).round(3), hide_index=True, use_container_width=True)
        st.caption("Research view only: archived V1.2/V1.3 prediction outputs remain unchanged.")

# 2025-trained research-only model output. Deliberately not a default score.
with st.expander("Experimental V1.2 Advanced total (unvalidated research preview)", expanded=False):
    st.warning("2025-only training. NOT cross-season validated or approved for betting. "
               "Original V1.2 / V1.3 predictions remain the production results.")
    from research_2025_fitted_totals import experimental_total
    research_frame = load_current_advanced()
    research_frame = research_frame.loc[
        (research_frame["gameId"].astype(str) == str(row["gameId"])) &
        (research_frame["season"] == selected_season) &
        (research_frame["week"] == selected_week)
    ] if not research_frame.empty else pd.DataFrame()
    if len(research_frame)==1:
        try:
            candidate_total = float(experimental_total(research_frame)[0])
            st.metric("Experimental total", f"{candidate_total:.1f}",
                      delta=f"{candidate_total-float(row['predictedTotal']):+.1f} vs frozen V1.2")
            st.caption("Total-score experiment only; no separately calibrated spread, winner, "
                       "ATS edge, moneyline, or validated win probability.")
        except (ValueError, KeyError, TypeError) as exc:
            st.error(f"Advanced research model unavailable: {exc}")
    else:
        st.info("No advanced research inputs available for this game.")
