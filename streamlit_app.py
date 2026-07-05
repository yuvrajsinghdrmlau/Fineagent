"""
streamlit_app.py
----------------
A simple demo UI for FinAgent. This is what you'll show in your
LinkedIn video / GitHub README screenshot.

Run with: streamlit run streamlit_app.py
"""

import streamlit as st
import pandas as pd

from app.db import init_db, get_all_transactions
from app.parser import load_statement
from app.agent import run_agent
from app.tools import get_spending_summary, detect_anomalies

st.set_page_config(page_title="FinAgent", page_icon="💰", layout="wide")
init_db()

st.title("💰 FinAgent — Agentic AI Finance Tracker")
st.caption("An LLM agent that plans, calls tools, and reasons over your real transaction data.")

# --- Sidebar: load data ---
with st.sidebar:
    st.header("Data")
    if st.button("Load sample statement"):
        n = load_statement("sample_data/transactions.csv")
        st.success(f"Loaded {n} transactions.")

    uploaded = st.file_uploader("Or upload your own CSV (date, description, amount)", type="csv")
    if uploaded:
        path = f"sample_data/{uploaded.name}"
        with open(path, "wb") as f:
            f.write(uploaded.getbuffer())
        n = load_statement(path)
        st.success(f"Loaded {n} transactions.")

transactions = get_all_transactions()

if not transactions:
    st.info("Load the sample statement from the sidebar to get started.")
    st.stop()

df = pd.DataFrame(transactions)

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Spending by category")
    summary = get_spending_summary()
    if summary["by_category"]:
        chart_df = pd.DataFrame(
            list(summary["by_category"].items()), columns=["Category", "Amount"]
        ).sort_values("Amount", ascending=False)
        st.bar_chart(chart_df.set_index("Category"))

    st.metric("Total Spent", f"₹{summary['total_spent']:,.0f}")
    st.metric("Total Income", f"₹{summary['total_income']:,.0f}")
    st.metric("Net", f"₹{summary['net']:,.0f}")

with col2:
    st.subheader("⚠️ Anomalies detected")
    anomalies = detect_anomalies()
    if anomalies:
        for a in anomalies:
            st.warning(
                f"**{a['description']}** on {a['date']}: ₹{a['amount']:,.0f} "
                f"is {a['pct_above_average']}% above the usual "
                f"₹{a['category_average']:,.0f} for {a['category']}."
            )
    else:
        st.write("No anomalies found.")

st.subheader("All transactions")
st.dataframe(df, use_container_width=True)

st.divider()
st.subheader("🤖 Ask FinAgent")
st.caption("Try: 'How much did I spend on food this month?' or 'Did anything unusual happen with my subscriptions?'")

question = st.text_input("Your question")
if st.button("Ask") and question:
    with st.spinner("FinAgent is reasoning through your data..."):
        answer = run_agent(question, verbose=False)
    st.success(answer)
