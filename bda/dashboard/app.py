import os
from datetime import datetime, timezone

import pandas as pd
import plotly.express as px
import streamlit as st
from pymongo import MongoClient


st.set_page_config(page_title="Fraud Operations", layout="wide")
st.title("Real-Time Fraud Detection")

uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
client = MongoClient(uri, serverSelectionTimeoutMS=2000)

try:
    alerts = list(client.fraud.alerts.find({}, {"_id": 0}).sort("timestamp", -1).limit(500))
except Exception as error:
    st.warning(f"MongoDB is unavailable: {error}")
    alerts = []

if alerts:
    frame = pd.DataFrame(alerts)
else:
    frame = pd.DataFrame(columns=["risk_level", "timestamp", "merchant_id", "account_id", "amount", "risk_score"])

left, middle, right = st.columns(3)
left.metric("Suspicious", int((frame.get("risk_level") == "Suspicious").sum()) if not frame.empty else 0)
middle.metric("High Risk", int((frame.get("risk_level") == "High Risk").sum()) if not frame.empty else 0)
right.metric("Last refresh", datetime.now(timezone.utc).strftime("%H:%M:%S UTC"))

col1, col2 = st.columns(2)
with col1:
    st.subheader("Alerts by risk level")
    if not frame.empty:
        st.plotly_chart(px.histogram(frame, x="risk_level", color="risk_level"), use_container_width=True)
    else:
        st.info("Waiting for scored alerts.")
with col2:
    st.subheader("Top risky accounts")
    if not frame.empty:
        top_accounts = frame.groupby("account_id", dropna=False)["risk_score"].mean().nlargest(10).reset_index()
        st.plotly_chart(px.bar(top_accounts, x="account_id", y="risk_score"), use_container_width=True)
    else:
        st.info("Waiting for scored alerts.")

st.subheader("Latest alerts")
st.dataframe(frame, use_container_width=True)
