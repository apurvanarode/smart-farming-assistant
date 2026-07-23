import streamlit as st
import requests
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Regional Disease Dashboard", page_icon="📍")

st.title("📍 Regional Disease Outbreak Dashboard")
st.write("Live view of crop disease detections across monitored regions.")

BACKEND_URL = "https://smart-farming-backend-vbv6.onrender.com"

try:
    response = requests.get(f"{BACKEND_URL}/regional-stats")
    response.raise_for_status()
    data = response.json()
except requests.exceptions.RequestException as e:
    st.error(f"Could not connect to backend: {e}")
    data = []

df = pd.DataFrame(data)

if not df.empty:
    st.subheader("Detection Map")
    fig_map = px.scatter_mapbox(
        df, lat="lat", lon="lon", color="disease",
        hover_name="disease",
        zoom=4, height=500,
        mapbox_style="carto-positron"
    )
    st.plotly_chart(fig_map, use_container_width=True)

    st.subheader("Detections Over Time")
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["date"] = df["timestamp"].dt.date
    trend = df.groupby(["date", "disease"]).size().reset_index(name="count")
    fig_trend = px.line(trend, x="date", y="count", color="disease", markers=True)
    st.plotly_chart(fig_trend, use_container_width=True)

    st.subheader("Most Common Diseases Detected")
    disease_counts = df["disease"].value_counts().reset_index()
    disease_counts.columns = ["disease", "count"]
    fig_bar = px.bar(disease_counts, x="disease", y="count")
    st.plotly_chart(fig_bar, use_container_width=True)

    st.subheader("Raw Detection Log")
    st.dataframe(df.sort_values("timestamp", ascending=False), use_container_width=True)
else:
    st.info("No detections logged yet. Go diagnose some leaves in the main app first!")