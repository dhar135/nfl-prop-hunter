import streamlit as st
import nflreadpy as nfl
import polars as pl
import datetime

# Page Config (Always first)
st.set_page_config(page_title="NFL Prop Hunter", page_icon="🏈")

# --- CONSTANTS ---
CURRENT_YEAR = datetime.datetime.now().year
# Adjust logic if running in Jan/Feb to get previous year's season
SEASON_YEAR = CURRENT_YEAR if datetime.datetime.now().month > 8 else CURRENT_YEAR - 1

# --- DATA LAYER ---
@st.cache_data(ttl=3600)  # Cache data for 1 hour
def load_roster_data(season: int) -> pl.DataFrame:
    """
    Fetches weekly roster data for a specific season and converts to Polars.
    """
    try:
        # Explicitly fetch only the season we care about to save memory/bandwidth
        df_pandas = nfl.load_player_stats(seasons=[season])
        
        # Convert to Polars for performance
        return df_pandas
    except Exception as e:
        st.error(f"Failed to fetch NFL data: {e}")
        return pl.DataFrame()

def get_current_nfl_week() -> int:
    """Safely retrieves the current NFL week."""
    try:
        return nfl.get_current_week()
    except Exception:
        return 1 # Fallback default

# --- UI LAYER ---
def main():
    st.title("🏈 NFL Prop Hunter")

    # 1. Load Data
    with st.spinner(f"Loading NFL Data for {SEASON_YEAR}..."):
        df = load_roster_data(SEASON_YEAR)

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

    # 3. Filtering Logic
    current_week = get_current_nfl_week()

    current_week = 12
    
    # Filter using Polars (Very fast)
    # Note: We filter for the specific player AND the current week
    player_stats = df.filter(
        (pl.col("player_display_name") == selected_player) & 
        (pl.col("week") == current_week)
    )

    # 4. Display Results
    st.divider()
    st.subheader(f"📊 Stats: {selected_player}")
    st.caption(f"Season: {SEASON_YEAR} | Week: {current_week}")

    if not player_stats.is_empty():
        # Clean up the view (exclude messy ID columns if desired)
        st.dataframe(player_stats)
    else:
        st.info(f"No active roster data found for {selected_player} in Week {current_week}.")

if __name__ == "__main__":
    main()