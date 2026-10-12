
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
# LOADERS
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
        c for c in required
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
# SIDEBAR
# ==================================================================================================

st.sidebar.header("Filters")

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

# ==================================================================================================
# MERGE OVERLAY
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
            c for c in overlay_keep
            if c in overlay_week.columns
        ]

        week_df = week_df.merge(
            overlay_week[
                overlay_keep
            ],
            on="gameId",
            how="left",
            validate="one_to_one",
        )

# ==================================================================================================
# HEADER
# ==================================================================================================

st.subheader(
    f"{selected_season} — Week {selected_week}"
)

st.write(
    f"{len(week_df)} games"
)

overlay_available = (
    "calibratedTotal"
    in week_df.columns
    and
    week_df["calibratedTotal"]
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
        "No betting calibration overlay is available for this week."
    )

# ==================================================================================================
# GAME CARDS
# ==================================================================================================

for _, row in week_df.iterrows():

    team_a = str(
        row["teamA"]
    )

    team_b = str(
        row["teamB"]
    )

    st.markdown("---")

    st.markdown(
        f"### {team_a} vs {team_b}"
    )

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

        st.metric(
            "V1.2 Margin",
            margin_text,
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

    # ----------------------------------------------------------------------------------------------
    # BETTING OVERLAY
    # ----------------------------------------------------------------------------------------------

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
            "#### Betting Calibration Overlay"
        )

        c1, c2, c3, c4 = st.columns(4)

        with c1:

            st.metric(
                "Calibrated Total",
                f"{row['calibratedTotal']:.1f}",
                delta=(
                    f"{row['calibratedTotal'] - row['predictedTotal']:+.1f}"
                    " vs raw"
                ),
            )

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

            st.metric(
                "Model Win Probability",
                f"{win_team} {win_prob:.1%}",
            )

        with c3:

            spread_play = row.get(
                "modelSpreadPlay",
                "",
            )

            if (
                pd.isna(spread_play)
                or
                spread_play == ""
            ):
                spread_play = "No market line"

            st.metric(
                "Model ATS Side",
                spread_play,
            )

        with c4:

            total_side = row.get(
                "totalSide",
                "",
            )

            total_edge = row.get(
                "calibratedTotalEdge",
                np.nan,
            )

            if pd.notna(total_edge):

                total_text = (
                    f"{total_side} "
                    f"{abs(float(total_edge)):.1f} pts"
                )

            else:
                total_text = "No market line"

            st.metric(
                "Total Edge",
                total_text,
            )

        # ------------------------------------------------------------------------------------------
        # MARKET
        # ------------------------------------------------------------------------------------------

        st.markdown(
            "##### Market Comparison"
        )

        market_cols = st.columns(4)

        with market_cols[0]:

            spread = row.get(
                "marketHomeSpread",
                np.nan,
            )

            if pd.notna(spread):
                st.write(
                    f"**{team_a} spread:** {float(spread):+.1f}"
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

            if pd.notna(market_total):
                st.write(
                    f"**Market total:** {float(market_total):.1f}"
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

            if pd.notna(team_a_ml):
                st.write(
                    f"**{team_a} ML:** {float(team_a_ml):+.0f}"
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

            if pd.notna(team_b_ml):
                st.write(
                    f"**{team_b} ML:** {float(team_b_ml):+.0f}"
                )
            else:
                st.write(
                    f"**{team_b} ML:** unavailable"
                )

        # ------------------------------------------------------------------------------------------
        # MONEYLINE EDGE
        # ------------------------------------------------------------------------------------------

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
            pd.notna(ml_edge)
            and
            ml_side
        ):

            st.write(
                f"**Moneyline model edge:** "
                f"{ml_side} | "
                f"{float(ml_edge):+.1%} probability edge | "
                f"{float(ml_ev):+.1f}% model EV"
            )

        # ------------------------------------------------------------------------------------------
        # CONTEXT WARNING
        # ------------------------------------------------------------------------------------------

        injury_flag = bool(
            row.get(
                "injuryReviewFlag",
                False,
            )
        )

        if injury_flag:

            st.warning(
                "Injury review recommended before using this matchup."
            )

        st.caption(
            "Betting overlay is a model-vs-market comparison tool, "
            "not a guarantee of a winning wager."
        )
