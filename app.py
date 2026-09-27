
from pathlib import Path
import json
import pandas as pd
import streamlit as st


# ============================================================
# PAGE
# ============================================================

st.set_page_config(
    page_title="CFB Model V1.2",
    page_icon="🏈",
    layout="wide",
    initial_sidebar_state="expanded",
)

APP_DIR = Path(__file__).resolve().parent

DATA_PATH = (
    APP_DIR /
    "v1_2" /
    "data" /
    "streamlit_predictions_2026.csv"
)

MANIFEST_PATH = (
    APP_DIR /
    "team_logo_manifest.json"
)


# ============================================================
# LOGOS
# ============================================================

@st.cache_data
def load_logo_manifest():

    if not MANIFEST_PATH.exists():
        return {}

    try:

        with open(
            MANIFEST_PATH,
            "r",
            encoding="utf-8",
        ) as f:

            return json.load(f)

    except Exception:

        return {}


CFB_LOGO_MANIFEST = load_logo_manifest()


def team_logo(team, style="Retro"):

    info = CFB_LOGO_MANIFEST.get(
        str(team),
        {},
    )

    retro = info.get("retro")
    modern = info.get("modern")

    if str(style).lower() == "retro":
        candidates = [retro, modern]
    else:
        candidates = [modern, retro]

    for candidate in candidates:

        if not candidate:
            continue

        path = Path(candidate)

        # Support both absolute and app-relative assets.
        if not path.is_absolute():
            path = APP_DIR / path

        if path.exists():
            return str(path)

    return None


# ============================================================
# DATA
# ============================================================

@st.cache_data
def load_predictions():

    if not DATA_PATH.exists():

        raise FileNotFoundError(
            f"V1.2 production data not found: {DATA_PATH}"
        )

    df = pd.read_csv(
        DATA_PATH,
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
            "Missing V1.2 compatibility columns: "
            + ", ".join(missing)
        )

    return df


try:

    games = load_predictions()

except Exception as exc:

    st.error(
        "CFB Model V1.2 production data "
        "could not be loaded."
    )

    st.exception(exc)
    st.stop()


# ============================================================
# STYLING
# ============================================================

st.markdown(
    """
    <style>

    .block-container {
        padding-top: 1.8rem;
        padding-bottom: 3rem;
        max-width: 1450px;
    }

    .main-title {
        font-size: 2.55rem;
        font-weight: 800;
        margin-bottom: 0rem;
    }

    .subtitle {
        font-size: 1.05rem;
        opacity: 0.70;
        margin-bottom: 1.7rem;
    }

    .prediction-card {
        border: 1px solid rgba(128,128,128,0.30);
        border-radius: 14px;
        padding: 1.4rem;
        margin-top: 0.5rem;
        margin-bottom: 1rem;
    }

    .prediction-number {
        font-size: 2.25rem;
        font-weight: 800;
    }

    .small-note {
        font-size: 0.86rem;
        opacity: 0.70;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# HEADER
# ============================================================

st.markdown(
    '<div class="main-title">🏈 CFB Model V1.2</div>',
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="subtitle">
    282-feature college football score + margin prediction engine
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.header("Model Controls")

    logo_style = st.radio(
        "Logo Style",
        ["Retro", "Modern"],
        index=0,
    )

    seasons = (
        games["season"]
        .dropna()
        .astype(int)
        .sort_values()
        .unique()
        .tolist()
    )

    selected_season = st.selectbox(
        "Season",
        seasons,
        index=len(seasons) - 1,
    )

    season_games = games[
        games["season"].astype(int)
        ==
        selected_season
    ].copy()

    weeks = (
        season_games["week"]
        .dropna()
        .astype(int)
        .sort_values()
        .unique()
        .tolist()
    )

    selected_week = st.selectbox(
        "Week",
        weeks,
        index=0,
    )

    week_games = season_games[
        season_games["week"].astype(int)
        ==
        selected_week
    ].copy()

    teams = sorted(
        set(
            week_games["teamA"]
            .dropna()
            .astype(str)
        )
        |
        set(
            week_games["teamB"]
            .dropna()
            .astype(str)
        )
    )

    if not teams:

        st.warning(
            "No teams available for this week."
        )

        st.stop()

    selected_team = st.selectbox(
        "Team",
        teams,
    )

    team_games = week_games[
        (
            week_games["teamA"].astype(str)
            ==
            selected_team
        )
        |
        (
            week_games["teamB"].astype(str)
            ==
            selected_team
        )
    ].copy()

    opponent_options = []

    for _, r in team_games.iterrows():

        if str(r["teamA"]) == selected_team:
            opponent_options.append(str(r["teamB"]))
        else:
            opponent_options.append(str(r["teamA"]))

    opponent_options = sorted(
        set(opponent_options)
    )

    selected_opponent = st.selectbox(
        "Opponent",
        opponent_options,
    )

    selected_games = team_games[
        (
            (
                team_games["teamA"].astype(str)
                ==
                selected_team
            )
            &
            (
                team_games["teamB"].astype(str)
                ==
                selected_opponent
            )
        )
        |
        (
            (
                team_games["teamB"].astype(str)
                ==
                selected_team
            )
            &
            (
                team_games["teamA"].astype(str)
                ==
                selected_opponent
            )
        )
    ]

    if len(selected_games) == 0:

        st.error("Selected game not found.")
        st.stop()

    game = selected_games.iloc[0]

    st.divider()

    st.caption("MODEL")
    st.write("CFB Model V1.2")
    st.caption("282 frozen features")

    # ============================================================
    # V1.2 PREDICTION SUPPORT GUARD
    # ============================================================
    #
    # Games outside the frozen V1.1-supported team universe
    # intentionally have no model prediction. Do not convert their
    # missing prediction fields to floats or create synthetic values.

    if "hasFrozenV11Prediction" not in game.index:
        st.error(
            "Prediction-support metadata is missing for this matchup."
        )
        st.stop()

    has_prediction = bool(
        game["hasFrozenV11Prediction"]
    )

    if not has_prediction:

        st.warning(
            "This matchup is on the Week 5 board, but it is outside "
            "the frozen V1.1-supported team universe."
        )

        st.info(
            "V1.2 intentionally does not generate a prediction for "
            "this game. No projected score, winner, margin, or total "
            "is available."
        )

        if "predictionMode" in game.index:
            st.caption(
                f"Prediction mode: "
                f"{game['predictionMode']}"
            )

        st.caption(
            "Production status: UNSUPPORTED"
        )

        st.stop()

    st.success("Production ready")

    if "predictionMode" in game.index:

        st.caption(
            f"Prediction mode: "
            f"{game['predictionMode']}"
        )


# ============================================================
# GAME VALUES
# ============================================================

team_a = str(game["teamA"])
team_b = str(game["teamB"])

team_a_score = float(
    game["projectedTeamAScore"]
)

team_b_score = float(
    game["projectedTeamBScore"]
)

margin = float(
    game["predictedMarginTeamA"]
)

winning_margin = float(
    game["projectedWinningMargin"]
)

predicted_total = float(
    game["predictedTotal"]
)

winner = str(
    game["projectedWinner"]
)


# ============================================================
# MATCHUP HEADER
# ============================================================

st.subheader(
    f"Week {selected_week}"
)

left, middle, right = st.columns(
    [5, 2, 5],
    vertical_alignment="center",
)

with left:

    logo = team_logo(
        team_a,
        logo_style,
    )

    if logo:
        st.image(logo, width=125)

    st.markdown(f"## {team_a}")


with middle:

    st.markdown(
        """
        <div style="
            text-align:center;
            font-size:1.35rem;
            font-weight:800;
            padding-top:1rem;
        ">
        VS
        </div>
        """,
        unsafe_allow_html=True,
    )


with right:

    logo = team_logo(
        team_b,
        logo_style,
    )

    if logo:
        st.image(logo, width=125)

    st.markdown(f"## {team_b}")


# ============================================================
# PROJECTED FINAL SCORE
# ============================================================

st.markdown(
    '<div class="prediction-card">',
    unsafe_allow_html=True,
)

st.markdown(
    "<div class='small-note'>PROJECTED FINAL SCORE</div>",
    unsafe_allow_html=True,
)

st.markdown(
    f"""
    <div class="prediction-number">
        {team_a} {round(team_a_score)}
        &nbsp;–&nbsp;
        {team_b} {round(team_b_score)}
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    f"""
    <div class="small-note">
        V1.2 projected winner: {winner}<br>
        Projected winning margin: {winning_margin:.1f} points<br>
        Projected game total: {predicted_total:.1f}
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    "</div>",
    unsafe_allow_html=True,
)


# ============================================================
# METRICS
# ============================================================

c1, c2, c3, c4 = st.columns(4)

with c1:

    st.metric(
        "Projected Winner",
        winner,
    )

    winner_logo = team_logo(
        winner,
        logo_style,
    )

    if winner_logo:
        st.image(
            winner_logo,
            width=55,
        )


with c2:

    st.metric(
        "Projected Margin",
        f"{winning_margin:.1f}",
    )


with c3:

    st.metric(
        "Projected Total",
        f"{predicted_total:.1f}",
    )


with c4:

    st.metric(
        "Model Features",
        "282",
    )


# ============================================================
# SCORE BREAKDOWN
# ============================================================

st.divider()
st.subheader("Score Projection")

s1, s2 = st.columns(2)

with s1:

    st.metric(
        team_a,
        f"{team_a_score:.1f}",
    )

with s2:

    st.metric(
        team_b,
        f"{team_b_score:.1f}",
    )

st.caption(
    "Team scores are reconstructed from the frozen "
    "V1.2 predicted total and predicted margin."
)


# ============================================================
# GAME INFORMATION
# ============================================================

with st.expander(
    "Game Information",
    expanded=False,
):

    info = {
        "Game ID":
            game["gameId"],

        "Season":
            game.get("season"),

        "Week":
            game.get("week"),

        "Season Type":
            game.get("seasonType"),

        "Start Date":
            game.get("startDate"),

        "Home Team":
            game.get("homeTeam"),

        "Away Team":
            game.get("awayTeam"),

        "Neutral Site":
            game.get("neutralSite"),

        "Home Conference":
            game.get("homeConference"),

        "Away Conference":
            game.get("awayConference"),

        "Prediction Mode":
            game.get("predictionMode"),
    }

    info_df = pd.DataFrame(
        {
            "Field": list(info.keys()),
            "Value": list(info.values()),
        }
    )

    st.dataframe(
        info_df,
        use_container_width=True,
        hide_index=True,
    )


# ============================================================
# TECHNICAL OUTPUT
# ============================================================

with st.expander(
    "V1.2 Technical Prediction",
    expanded=False,
):

    technical = pd.DataFrame(
        {
            "Metric": [
                "Predicted margin from Team A perspective",
                "Predicted total",
                "Projected Team A score",
                "Projected Team B score",
                "Projected winning margin",
            ],
            "Value": [
                margin,
                predicted_total,
                team_a_score,
                team_b_score,
                winning_margin,
            ],
        }
    )

    st.dataframe(
        technical,
        use_container_width=True,
        hide_index=True,
    )

    st.caption(
        "Team A for this stored game is "
        f"{team_a}. Positive margin favors {team_a}; "
        f"negative margin favors {team_b}."
    )


# ============================================================
# WEEKLY BOARD
# ============================================================

st.divider()

st.subheader(
    f"Week {selected_week} V1.2 Model Board"
)

board = week_games[
    [
        "gameId",
        "teamA",
        "teamB",
        "displayScore",
        "projectedWinner",
        "projectedWinningMargin",
        "predictedTotal",
    ]
].copy()

board = board.rename(
    columns={
        "teamA": "Team A",
        "teamB": "Team B",
        "displayScore": "Projected Score",
        "projectedWinner": "Projected Winner",
        "projectedWinningMargin": "Projected Margin",
        "predictedTotal": "Projected Total",
    }
)

board = board.sort_values(
    "Projected Margin",
    ascending=False,
)

st.dataframe(
    board,
    use_container_width=True,
    hide_index=True,
)


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "CFB Model V1.2 • "
    "282-feature frozen prediction contract • "
    "Margin + total score engine"
)

st.caption(
    "Projected scores are model estimates, not guarantees."
)
