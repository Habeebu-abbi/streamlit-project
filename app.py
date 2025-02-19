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

# User inputs Query ID
query_id = st.sidebar.number_input("Enter Metabase Query ID", min_value=1, value=3012, step=1)

# Fetch data
df = fetch_metabase_data(query_id)

if df is not None:
    st.write(f"### 🔹 Retrieved Data (Query ID: {query_id})")
    st.dataframe(df)

    # Convert columns to appropriate data types
    df['Scheduled At Time'] = pd.to_datetime(df['Scheduled At Time'], errors='coerce', format='%I:%M %p')
    df['Started At Time'] = pd.to_datetime(df['Started At Time'], errors='coerce', format='%I:%M %p')

    # Add new columns for analysis
    df['Before 09:00 AM'] = df['Scheduled At Time'].dt.hour < 9
    df['Not Started'] = df['Started At Time'].isna()

    # Filter for rows where Scheduled At Time is before 09:00 AM and not started
    df_filtered = df[df['Before 09:00 AM'] & df['Not Started']]

    st.write("### 🧹 Data Analysis: Scheduled Before 09:00 AM & Not Started")
    st.dataframe(df_filtered)

    # Bar Chart: Scheduled before 9 AM vs Not Started
    st.subheader("📊 Bar Chart: Scheduled Before 09:00 AM & Not Started")
    df_grouped = df_filtered.groupby(['Duty Type', 'Customer', 'Hub']).size().reset_index(name='Count')
    fig_bar = px.bar(
        df_grouped, 
        x='Duty Type', 
        y='Count', 
        color='Hub', 
        title="Not Started Orders Before 09:00 AM",
        text_auto=True
    )
    st.plotly_chart(fig_bar)

    # Table: Customer and Total Vehicle Count
    st.subheader("📋 Customer-wise Total Vehicle Count")
    df['Total Vehicles'] = pd.to_numeric(df['Total Vehicles'], errors='coerce')
    df_customer_vehicles = df.groupby('Customer')['Total Vehicles'].sum().reset_index()
    st.dataframe(df_customer_vehicles)

    # Bar Chart: Customer-wise Total Vehicle Count
    st.subheader("📊 Customer-wise Total Vehicle Count Graph")
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
    st.warning("⚠️ No data found. Check your Metabase Query ID.")
