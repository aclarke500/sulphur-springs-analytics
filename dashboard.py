import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Set page config for better mobile experience
st.set_page_config(
    page_title="Race Results Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Sidebar: Race selection
race_file = st.sidebar.selectbox(
    "Select race:",
    ["20k_race_results.csv", "10k_race_results.csv"],
    format_func=lambda x: "20k Race" if "20k" in x else "10k Race"
)

# Define column mappings for each race
column_maps = {
    "20k_race_results.csv": {
        'place': 'Race Place',
        'bib': 'Bib',
        'name': 'Full Name',
        'gender': 'Gender',
        'age': 'Age',
        'city': 'City',
        'lap_count': 'Lap Count',
        'gun_time': 'Gun Elapsed Time',
        'chip_time': 'Chip Elapsed Time',
        'pace': 'Overall Pace',
    },
    "10k_race_results.csv": {
        'place': 'Race Place',
        'bib': 'Bib',
        'name': 'Full Name',
        'gender': 'Gender',
        'age': 'Age',
        'city': 'City',
        'lap_count': 'Lap Count',
        'gun_time': 'Gun Elapsed Time',
        'chip_time': 'Chip Elapsed Time',
        'pace': 'Overall Pace',
    }
}

# Load the data
@st.cache_data
def load_data(race_file):
    df = pd.read_csv(race_file, dtype=str)
    col_map = column_maps[race_file]
    # Standardize columns for internal use
    df_std = pd.DataFrame()
    for key, col in col_map.items():
        if col in df.columns:
            df_std[key] = df[col]
        else:
            df_std[key] = None
    # Prune out anyone whose Lap Count is 0 (did not finish)
    if 'lap_count' in df_std.columns:
        df_std = df_std[df_std['lap_count'] != '0']
    # Parse chip time
    df_std['chip_time_sec'] = pd.to_datetime(df_std['chip_time'], format='%H:%M:%S', errors='coerce')
    df_std = df_std.dropna(subset=['chip_time_sec'])
    df_std['chip_time_sec'] = df_std['chip_time_sec'].dt.hour * 3600 + df_std['chip_time_sec'].dt.minute * 60 + df_std['chip_time_sec'].dt.second
    # Parse pace robustly
    def pace_to_sec(x):
        try:
            if pd.isnull(x) or ':' not in str(x):
                return None
            parts = str(x).split(':')
            if len(parts) == 2:
                return int(parts[0]) * 60 + int(parts[1])
            elif len(parts) == 3:  # In case of HH:MM:SS
                return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
            else:
                return None
        except Exception:
            return None
    df_std['pace_sec'] = df_std['pace'].apply(pace_to_sec)
    df_std = df_std.dropna(subset=['pace_sec'])
    df_std['pace_min_per_km'] = df_std['pace_sec'].apply(lambda s: f"{int(s)//60}:{int(s)%60:02d}")
    # Age as int
    df_std['age'] = pd.to_numeric(df_std['age'], errors='coerce')
    return df_std

df = load_data(race_file)

# Sidebar: Multi-runner selection
all_names = df['name'].drop_duplicates().sort_values().tolist()
def_name = all_names[0:1] if all_names else []
selected_names = st.sidebar.multiselect(
    "Compare runners (select one or more):",
    options=all_names,
    default=def_name
)

# Sidebar: Remove selected runners
if selected_names:
    st.sidebar.write("**Selected runners:**")
    for name in selected_names:
        if st.sidebar.button(f"Remove {name}"):
            selected_names.remove(name)
            st.experimental_rerun()

# Get runner data for all selected
selected_runners = df[df['name'].isin(selected_names)] if selected_names else pd.DataFrame()

# Main content
st.title("Race Results Analysis")

# Create three columns for the plots
col1, col2, col3 = st.columns(3)

# Chip Elapsed Time Distribution
with col1:
    st.subheader("Chip Elapsed Time Distribution")
    fig_time = px.histogram(df, x='chip_time_sec', 
                           title="Distribution of Finish Times",
                           labels={'chip_time_sec': 'Time (seconds)'})
    # Add lines for each selected runner
    for _, runner in selected_runners.iterrows():
        fig_time.add_vline(x=runner['chip_time_sec'], 
                          line_dash="dash", 
                          line_color="red",
                          annotation_text=runner['name'])
    st.plotly_chart(fig_time, use_container_width=True)

# Overall Pace Distribution
with col2:
    st.subheader("Overall Pace Distribution")
    # Set a reasonable lower bound for the axis (e.g., 3:00)
    axis_min = 180  # 3:00 in seconds
    axis_max = ((df['pace_sec'].max() // 60) + 2) * 60  # round up to the next full minute
    bin_size = 20
    bins = list(range(axis_min, axis_max + bin_size, bin_size))
    fig_pace = px.histogram(
        df, x='pace_sec',
        nbins=len(bins),
        title="Distribution of Paces",
        labels={'pace_sec': 'Pace (min/km)'}
    )
    for _, runner in selected_runners.iterrows():
        fig_pace.add_vline(
            x=runner['pace_sec'],
            line_dash="dash",
            line_color="red",
            annotation_text=runner['name']
        )
    # X-ticks every 3 minutes
    tickvals = list(range(axis_min, axis_max + 1, 180))
    x = [f"{int(s)//60}:{int(s)%60:02d}" for s in tickvals]
    ticktext = ["0:00"] +x
    # st.write("Tick mapping (seconds -> label):", list(zip(tickvals, ticktext)))
    fig_pace.update_xaxes(
        tickvals=tickvals,
        ticktext=ticktext,
        tickangle=45,
        range=[axis_min, axis_max]
    )
    st.plotly_chart(fig_pace, use_container_width=True)

# Age Distribution
with col3:
    st.subheader("Age Distribution")
    fig_age = px.histogram(df, x='age',
                          title="Distribution of Ages",
                          labels={'age': 'Age (years)'})
    for _, runner in selected_runners.iterrows():
        fig_age.add_vline(x=runner['age'],
                         line_dash="dash",
                         line_color="red",
                         annotation_text=runner['name'])
    st.plotly_chart(fig_age, use_container_width=True)

# Additional statistics
st.subheader("Race Statistics")
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total Runners", len(df))
with col2:
    st.metric("Average Time", f"{df['chip_time_sec'].mean()/60:.1f} minutes")
with col3:
    st.metric("Average Pace", f"{df['pace_sec'].mean()/60:.1f} min/km")
with col4:
    st.metric("Average Age", f"{df['age'].mean():.1f} years")

# Show full results table
st.subheader("Full Results")
st.dataframe(df, use_container_width=True) 