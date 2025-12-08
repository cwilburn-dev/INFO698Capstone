# North Atlantic Migration Explorer (1880-1914) - Streamlit App
# --------------------------------------------------------------
# This application visualizes and analyzes transatlantic migration patterns
# during the late 19th and early 20th centuries, using historical passenger
# lists from New York arrivals. The system:
#
# 1. Loads cleaned migration data and caches it for efficient reuse
# 2. Samples the data by migration bins for balanced visualization
# 3. Allows user-driven filtering by year range, birthplace, and smoothing
# 4. Displays multiple views:
#    - Project Overview (summary, methodology, key findings)
#    - Demographics (age, gender, nationality, children)
#    - Temporal Trends (migration counts over time with historical event annotations)
#    - Clustering (KModes analysis over route, season, age, and gender)
# 5. Integrates historical context via annotated charts and a Timeline.js visualization
#
# Code sections:
# - Initialization (session state, random seed, data loading)
# - Constants (historical counts, bin labels, mappings)
# - Utility Methods (sampling, chart annotation, season/age categorization)
# - Streamlit Interface (landing page, sidebar controls, tabs)
# - Demographics, Temporal, and Clustering Visualizations
# - Timeline Integration and Event Annotation

# ============================================================
#                       IMPORTS
# ============================================================
# === Standard library ===
import json
import time
import random

# === Third-party libraries ===
import streamlit as st
import altair as alt
import pandas as pd
import plotly.express as px
import numpy as np

# === Local / project-specific ===
from kmodes.kmodes import KModes

# region INITIALIZATION
# ============================================================
#                       INITIALIZATION
# ============================================================
# === Landing Page ===
if "show_intro" not in st.session_state:
    st.session_state.show_intro = True

def begin_analysis():
    st.session_state.show_intro = False

# === load data ===
@st.cache_data
def load_data():
    df = pd.read_csv("migration_analysis_ready_clean.csv")
    return df
# endregion

# region CONSTANTS
# ============================================================
#                       CONSTANTS
# ============================================================
historical_counts = {
    1: 3749,
    2: 4311,
    3: 3506,
    4: 3857,
    5: 5902,
    6: 7213,
    7: 5934
}

bin_labels = {
    1: "1880-1884",
    2: "1885-1889",
    3: "1890-1894",
    4: "1895-1899",
    5: "1900-1904",
    6: "1905-1909",
    7: "1910-1914"
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

birthplace_to_country = {
    "England": "United Kingdom",
    "Ireland": "United Kingdom",
    "Scotland": "United Kingdom",
    "Wales": "United Kingdom",

    "Germany": "German Empire",
    "Prussia": "German Empire",
    "Bavaria": "German Empire",

    "Russia": "Russian Empire",
    "Poland": "Russian Empire",

    "Norway": "Scandinavia",
    "Sweden": "Scandinavia",
    "Denmark": "Scandinavia",
    "Finland": "Scandinavia",
}
# endregion

# region METHODS
# ============================================================
#                       METHODS
# ============================================================
def get_sample(df, sample_per_bin=80):
    """
    Generate a sampled dataset by bin, limiting each bin to a maximum number of records.

    Args:
        df (pd.DataFrame): The original DataFrame containing migration data, including a 'Bin' column.
        sample_per_bin (int): Maximum number of rows to sample per bin. Defaults to 60.

    Returns:
        pd.DataFrame: A new DataFrame containing the sampled records, concatenated across all bins.
    
    Notes:
        - If a bin contains fewer rows than sample_per_bin, all rows are included.
        - The resulting DataFrame index is reset.
    """
    sampled_groups = []

    for bin_value, group in df.groupby("Bin"):
        if len(group) >= sample_per_bin:
            sampled_groups.append(group.sample(n=sample_per_bin, replace=False))
        else:
            sampled_groups.append(group)

    return pd.concat(sampled_groups).reset_index(drop=True)

# adds vertical event marks to chart
# events is a list of {"year": int, "label": str}.
def annotate_chart(base_chart, events):
    """
    Layer vertical event markers and labels onto an Altair chart.

    Args:
        base_chart (alt.Chart): The Altair chart to annotate.
        events (list[dict]): List of events, where each dict contains:
            - 'year' (int): The year of the event.
            - 'label' (str): The text label for the event.

    Returns:
        alt.LayerChart: The original chart overlaid with vertical rules and staggered text labels.
    
    Notes:
        - Label offsets are staggered for readability to avoid overlapping text.
        - Each event is drawn with a red dashed line and a corresponding text annotation.
        - Designed for time series plots with an 'ArrivalYear' axis.
    """
    # staggered offsets for readability
    offsets = [ -20, -35, -50, -65, -80, -95 ]
    layers = [base_chart]

    for idx, e in enumerate(events):
        df_event = pd.DataFrame({"ArrivalYear": [e["year"]], "Event": [e["label"]]})

        # label offset
        offset = offsets[idx % len(offsets)]

        # draws lines
        rule = (
            alt.Chart(df_event)
            .mark_rule(color="red", strokeDash=[4, 4])
            .encode(
                x='ArrivalYear:O',
                tooltip=['ArrivalYear:O', 'Event:N']
            )
        )

        # labels - staggered
        text = (
            alt.Chart(df_event)
            .mark_text(
                align="left",
                dy=offset,
                dx=5,
                color="white"
            )
            .encode(
                x='ArrivalYear:O',
                text='Event:N'
            )
        )

        layers.extend([rule, text])

    return alt.layer(*layers)
# endregion

# region MAIN
# ============================================================
#                        MAIN & LANDING
# ============================================================
st.set_page_config(page_title="North Atlantic Migration Pattern Explorer (1880-1914)", layout="wide")

# === Landing Page ===
if st.session_state.show_intro:
    st.markdown("""
    # North Atlantic Migration Explorer  
    ### 1880-1914

    The late 19th through early 20th centuries marked one of the most dramatic population movements 
    in human history. Millions of Europeans left small towns, farming villages, and crowded 
    industrial cities, driven by economic hardship, land shortages, political instability, and 
    the hope of better opportunities abroad.

    Between 1871 and 1914, an estimated 30-35.5 million people departed Europe. The largest annual 
    flows occurred between 1880 and 1914, when nearly 3 million immigrants from Great Britain and 
    more than 2.2 million from Ireland arrived in the United States, along with large numbers from 
    Germany, Scandinavia, Eastern Europe, and Southern Europe.

    This great wave of migration slowed abruptly with the outbreak of World War I in 1914.  In the 
    1920s, the United States Congress passed the Emergency Quota Act (1921) and the Immigration 
    Act (1924), which introduced strict immigration quotas and brought about the end of the age of 
    mass European migration.

    Notice: If you are viewing this before December 10th, 2025, the project is still undergoing minor
    refinements that may result in interruptions.  Thank you for your understanding.
                
    ---
    ### Click below to begin exploring the data.
    """)

    st.button("**Begin Analysis**", on_click=begin_analysis, type="primary")
    st.stop()

df = load_data()
df["BinLabel"] = df["Bin"].map(bin_labels)

sampled_df = get_sample(df, sample_per_bin=60)
# endregion

# region SIDEBAR
# ============================================================
#                           SIDEBAR
# ============================================================
with st.sidebar:
    st.title("Controls")
    st.sidebar.header("Sampling Controls")

    seed = st.sidebar.number_input(
        "Random Seed",
        min_value=0,
        max_value=1_000_000_000,
        value=42,
        step=1
    )

    np.random.seed(seed)
    random.seed(seed)

    # year selection - used for timeline, selected_df, all tabs
    year_min = int(sampled_df['ArrivalYear'].min())
    year_max = int(sampled_df['ArrivalYear'].max())
    year_range = st.slider(
        "Select Year Range:",
        year_min, year_max,
        (year_min, year_max)
    )

    # temporal trends
    st.subheader("Temporal Trends")
    valid_birthplaces = (
        sampled_df['BirthPlace']
        .value_counts()
        .loc[lambda x: x >= 3]
        .index
        .tolist()
    )
    selected_birthplaces = st.multiselect(
        "Select Birthplaces:",
        options=sorted(valid_birthplaces),
        default=[bp for bp in ["England", "Ireland"] if bp in valid_birthplaces]
    )
    apply_smoothing = st.checkbox("Apply 3-Year Rolling Average", value=False)

    # clustering
    st.subheader("KModes Clustering")
    n_clusters_rel = st.slider("Number of clusters:", 2, 8, 3)
    init_method_rel = st.selectbox("Initialization method:", ["Huang", "Cao"], index=0)

if sampled_df is not None:
    # clears the sample message
    msg = st.empty()
    msg.success(f"Sample generated successfully ({len(sampled_df)} records).")
    time.sleep(1)
    msg.empty()
    
    st.title("North Atlantic Migration Explorer (1880-1914)")
    
    # filtered dataset for all tabs
    selected_df = sampled_df[
        (sampled_df["ArrivalYear"] >= year_range[0]) &
        (sampled_df["ArrivalYear"] <= year_range[1])
    ]

    # remove birthplaces with fewer than n records in the selected range
    MIN_RECORDS = 3
    counts = selected_df["BirthPlace"].value_counts()
    valid_birthplaces = counts[counts >= MIN_RECORDS].index
    selected_df = selected_df[selected_df["BirthPlace"].isin(valid_birthplaces)]
# endregion

# region TIMELINE
# ============================================================
#                           TIMELINE
# ============================================================
    # load events
    events = pd.read_json("historical_events.json")

    name_map = {
        "Global": "Global",
        "Germany": "German Empire",
        "Russia": "Russian Empire",
        "Scandinavia": "Scandinavia",
        "United Kingdom": "United Kingdom",
        "United States": "United States",
    }
    events["country"] = events["country"].map(name_map).fillna(events["country"])

    desired_order = [
        "Global",
        "German Empire",
        "Russian Empire",
        "Scandinavia",
        "United Kingdom",
        "United States"
    ]

    prefix_map = {
        c: f"{i+1}_{c}"
        for i, c in enumerate(desired_order)
    }

    country_colors = {
        "Global": "#2E8B57",          # earth green
        "German Empire": "#003153",   # prussian blue
        "Russian Empire": "#5E4B2A",  # imperial brown
        "Scandinavia": "#7B1A1A",     # nordic red
        "United Kingdom": "#1f77b4",  # union jack blue
        "United States":  "#002868",  # old glory blue
    }

    timeline_data = {
        "title": {"text": {"headline": "Historical Context", "text": "Events impacting migration"}},
        "events": [
            {
                "start_date": {"year": int(row.year)},
                "text": {
                    "headline": "" if row.type == "order_stub" else row.title,
                    "text": "" if row.type == "order_stub" else row.description
                },
                "group": prefix_map.get(row.country, f"999_{row.country}"),
                "unique_id": f"event_{i}",
                "background": {
                    "color": "#FFFFFF00" if row.type == "order_stub" else country_colors.get(row.country, "#888888")
                }
            }
            for i, row in events.iterrows()
        ],
    }

    # serialize to js string
    timeline_json = json.dumps(timeline_data)

    # html for timeline
    custom_html = f"""
    <div id="timeline-embed" style="border-radius: 12px; padding: 10px; height: 450px;"></div>

    <link rel="stylesheet"
        href="https://cdn.knightlab.com/libs/timeline3/latest/css/timeline.css">
    <script src="https://cdn.knightlab.com/libs/timeline3/latest/js/timeline.js"></script>

    <script>
    const data = {timeline_json};

    const isDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    const bgColor = isDark ? '#0E1117' : '#FFFFFF';
    const textColor = isDark ? '#FAFAFA' : '#000000';
    const accentColor = '#4C8BF5';  // Streamlit blue

    // initialize timeline
    window.timeline = new TL.Timeline('timeline-embed', data, {{
        theme_color: accentColor,
        hash_bookmark: false,
        initial_zoom: 3,
        start_at_slide: 1,
        start_at_end: false
    }});

    document.addEventListener("DOMContentLoaded", function() {{
        const el = document.getElementById("timeline-embed");
        el.style.backgroundColor = bgColor;
        el.style.color = textColor;

        // wait until the timeline is ready
        const tryGoTo = () => {{
            if (window.timeline && window.timeline._timeline) {{

                // force-scroll bottom panel to 1845
                window.timeline._timeline.navigateTo(new Date(1845, 0, 1));

                // also jump top panel to first real event
                const firstReal = data.events.find(e => e.text.headline !== "");
                if (firstReal && window.timeline.goToId) {{
                    window.timeline.goToId(firstReal.unique_id);
                }}

            }} else {{
                setTimeout(tryGoTo, 50);
            }}
        }};
        tryGoTo();
    }});
    </script>
    """

    st.components.v1.html(custom_html, height=500)
    tab1, tab2, tab3, tab4 = st.tabs(["Project Overview", "Demographics", "Temporal Trends", "Clustering"])
# endregion

# region PROJECT OVERVIEW
# ============================================================
#                      PROJECT OVERVIEW
# ============================================================
    with tab1:
        st.markdown("### Project Overview")
        st.markdown("#### Project Summary")
        st.markdown("""
        This project investigates migration to the United States by way of the United Kingdom during the peak years of the ocean 
        liner era (1880-1914) by analyzing digitized passenger-list data from the New York Arriving Passenger and Crew Lists 
        collection.
                    
        The goal for this project is to identify migration patterns, validate or challenge traditional historical interpretations, 
        and present the results through an interactive application that allows users to explore demographic, temporal, and 
        event-driven aspects of transatlantic travel.

        The app integrates structured passenger data, historical event context, visual analytics, and clustering methods to 
        create a narrative about who migrated, when they traveled, and how external forces may have influenced these 
        movements.            
        """)

        st.markdown("#### Research Question & Hypothesis")
        st.markdown("""
        The informal guiding hypothesis for this project was twofold:

        1) Discovery-oriented goal:
        Determine whether patterns or insights could be uncovered in the passenger lists that have been overlooked or 
        underexplored in traditional summaries of transatlantic migration.
        2) Accessibility-oriented goal:
        If no novel patterns emerged (due to dataset size, manual collection constraints, or temporal sampling), the 
        expectation was that the dataset would still support well-established migration trends, offering a reliable and engaging 
        way of exploring the records interactively.

        As the project scope required fully manual data extraction and cleaning, advanced NLP or large-scale geospatial 
        work that were initially part of the proposal, were not feasible within the available time.  However, the resulting 
        dataset still supports meaningful analysis and historically consistent conclusions.
        """)

        st.markdown("#### Data Collection & Methodology")
        st.markdown("""
        A total of 448 records were manually collected from the Ancestry.com “New York, U.S., Arriving Passenger and Crew Lists 
        (1820-1957)” collection.
        
        To create a manageable yet representative dataset:  
        •	A letter-based random sampling strategy was used to stagger record selection.  
        •	Data was gathered in batches of 140 entries and later reorganized into five-year migration bins to ensure balanced temporal coverage.  
        •	Manual entry ensured consistent cleaning and formatting, but time limitations prevented expansion to a larger dataset.  
                    
        In compliance with Ancestry's policies, the full dataset cannot be publicly distributed within the app, but it is available 
        upon request for academic or instructional purposes.
        """)

        st.markdown("#### Analytics Approach")
        st.markdown("""
        Several visualization and modeling strategies were selected to make the dataset easy to explore:  
        •	Temporal charts (area and line plots) to show migration flow over time.  
        •	Demographic breakdowns (age, gender, birth place/nationality) to identify population-level characteristics.  
        •	Port-of-departure and ship-based visualizations to explore travel logistics.  
        •	A historical event timeline to help viewers correlate migration patterns with contextual events.  
        •	KModes clustering to explore whether demographic and temporal variables formed meaningful groups.  
                    
        These components were chosen because they allow users to engage with the data from multiple angles (temporal, demographic, 
        historical, and exploratory), mirroring the approach used in traditional historical research.
        """)
        
        st.markdown("#### Key Findings")
        st.markdown("""
        Although the dataset is modest in size, several trends emerged:  
        •	The majority of travelers were adults aged 18-40, which is consistent with known migration patterns during this period.  
        •	Seasonal trends appear in several visualizations, with peaks aligning with typical shipping schedules and weather windows.  
        •	Clustering did not reveal strong novel groupings, likely due to dataset size, but did align with expected demographic patterns.  
        •	The data overall supports established understandings of migration from the United Kingdom to the United States during the era, reinforcing patterns seen in traditional studies.  
        """)

        st.markdown("#### Limitations")
        st.markdown("""
        Several constraints affected the scope of analysis:  
        •	Manual data collection restricted dataset size.   
        •	NLP and large-scale geospatial analyses were not feasible within the available timeline.  
        •	Some historical events may influence migration timing indirectly, making correlations suggestive rather than definitive.  
                    
        Future work could incorporate a larger dataset, automated extraction methods, or more advanced modeling approaches.
        """)

        st.markdown("### Sample Data")
        st.markdown("""
        The 448 records used in this analysis were drawn from the **'New York, U.S., Arriving Passenger and Crew Lists
        (Castle Garden and Ellis Island), 1820-1957'** collection available through Ancestry.com.  Records were selected 
        using a random letter-based sampling approach, collected in batches of 140 entries, and later grouped into 
        five-year migration bins to ensure balanced temporal representation across the study period.
        """)

        st.markdown("In compliance with Ancestry.com's data policies, the full dataset is available upon request only.")
        st.dataframe(sampled_df.head(10))
# endregion

# region DEMOGRAPHICS
# ============================================================
#                       DEMOGRAPHICS
# ============================================================
    with tab2:
        st.markdown("## Demographic Overview")
        st.markdown("""
        The migrants arriving in New York between 1880 and 1914 were predominantly young adults, with a notable 
        male bias, reflecting labor-driven migration patterns.  While most travelers were adults, children (< 15) were 
        also present, particularly among migrants from England and Ireland, indicating that family migration occurred 
        alongside individual economic migration, which could include both labor settlement and short-term wage-seeking.

        Nationality strongly shaped migration patterns. The largest groups came from England, Ireland, and 
        the German Empire, with smaller but significant contributions from the Scandinavian countries and the 
        Russian Empire.  Differences in age, gender, and the presence of children reflect that migration strategies 
        varied by origin: some communities migrated as families, while others sent primarily working-age adults.
        
        Overall, the demographic profile shows a migration flow that was young, male-skewed, and  nationality-dependent, 
        highlighting the social dynamics and decision-making that shaped transatlantic movement.
        """)

        # === HISTORICAL BAR PLOT ===
        st.subheader("Total Migrants per Year (Historical)")
        historical_df = (
            pd.DataFrame(list(historical_counts.items()), columns=["Bin", "Count"])
            .assign(BinLabel=lambda x: x["Bin"].map(bin_labels))
            .sort_values("Bin")
        )

        fig_hist = px.bar(
            historical_df,
            x="BinLabel",
            y="Count",
            text="Count",
            title="Estimated Total Migrants per Year (1880-1914)",
            labels={"BinLabel": "Year Range", "Count": "Estimated Migrant Count"}
        )
        fig_hist.update_traces(textposition="outside")
        fig_hist.update_layout(xaxis={"categoryorder": "array", "categoryarray": list(bin_labels.values())})
        st.plotly_chart(fig_hist, width="stretch")

        # === PIE CHARTS ===
        col1, col2 = st.columns(2)

        # --- nationality - top 10 ---
        with col1:
            if "BirthPlace" in selected_df.columns:
                st.subheader("Top 10 Birthplaces / Nationalities")
                bp_counts = selected_df["BirthPlace"].value_counts().head(10)
                bp_df = bp_counts.reset_index()
                bp_df.columns = ["BirthPlace", "Count"]

                fig_bp = px.pie(
                    bp_df,
                    names="BirthPlace",
                    values="Count",
                    title="Top 10 Nationalities",
                    hole=0.3
                )
                fig_bp.update_traces(textposition="inside", textinfo="percent+label")
                st.plotly_chart(fig_bp, width="stretch")
            else:
                st.warning("WARNING: 'BirthPlace' column not found.")

        # --- gender ---        
        with col2:
            if "Gender" in sampled_df.columns:
                st.subheader("Gender Distribution")
                gender_counts = (
                    sampled_df["Gender"]
                    .value_counts()
                    .rename_axis("Gender")
                    .reset_index(name="Count")
                )
                fig_gender = px.pie(
                    gender_counts,
                    names="Gender",
                    values="Count",
                    title="Percentage of Men vs Women",
                    hole=0.3
                )
                fig_gender.update_traces(textposition="inside", textinfo="percent+label")
                st.plotly_chart(fig_gender, width="stretch")
            else:
                st.warning("WARNING: 'Gender' column not found.")

        # === AGE & CHILDREN BAR CHARTS ===
        # --- age at arrival ---
        if "AgeAtArrival" in sampled_df.columns:
            st.subheader("Age Distribution of Migrants")
            age_counts = (
                sampled_df["AgeAtArrival"]
                .value_counts()
                .rename_axis("Age")
                .reset_index(name="Count")
                .sort_values("Age")
            )
            fig_age = px.bar(
                age_counts,
                x="Age",
                y="Count",
                text="Count",
                title="Number of Migrants by Age",
                labels={"Age": "Age at Arrival", "Count": "Number of Migrants"}
            )
            fig_age.update_traces(textposition="outside")
            st.plotly_chart(fig_age, width="stretch")
        else:
            st.warning("WARNING: 'AgeAtArrival' column not found.")

        # --- children by nationality ---
        if {"AgeAtArrival", "BirthPlace"}.issubset(sampled_df.columns):
            st.subheader("Children by Nationality")
            children_df = sampled_df[sampled_df["AgeAtArrival"] < 15]
            nationality_counts = (
                children_df["BirthPlace"]
                .value_counts()
                .rename_axis("BirthPlace")
                .reset_index(name="Count")
                .sort_values("Count", ascending=False)
            )
            if nationality_counts.empty:
                st.info("No children (Age < 15) found in the sample.")
            else:
                fig_children = px.bar(
                    nationality_counts,
                    x="BirthPlace",
                    y="Count",
                    text="Count",
                    title="Number of Children by Nationality (Age < 15)"
                )
                fig_children.update_traces(textposition="outside")
                fig_children.update_layout(xaxis={"categoryorder": "total descending"})
                st.plotly_chart(fig_children, width="stretch")
        else:
            st.warning("WARNING: Missing 'AgeAtArrival' or 'BirthPlace' columns.")
# endregion

# region TEMPORAL
# ============================================================
#                       TEMPORAL
# ============================================================
    with tab3:
        st.markdown("## Temporal Migration Trends Over Time")

        if 'ArrivalYear' not in selected_df.columns:
            st.error("ERROR: The dataset does not include 'ArrivalYear'. Please add it during preprocessing.")
        else:
            df_grouped = (
                selected_df.groupby(['ArrivalYear', 'BirthPlace'])
                .size()
                .reset_index(name='Count')
            )

            filtered = df_grouped[df_grouped['BirthPlace'].isin(selected_birthplaces)]

            if filtered.empty:
                st.warning("WARNING: No data available for the selected filters.")
            else:
                chart = (
                    alt.Chart(filtered)
                    .mark_line(point=True)
                    .encode(
                        x=alt.X('ArrivalYear:O', title='Year of Arrival'),
                        y=alt.Y('Count:Q', title='Number of Migrants'),
                        color=alt.Color('BirthPlace:N', title='Birthplace'),
                        tooltip=['ArrivalYear', 'BirthPlace', 'Count']
                    )
                    .properties(width=700, height=400, title="Migration Counts by Birthplace and Year")
                    .interactive()
                )

                countries = set()
                for bp in selected_birthplaces:
                    c = birthplace_to_country.get(bp)
                    if c and c in historical_events_by_country:
                        countries.add(c)

                events_to_annotate = []
                for country in countries:
                    events_to_annotate.extend(historical_events_by_country[country])

                annotated = annotate_chart(chart, events_to_annotate)
                st.altair_chart(annotated, width="stretch")
                st.caption("💡Tip: If the chart ever appears blank, double-click inside the plot to refresh it.")

                if apply_smoothing:
                    smoothed = (
                        filtered.sort_values(['BirthPlace', 'ArrivalYear'])
                        .groupby('BirthPlace')
                        .rolling(window=3, on='ArrivalYear', min_periods=1)['Count']
                        .mean()
                        .reset_index()
                    )
                    smoothed_chart = (
                        alt.Chart(smoothed)
                        .mark_line(strokeDash=[5, 3])
                        .encode(
                            x='ArrivalYear:O',
                            y='Count:Q',
                            color='BirthPlace:N',
                            tooltip=['ArrivalYear', 'BirthPlace', 'Count']
                        )
                        .properties(width=700, height=400, title="3-Year Rolling Average (Smoothed)")
                    )
                    st.altair_chart(smoothed_chart, width="stretch")

        st.markdown("""
            ### Understanding Migration Patterns Over Time
                    
            The temporal trends chart allows you to compare how migration from different birthplaces changes year-by-year. 
            Each line represents one nationality, revealing long-term shifts, short-term disruptions, and responses to 
            historical events.
                    
            To illustrate how this works, if you select England and Ireland together (using the default seed), a few notable 
            patterns appear:
                    
            1. Inverse relationship between English and Irish migration  
            Across much of the period, migration from England and Ireland tends to move in opposite directions: when English 
            migration rises, Irish migration often declines, and vice-versa.  
                    
                This suggests one of two possibilities:  
                •	Delayed effects — the same event may reach or impact each country at slightly different times, producing 
                staggered responses.  
                •	Different push/pull dynamics — the economic, political, or social forces influencing migration were not identical 
                in the two regions, even though both were part of the UK.  
                
                This contrast makes the two countries useful for comparison.
                    
            2. Shared low point in 1888  
            Both England and Ireland reach their lowest migration levels in 1888, and they converge sharply at the same time. 
            While short declines occur elsewhere in the series, this joint minimum indicates a common external pressure acting 
            on both populations.
                    
                Historical records align with this pattern:  
                •	The United States experienced a recession beginning in the mid-1880s  
                •	The United Kingdom faced widespread industrial strikes and coal shortages in 1887-1888  
                
                These disruptions would have increased uncertainty on both sides of the Atlantic, reducing the resources needed to 
                emigrate and the opportunities available upon arrival.
                    
            ### What This Demonstrates
            This example shows how the chart can reveal:  
            •	Linked historical pressures affecting multiple countries  
            •	Unique national responses to similar circumstances   
            •	Patterns that become visible only when comparing multiple birthplaces together  
            
            Users can explore similar relationships for any combination of nationalities by adjusting the filters and smoothing
            options.
            """)
# endregion

# region CLUSTERS
# ============================================================
#                       CLUSTERS
# ============================================================
    with tab4:
        st.markdown("## Cluster Analysis - Relationship Features")

        df_rel = selected_df.copy()

        # route code is birthplace + departure
        df_rel["RouteCode"] = df_rel["BirthPlace"].astype(str) + " → " + df_rel["DeparturePlace"].astype(str)

        # === season ===
        def get_season(month_name):
            """
            Convert a month name to a meteorological season.

            Args:
                month_name (str): Name of the month (e.g., 'January').

            Returns:
                str: One of 'Winter', 'Spring', 'Summer', 'Fall', or 'Unknown' if the month name is not recognized.
            """
            winter = ["December", "January", "February"]
            spring = ["March", "April", "May"]
            summer = ["June", "July", "August"]
            fall   = ["September", "October", "November"]
            
            if month_name in winter:
                return "Winter"
            elif month_name in spring:
                return "Spring"
            elif month_name in summer:
                return "Summer"
            elif month_name in fall:
                return "Fall"
            else:
                return "Unknown" 

        df_rel["Season"] = df_rel["ArrivalMonth"].apply(get_season)
        
        # === age ===
        def get_age_cat(age):
            """
            Categorize an individual's age into a general age group.

            Args:
                age (int or float): Age at arrival.

            Returns:
                str: One of the categories 'Child', 'YoungAdult', 'Adult', or 'Senior'.
            """
            if age < 15:
                return "Child"
            elif age < 24:
                return "YoungAdult"
            elif age < 55:
                return "Adult"
            else:
                return "Senior"

        df_rel["AgeCategory"] = df_rel["AgeAtArrival"].apply(get_age_cat)

        # === KMODES ===
        # categories
        cat_cols_rel = ["RouteCode", "Season", "AgeCategory", "Gender"]
        missing_cols = [col for col in cat_cols_rel if col not in df_rel.columns]

        if missing_cols:
            st.warning(f"WARNING: KModes clustering skipped: missing required columns: {missing_cols}")
            kmodes_ready = False
        else:
            # null check
            null_summary = df_rel[cat_cols_rel].isna().sum()
            if null_summary.sum() > 0:
                st.warning("WARNING: KModes clustering skipped: required categorical columns contain null values.")
                st.write(null_summary)
                kmodes_ready = False
            else:
                kmodes_ready = True

        # only proceed if ready
        if kmodes_ready:

            df_km_rel = df_rel[cat_cols_rel].astype(str)

            km_rel = KModes(
                n_clusters=n_clusters_rel,
                init=init_method_rel,
                n_init=5,
                verbose=0,
                random_state=42
            )

            clusters_rel = km_rel.fit_predict(df_km_rel)
            df_km_rel["Cluster"] = clusters_rel

            # cluster profiles
            cluster_profiles_rel = {}
            for cluster in sorted(df_km_rel["Cluster"].unique()):
                profile = {
                    col: df_km_rel.loc[df_km_rel["Cluster"] == cluster, col].mode()[0]
                    for col in cat_cols_rel
                }
                cluster_profiles_rel[cluster] = profile

            # heatmap plotting 
            def plot_heatmap_with_profile(df, x_col, cluster_profiles):
                """
                Generate an Altair heatmap showing the distribution of clusters across a categorical feature.

                Args:
                    df (pd.DataFrame): DataFrame containing a 'Cluster' column and the categorical feature column (x_col).
                    x_col (str): The name of the categorical column to plot on the x-axis.
                    cluster_profiles (dict): Mapping of cluster ID to dict of representative feature values.

                Returns:
                    alt.Chart: Altair chart object visualizing the count of each cluster for each x_col value with tooltips showing cluster profiles.
                
                Notes:
                    - Darker colors indicate higher counts.
                    - The tooltip displays cluster number, count, and the defining profile for the cluster.
                """ 
                heat_data = df.groupby([x_col, "Cluster"]).size().reset_index(name="Count") 
                profile_strings = [] 
                for _, row in heat_data.iterrows(): 
                    cluster = row['Cluster'] 
                    profile = cluster_profiles[cluster] 
                    other_features = [f"{k}: {v}" for k, v in profile.items() if k != x_col] 
                    profile_strings.append(", ".join(other_features)) 
                heat_data['Profile'] = profile_strings 
                
                chart = ( 
                    alt.Chart(heat_data) 
                    .mark_rect() 
                    .encode( 
                        x=alt.X(f"{x_col}:N", title=x_col), 
                        y=alt.Y("Cluster:O", title="Cluster"), 
                        color=alt.Color("Count:Q", scale=alt.Scale(scheme="blues")), 
                        tooltip=[x_col, "Cluster", "Count", "Profile"] 
                    ) 
                    .properties(width=700, height=350) 
                ) 
                return chart
            
            st.write("### Cluster vs RouteCode")
            st.altair_chart(plot_heatmap_with_profile(df_km_rel, "RouteCode", cluster_profiles_rel), width="stretch")

            st.write("### Cluster vs Season")
            st.altair_chart(plot_heatmap_with_profile(df_km_rel, "Season", cluster_profiles_rel), width="stretch")

            st.write("### Cluster vs AgeCategory")
            st.altair_chart(plot_heatmap_with_profile(df_km_rel, "AgeCategory", cluster_profiles_rel), width="stretch")

            st.write("### Cluster vs Gender")
            st.altair_chart(plot_heatmap_with_profile(df_km_rel, "Gender", cluster_profiles_rel), width="stretch")

        else:
            st.info("KModes clustering unavailable due to missing or invalid data.")

        st.markdown("""
        ### KModes Initialization Methods

        The KModes algorithm starts by selecting initial cluster modes (centroids), and the method used can affect cluster results:  
        • **Huang (default)**: Chooses initial modes randomly with probabilities proportional to category frequencies.  
        • Tends to favor more common categories.  
        • Fast and works well for small or moderately diverse datasets.  

        • **Cao**: Selects initial modes to be as distinct as possible using a density-based approach.  
        • Produces more spread-out starting clusters.  
        • Often results in better separation for datasets with diverse categorical values, but may be slightly slower.

        You can experiment with both methods to see how cluster assignments change in your data.
                    
        ### Interpretation of the KModes Clustering Results
                    
        The KModes algorithm groups migrants based on their most common combinations of four categorical variables:  
        •	Birthplace → DeparturePort (RouteCode)  
        •	Season of Arrival  
        •	Age Category  
        •	Gender  

        As KModes identifies common patterns rather than evaluating all possible relationships, the clusters reflect the 
        most typical combinations in the dataset.  The heatmaps visualize how strongly each cluster is associated with each 
        route, season, age category, and gender.  The dark or empty regions are also meaningful as they indicate 
        combinations that are rare or absent in the sample.

        For example, using 3 clusters:  
        •	Cluster 0 may represent a common pattern such as adult men arriving in the fall.  
        •	Cluster 1 may capture young adult women arriving in winter.  
        •	Cluster 2 may reflect young adult men arriving in spring.  
        
        These examples demonstrate how clusters summarize frequently occurring migrant profiles.
        
        ### Understanding the “Cluster vs RouteCode” Heatmap
                    
        This heatmap shows which birthplace → departure port routes are most common within each cluster, with darker cells 
        indicating routes that appear frequently within that cluster, while pale cells indicate rare or nonexistent 
        combinations.

        Hovering over a cell reveals:  
        •	The route  
        •	The cluster  
        •	The number of migrants  
        •	The cluster's defining features

        This view helps you see which routes dominate each cluster's pattern.
                    
        ### Understanding the “Cluster vs Season” Heatmap
                    
        This heatmap shows seasonal tendencies for each cluster.  A cluster with a strong seasonal preference will display a
        noticeably darker cell for that season.  
        Hover tooltips reveal how season pairs with the cluster's route, age category, and gender.
        """)
# endregion