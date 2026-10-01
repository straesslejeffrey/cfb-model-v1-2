from pathlib import Path
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="CFB Model V1.3",
    page_icon="🏈",
    layout="wide",
    initial_sidebar_state="expanded",
)

APP_DIR = Path(__file__).resolve().parent
DATA_PATH = APP_DIR / "v1_3" / "data" / "streamlit_predictions_2026.csv"

@st.cache_data
def load_predictions():
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"V1.3 repaired prediction data not found: {DATA_PATH}")

    df = pd.read_csv(DATA_PATH, low_memory=False)

    required = [
        "gameId", "season", "week", "homeTeam", "awayTeam",
        "repairedHomeMargin", "repairedGameTotal",
        "repairedHomePoints", "repairedAwayPoints", "repairedWinner",
    ]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise RuntimeError("Missing repaired V1.3 columns: " + ", ".join(missing))

    df = df.copy()
    df["teamA"] = df["homeTeam"].astype(str)
    df["teamB"] = df["awayTeam"].astype(str)
    df["projectedTeamAScore"] = pd.to_numeric(df["repairedHomePoints"], errors="coerce")
    df["projectedTeamBScore"] = pd.to_numeric(df["repairedAwayPoints"], errors="coerce")
    df["predictedMarginTeamA"] = pd.to_numeric(df["repairedHomeMargin"], errors="coerce")
    df["predictedTotal"] = pd.to_numeric(df["repairedGameTotal"], errors="coerce")
    df["projectedWinner"] = df["repairedWinner"].astype(str)
    df["projectedWinningMargin"] = df["predictedMarginTeamA"].abs()
    df["displayScore"] = (
        df["teamA"] + " " + df["projectedTeamAScore"].round(1).astype(str)
        + " – " + df["teamB"] + " " + df["projectedTeamBScore"].round(1).astype(str)
    )
    return df

try:
    games = load_predictions()
except Exception as exc:
    st.error("CFB Model V1.3 repaired prediction data could not be loaded.")
    st.exception(exc)
    st.stop()

st.markdown(
    '''
    <style>
    .block-container {padding-top:1.8rem;padding-bottom:3rem;max-width:1450px;}
    .main-title {font-size:2.55rem;font-weight:800;margin-bottom:0rem;}
    .subtitle {font-size:1.05rem;opacity:.70;margin-bottom:1.1rem;}
    .status-box {border:1px solid rgba(128,128,128,.30);border-radius:14px;padding:1rem 1.2rem;margin-bottom:1.25rem;}
    .prediction-card {border:1px solid rgba(128,128,128,.30);border-radius:14px;padding:1.4rem;margin-top:.5rem;margin-bottom:1rem;}
    .prediction-number {font-size:2.25rem;font-weight:800;}
    .small-note {font-size:.86rem;opacity:.72;}
    </style>
    ''',
    unsafe_allow_html=True,
)

st.markdown('<div class="main-title">🏈 CFB Model V1.3 — Repaired</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle">Symmetric college football margin + total prediction engine</div>',
    unsafe_allow_html=True,
)
st.markdown(
    '''
    <div class="status-box">
    <b>Repaired V1.3 candidate:</b> the structural home/away bug from the original
    V1.3 production contract has been removed. This app is separate from V1.2,
    so both models remain independently accessible.
    </div>
    ''',
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("Model Controls")

    seasons = games["season"].dropna().astype(int).sort_values().unique().tolist()
    selected_season = st.selectbox("Season", seasons, index=len(seasons)-1)

    season_games = games[games["season"].astype(int) == selected_season].copy()
    weeks = season_games["week"].dropna().astype(int).sort_values().unique().tolist()
    selected_week = st.selectbox("Week", weeks, index=len(weeks)-1)

    week_games = season_games[season_games["week"].astype(int) == selected_week].copy()

    teams = sorted(
        set(week_games["teamA"].dropna().astype(str))
        | set(week_games["teamB"].dropna().astype(str))
    )
    if not teams:
        st.warning("No teams available for this week.")
        st.stop()

    selected_team = st.selectbox("Team", teams)
    team_games = week_games[
        (week_games["teamA"].astype(str) == selected_team)
        | (week_games["teamB"].astype(str) == selected_team)
    ].copy()

    opponent_options = []
    for _, r in team_games.iterrows():
        opponent_options.append(
            str(r["teamB"]) if str(r["teamA"]) == selected_team else str(r["teamA"])
        )
    opponent_options = sorted(set(opponent_options))
    selected_opponent = st.selectbox("Opponent", opponent_options)

    selected_games = team_games[
        (
            (team_games["teamA"].astype(str) == selected_team)
            & (team_games["teamB"].astype(str) == selected_opponent)
        )
        | (
            (team_games["teamB"].astype(str) == selected_team)
            & (team_games["teamA"].astype(str) == selected_opponent)
        )
    ]
    if len(selected_games) == 0:
        st.error("Selected game not found.")
        st.stop()

    game = selected_games.iloc[0]
    st.divider()
    st.caption("MODEL")
    st.write("CFB Model V1.3 — Repaired")
    st.caption("120 matched HOME/AWAY feature pairs")
    st.success("Structurally repaired")
    if "sourceWeek" in game.index:
        st.caption(f"Source data through Week {game.get('sourceWeek')}")

team_a = str(game["teamA"])
team_b = str(game["teamB"])
team_a_score = float(game["projectedTeamAScore"])
team_b_score = float(game["projectedTeamBScore"])
margin = float(game["predictedMarginTeamA"])
winning_margin = float(game["projectedWinningMargin"])
predicted_total = float(game["predictedTotal"])
winner = str(game["projectedWinner"])

st.subheader(f"Week {selected_week}")
left, middle, right = st.columns([5,2,5], vertical_alignment="center")

with left:
    st.markdown(f"## {team_a}")
    st.caption("HOME")
with middle:
    st.markdown('<div style="text-align:center;font-size:1.35rem;font-weight:800;padding-top:1rem;">VS</div>', unsafe_allow_html=True)
with right:
    st.markdown(f"## {team_b}")
    st.caption("AWAY")

st.markdown('<div class="prediction-card">', unsafe_allow_html=True)
st.markdown("<div class='small-note'>PROJECTED FINAL SCORE</div>", unsafe_allow_html=True)
st.markdown(
    f'<div class="prediction-number">{team_a} {round(team_a_score)} &nbsp;–&nbsp; {team_b} {round(team_b_score)}</div>',
    unsafe_allow_html=True,
)
st.markdown(
    f'''<div class="small-note">
    Repaired V1.3 projected winner: {winner}<br>
    Projected winning margin: {winning_margin:.1f} points<br>
    Projected game total: {predicted_total:.1f}
    </div>''',
    unsafe_allow_html=True,
)
st.markdown("</div>", unsafe_allow_html=True)

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.metric("Projected Winner", winner)
with c2:
    st.metric("Projected Margin", f"{winning_margin:.1f}")
with c3:
    st.metric("Projected Total", f"{predicted_total:.1f}")
with c4:
    st.metric("Matched Feature Pairs", "120")

st.divider()
st.subheader("Score Projection")
s1, s2 = st.columns(2)
with s1:
    st.metric(team_a, f"{team_a_score:.1f}")
with s2:
    st.metric(team_b, f"{team_b_score:.1f}")
st.caption(
    "Scores are reconstructed from the repaired V1.3 predicted total "
    "and symmetric predicted home margin."
)

with st.expander("Model Coverage", expanded=False):
    coverage = {
        "Home prior source games": game.get("homePriorSourceGames"),
        "Away prior source games": game.get("awayPriorSourceGames"),
        "Both teams have prior history": game.get("bothTeamsHaveHistory"),
        "Source week": game.get("sourceWeek"),
        "Target week": game.get("targetWeek"),
    }
    st.dataframe(
        pd.DataFrame({"Field": list(coverage.keys()), "Value": list(coverage.values())}),
        use_container_width=True,
        hide_index=True,
    )

with st.expander("Game Information", expanded=False):
    info = {
        "Game ID": game.get("gameId"),
        "Season": game.get("season"),
        "Week": game.get("week"),
        "Season Type": game.get("seasonType"),
        "Start Date": game.get("startDateParsed"),
        "Home Team": game.get("homeTeam"),
        "Away Team": game.get("awayTeam"),
        "Model Version": "V1.3 Repaired",
    }
    st.dataframe(
        pd.DataFrame({"Field": list(info.keys()), "Value": list(info.values())}),
        use_container_width=True,
        hide_index=True,
    )

with st.expander("V1.3 Repaired Technical Prediction", expanded=False):
    technical = pd.DataFrame({
        "Metric": [
            "Predicted home margin",
            "Predicted total",
            "Projected home score",
            "Projected away score",
            "Projected winning margin",
        ],
        "Value": [
            margin,
            predicted_total,
            team_a_score,
            team_b_score,
            winning_margin,
        ],
    })
    st.dataframe(technical, use_container_width=True, hide_index=True)
    st.caption(
        f"Positive home margin favors {team_a}; negative home margin favors {team_b}."
    )

st.divider()
st.subheader(f"Week {selected_week} V1.3 Repaired Model Board")

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
board = board.rename(columns={
    "teamA": "Home Team",
    "teamB": "Away Team",
    "displayScore": "Projected Score",
    "projectedWinner": "Projected Winner",
    "projectedWinningMargin": "Projected Margin",
    "predictedTotal": "Projected Total",
})
board = board.sort_values("Projected Margin", ascending=False)
st.dataframe(board, use_container_width=True, hide_index=True)

st.divider()
st.caption(
    "CFB Model V1.3 Repaired • 120 matched HOME/AWAY feature pairs • "
    "Symmetric margin + total score engine"
)
st.caption(
    "Repaired V1.3 remains separate from V1.2. "
    "Projected scores are model estimates, not guarantees."
)
