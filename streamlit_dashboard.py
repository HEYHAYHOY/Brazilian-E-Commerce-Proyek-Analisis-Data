import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st

st.set_page_config(page_title="Dashboard Produk", layout="wide")
st.title("Dashboard Penjualan Produk Di Sao Paulo")

df = pd.read_csv("all_data.csv") 

df["price"] = pd.to_numeric(df["price"], errors="coerce")
df["freight_value"] = pd.to_numeric(df["freight_value"], errors="coerce")
df["delivery_time"] = pd.to_numeric(df["delivery_time"], errors="coerce")
df["order_delivered_customer_date"] = pd.to_datetime(df["order_delivered_customer_date"], errors="coerce")
df["order_estimated_delivery_date"] = pd.to_datetime(df["order_estimated_delivery_date"], errors="coerce")

df = df.dropna(subset=["product_category_name_english"])

# =====================================================
# SIDEBAR FILTERS
# =====================================================
st.sidebar.header("Filter Data")

# Filter kategori
kategori = st.sidebar.multiselect(
    "Pilih Kategori Produk",
    sorted(df["product_category_name_english"].dropna().unique()),
    help="Kosongkan untuk semua kategori"
)

# Filter top N
top_n = st.sidebar.slider("Top N Kategori", 5, 20, 15)

# Filter tanggal
min_date = pd.to_datetime(df["order_delivered_customer_date"].min()).date()
max_date = pd.to_datetime(df["order_delivered_customer_date"].max()).date()

start_date, end_date = st.sidebar.date_input(
    "Pilih Rentang Tanggal",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

# =====================================================
# APPLY FILTERS
# =====================================================
filtered_df = df.copy()

# Filter berdasarkan kategori
if kategori:
    filtered_df = filtered_df[
        filtered_df["product_category_name_english"].isin(kategori)
    ]

# Filter berdasarkan tanggal
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
    st.subheader(f"1. Top {top_n} Kategori Produk Jumlah Terjual")
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.barplot(x=jual.values, y=jual.index, ax=ax)
    ax.set_xlabel("Jumlah Terjual")
    ax.set_ylabel("Kategori")
    ax.set_title(f"Top {top_n} Kategori Produk Jumlah Terjual")
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

# Pertanyaan 2: Analisis Bivariate antara Jumlah Unit Terjual dan Omzet per Kategori
st.header("Pertanyaan 2")

#Filter Data Untuk Pertanyaan ke 2
@st.cache_data
def load_data():
    df = pd.read_csv('all_data.csv')
    return df

df = load_data()

# Konversi kolom datetime
if 'order_date' in df.columns:
    df['order_date'] = pd.to_datetime(df['order_date'])
    df['order_year'] = df['order_date'].dt.year

if 'order_delivered_customer_date' in df.columns:
    df['order_delivered_customer_date'] = pd.to_datetime(df['order_delivered_customer_date'])

# =====================================================
# APPLY FILTERS
# =====================================================
filtered_df = df.copy()

# Filter berdasarkan kategori
if kategori:
    filtered_df = filtered_df[
        filtered_df["product_category_name_english"].isin(kategori)
    ]

# Filter berdasarkan tanggal
filtered_df = filtered_df[
    (filtered_df["order_delivered_customer_date"].dt.date >= start_date) &
    (filtered_df["order_delivered_customer_date"].dt.date <= end_date)
]

# =====================================================
# DATA AGGREGATION
# =====================================================
kategori_agg = (filtered_df
    .groupby('product_category_name_english')
    .agg({
        'product_id': 'count',
        'price': 'sum',
    })
    .round(2)
)

kategori_agg.columns = ['units_sold', 'total_omzet']
kategori_agg = kategori_agg.sort_values('total_omzet', ascending=False)

# Ambil top N
top_data = kategori_agg.head(top_n).copy()

# SCATTER PLOT
# =====================================================
st.subheader(f"Unit Terjual vs Omzet (Top {top_n} Kategori)")

if len(top_data) > 0:
    fig, ax = plt.subplots(figsize=(14, 9))
    
    # Scatter plot
    scatter = ax.scatter(
        top_data['units_sold'], 
        top_data['total_omzet'],
        s=400, 
        alpha=0.7, 
        c=range(len(top_data)),
        cmap='viridis', 
        edgecolors='black', 
        linewidth=2
    )
    
    # Labels dan title
    ax.set_xlabel('Units Sold (Jumlah Produk Terjual)', 
                  fontsize=13, fontweight='bold')
    ax.set_ylabel('Total Omzet (Revenue in BRL)', 
                  fontsize=13, fontweight='bold')
    ax.set_title(
        f'Bivariate Analysis: Units Sold vs Total Omzet\n'
        f'Periode: {start_date} hingga {end_date}',
        fontsize=15, fontweight='bold', pad=20
    )
    
    # Grid
    ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.7)
    
    # Anotasi untuk setiap kategori
    for category, row in top_data.iterrows():
        ax.annotate(
            category,
            xy=(row['units_sold'], row['total_omzet']),
            xytext=(8, 8),
            textcoords='offset points',
            fontsize=9,
            alpha=0.85,
            bbox=dict(boxstyle='round,pad=0.3', 
                     facecolor='yellow', alpha=0.3),
            arrowprops=dict(arrowstyle='->', 
                           connectionstyle='arc3,rad=0',
                           lw=0.8, color='gray', alpha=0.6)
        )
    
    plt.tight_layout()
    st.pyplot(fig)
