import numpy as np
import pandas as pd
import streamlit as st


st.set_page_config(page_title="Business Dashboard", page_icon="📊", layout="wide")


@st.cache_data
def load_data():
	dates = pd.date_range(end=pd.Timestamp.today().normalize(), periods=30)
	rng = np.random.default_rng(42)
	return pd.DataFrame(
		{
			"Date": dates,
			"Revenue": rng.integers(1800, 5200, len(dates)),
			"Orders": rng.integers(25, 95, len(dates)),
			"Visitors": rng.integers(500, 1800, len(dates)),
		}
	)


st.title("📊 Business Dashboard")
st.caption("A simple overview of business performance")
data = load_data()

with st.sidebar:
	st.header("Filters")
	start = st.date_input("Start date", data["Date"].min().date())
	end = st.date_input("End date", data["Date"].max().date())

filtered = data[(data["Date"].dt.date >= start) & (data["Date"].dt.date <= end)]

if filtered.empty:
	st.warning("No data is available for the selected date range.")
	st.stop()

revenue = filtered["Revenue"].sum()
orders = filtered["Orders"].sum()
visitors = filtered["Visitors"].sum()

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total revenue", f"${revenue:,.0f}")
col2.metric("Total orders", f"{orders:,}")
col3.metric("Visitors", f"{visitors:,}")
col4.metric("Conversion rate", f"{orders / visitors:.2%}")

st.divider()
left, right = st.columns(2)
with left:
	st.subheader("Revenue over time")
	st.line_chart(filtered.set_index("Date")["Revenue"])
with right:
	st.subheader("Orders and visitors")
	st.bar_chart(filtered.set_index("Date")[["Orders", "Visitors"]])

st.subheader("Daily performance")
st.dataframe(filtered.sort_values("Date", ascending=False), use_container_width=True, hide_index=True)
