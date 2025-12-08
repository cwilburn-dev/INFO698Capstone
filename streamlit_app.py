import streamlit as st
import altair as alt
import pandas as pd
import plotly.express as px
import numpy as np
import json
import time
import random
from kmodes.kmodes import KModes

# region INITIALIZATION
# ============================================================
#                    INITIALIZATION & LANDING
# ============================================================
st.set_page_config(page_title="North Atlantic Migration Pattern Explorer (1880-1914)", layout="wide")

# Landing page session state
if "show_intro" not in st.session_state:
    st.session_state.show_intro = True

def begin_analysis():
    """Hide the landing page and begin the analysis."""
    st.session_state.show_intro = False
# endregion

# region CONSTANTS
# ============================================================
#                       CONSTANTS
# ============================================================
historical_counts = {
    1: 3749, 2: 4311, 3: 3506, 4: 3857, 5: 5902, 6: 7213, 7: 5934
}

bin_labels = {
    1: "1880-1884", 2: "1885-1889", 3: "1890-1894",
    4: "1895-1899", 5: "1900-1904", 6: "1905-1909", 7: "1910-1914"
}

birthplace_to_country = {
    "England": "United Kingdom", "Ireland": "United Kingdom",
    "Scotland": "United Kingdom", "Wales": "United Kingdom",
    "Germany": "German Empire", "Prussia": "German Empire", "Bavaria": "German Empire",
    "Russia": "Russian Empire", "Poland": "Russian Empire",
    "Norway": "Scandinavia", "Sweden": "Scandinavia", "Denmark": "Scandinavia", "Finland": "Scandinavia",
}

historical_events_by_country = {
    "United Kingdom": [
        {"year": 1885, "label": "U.S. Recovery Begins"},
        {"year": 1886, "label": "U.S. Recession"},
        {"year": 1887, "label": "English Disruptions"},
        {"year": 1888, "label": "Shipping Bottlenecks"}
    ],
    "German Empire": [
        {"year": 1871, "label": "German Unification"},
        {"year": 1886, "label": "Ruhr Mining Crisis"},
        {"year": 1890, "label": "Industrial Expansion"}
    ],
    "Russian Empire": [
        {"year": 1881, "label": "Assassination of Tsar Alexander II"},
        {"year": 1881, "label": "Pogroms & Anti-Jewish Legislation"},
        {"year": 1905, "label": "Russian Revolution of 1905"}
    ],
    "Scandinavia": [
        {"year": 1870, "label": "Scandinavian Agricultural Decline"},
        {"year": 1880, "label": "Sweden Industrializes"},
        {"year": 1905, "label": "Norway-Sweden Dissolution"}
    ],
    "Global": [
        {"year": 1873, "label": "Long Depression"},
        {"year": 1880, "label": "Steamships Revolutionize Travel"},
        {"year": 1914, "label": "World War I Begins"}
    ],
}
# endregion

# region DATA LOADING
# ============================================================
#                       DATA LOADING
# ============================================================
@st.cache_data
def load_data(file_path: str = "migration_analysis_ready_clean.csv") -> pd.DataFrame:
    """
    Load the cleaned migration dataset and remove columns that do not contribute
    to analysis (no variance or redundant).

    Drops:
        - ArrivalPlace: same value for all records
        - Source: same value for all records

    Args:
        file_path (str): Path to the CSV file.

    Returns:
        pd.DataFrame: Cleaned dataset ready for sampling, visualization, and clustering.
    """
    df = pd.read_csv(file_path)

    # Drop columns with no analytical value
    for col in ["ArrivalPlace", "Source"]:
        if col in df.columns:
            df.drop(columns=[col], inplace=True)

    return df
# endregion

# region METHODS
# ============================================================
#                       HELPER METHODS
# ============================================================
def get_sample(df: pd.DataFrame, sample_per_bin: int = 60) -> pd.DataFrame:
    """
    Return a sampled dataset, limiting each bin to sample_per_bin rows.

    Args:
        df (pd.DataFrame): Original dataframe
        sample_per_bin (int): Max rows per Bin

    Returns:
        pd.DataFrame: Sampled dataframe
    """
    sampled_groups = []
    for bin_value, group in df.groupby("Bin"):
        if len(group) >= sample_per_bin:
            sampled_groups.append(group.sample(n=sample_per_bin, replace=False))
        else:
            sampled_groups.append(group)
    return pd.concat(sampled_groups).reset_index(drop=True)

def annotate_chart(base_chart, events):
    """
    Annotate an Altair chart with vertical event markers.

    Args:
        base_chart: Altair chart object
        events: List of dicts {"year": int, "label": str}

    Returns:
        Altair layered chart with rules and text annotations
    """
    offsets = [-20, -35, -50, -65, -80, -95]
    layers = [base_chart]

    for idx, e in enumerate(events):
        df_event = pd.DataFrame({"ArrivalYear": [e["year"]], "Event": [e["label"]]})
        offset = offsets[idx % len(offsets)]

        rule = (
            alt.Chart(df_event)
            .mark_rule(color="red", strokeDash=[4, 4])
            .encode(x='ArrivalYear:O', tooltip=['ArrivalYear:O', 'Event:N'])
        )

        text = (
            alt.Chart(df_event)
            .mark_text(align="left", dy=offset, dx=5, color="white")
            .encode(x='ArrivalYear:O', text='Event:N')
        )

        layers.extend([rule, text])

    return alt.layer(*layers)
# endregion

# region SIDEBAR
# ============================================================
#                       SIDEBAR CONTROLS
# ============================================================
with st.sidebar:
    st.title("Controls")
    st.sidebar.header("Sampling Controls")

    df = load_data("migration_analysis_ready_clean.csv")

    seed = st.sidebar.number_input("Random Seed", min_value=0, max_value=1_000_000_000, value=42, step=1)
    np.random.seed(seed)
    random.seed(seed)

    sampled_df = get_sample(df, sample_per_bin=60)

    year_min, year_max = int(sampled_df['ArrivalYear'].min()), int(sampled_df['ArrivalYear'].max())
    year_range = st.slider("Select Year Range:", year_min, year_max, (year_min, year_max))

    st.subheader("Temporal Trends")
    valid_birthplaces = sampled_df['BirthPlace'].value_counts().loc[lambda x: x >= 3].index.tolist()
    selected_birthplaces = st.multiselect(
        "Select Birthplaces:", options=sorted(valid_birthplaces),
        default=[bp for bp in ["England", "Ireland"] if bp in valid_birthplaces]
    )
    apply_smoothing = st.checkbox("Apply 3-Year Rolling Average", value=False)

    st.subheader("KModes Clustering")
    n_clusters_rel = st.slider("Number of clusters:", 2, 8, 3)
    init_method_rel = st.selectbox("Initialization method:", ["Huang", "Cao"], index=0)
# endregion

# region LANDING PAGE
# ============================================================
#                    LANDING / INTRODUCTION
# ============================================================
if st.session_state.show_intro:
    st.markdown("""
    # North Atlantic Migration Explorer  
    ### 1880-1914

    Explore migration to the U.S. during the ocean liner era, capturing demographic patterns, 
    temporal trends, and historical context.
    
    Click below to begin exploring the data.
    """)
    st.button("**Begin Analysis**", on_click=begin_analysis, type="primary")
    st.stop()
# endregion

# region FILTERED DATA
# ============================================================
#                FILTER SAMPLE FOR ANALYSIS
# ============================================================
selected_df = sampled_df[
    (sampled_df["ArrivalYear"] >= year_range[0]) &
    (sampled_df["ArrivalYear"] <= year_range[1])
]

# Remove birthplaces with fewer than 3 records in selected range
MIN_RECORDS = 3
counts = selected_df["BirthPlace"].value_counts()
valid_birthplaces = counts[counts >= MIN_RECORDS].index
selected_df = selected_df[selected_df["BirthPlace"].isin(valid_birthplaces)]
# endregion

# region TIMELINE
# ============================================================
#                        TIMELINE
# ============================================================
def build_timeline_html(events_file="historical_events.json"):
    """
    Build HTML and JavaScript to embed the Knight Lab timeline.

    Args:
        events_file (str): Path to JSON file containing events

    Returns:
        str: HTML + JS code for timeline
    """
    events = pd.read_json(events_file)

    # Normalize country names
    name_map = {
        "Global": "Global",
        "Germany": "German Empire",
        "Russia": "Russian Empire",
        "Scandinavia": "Scandinavia",
        "United Kingdom": "United Kingdom",
        "United States": "United States",
    }
    events["country"] = events["country"].map(name_map).fillna(events["country"])

    desired_order = ["Global", "German Empire", "Russian Empire", "Scandinavia", "United Kingdom", "United States"]
    prefix_map = {c: f"{i+1}_{c}" for i, c in enumerate(desired_order)}

    country_colors = {
        "Global": "#2E8B57", "German Empire": "#003153", "Russian Empire": "#5E4B2A",
        "Scandinavia": "#7B1A1A", "United Kingdom": "#1f77b4", "United States": "#002868"
    }

    timeline_data = {
        "title": {"text": {"headline": "Historical Context", "text": "Events impacting migration"}},
        "events": [
            {
                "start_date": {"year": int(row.year)},
                "text": {"headline": "" if row.type == "order_stub" else row.title,
                         "text": "" if row.type == "order_stub" else row.description},
                "group": prefix_map.get(row.country, f"999_{row.country}"),
                "unique_id": f"event_{i}",
                "background": {"color": "#FFFFFF00" if row.type == "order_stub" else country_colors.get(row.country, "#888888")}
            }
            for i, row in events.iterrows()
        ],
    }

    return f"""
    <div id="timeline-embed" style="border-radius: 12px; padding: 10px; height: 450px;"></div>
    <link rel="stylesheet" href="https://cdn.knightlab.com/libs/timeline3/latest/css/timeline.css">
    <script src="https://cdn.knightlab.com/libs/timeline3/latest/js/timeline.js"></script>
    <script>
    const data = {json.dumps(timeline_data)};
    const isDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    const bgColor = isDark ? '#0E1117' : '#FFFFFF';
    const textColor = isDark ? '#FAFAFA' : '#000000';
    const accentColor = '#4C8BF5';
    window.timeline = new TL.Timeline('timeline-embed', data, {{
        theme_color: accentColor,
        hash_bookmark: false,
        initial_zoom: 3,
        start_at_slide: 1
    }});
    document.addEventListener("DOMContentLoaded", function() {{
        const el = document.getElementById("timeline-embed");
        el.style.backgroundColor = bgColor;
        el.style.color = textColor;
    }});
    </script>
    """

st.components.v1.html(build_timeline_html(), height=500)
# endregion

# region TABS
# ============================================================
#                        MAIN TABS
# ============================================================
tab1, tab2, tab3, tab4 = st.tabs(["Project Overview", "Demographics", "Temporal Trends", "Clustering"])
# endregion

# region PROJECT OVERVIEW
# ============================================================
with tab1:
    st.markdown("### Project Overview")
    st.markdown("""
    This project investigates migration to the U.S. via the UK between 1880-1914 using digitized passenger lists.
    Goals: identify patterns, validate historical interpretations, present interactive visualization.
    """)
    st.markdown("### Sample Data")
    st.dataframe(sampled_df.head(10))
# endregion

# region DEMOGRAPHICS
# ============================================================
with tab2:
    st.markdown("## Demographic Overview")
    st.markdown("Predominantly young adults, male-skewed, varying by nationality.")

    # Top 10 Birthplaces
    bp_counts = selected_df["BirthPlace"].value_counts().head(10)
    bp_df = bp_counts.reset_index()
    bp_df.columns = ["BirthPlace", "Count"]
    fig_bp = px.pie(bp_df, names="BirthPlace", values="Count", title="Top 10 Birthplaces", hole=0.3)
    st.plotly_chart(fig_bp, width="stretch")

    # Gender distribution
    gender_counts = sampled_df["Gender"].value_counts().rename_axis("Gender").reset_index(name="Count")
    fig_gender = px.pie(gender_counts, names="Gender", values="Count", title="Gender Distribution", hole=0.3)
    st.plotly_chart(fig_gender, width="stretch")

    # Age distribution
    age_counts = sampled_df["AgeAtArrival"].value_counts().rename_axis("Age").reset_index(name="Count").sort_values("Age")
    fig_age = px.bar(age_counts, x="Age", y="Count", text="Count", title="Age Distribution")
    st.plotly_chart(fig_age, width="stretch")
# endregion

# region TEMPORAL TRENDS
# ============================================================
with tab3:
    st.markdown("## Temporal Migration Trends")

    df_grouped = selected_df.groupby(['ArrivalYear', 'BirthPlace']).size().reset_index(name='Count')
    filtered = df_grouped[df_grouped['BirthPlace'].isin(selected_birthplaces)]
    chart = alt.Chart(filtered).mark_line(point=True).encode(
        x=alt.X('ArrivalYear:O', title='Year of Arrival'),
        y=alt.Y('Count:Q', title='Number of Migrants'),
        color=alt.Color('BirthPlace:N', title='Birthplace'),
        tooltip=['ArrivalYear', 'BirthPlace', 'Count']
    ).properties(width=700, height=400)
    annotated = annotate_chart(chart, sum([historical_events_by_country.get(bp_to_country, []) for bp_to_country in selected_birthplaces], []))
    st.altair_chart(annotated, width="stretch")

    if apply_smoothing:
        smoothed = filtered.sort_values(['BirthPlace', 'ArrivalYear']).groupby('BirthPlace').rolling(window=3, on='ArrivalYear', min_periods=1)['Count'].mean().reset_index()
        smoothed_chart = alt.Chart(smoothed).mark_line(strokeDash=[5, 3]).encode(
            x='ArrivalYear:O', y='Count:Q', color='BirthPlace:N', tooltip=['ArrivalYear', 'BirthPlace', 'Count']
        ).properties(width=700, height=400, title="3-Year Rolling Average")
        st.altair_chart(smoothed_chart, width="stretch")
# endregion

# region CLUSTERS
# ============================================================
with tab4:
    st.markdown("## KModes Cluster Analysis")

    df_rel = selected_df.copy()
    df_rel["RouteCode"] = df_rel["BirthPlace"].astype(str) + " → " + df_rel["DeparturePlace"].astype(str)

    def get_season(month_name: str) -> str:
        """Convert month name to season."""
        seasons = {
            "Winter": ["December", "January", "February"],
            "Spring": ["March", "April", "May"],
            "Summer": ["June", "July", "August"],
            "Fall":   ["September", "October", "November"]
        }
        for season, months in seasons.items():
            if month_name in months:
                return season
        return "Unknown"

    df_rel["Season"] = df_rel["ArrivalMonth"].apply(get_season)

    def get_age_cat(age: int) -> str:
        """Categorize age into buckets."""
        if age < 15: return "Child"
        elif age < 24: return "YoungAdult"
        elif age < 55: return "Adult"
        else: return "Senior"

    df_rel["AgeCategory"] = df_rel["AgeAtArrival"].apply(get_age_cat)

    cat_cols_rel = ["RouteCode", "Season", "AgeCategory", "Gender"]
    if set(cat_cols_rel).issubset(df_rel.columns) and df_rel[cat_cols_rel].notna().all().all():
        df_km_rel = df_rel[cat_cols_rel].astype(str)
        km_rel = KModes(n_clusters=n_clusters_rel, init=init_method_rel, n_init=5, verbose=0, random_state=42)
        clusters_rel = km_rel.fit_predict(df_km_rel)
        df_km_rel["Cluster"] = clusters_rel

        # Cluster profiles
        cluster_profiles_rel = {c: {col: df_km_rel[df_km_rel["Cluster"]==c][col].mode()[0] for col in cat_cols_rel} for c in sorted(df_km_rel["Cluster"].unique())}

        # Plot heatmaps
        def plot_heatmap_with_profile(df, x_col, cluster_profiles):
            heat_data = df.groupby([x_col, "Cluster"]).size().reset_index(name="Count")
            profile_strings = [", ".join([f"{k}: {v}" for k, v in cluster_profiles[row["Cluster"]].items() if k != x_col]) for _, row in heat_data.iterrows()]
            heat_data["Profile"] = profile_strings
            chart = alt.Chart(heat_data).mark_rect().encode(
                x=alt.X(f"{x_col}:N", title=x_col),
                y=alt.Y("Cluster:O", title="Cluster"),
                color=alt.Color("Count:Q", scale=alt.Scale(scheme="blues")),
                tooltip=[x_col, "Cluster", "Count", "Profile"]
            ).properties(width=700, height=350)
            return chart

        st.altair_chart(plot_heatmap_with_profile(df_km_rel, "RouteCode", cluster_profiles_rel), width="stretch")
        st.altair_chart(plot_heatmap_with_profile(df_km_rel, "Season", cluster_profiles_rel), width="stretch")
        st.altair_chart(plot_heatmap_with_profile(df_km_rel, "AgeCategory", cluster_profiles_rel), width="stretch")
        st.altair_chart(plot_heatmap_with_profile(df_km_rel, "Gender", cluster_profiles_rel), width="stretch")
    else:
        st.info("KModes clustering unavailable due to missing or invalid data.")
# endregion