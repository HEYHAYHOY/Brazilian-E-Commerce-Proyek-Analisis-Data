import pandas as pd
import matplotlib as plt
import seaborn as sns
import streamlit as st

st.set_page_config(page_title="Dashboard Produk", layout="wide")
st.title("Dashboard Penjualan Produk Di Sao Paulo")

df = pd.read_csv("dashboard/all_data.csv")

df["price"] = pd.to_numeric(df["price"], errors="coerce")
df["freight_value"] = pd.to_numeric(df["freight_value"], errors="coerce")
df["delivery_time"] = pd.to_numeric(df["delivery_time"], errors="coerce")
df["order_delivered_customer_date"] = pd.to_datetime(df["order_delivered_customer_date"], errors="coerce")
df["order_estimated_delivery_date"] = pd.to_datetime(df["order_estimated_delivery_date"], errors="coerce")

df = df.dropna(subset=["product_category_name_english"])

# Sidebar filter
kategori = st.sidebar.multiselect(
    "Pilih Kategori",
    sorted(df["product_category_name_english"].dropna().unique())
)

top_n = st.sidebar.slider("Top N Kategori", 5, 10, 10)

# Filter data
filtered_df = df.copy()
if kategori:
    filtered_df = filtered_df[filtered_df["product_category_name_english"].isin(kategori)]

# Tambahkan filter tanggal
min_date = pd.to_datetime(filtered_df["order_delivered_customer_date"].min()).date()
max_date = pd.to_datetime(filtered_df["order_delivered_customer_date"].max()).date()

start_date, end_date = st.sidebar.date_input(
    "Pilih Rentang Tanggal",
    value=(min_date, max_date)
)

filtered_df = filtered_df[
    (filtered_df["order_delivered_customer_date"].dt.date >= start_date) &
    (filtered_df["order_delivered_customer_date"].dt.date <= end_date)
]

# Buat layout kolom
col1, col2 = st.columns(2)
col3, col4 = st.columns(2)
col5, col6 = st.columns(2)

# 1. Top Kategori Produk jumlah terjual
jual = (
    filtered_df.groupby("product_category_name_english")["order_item_id"]
    .count()
    .sort_values(ascending=False)
    .head(top_n)
)

with col1:
    st.subheader("1. Top Kategori Produk Jumlah Terjual")
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.barplot(x=jual.values, y=jual.index, ax=ax)
    ax.set_xlabel("Jumlah Terjual")
    ax.set_ylabel("Kategori")
    ax.set_title("Top Kategori Produk Jumlah Terjual")
    st.pyplot(fig)

# 2. Total Revenue per Kategori
revenue = (
    filtered_df.groupby("product_category_name_english")["price"]
    .sum()
    .sort_values(ascending=False)
    .head(top_n)
)

with col2:
    st.subheader("2. Total Revenue per Kategori")
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.barplot(x=revenue.values, y=revenue.index, ax=ax)
    ax.set_xlabel("Total Revenue")
    ax.set_ylabel("Kategori")
    ax.set_title("Total Revenue per Kategori")
    st.pyplot(fig)

# 3. Freight Value Rata-rata per Kategori
freight = (
    filtered_df.groupby("product_category_name_english")["freight_value"]
    .mean()
    .sort_values(ascending=False)
    .head(top_n)
)

with col3:
    st.subheader("3. Freight Value Rata-rata per Kategori")
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.barplot(x=freight.values, y=freight.index, ax=ax)
    ax.set_xlabel("Freight Value Rata-rata")
    ax.set_ylabel("Kategori")
    ax.set_title("Freight Value Rata-rata per Kategori")
    st.pyplot(fig)

# 4. Ketepatan Waktu Pengiriman
df_time = filtered_df.dropna(subset=["order_delivered_customer_date", "order_estimated_delivery_date"]).copy()
df_time["status_waktu"] = df_time["order_delivered_customer_date"] <= df_time["order_estimated_delivery_date"]

ketepatan = df_time["status_waktu"].map({True: "Tepat Waktu", False: "Terlambat"}).value_counts()

with col4:
    st.subheader("4. Ketepatan Waktu Pengiriman")
    fig, ax = plt.subplots(figsize=(8, 6))
    sns.barplot(x=ketepatan.index, y=ketepatan.values, ax=ax)
    ax.set_xlabel("Status")
    ax.set_ylabel("Jumlah")
    ax.set_title("Ketepatan Waktu Pengiriman")
    st.pyplot(fig)

# ===== BAGIAN YANG DIPERBAIKI =====
# col5 dan col6 sekarang menggunakan filtered_df, bukan df / df_2017
st.header("Pertanyaan 2")

# Gunakan filtered_df sebagai sumber (sudah terkena filter kategori & tanggal)
summary = (
    filtered_df.groupby("product_category_name_english")
    .agg(
        unit_terjual=("order_item_id", "count"),
        omzet=("price", "sum")
    )
    .reset_index()
    .sort_values(by="omzet", ascending=False)
)

top_unit = summary.sort_values("unit_terjual", ascending=False).head(top_n)
top_revenue = summary.sort_values("omzet", ascending=False).head(top_n)

with col5:
    st.subheader("Top Kategori Berdasarkan Jumlah Unit Terjual")
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.barplot(data=top_unit, x="unit_terjual", y="product_category_name_english", ax=ax)
    ax.set_xlabel("Jumlah Unit Terjual")
    ax.set_ylabel("Kategori Produk")
    ax.set_title("Top Kategori Produk Berdasarkan Unit Terjual")
    st.pyplot(fig)

# Bar chart omzet
with col6:
    st.subheader("Top Kategori Berdasarkan Omzet")
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.barplot(data=top_revenue, x="omzet", y="product_category_name_english", ax=ax)
    ax.set_xlabel("Omzet")
    ax.set_ylabel("Kategori Produk")
    ax.set_title("Top Kategori Produk Berdasarkan Omzet")
    st.pyplot(fig)

st.subheader("Scatterplot: Unit Terjual vs Omzet")
fig, ax = plt.subplots(figsize=(10, 6))
sns.scatterplot(
    data=summary,
    x="unit_terjual",
    y="omzet",
    ax=ax
)
ax.set_xlabel("Jumlah Unit Terjual")
ax.set_ylabel("Omzet")
ax.set_title("Hubungan Unit Terjual dan Omzet per Kategori Produk")
st.pyplot(fig)

st.subheader("Tabel Ringkasan Top Kategori")
st.dataframe(summary.head(top_n))
