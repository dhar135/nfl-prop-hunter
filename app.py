import streamlit as st
import nflreadpy as nfl
import polars as pl
import datetime

# Page Config (Always first)
st.set_page_config(page_title="NFL Prop Hunter", page_icon="🏈")

# --- CONSTANTS ---
CURRENT_YEAR = datetime.datetime.now().year
SEASON_YEAR = CURRENT_YEAR if datetime.datetime.now().month > 8 else CURRENT_YEAR - 1

GENERAL_PLAYER_STATS_WHITELIST = ["season", "week", "opponent_team"]
RELEVANT_POSITIONS = ["QB"]
QB_STATS_WHITELIST = ["passing_yards", "passing_tds", "completions"]

# --- DATA LAYER ---
@st.cache_data(ttl=3600 * 6)  # Cache data for 6 hours
def load_player_stats() -> pl.DataFrame:
    """
    Fetches player stats for current and previous season
    """
    try:
        # Explicitly fetch only the season we care about to save memory/bandwidth
        season_data = nfl.load_player_stats(seasons=[SEASON_YEAR, SEASON_YEAR - 1])

        # Filter relevant positions
        return season_data.filter(pl.col("position").is_in(RELEVANT_POSITIONS))
    except Exception as e:
        st.error(f"Failed to fetch NFL data: {e}")
        return pl.DataFrame()

def get_player_props() -> list:
    """
    Docstring for get_player_props
    """
    raise NotImplementedError

def get_hit_rate(prop_value_input: float, position_prop: str ,player_stats: pl.DataFrame, number_of_prev_games: int) -> pl.DataFrame:
    """
    Given: Prop value input and player stats
    
    Returns: Number of games hit over the inputed prop
    """

    # Get 5 last games for the given prop
    last_n_games = player_stats.select([position_prop, "week"]).tail(number_of_prev_games)

    # Compare the player stat to the prop value
    # 1. (pl.col(position_prop) > prop_value_input) creates a list of Booleans (True/False)
    # 2. .sum() counts the "True" values
    # 3. .item() extracts the single integer result from the DataFrame

    return last_n_games

# --- UI LAYER ---
def main():
    st.title("🏈 NFL Prop Hunter")

    # 1. Load Data
    with st.spinner("Loading NFL Data..."):
        df = load_player_stats()

    if df.is_empty():
        st.warning("No data found. Please check your internet connection or season settings.")
        return

    # 2. Sidebar / Controls
    # Get unique players efficiently
    unique_players = df.select("player_display_name").unique().sort("player_display_name")["player_display_name"].to_list()

    # Create the selectbox for players
    selected_player = st.selectbox(
        "Select Player", 
        options=unique_players,
        index=0
    )

    # Filter using Polars (Very fast)
    player_stats = df.filter(
        (pl.col("player_display_name") == selected_player)
    ).sort(pl.col("season"))

    # TODO: Get props for selected player's postion (will add when I implement other postions)
    # player_props: list = get_player_props()

    # Create the select box for props
    posititon_prop = st.selectbox(
        "Select Player Prop",
        options=QB_STATS_WHITELIST
    )

    # Create number input for props
    prop_value_input = st.number_input(
        "Input Value",
        step=.5
    )

    last_n_games = st.number_input(
        "Last N Games",
        step=1
    )

    # Get hit rate for last 5 games after getting value input
    hit_rate = get_hit_rate(prop_value_input, posititon_prop, player_stats, last_n_games)

    # Define colors (Hex codes)
    COLOR_OVER = "#4CAF50"  # Green
    COLOR_UNDER = "#070707" # Red

    # Create a column with hex codes based on the condition
    hit_rate = hit_rate.with_columns(
        pl.when(pl.col(posititon_prop) > prop_value_input)
        .then(pl.lit("#2ca02c")) # Green
        .otherwise(pl.lit("#d62728")) # Red
        .alias("color_condition")
    )

    # 3. Display Results
    st.divider()
    st.subheader(f"📊 Stats: {selected_player}")
    st.write(f"Hit Rate for last {last_n_games} games")

    # Use the dynamic variable 'posititon_prop' for y, and the new color column
    st.bar_chart(
        hit_rate, 
        x="week", 
        y=posititon_prop, 
        color="color_condition"
    )


    if not player_stats.is_empty():
        st.dataframe(player_stats.select(GENERAL_PLAYER_STATS_WHITELIST + [posititon_prop]).sort(pl.col("season"), descending=True))
    else:
        st.info(f"No active roster data found for {selected_player}")

if __name__ == "__main__":
    main()