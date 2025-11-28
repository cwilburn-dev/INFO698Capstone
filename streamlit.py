import streamlit as st
import altair as alt
import pandas as pd
import plotly.express as px
import numpy as np
import json
import time
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.cluster import KMeans
from streamlit_timeline import timeline
from textwrap import dedent

# === Landing Page Session State ===
if "show_intro" not in st.session_state:
    st.session_state.show_intro = True

def begin_analysis():
    st.session_state.show_intro = False

# === Load Data ===
@st.cache_data
def load_data():
    df = pd.read_csv("migration_analysis_ready_clean.csv")
    return df

# === Historical Counts ===
historical_counts = {
    1: 3749,
    2: 4311,
    3: 3506,
    4: 3857,
    5: 5902,
    6: 7213,
    7: 5934
}

# === Bin Labels ===
bin_labels = {
    1: "1880–1884",
    2: "1885–1889",
    3: "1890–1894",
    4: "1895–1899",
    5: "1900–1904",
    6: "1905–1909",
    7: "1910–1914"
}

historical_events = [
    {"year": 1885, "label": "U.S. Recovery Begins"},
    {"year": 1886, "label": "U.S. Recession"},
    {"year": 1887, "label": "English Disruptions"},
    {"year": 1888, "label": "Shipping Bottlenecks"}
]

# === Methods  ===
def get_sample(df, sample_per_bin=60):
    sampled_groups = []

    for bin_value, group in df.groupby("Bin"):
        if len(group) >= sample_per_bin:
            sampled_groups.append(group.sample(n=sample_per_bin, replace=False))
        else:
            sampled_groups.append(group)

    return pd.concat(sampled_groups).reset_index(drop=True)

def annotate_chart(base_chart, events):
    """
    Adds vertical event markers to an Altair chart.
    events is a list of {"year": int, "label": str}.
    """
    # staggered offsets for readability
    offsets = [ -20, -35, -50, -65, -80, -95 ]
    layers = [base_chart]

    for idx, e in enumerate(events):
        df_event = pd.DataFrame({"ArrivalYear": [e["year"]], "Event": [e["label"]]})

        # Get stagger offset based on index
        offset = offsets[idx % len(offsets)]

        # Vertical line
        rule = (
            alt.Chart(df_event)
            .mark_rule(color="red", strokeDash=[4, 4])
            .encode(
                x='ArrivalYear:O',
                tooltip=['ArrivalYear:O', 'Event:N']
            )
        )

        # Text label (staggered vertically)
        text = (
            alt.Chart(df_event)
            .mark_text(
                align="left",
                dy=offset,      # <-- staggered offset
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


# region MAIN
st.set_page_config(page_title="Transatlantic Migration Explorer (1880–1914)", layout="wide")
#st.title("Transatlantic Migration Explorer (1880–1914)")

# --- Landing Page ---
if st.session_state.show_intro:
    st.markdown("""
    # Transatlantic Migration Explorer  
    ### 1880–1914

    The late 19th through early 20th centuries marked one of the most dramatic population movements 
    in human history. Millions of Europeans left small towns, farming villages, and crowded 
    industrial cities, driven by economic hardship, land shortages, political instability, and 
    the hope of better opportunities abroad.

    Between 1871 and 1914, an estimated 30–35.5 million people departed Europe. The peak occurred 
    between 1880 and 1914, when nearly 3 million immigrants from Great Britain and more than 
    2.2 million from Ireland arrived in the United States, along with large numbers from 
    Germany, Scandinavia, Eastern Europe, and Southern Europe.

    This great wave of migration slowed abruptly with the outbreak of World War I in 1914.  In the 
    1920s, the United States Congress passed the Emergency Quota Act (1921) and the Immigration 
    Act (1924), which introduced strict immigration quotas and brought about the end of the age of 
    mass European migration.

    ---
    ### Click below to begin exploring the data.
    """)

    st.button("**Begin Analysis**", on_click=begin_analysis, type="primary")
    st.stop()   # ⛔ IMPORTANT: Prevents the rest of the app from loading


df = load_data()
df["BinLabel"] = df["Bin"].map(bin_labels)

#sampled_df = st.session_state.get("sampled_df", None)
sampled_df = get_sample(df, sample_per_bin=60)

if sampled_df is not None:
    # clears the sample message
    msg = st.empty()
    msg.success(f"✅ Sample generated successfully ({len(sampled_df)} records).")
    time.sleep(1)
    msg.empty()
    
    st.title("Transatlantic Migration Explorer (1880–1914)")

    # --- TIMELINE ---
    year_range = st.slider("Select Year Range", 1880, 1914, (1880, 1914))

    # load json events
    events = pd.read_json("historical_events.json")
    filtered = events[(events["year"] >= year_range[0]) & (events["year"] <= year_range[1])]

    timeline_data = {
        "title": {"text": {"headline": "Historical Context", "text": "Events impacting migration"}},
        "events": [
            {
                "start_date": {"year": int(row.year)},
                "text": {"headline": row.title, "text": row.description},
                "group": row.country
            }
            for _, row in filtered.iterrows()
        ]
    }

    # Serialize to JS string safely
    timeline_json = json.dumps(timeline_data)

    # Build themed HTML
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

    window.timeline = new TL.Timeline('timeline-embed', data, {{
        theme_color: accentColor,
        hash_bookmark: false,
        initial_zoom: 3,
        start_at_end: false
    }});

    document.addEventListener("DOMContentLoaded", function() {{
        const el = document.getElementById("timeline-embed");
        el.style.backgroundColor = bgColor;
        el.style.color = textColor;
    }});
    </script>
    """

    st.components.v1.html(custom_html, height=500)


    tab1, tab2, tab3, tab4 = st.tabs(["Demographics", "Temporal Trends", "Clustering", "Sample Data"])
# endregion

    # region DEMOGRAPHICS
    with tab1:
        st.markdown("## 👥 Demographic Overview")
        st.markdown("Lorem ipsum baby.  This section contains demographic information related to emigrants that traveled the North Atlantic by way of the United Kingdom.")

        # Total Migrants
        st.subheader("Total Migrants per Year (Weighted Historical Distribution)")

        # Convert the historical counts dict into a DataFrame
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
            title="Estimated Total Migrants per Year (1880–1914)",
            labels={"BinLabel": "Year Range", "Count": "Estimated Migrant Count"}
        )
        fig_hist.update_traces(textposition="outside")
        fig_hist.update_layout(xaxis={"categoryorder": "array", "categoryarray": list(bin_labels.values())})
        st.plotly_chart(fig_hist, use_container_width=True)

        # Gender
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
            st.plotly_chart(fig_gender, use_container_width=True)
        else:
            st.warning("⚠️ 'Gender' column not found.")

        # Age
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
            st.plotly_chart(fig_age, use_container_width=True)
        else:
            st.warning("⚠️ 'AgeAtArrival' column not found.")

        # Children by Nationality
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
                st.plotly_chart(fig_children, use_container_width=True)
        else:
            st.warning("⚠️ Missing 'AgeAtArrival' or 'BirthPlace' columns.")
        # endregion

    # region TEMPORAL
    with tab2:
        st.markdown("## Temporal Migration Trends Over Time")

        if 'ArrivalYear' not in sampled_df.columns:
            st.error("❌ The dataset does not include 'ArrivalYear'. Please add it during preprocessing.")
        else:
            # Sidebar-like controls (still appear on left, but scoped to this tab)
            with st.sidebar:
                st.sidebar.title("Controls")
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
                    default=[bp for bp in ["Germany"] if bp in valid_birthplaces]
                )

                year_min = int(sampled_df['ArrivalYear'].min())
                year_max = int(sampled_df['ArrivalYear'].max())
                year_range = st.slider("Select Year Range:", year_min, year_max, (year_min, year_max))
                apply_smoothing = st.checkbox("Apply 3-Year Rolling Average", value=False)

            # Group and filter data
            df_grouped = (
                sampled_df.groupby(['ArrivalYear', 'BirthPlace'])
                .size()
                .reset_index(name='Count')
            )
            filtered = df_grouped[
                (df_grouped['BirthPlace'].isin(selected_birthplaces)) &
                (df_grouped['ArrivalYear'] >= year_range[0]) &
                (df_grouped['ArrivalYear'] <= year_range[1])
            ]

            if filtered.empty:
                st.warning("⚠️ No data available for the selected filters.")
            else:
                # Base line chart
                chart = (
                    alt.Chart(filtered)
                    .mark_line(point=True)
                    .encode(
                        x=alt.X('ArrivalYear:O', title='Year of Arrival'),
                        y=alt.Y('Count:Q', title='Number of Migrants'),
                        color=alt.Color('BirthPlace:N', title='Birthplace'),
                        tooltip=['ArrivalYear', 'BirthPlace', 'Count']
                    )
                    .properties(
                        width=700,
                        height=400,
                        title="Migration Counts by Birthplace and Year"
                    )
                    .interactive()
                )
                annotated = annotate_chart(chart, historical_events)
                st.altair_chart(annotated, use_container_width=True)

                # Optional smoothing overlay
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
                    st.altair_chart(smoothed_chart, use_container_width=True)
    # endregion

    # region CLUSTER
    with tab3:
        st.markdown("## 🔍 Cluster Analysis – Relationship Features")

        # sidebar controls for kmodes
        with st.sidebar:
            st.subheader("KModes Clustering")
            n_clusters_rel = st.slider("Number of clusters:", 2, 12, 5)
            init_method_rel = st.selectbox("Initialization method:", ["Huang", "Cao"], index=0)

        df_rel = sampled_df.copy()

        # route code: birth → departure
        df_rel["RouteCode"] = df_rel["BirthPlace"].astype(str) + " → " + df_rel["DeparturePlace"].astype(str)

        # Season
        def get_season(month_name):
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

        def get_age_cat(age):
            if age < 15:
                return "Child"
            elif age < 24:
                return "YoungAdult"
            elif age < 55:
                return "Adult"
            else:
                return "Senior"

        df_rel["AgeCategory"] = df_rel["AgeAtArrival"].apply(get_age_cat)

        # Columns for KModes
        cat_cols_rel = ["RouteCode", "Season", "AgeCategory", "Gender"]
        df_km_rel = df_rel[cat_cols_rel].dropna().astype(str)

        # Run KModes
        from kmodes.kmodes import KModes
        km_rel = KModes(n_clusters=n_clusters_rel, init=init_method_rel, n_init=5, verbose=0, random_state=42)
        clusters_rel = km_rel.fit_predict(df_km_rel)
        df_km_rel["Cluster"] = clusters_rel

        # Cluster profiles
        cluster_profiles_rel = {}
        for cluster in sorted(df_km_rel["Cluster"].unique()):
            profile = {col: df_km_rel.loc[df_km_rel["Cluster"] == cluster, col].mode()[0] for col in cat_cols_rel}
            cluster_profiles_rel[cluster] = profile

        # Heatmap plotting function
        def plot_heatmap_with_profile(df, x_col, cluster_profiles):
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
        st.altair_chart(plot_heatmap_with_profile(df_km_rel, "RouteCode", cluster_profiles_rel), use_container_width=True)

        st.write("### Cluster vs Season")
        st.altair_chart(plot_heatmap_with_profile(df_km_rel, "Season", cluster_profiles_rel), use_container_width=True)

        st.write("### Cluster vs AgeCategory")
        st.altair_chart(plot_heatmap_with_profile(df_km_rel, "AgeCategory", cluster_profiles_rel), use_container_width=True)

        st.write("### Cluster vs Gender")
        st.altair_chart(plot_heatmap_with_profile(df_km_rel, "Gender", cluster_profiles_rel), use_container_width=True)
    # endregion
    # region SAMPLE DATA
    with tab4:
        st.markdown("### Sample Data")
        st.markdown("""
        The 420 records used in this analysis were drawn from the **'New York, U.S., Arriving Passenger and Crew Lists
        (Castle Garden and Ellis Island), 1820–1957'** collection available through Ancestry.com.  Records were selected 
        using a random letter-based sampling approach, collected in batches of 140 entries, and subsequently grouped into 
        five-year migration bins to ensure balanced temporal representation across the study period.
        """    
    )
        st.markdown("In compliance with Ancestry.com's data policies, the full dataset is available upon request only.")
        st.dataframe(sampled_df.head(10))
    # endregion
else:
    st.info("👈 Select parameters and click **Generate Sample** to begin.")
