import streamlit as st
import requests
import pandas as pd
import os
import plotly.express as px
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Metabase credentials
METABASE_URL = os.getenv("METABASE_URL")
METABASE_USERNAME = os.getenv("METABASE_USERNAME")
METABASE_PASSWORD = os.getenv("METABASE_PASSWORD")

# Function to authenticate with Metabase
def get_metabase_session():
    login_url = f"{METABASE_URL}/api/session"
    credentials = {"username": METABASE_USERNAME, "password": METABASE_PASSWORD}
    
    try:
        response = requests.post(login_url, json=credentials)
        response.raise_for_status()
        return response.json().get("id")
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Authentication Failed! Error: {e}")
        return None

# Function to fetch data from Metabase query
def fetch_metabase_data(query_id):
    session_token = get_metabase_session()
    if not session_token:
        return None

    query_url = f"{METABASE_URL}/api/card/{query_id}/query/json"
    headers = {"X-Metabase-Session": session_token}

    try:
        response = requests.post(query_url, headers=headers)
        response.raise_for_status()
        data = response.json()
        if not data:
            st.warning("⚠️ Query returned no data.")
            return None
        return pd.DataFrame(data)  # Convert to DataFrame
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Error fetching data: {e}")
        return None

# Streamlit UI
st.title("📊 Metabase Data Viewer & Visualization")
st.sidebar.header("🔍 Query Settings")

# User inputs Query IDs
query_id_1 = st.sidebar.number_input("Enter Metabase Query ID (First Dataset)", min_value=1, value=3021, step=1)
query_id_2 = st.sidebar.number_input("Enter Metabase Query ID (Second Dataset)", min_value=1, value=3023, step=1)

# Fetch data
df_1 = fetch_metabase_data(query_id_1)
df_2 = fetch_metabase_data(query_id_2)

## ------------------- QUERY 1: VEHICLE SCHEDULE DATA -------------------
if df_1 is not None:
    st.write(f"### 🔹 Retrieved Data (Query ID: {query_id_1})")
    st.dataframe(df_1)

    # Bar Chart: Customer-wise Total Vehicle Count
    st.subheader("📊 Customer-wise Total Vehicle Count Graph")
    df_1['Total Vehicles'] = pd.to_numeric(df_1['Total Vehicles'], errors='coerce')
    df_customer_vehicles = df_1.groupby('Customer')['Total Vehicles'].sum().reset_index()
    
    fig_customer_bar = px.bar(
        df_customer_vehicles, 
        x='Customer', 
        y='Total Vehicles', 
        title="Total Vehicle Count per Customer", 
        color='Total Vehicles', 
        text_auto=True
    )
    st.plotly_chart(fig_customer_bar)
else:
    st.warning(f"⚠️ No data found for Query ID {query_id_1}.")

## ------------------- QUERY 2: TRIP DATA -------------------
if df_2 is not None:
    st.write(f"### 🚚 Trip Data from Query ID: {query_id_2}")
    st.dataframe(df_2)

    # Bar Chart: Number of Trips per Hub
    st.subheader("📊 Number of Trips per Hub")
    df_hub_trips = df_2.groupby('Hub').size().reset_index(name='Trip Count')
    fig_hub_bar = px.bar(
        df_hub_trips, 
        x='Hub', 
        y='Trip Count', 
        title="Trips per Hub", 
        color='Trip Count', 
        text_auto=True
    )
    st.plotly_chart(fig_hub_bar)

    # Count Unique Drivers and Their Trip Counts
    st.subheader("🚛 Driver-wise Trip Count")
    df_driver_trips = df_2.groupby('Driver').size().reset_index(name='Total Trips')
    st.dataframe(df_driver_trips)

    # Bar Chart: Driver-wise Trip Count
    fig_driver_bar = px.bar(
        df_driver_trips, 
        x='Driver', 
        y='Total Trips', 
        title="Trips per Driver", 
        color='Total Trips', 
        text_auto=True
    )
    st.plotly_chart(fig_driver_bar)

    # SPOC-wise Trip Count
    st.subheader("👤 SPOC-wise Trip Count")
    if 'Spoc' in df_2.columns:  # Check if Spoc column exists
        df_spoc_trips = df_2.groupby('Spoc').size().reset_index(name='Total Trips')
        st.dataframe(df_spoc_trips)

        # Bar Chart: SPOC-wise Trip Count
        fig_spoc_bar = px.bar(
            df_spoc_trips, 
            x='Spoc', 
            y='Total Trips', 
            title="Trips per SPOC", 
            color='Total Trips', 
            text_auto=True
        )
        st.plotly_chart(fig_spoc_bar)
    else:
        st.warning("⚠️ No 'Spoc' column found in the dataset.")
else:
    st.warning(f"⚠️ No data found for Query ID {query_id_2}.")
