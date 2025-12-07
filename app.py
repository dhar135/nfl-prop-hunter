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
QB_STATS_WHITELIST = ["passing_yards"]

# --- DATA LAYER ---
@st.cache_data(ttl=3600 * 6)  # Cache data for 6 hours
def load_player_stats(season: int) -> pl.DataFrame:
    """
    Fetches player stats
    """
    try:
        # Explicitly fetch only the season we care about to save memory/bandwidth
        season_data = nfl.load_player_stats(seasons=[season, season - 1])

        # Filter relevant positions
        return season_data.filter(pl.col("position").is_in(RELEVANT_POSITIONS))
    except Exception as e:
        st.error(f"Failed to fetch NFL data: {e}")
        return pl.DataFrame()

# --- UI LAYER ---
def main():
    st.title("🏈 NFL Prop Hunter")

    # 1. Load Data
    with st.spinner("Loading NFL Data..."):
        df = load_player_stats(SEASON_YEAR)

    if df.is_empty():
        st.warning("No data found. Please check your internet connection or season settings.")
        return

    # 2. Sidebar / Controls
    # Get unique players efficiently
    unique_players = df.select("player_display_name").unique().sort("player_display_name")["player_display_name"].to_list()

    # Create the selectbox
    selected_player = st.selectbox(
        "Select Player", 
        options=unique_players,
        index=0
    )
    
    # Filter using Polars (Very fast)
    player_stats = df.filter(
        (pl.col("player_display_name") == selected_player)
    )

    # 4. Display Results
    st.divider()
    st.subheader(f"📊 Stats: {selected_player}")
    st.caption(f"Season: {SEASON_YEAR}")

    if not player_stats.is_empty():
        st.dataframe(player_stats.select(GENERAL_PLAYER_STATS_WHITELIST + QB_STATS_WHITELIST))
    else:
        st.info(f"No active roster data found for {selected_player}")

if __name__ == "__main__":
    main()