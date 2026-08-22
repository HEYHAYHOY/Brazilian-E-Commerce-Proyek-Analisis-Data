import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================
st.set_page_config(
    page_title="E-Commerce Analytics",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS untuk tampilan yang lebih compact
st.markdown("""
<style>
    .main {
        padding: 1rem;
    }
    .metric-box {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 8px;
        text-align: center;
    }
    .insight-box {
        background-color: #e8f4f8;
        border-left: 4px solid #1f77b4;
        padding: 12px;
        border-radius: 5px;
        margin: 8px 0;
        font-size: 13px;
    }
    h1 { margin-bottom: 10px; }
    h2 { margin: 15px 0 10px 0; font-size: 18px; }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# LOAD DATA
# ============================================================================
@st.cache_data
def load_and_prepare_data():
    """Load dan preprocessing data"""
    try:
        orders = pd.read_csv('orders.csv')
        order_items = pd.read_csv('order_items.csv')
        customers = pd.read_csv('customers.csv')
        products = pd.read_csv('products.csv')
        sellers = pd.read_csv('sellers.csv')
        
        # Konversi tipe data datetime
        date_cols = ['order_purchase_timestamp', 'order_approved_at',
                     'order_delivered_carrier_date', 'order_delivered_customer_date',
                     'order_estimated_delivery_date']
        for c in date_cols:
            orders[c] = pd.to_datetime(orders[c], errors='coerce')
        
        order_items['shipping_limit_date'] = pd.to_datetime(order_items['shipping_limit_date'])
        
        # Filter hanya delivered orders
        orders_clean = orders[orders['order_status'] == 'delivered'].copy()
        
        # Tangani missing values
        products['product_category_name'] = products['product_category_name'].fillna('unknown')
        
        # Merge semua tabel
        df = (orders_clean
            .merge(order_items, on='order_id', how='left')
            .merge(customers, on='customer_id', how='left')
            .merge(products[['product_id', 'product_category_name']],
                   on='product_id', how='left')
            .merge(sellers[['seller_id', 'seller_city', 'seller_state']],
                   on='seller_id', how='left')
        )
        
        # Feature engineering
        df['order_year'] = df['order_purchase_timestamp'].dt.year
        df['order_month'] = df['order_purchase_timestamp'].dt.month
        df['order_date'] = df['order_purchase_timestamp'].dt.date
        
        # Delivery metrics
        df['delivery_delay'] = (
            df['order_delivered_customer_date'] -
            df['order_estimated_delivery_date']
        ).dt.days
        
        df['is_on_time'] = df['delivery_delay'] <= 0
        
        df['delivery_days'] = (
            df['order_delivered_customer_date'] -
            df['order_purchase_timestamp']
        ).dt.days
        
        return df
    
    except FileNotFoundError:
        st.error("❌ File CSV tidak ditemukan!")
        return None

# Load data
df = load_and_prepare_data()

if df is not None:
    # ============================================================================
    # HEADER & FILTER
    # ============================================================================
    st.title("🛒 E-Commerce Analytics Dashboard")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        selected_years = st.multiselect("📅 Tahun", 
                                       sorted(df['order_year'].dropna().unique()),
                                       default=sorted(df['order_year'].dropna().unique()))
    with col2:
        selected_states = st.multiselect("📍 State", 
                                        sorted(df['customer_state'].dropna().unique()),
                                        default=['SP'])
    with col3:
        selected_categories = st.multiselect("📦 Kategori", 
                                            sorted(df['product_category_name'].dropna().unique()),
                                            default=sorted(df['product_category_name'].dropna().unique())[:8])
    
    # Filter data
    df_filtered = df[
        (df['order_year'].isin(selected_years)) &
        (df['customer_state'].isin(selected_states)) &
        (df['product_category_name'].isin(selected_categories))
    ].copy()
    
    st.divider()
    
    # ============================================================================
    # KEY METRICS
    # ============================================================================
    col1, col2, col3, col4, col5 = st.columns(5)
    
    total_orders = df_filtered['order_id'].nunique()
    total_revenue = df_filtered['price'].sum()
    on_time_rate = df_filtered['is_on_time'].mean() * 100
    avg_freight = df_filtered['freight_value'].mean()
    avg_delivery_days = df_filtered['delivery_days'].mean()
    
    with col1:
        st.metric("📊 Total Orders", f"{total_orders:,}")
    with col2:
        st.metric("💰 Revenue", f"R$ {total_revenue/1e6:.1f}M")
    with col3:
        st.metric("✅ On-Time Rate", f"{on_time_rate:.1f}%")
    with col4:
        st.metric("📦 Avg Freight", f"R$ {avg_freight:.0f}")
    with col5:
        st.metric("⏱️ Delivery Days", f"{avg_delivery_days:.1f}")
    
    st.divider()
    
    # ============================================================================
    # VISUALIZATIONS (2x2 Grid)
    # ============================================================================
    col1, col2 = st.columns(2)
    
    # 1. Top Categories
    with col1:
        st.subheader("📈 Top 8 Categories (Orders)")
        top_cat = df_filtered['product_category_name'].value_counts().head(8)
        fig, ax = plt.subplots(figsize=(8, 4))
        sns.barplot(y=top_cat.index, x=top_cat.values, palette='viridis', ax=ax)
        ax.set_xlabel('Orders')
        ax.set_ylabel('')
        for i, v in enumerate(top_cat.values):
            ax.text(v + 5, i, str(v), va='center', fontsize=9)
        plt.tight_layout()
        st.pyplot(fig, use_container_width=True)
    
    # 2. Revenue by Category
    with col2:
        st.subheader("💵 Revenue by Category (Top 8)")
        rev_cat = df_filtered.groupby('product_category_name')['price'].sum().sort_values(ascending=False).head(8)
        fig, ax = plt.subplots(figsize=(8, 4))
        sns.barplot(y=rev_cat.index, x=rev_cat.values, palette='coolwarm', ax=ax)
        ax.set_xlabel('Revenue (BRL)')
        ax.set_ylabel('')
        for i, v in enumerate(rev_cat.values):
            ax.text(v + 10000, i, f'R$ {v/1000:.0f}K', va='center', fontsize=9)
        plt.tight_layout()
        st.pyplot(fig, use_container_width=True)
    
    col3, col4 = st.columns(2)
    
    # 3. Delivery Performance
    with col3:
        st.subheader("⏱️ Delivery Performance by Category (Top 8)")
        on_time_cat = df_filtered.groupby('product_category_name')['is_on_time'].mean().sort_values(ascending=False).head(8)
        fig, ax = plt.subplots(figsize=(8, 4))
        colors = ['green' if x >= 0.7 else 'orange' if x >= 0.5 else 'red' for x in on_time_cat.values]
        ax.barh(range(len(on_time_cat)), on_time_cat.values * 100, color=colors)
        ax.set_yticks(range(len(on_time_cat)))
        ax.set_yticklabels(on_time_cat.index)
        ax.set_xlabel('On-Time Rate (%)')
        ax.set_xlim([0, 100])
        for i, v in enumerate(on_time_cat.values * 100):
            ax.text(v + 2, i, f'{v:.0f}%', va='center', fontsize=9)
        plt.tight_layout()
        st.pyplot(fig, use_container_width=True)
    
    # 4. Monthly Trend
    with col4:
        st.subheader("📅 Monthly Trend (Orders & Revenue)")
        monthly = (df_filtered
                  .groupby(df_filtered['order_purchase_timestamp'].dt.to_period('M'))
                  .agg({'order_id': 'nunique', 'price': 'sum'})
                  .reset_index())
        monthly.columns = ['Period', 'Orders', 'Revenue']
        monthly['Period'] = monthly['Period'].astype(str)
        
        fig, ax1 = plt.subplots(figsize=(8, 4))
        ax1.plot(range(len(monthly)), monthly['Orders'], marker='o', linewidth=2, label='Orders', color='#1f77b4')
        ax1.set_ylabel('Orders', color='#1f77b4')
        ax1.tick_params(axis='y', labelcolor='#1f77b4')
        ax1.set_xticks(range(len(monthly)))
        ax1.set_xticklabels(monthly['Period'], rotation=45, ha='right', fontsize=8)
        
        ax2 = ax1.twinx()
        ax2.plot(range(len(monthly)), monthly['Revenue'], marker='s', linewidth=2, label='Revenue', color='#ff7f0e')
        ax2.set_ylabel('Revenue (BRL)', color='#ff7f0e')
        ax2.tick_params(axis='y', labelcolor='#ff7f0e')
        
        plt.tight_layout()
        st.pyplot(fig, use_container_width=True)
    
    st.divider()
    
    # ============================================================================
    # DISTRIBUTIONS & CORRELATIONS
    # ============================================================================
    col5, col6, col7 = st.columns(3)
    
    # 5. Price Distribution
    with col5:
        st.subheader("💰 Price Distribution")
        fig, ax = plt.subplots(figsize=(7, 3.5))
        ax.hist(df_filtered['price'], bins=40, color='steelblue', edgecolor='black', alpha=0.7)
        ax.axvline(df_filtered['price'].mean(), color='red', linestyle='--', linewidth=2, label=f'Mean: R$ {df_filtered["price"].mean():.0f}')
        ax.set_xlabel('Price (BRL)')
        ax.set_ylabel('Frequency')
        ax.legend(fontsize=8)
        plt.tight_layout()
        st.pyplot(fig, use_container_width=True)
    
    # 6. Delivery Days Distribution
    with col6:
        st.subheader("⏱️ Delivery Days Distribution")
        fig, ax = plt.subplots(figsize=(7, 3.5))
        ax.hist(df_filtered['delivery_days'].dropna(), bins=40, color='lightgreen', edgecolor='black', alpha=0.7)
        ax.axvline(df_filtered['delivery_days'].mean(), color='red', linestyle='--', linewidth=2, label=f'Mean: {df_filtered["delivery_days"].mean():.1f} days')
        ax.set_xlabel('Delivery Days')
        ax.set_ylabel('Frequency')
        ax.legend(fontsize=8)
        plt.tight_layout()
        st.pyplot(fig, use_container_width=True)
    
    # 7. Correlation Matrix
    with col7:
        st.subheader("🔗 Correlation Matrix")
        corr_cols = ['price', 'freight_value', 'delivery_days', 'delivery_delay']
        corr_matrix = df_filtered[corr_cols].corr()
        
        fig, ax = plt.subplots(figsize=(7, 3.5))
        sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', center=0, fmt='.2f',
                    square=True, cbar_kws={"shrink": 0.8}, ax=ax, vmin=-1, vmax=1)
        ax.set_xticklabels(['Price', 'Freight', 'Del Days', 'Delay'], fontsize=8)
        ax.set_yticklabels(['Price', 'Freight', 'Del Days', 'Delay'], fontsize=8, rotation=0)
        plt.tight_layout()
        st.pyplot(fig, use_container_width=True)
    
    st.divider()
    
    # ============================================================================
    # INSIGHTS
    # ============================================================================
    st.subheader("💡 Key Insights")
    
    col_i1, col_i2, col_i3, col_i4 = st.columns(4)
    
    with col_i1:
        top_category = df_filtered['product_category_name'].value_counts().index[0]
        top_cat_pct = df_filtered['product_category_name'].value_counts().iloc[0] / len(df_filtered) * 100
        st.markdown(f"""
        <div class="insight-box">
        <b>🥇 Top Category</b><br>
        <b>{top_category}</b><br>
        {top_cat_pct:.1f}% of orders<br>
        R$ {df_filtered[df_filtered['product_category_name'] == top_category]['price'].sum():,.0f}
        </div>
        """, unsafe_allow_html=True)
    
    with col_i2:
        delayed_pct = (1 - df_filtered['is_on_time'].mean()) * 100
        st.markdown(f"""
        <div class="insight-box">
        <b>⏱️ Delivery Status</b><br>
        On-Time: <b>{on_time_rate:.1f}%</b><br>
        Delayed: <b>{delayed_pct:.1f}%</b><br>
        Avg Delay: {df_filtered['delivery_delay'].mean():.1f} days
        </div>
        """, unsafe_allow_html=True)
    
    with col_i3:
        price_delay_corr = df_filtered['price'].corr(df_filtered['delivery_delay'])
        st.markdown(f"""
        <div class="insight-box">
        <b>📊 Price-Delay Correlation</b><br>
        <b>{price_delay_corr:.3f}</b><br>
        {'Strong positive' if price_delay_corr > 0.3 else 'Weak' if price_delay_corr > 0 else 'Negative'}<br>
        relationship
        </div>
        """, unsafe_allow_html=True)
    
    with col_i4:
        freight_pct = (df_filtered['freight_value'].sum() / df_filtered['price'].sum() * 100)
        st.markdown(f"""
        <div class="insight-box">
        <b>📦 Freight Impact</b><br>
        {freight_pct:.2f}% of revenue<br>
        R$ {df_filtered['freight_value'].sum():,.0f} total<br>
        R$ {df_filtered['freight_value'].mean():.0f} avg
        </div>
        """, unsafe_allow_html=True)
    
    st.divider()
    
    # ============================================================================
    # DATA TABLE & DOWNLOAD
    # ============================================================================
    st.subheader("📋 Detailed Data")
    
    # Prepare display data
    display_cols = ['order_id', 'order_purchase_timestamp', 'customer_state', 
                    'product_category_name', 'price', 'freight_value', 
                    'delivery_delay', 'is_on_time', 'delivery_days']
    
    display_data = df_filtered[display_cols].copy()
    display_data['order_purchase_timestamp'] = display_data['order_purchase_timestamp'].dt.strftime('%Y-%m-%d')
    display_data['price'] = display_data['price'].apply(lambda x: f'R$ {x:,.2f}')
    display_data['freight_value'] = display_data['freight_value'].apply(lambda x: f'R$ {x:,.2f}')
    display_data['is_on_time'] = display_data['is_on_time'].apply(lambda x: '✅' if x else '❌')
    
    display_data.columns = ['Order ID', 'Date', 'State', 'Category', 'Price', 'Freight', 'Delay (days)', 'On-Time', 'Del Days']
    
    # Show table
    st.dataframe(display_data.head(20), use_container_width=True, height=300)
    
    # Download button
    csv = display_data.to_csv(index=False)
    st.download_button(
        label="📥 Download Data (CSV)",
        data=csv,
        file_name=f"ecommerce_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv"
    )
    
    st.divider()
    
    # Footer
    col_f1, col_f2, col_f3 = st.columns([2, 1, 2])
    with col_f2:
        st.caption(f"📊 Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Records: {len(df_filtered):,}")

else:
    st.error("❌ Gagal memuat data")
