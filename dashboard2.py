import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================
st.set_page_config(
    page_title="E-Commerce Analytics Dashboard",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        color: #1f77b4;
        font-size: 2.5rem;
        font-weight: bold;
        margin-bottom: 10px;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .insight-box {
        background-color: #e8f4f8;
        border-left: 4px solid #1f77b4;
        padding: 15px;
        border-radius: 5px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# LOAD & PREPARE DATA (Simulasi - Ganti dengan data Anda)
# ============================================================================
@st.cache_data
def load_data():
    """
    Load data dari CSV files
    Ganti path sesuai dengan lokasi file Anda
    """
    try:
        orders = pd.read_csv('orders.csv')
        order_items = pd.read_csv('order_items.csv')
        customers = pd.read_csv('customers.csv')
        products = pd.read_csv('products.csv')
        sellers = pd.read_csv('sellers.csv')
        
        return orders, order_items, customers, products, sellers
    except FileNotFoundError:
        st.error("❌ File CSV tidak ditemukan. Pastikan semua file ada di direktori yang sama.")
        return None, None, None, None, None

@st.cache_data
def prepare_data(orders, order_items, customers, products, sellers):
    """
    Data preprocessing & feature engineering
    """
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
    df_analysis = (orders_clean
        .merge(order_items, on='order_id', how='left')
        .merge(customers, on='customer_id', how='left')
        .merge(products[['product_id', 'product_category_name']],
               on='product_id', how='left')
        .merge(sellers[['seller_id', 'seller_city', 'seller_state']],
               on='seller_id', how='left')
    )
    
    # Feature engineering
    df_analysis['order_year'] = df_analysis['order_purchase_timestamp'].dt.year
    df_analysis['order_month'] = df_analysis['order_purchase_timestamp'].dt.month
    df_analysis['order_date'] = df_analysis['order_purchase_timestamp'].dt.date
    
    # Delivery metrics
    df_analysis['delivery_delay'] = (
        df_analysis['order_delivered_customer_date'] -
        df_analysis['order_estimated_delivery_date']
    ).dt.days
    
    df_analysis['is_on_time'] = df_analysis['delivery_delay'] <= 0
    
    df_analysis['delivery_status'] = pd.cut(
        df_analysis['delivery_delay'],
        bins=[-float('inf'), 0, 7, 14, float('inf')],
        labels=['On-Time', 'Delay 1-7 hari', 'Delay 8-14 hari', 'Delay >14 hari']
    )
    
    df_analysis['delivery_days'] = (
        df_analysis['order_delivered_customer_date'] -
        df_analysis['order_purchase_timestamp']
    ).dt.days
    
    return df_analysis

# Load data
orders, order_items, customers, products, sellers = load_data()

if all([orders is not None, order_items is not None, customers is not None, 
        products is not None, sellers is not None]):
    
    df_analysis = prepare_data(orders, order_items, customers, products, sellers)
    
    # ============================================================================
    # SIDEBAR FILTERS
    # ============================================================================
    with st.sidebar:
        st.markdown("### 🔍 FILTER DATA")
        
        # Filter tahun
        available_years = sorted(df_analysis['order_year'].dropna().unique())
        selected_years = st.multiselect(
            "Pilih Tahun:",
            options=available_years,
            default=available_years
        )
        
        # Filter state
        available_states = sorted(df_analysis['customer_state'].dropna().unique())
        selected_states = st.multiselect(
            "Pilih State Pelanggan:",
            options=available_states,
            default=['SP']
        )
        
        # Filter kategori produk
        available_categories = sorted(df_analysis['product_category_name'].dropna().unique())
        selected_categories = st.multiselect(
            "Pilih Kategori Produk:",
            options=available_categories,
            default=available_categories[:10]
        )
    
    # Filter data berdasarkan sidebar
    df_filtered = df_analysis[
        (df_analysis['order_year'].isin(selected_years)) &
        (df_analysis['customer_state'].isin(selected_states)) &
        (df_analysis['product_category_name'].isin(selected_categories))
    ].copy()
    
    # ============================================================================
    # MAIN CONTENT - HEADER
    # ============================================================================
    st.markdown('<p class="main-header">🛒 E-Commerce Analytics Dashboard</p>', 
                unsafe_allow_html=True)
    st.markdown(f"**Periode:** {df_filtered['order_purchase_timestamp'].min().date()} hingga {df_filtered['order_purchase_timestamp'].max().date()}")
    st.markdown(f"**Filter:** {', '.join(selected_states)} | {len(selected_categories)} Kategori Produk | Tahun: {', '.join(map(str, selected_years))}")
    st.divider()
    
    # ============================================================================
    # SECTION 1: KEY METRICS
    # ============================================================================
    st.markdown("### 📊 Key Metrics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_orders = df_filtered['order_id'].nunique()
        st.metric(
            label="Total Orders",
            value=f"{total_orders:,}",
            delta=f"Units: {len(df_filtered):,}"
        )
    
    with col2:
        total_revenue = df_filtered['price'].sum()
        st.metric(
            label="Total Revenue",
            value=f"R$ {total_revenue:,.0f}",
            delta=f"Avg: R$ {df_filtered['price'].mean():,.0f}"
        )
    
    with col3:
        on_time_rate = df_filtered['is_on_time'].mean() * 100
        st.metric(
            label="On-Time Delivery Rate",
            value=f"{on_time_rate:.1f}%",
            delta=f"Avg Delay: {df_filtered['delivery_delay'].mean():.1f} days"
        )
    
    with col4:
        avg_freight = df_filtered['freight_value'].mean()
        st.metric(
            label="Average Freight Value",
            value=f"R$ {avg_freight:,.2f}",
            delta=f"Total: R$ {df_filtered['freight_value'].sum():,.0f}"
        )
    
    st.divider()
    
    # ============================================================================
    # SECTION 2: PRODUCT CATEGORY ANALYSIS
    # ============================================================================
    st.markdown("### 📦 Product Category Analysis")
    
    tab1, tab2, tab3 = st.tabs(["📈 Top Categories", "💰 Revenue Analysis", "⏱️ Delivery Performance"])
    
    with tab1:
        col1, col2 = st.columns(2)
        
        with col1:
            # Top kategori berdasarkan jumlah order
            top_kategori = df_filtered['product_category_name'].value_counts().head(10)
            
            fig, ax = plt.subplots(figsize=(10, 6))
            sns.barplot(y=top_kategori.index, x=top_kategori.values, palette='viridis', ax=ax)
            ax.set_title('Top 10 Kategori Produk (Jumlah Order)', fontsize=14, fontweight='bold')
            ax.set_xlabel('Jumlah Order')
            ax.set_ylabel('Kategori')
            
            for i, v in enumerate(top_kategori.values):
                ax.text(v + 5, i, str(v), va='center')
            
            plt.tight_layout()
            st.pyplot(fig)
        
        with col2:
            # Statistik kategori produk
            kategori_stats = (df_filtered
                .groupby('product_category_name')
                .agg({
                    'order_id': 'nunique',
                    'price': ['sum', 'mean'],
                    'is_on_time': 'mean'
                })
                .round(2)
            )
            
            kategori_stats.columns = ['Total Orders', 'Total Revenue', 'Avg Price', 'On-Time Rate']
            kategori_stats = kategori_stats.sort_values('Total Orders', ascending=False).head(10)
            
            st.dataframe(kategori_stats, use_container_width=True)
    
    with tab2:
        col1, col2 = st.columns(2)
        
        with col1:
            # Revenue per kategori
            revenue_kategori = df_filtered.groupby('product_category_name')['price'].sum().sort_values(ascending=False).head(10)
            
            fig, ax = plt.subplots(figsize=(10, 6))
            colors = plt.cm.RdYlGn(np.linspace(0.3, 0.7, len(revenue_kategori)))
            ax.barh(range(len(revenue_kategori)), revenue_kategori.values, color=colors)
            ax.set_yticks(range(len(revenue_kategori)))
            ax.set_yticklabels(revenue_kategori.index)
            ax.set_xlabel('Total Revenue (BRL)')
            ax.set_title('Top 10 Kategori Produk (Revenue)', fontsize=14, fontweight='bold')
            
            for i, v in enumerate(revenue_kategori.values):
                ax.text(v + 5000, i, f'R$ {v:,.0f}', va='center', fontsize=9)
            
            plt.tight_layout()
            st.pyplot(fig)
        
        with col2:
            # Pie chart - Top kategori
            top_10_revenue = df_filtered.groupby('product_category_name')['price'].sum().sort_values(ascending=False).head(10)
            other = df_filtered[~df_filtered['product_category_name'].isin(top_10_revenue.index)]['price'].sum()
            
            pie_data = pd.concat([top_10_revenue, pd.Series({'Others': other})])
            
            fig, ax = plt.subplots(figsize=(10, 8))
            colors = plt.cm.Set3(range(len(pie_data)))
            wedges, texts, autotexts = ax.pie(pie_data.values, labels=pie_data.index, autopct='%1.1f%%',
                                               startangle=90, colors=colors)
            
            for autotext in autotexts:
                autotext.set_color('black')
                autotext.set_fontsize(9)
                autotext.set_weight('bold')
            
            ax.set_title('Revenue Distribution (Top 10 + Others)', fontsize=14, fontweight='bold')
            plt.tight_layout()
            st.pyplot(fig)
    
    with tab3:
        col1, col2 = st.columns(2)
        
        with col1:
            # On-time delivery rate per kategori
            on_time_kategori = df_filtered.groupby('product_category_name')['is_on_time'].mean().sort_values(ascending=False).head(10)
            
            fig, ax = plt.subplots(figsize=(10, 6))
            colors = ['green' if x >= 0.5 else 'orange' if x >= 0.3 else 'red' for x in on_time_kategori.values]
            ax.barh(range(len(on_time_kategori)), on_time_kategori.values * 100, color=colors)
            ax.set_yticks(range(len(on_time_kategori)))
            ax.set_yticklabels(on_time_kategori.index)
            ax.set_xlabel('On-Time Rate (%)')
            ax.set_xlim([0, 100])
            ax.set_title('On-Time Delivery Rate (Top 10 Kategori)', fontsize=14, fontweight='bold')
            
            for i, v in enumerate(on_time_kategori.values * 100):
                ax.text(v + 2, i, f'{v:.1f}%', va='center', fontsize=9)
            
            plt.tight_layout()
            st.pyplot(fig)
        
        with col2:
            # Delivery status distribution
            delivery_status_counts = df_filtered['delivery_status'].value_counts()
            
            fig, ax = plt.subplots(figsize=(10, 6))
            colors_status = ['green', 'yellow', 'orange', 'red']
            bars = ax.bar(range(len(delivery_status_counts)), delivery_status_counts.values, color=colors_status[:len(delivery_status_counts)])
            ax.set_xticks(range(len(delivery_status_counts)))
            ax.set_xticklabels(delivery_status_counts.index, rotation=45, ha='right')
            ax.set_ylabel('Jumlah Order')
            ax.set_title('Delivery Status Distribution', fontsize=14, fontweight='bold')
            
            for i, v in enumerate(delivery_status_counts.values):
                ax.text(i, v + 5, str(v), ha='center', fontweight='bold')
            
            plt.tight_layout()
            st.pyplot(fig)
    
    st.divider()
    
    # ============================================================================
    # SECTION 3: TEMPORAL ANALYSIS
    # ============================================================================
    st.markdown("### 📅 Temporal Analysis")
    
    # Monthly trend
    monthly_data = (df_filtered
        .groupby(df_filtered['order_purchase_timestamp'].dt.to_period('M'))
        .agg({
            'order_id': 'nunique',
            'price': 'sum',
            'freight_value': 'mean',
            'is_on_time': 'mean',
            'delivery_days': 'mean'
        })
        .reset_index()
    )
    monthly_data.columns = ['Period', 'Orders', 'Revenue', 'Avg_Freight', 'On_Time_Rate', 'Delivery_Days']
    monthly_data['Period'] = monthly_data['Period'].astype(str)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Order & Revenue trend
        fig, ax1 = plt.subplots(figsize=(12, 5))
        
        ax1.plot(range(len(monthly_data)), monthly_data['Orders'], marker='o', linewidth=2, label='Orders', color='#1f77b4')
        ax1.set_xlabel('Bulan')
        ax1.set_ylabel('Jumlah Order', color='#1f77b4')
        ax1.tick_params(axis='y', labelcolor='#1f77b4')
        ax1.grid(True, alpha=0.3)
        
        ax2 = ax1.twinx()
        ax2.plot(range(len(monthly_data)), monthly_data['Revenue'], marker='s', linewidth=2, label='Revenue', color='#ff7f0e')
        ax2.set_ylabel('Revenue (BRL)', color='#ff7f0e')
        ax2.tick_params(axis='y', labelcolor='#ff7f0e')
        
        ax1.set_xticks(range(len(monthly_data)))
        ax1.set_xticklabels(monthly_data['Period'], rotation=45, ha='right')
        ax1.set_title('Monthly Orders & Revenue Trend', fontsize=12, fontweight='bold')
        
        fig.legend(loc='upper left', bbox_to_anchor=(0.1, 0.95))
        plt.tight_layout()
        st.pyplot(fig)
    
    with col2:
        # On-time rate & delivery days trend
        fig, ax1 = plt.subplots(figsize=(12, 5))
        
        ax1.plot(range(len(monthly_data)), monthly_data['On_Time_Rate'] * 100, marker='o', linewidth=2, label='On-Time Rate', color='green')
        ax1.set_xlabel('Bulan')
        ax1.set_ylabel('On-Time Rate (%)', color='green')
        ax1.set_ylim([0, 100])
        ax1.tick_params(axis='y', labelcolor='green')
        ax1.grid(True, alpha=0.3)
        
        ax2 = ax1.twinx()
        ax2.plot(range(len(monthly_data)), monthly_data['Delivery_Days'], marker='s', linewidth=2, label='Delivery Days', color='red')
        ax2.set_ylabel('Avg Delivery Days', color='red')
        ax2.tick_params(axis='y', labelcolor='red')
        
        ax1.set_xticks(range(len(monthly_data)))
        ax1.set_xticklabels(monthly_data['Period'], rotation=45, ha='right')
        ax1.set_title('On-Time Rate & Delivery Days Trend', fontsize=12, fontweight='bold')
        
        fig.legend(loc='upper left', bbox_to_anchor=(0.1, 0.95))
        plt.tight_layout()
        st.pyplot(fig)
    
    st.divider()
    
    # ============================================================================
    # SECTION 4: TRANSACTION ANALYSIS
    # ============================================================================
    st.markdown("### 💳 Transaction Analysis")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Price distribution
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.hist(df_filtered['price'], bins=50, color='steelblue', edgecolor='black', alpha=0.7)
        ax.set_xlabel('Price (BRL)')
        ax.set_ylabel('Frequency')
        ax.set_title('Price Distribution', fontsize=12, fontweight='bold')
        ax.axvline(df_filtered['price'].mean(), color='red', linestyle='--', linewidth=2, label=f'Mean: R$ {df_filtered["price"].mean():.2f}')
        ax.axvline(df_filtered['price'].median(), color='green', linestyle='--', linewidth=2, label=f'Median: R$ {df_filtered["price"].median():.2f}')
        ax.legend()
        plt.tight_layout()
        st.pyplot(fig)
    
    with col2:
        # Freight value distribution
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.hist(df_filtered['freight_value'], bins=50, color='coral', edgecolor='black', alpha=0.7)
        ax.set_xlabel('Freight Value (BRL)')
        ax.set_ylabel('Frequency')
        ax.set_title('Freight Value Distribution', fontsize=12, fontweight='bold')
        ax.axvline(df_filtered['freight_value'].mean(), color='red', linestyle='--', linewidth=2, label=f'Mean: R$ {df_filtered["freight_value"].mean():.2f}')
        plt.tight_layout()
        st.pyplot(fig)
    
    with col3:
        # Delivery days distribution
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.hist(df_filtered['delivery_days'].dropna(), bins=50, color='lightgreen', edgecolor='black', alpha=0.7)
        ax.set_xlabel('Delivery Days')
        ax.set_ylabel('Frequency')
        ax.set_title('Delivery Days Distribution', fontsize=12, fontweight='bold')
        ax.axvline(df_filtered['delivery_days'].mean(), color='red', linestyle='--', linewidth=2, label=f'Mean: {df_filtered["delivery_days"].mean():.1f} days')
        ax.legend()
        plt.tight_layout()
        st.pyplot(fig)
    
    st.divider()
    
    # ============================================================================
    # SECTION 5: CORRELATION ANALYSIS
    # ============================================================================
    st.markdown("### 🔗 Correlation Analysis")
    
    correlation_cols = ['price', 'freight_value', 'delivery_days', 'delivery_delay']
    correlation_data = df_filtered[correlation_cols].corr()
    
    fig, ax = plt.subplots(figsize=(8, 6))
    sns.heatmap(correlation_data, annot=True, cmap='coolwarm', center=0, fmt='.2f',
                square=True, cbar_kws={"shrink": 0.8}, ax=ax, vmin=-1, vmax=1)
    ax.set_title('Correlation Matrix - Key Variables', fontsize=14, fontweight='bold')
    plt.tight_layout()
    st.pyplot(fig)
    
    st.divider()
    
    # ============================================================================
    # SECTION 6: DETAILED DATA TABLE
    # ============================================================================
    st.markdown("### 📋 Detailed Data")
    
    # Prepare display data
    display_cols = ['order_id', 'order_purchase_timestamp', 'customer_state', 
                    'product_category_name', 'price', 'freight_value', 
                    'delivery_delay', 'is_on_time', 'delivery_days']
    
    display_data = df_filtered[display_cols].copy()
    display_data['order_purchase_timestamp'] = display_data['order_purchase_timestamp'].dt.strftime('%Y-%m-%d %H:%M')
    display_data['price'] = display_data['price'].apply(lambda x: f'R$ {x:,.2f}')
    display_data['freight_value'] = display_data['freight_value'].apply(lambda x: f'R$ {x:,.2f}')
    display_data['is_on_time'] = display_data['is_on_time'].apply(lambda x: '✅' if x else '❌')
    
    display_data.columns = ['Order ID', 'Date', 'State', 'Category', 'Price', 
                            'Freight', 'Delay (days)', 'On-Time', 'Delivery Days']
    
    st.dataframe(display_data, use_container_width=True, height=400)
    
    # Download button
    csv = display_data.to_csv(index=False)
    st.download_button(
        label="📥 Download Data as CSV",
        data=csv,
        file_name=f"ecommerce_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv"
    )
    
    st.divider()
    
    # ============================================================================
    # SECTION 7: INSIGHTS & SUMMARY
    # ============================================================================
    st.markdown("### 💡 Key Insights & Recommendations")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="insight-box">', unsafe_allow_html=True)
        
        # Insight 1
        top_category = df_filtered['product_category_name'].value_counts().index[0]
        top_cat_pct = (df_filtered['product_category_name'].value_counts().iloc[0] / len(df_filtered) * 100)
        
        st.markdown(f"""
        **📊 Top Performing Category**
        
        Kategori **{top_category}** adalah yang terbaik dengan:
        - {top_cat_pct:.1f}% dari total orders
        - Revenue: R$ {df_filtered[df_filtered['product_category_name'] == top_category]['price'].sum():,.0f}
        """)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="insight-box">', unsafe_allow_html=True)
        
        # Insight 2
        delayed_pct = (1 - df_filtered['is_on_time'].mean()) * 100
        
        st.markdown(f"""
        **⏱️ Delivery Performance**
        
        - On-Time Rate: **{on_time_rate:.1f}%**
        - Delayed Orders: **{delayed_pct:.1f}%**
        - Avg Delay: **{df_filtered['delivery_delay'].mean():.1f} days**
        """)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    col3, col4 = st.columns(2)
    
    with col3:
        st.markdown('<div class="insight-box">', unsafe_allow_html=True)
        
        # Insight 3
        price_delay_corr = df_filtered['price'].corr(df_filtered['delivery_delay'])
        
        st.markdown(f"""
        **💰 Price vs Delivery Correlation**
        
        Korelasi: **{price_delay_corr:.3f}**
        
        {'Harga lebih tinggi cenderung terlambat' if price_delay_corr > 0.1 else 'Tidak ada korelasi kuat'}
        """)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col4:
        st.markdown('<div class="insight-box">', unsafe_allow_html=True)
        
        # Insight 4
        freight_pct = (df_filtered['freight_value'].sum() / df_filtered['price'].sum() * 100)
        
        st.markdown(f"""
        **📦 Freight Cost Analysis**
        
        - Freight % of Revenue: **{freight_pct:.2f}%**
        - Avg Freight: R$ **{df_filtered['freight_value'].mean():.2f}**
        - Total Freight: R$ **{df_filtered['freight_value'].sum():,.0f}**
        """)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.divider()
    
    # ============================================================================
    # FOOTER
    # ============================================================================
    st.markdown("""
    ---
    **Dashboard Information:**
    - Data terakhir diupdate: """ + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + """
    - Total records ditampilkan: """ + f"{len(df_filtered):,}" + """
    """)

else:
    st.error("❌ Tidak dapat memuat data. Silakan pastikan semua file CSV tersedia.")