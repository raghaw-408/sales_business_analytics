from pathlib import Path
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="Sales Business Analytics Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------- THEME & CSS STYLING (DARK CYBER THEME) ----------------
st.markdown("""
<style>
.stApp {
    background-color: #080d18;
    color: #e5f3ff;
}
[data-testid="stSidebar"] {
    background-color: #060913;
    border-right: 1px solid #164e63;
}
[data-testid="stMetric"] {
    background: #111b2e;
    border: 1px solid #164e63;
    padding: 12px 14px;
    border-radius: 10px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.4);
}
[data-testid="stMetricLabel"] {
    color: #8ba9c7 !important;
    font-weight: 600;
    font-size: 0.8rem !important;
}
[data-testid="stMetricValue"] {
    color: #22d3ee !important;
    font-weight: 700;
    font-size: 1.35rem !important;
}
[data-testid="stMetricDelta"] {
    font-size: 0.75rem !important;
}
h1, h2, h3 {
    color: #67e8f9 !important;
}
.stDataFrame {
    border: 1px solid #164e63;
    border-radius: 8px;
}
</style>
""", unsafe_allow_html=True)

# ---------------- DATA LOADING & CACHING ----------------
BASE_DIR = Path(__file__).resolve().parent

@st.cache_data
def load_data():
    possible_paths = [
        BASE_DIR / "reports" / "sales_dashboard_data.csv",
        BASE_DIR / "sales_dashboard_data.csv",
        Path("reports/sales_dashboard_data.csv"),
        Path("sales_dashboard_data.csv")
    ]
    
    data_path = None
    for p in possible_paths:
        if p.exists():
            data_path = p
            break

    if data_path is None:
        return None

    df = pd.read_csv(data_path, low_memory=False)
    df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"], errors="coerce")
    df["Year"] = df["InvoiceDate"].dt.year
    df["Month"] = df["InvoiceDate"].dt.strftime("%b")
    df["MonthNum"] = df["InvoiceDate"].dt.month
    df["YearMonth"] = df["YearMonth"].astype(str)
    df["Revenue"] = pd.to_numeric(df["Revenue"], errors="coerce").fillna(0)
    df["Quantity"] = pd.to_numeric(df["Quantity"], errors="coerce").fillna(0)
    df["UnitPrice"] = pd.to_numeric(df["UnitPrice"], errors="coerce").fillna(0)
    df["CustomerID"] = pd.to_numeric(df["CustomerID"], errors="coerce")
    
    return df

df = load_data()

if df is None:
    st.error("⚠️ `sales_dashboard_data.csv` was not found. Please ensure your file is located inside `reports/sales_dashboard_data.csv`.")
    st.stop()

# ---------------- SIDEBAR NAVIGATION & CONTROLS ----------------
st.sidebar.markdown("### **Sales Analytics**")
st.sidebar.markdown("---")
st.sidebar.markdown("#### Navigation Menu")

nav_selection = st.sidebar.radio(
    "Go to",
    ["Overview", "Product Sales", "Geographic Sales", "Transaction Data", "Settings"],
    label_visibility="collapsed"
)

st.sidebar.markdown("---")
st.sidebar.markdown("#### Filter Controls")

available_years = sorted(df["Year"].dropna().astype(int).unique().tolist())
year_options = ["All Years"] + available_years
selected_year = st.sidebar.selectbox("Select Year Scope", year_options, index=len(year_options)-1)

# Dynamic Date Range Filter based on selected year scope
if selected_year == "All Years":
    min_d, max_d = df["InvoiceDate"].min().date(), df["InvoiceDate"].max().date()
else:
    min_d = df[df["Year"] == selected_year]["InvoiceDate"].min().date()
    max_d = df[df["Year"] == selected_year]["InvoiceDate"].max().date()

date_range = st.sidebar.date_input("Date Range Filter", value=(min_d, max_d), min_value=min_d, max_value=max_d)

st.sidebar.markdown("---")
if st.sidebar.button("🔄 Clear Cache & Reset", use_container_width=True):
    st.cache_data.clear()
    st.success("Cache cleared!")
    st.rerun()

# ---------------- FILTERING APPLICATION ----------------
if selected_year == "All Years":
    df_year = df.copy()
else:
    df_year = df[df["Year"] == selected_year].copy()

if isinstance(date_range, tuple) and len(date_range) == 2:
    start_d, end_d = date_range
    df_year = df_year[df_year["InvoiceDate"].dt.date.between(start_d, end_d)]

# ---------------- MAIN HEADER ----------------
top_col1, top_col2 = st.columns([3, 1])
with top_col1:
    st.markdown(f"## Sales Business Analytics <span style='color:#8ba9c7; font-size:1.1rem;'>| {nav_selection}</span>", unsafe_allow_html=True)
with top_col2:
    st.markdown(f"<div style='text-align: right; color: #22d3ee; font-weight: 600; padding-top: 10px;'>Scope: {selected_year}</div>", unsafe_allow_html=True)

st.markdown("---")


# =========================================================================
# 1. OVERVIEW SECTION
# =========================================================================
if nav_selection == "Overview":
    total_revenue = df_year["Revenue"].sum()
    total_orders = df_year["InvoiceNo"].nunique()
    total_units = df_year["Quantity"].sum()
    active_customers = df_year["CustomerID"].dropna().nunique()
    avg_order_value = total_revenue / total_orders if total_orders > 0 else 0

    # Calculate YoY Growth if a single discrete year is selected
    rev_delta, ord_delta = None, None
    if isinstance(selected_year, int):
        prev_year = selected_year - 1
        prev_df = df[df["Year"] == prev_year]
        if not prev_df.empty:
            prev_rev = prev_df["Revenue"].sum()
            prev_ords = prev_df["InvoiceNo"].nunique()
            rev_delta = f"{((total_revenue - prev_rev) / prev_rev) * 100:+.1f}% vs PY"
            ord_delta = f"{((total_orders - prev_ords) / prev_ords) * 100:+.1f}% vs PY"

    # Executive KPI Cards with Dynamic Deltas
    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Total Revenue", f"£{total_revenue:,.0f}", delta=rev_delta)
    k2.metric("Unique Orders", f"{total_orders:,}", delta=ord_delta)
    k3.metric("Units Sold", f"{total_units:,.0f}")
    k4.metric("Active Customers", f"{active_customers:,}")
    k5.metric("Avg. Order Value", f"£{avg_order_value:,.2f}")

    st.markdown("<br>", unsafe_allow_html=True)

    # Middle Row: Monthly Trend & Country Summary Table
    chart_col1, chart_col2 = st.columns([1.3, 1])

    with chart_col1:
        st.markdown("### Monthly Revenue Trend")
        monthly_trend = (
            df_year.groupby("YearMonth", as_index=False)["Revenue"]
            .sum()
            .sort_values("YearMonth")
        )
        
        fig_monthly = px.area(
            monthly_trend,
            x="YearMonth",
            y="Revenue",
            template="plotly_dark",
            markers=True
        )
        fig_monthly.update_traces(
            line=dict(color="#22d3ee", width=3),
            fillcolor="rgba(34, 211, 238, 0.15)",
            marker=dict(size=7, color="#22d3ee"),
            hovertemplate="<b>%{x}</b><br>Revenue: £%{y:,.2f}<extra></extra>"
        )
        fig_monthly.update_layout(
            paper_bgcolor="#080d18", plot_bgcolor="#080d18",
            margin=dict(l=10, r=10, t=20, b=10), height=320,
            xaxis=dict(showgrid=False, title="Year-Month"),
            yaxis=dict(showgrid=True, gridcolor="#164e63", title="Revenue (£)")
        )
        st.plotly_chart(fig_monthly, use_container_width=True)

    with chart_col2:
        st.markdown("### Top Countries by Sales")
        country_display = (
            df_year.groupby("Country", as_index=False)["Revenue"]
            .sum()
            .sort_values("Revenue", ascending=False)
            .head(8)
        )
        country_display["Total Revenue (£)"] = country_display["Revenue"].apply(lambda x: f"£{x:,.2f}")
        st.dataframe(country_display[["Country", "Total Revenue (£)"]], use_container_width=True, hide_index=True, height=255)
        
        # Export Button for Country Summary
        country_csv = country_display.to_csv(index=False).encode("utf-8")
        st.download_button("📥 Export Country Summary CSV", country_csv, "top_countries_summary.csv", "text/csv", use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Bottom Row: Top Products & Regional Share
    b_col1, b_col2 = st.columns(2)

    with b_col1:
        st.markdown("### Top 5 Best-Selling Products")
        top_prod = (
            df_year.groupby("Description", as_index=False)["Revenue"]
            .sum()
            .nlargest(5, "Revenue")
            .sort_values("Revenue", ascending=True)
        )
            
        fig_prod = px.bar(
            top_prod, x="Revenue", y="Description", orientation="h",
            template="plotly_dark", text_auto=".2s"
        )
        fig_prod.update_traces(
            marker_color="#14b8a6", cliponaxis=False,
            hovertemplate="<b>%{y}</b><br>Revenue: £%{x:,.2f}<extra></extra>"
        )
        fig_prod.update_layout(
            paper_bgcolor="#080d18", plot_bgcolor="#080d18", height=280,
            margin=dict(l=10, r=30, t=10, b=10),
            xaxis=dict(showgrid=True, gridcolor="#164e63"),
            yaxis=dict(showgrid=False)
        )
        st.plotly_chart(fig_prod, use_container_width=True)

    with b_col2:
        st.markdown("### Regional Sales Share (Top Markets)")
        top_markets = (
            df_year.groupby("Country", as_index=False)["Revenue"]
            .sum()
            .nlargest(6, "Revenue")
        )
        fig_donut = px.pie(
            top_markets, names="Country", values="Revenue", hole=0.6,
            template="plotly_dark", color_discrete_sequence=px.colors.qualitative.Dark24
        )
        fig_donut.update_traces(hovertemplate="<b>%{label}</b><br>Revenue: £%{value:,.2f}<br>Share: %{percent}<extra></extra>")
        fig_donut.update_layout(
            paper_bgcolor="#080d18", plot_bgcolor="#080d18", height=280,
            margin=dict(l=10, r=10, t=10, b=10), showlegend=True
        )
        st.plotly_chart(fig_donut, use_container_width=True)


# =========================================================================
# 2. PRODUCT SALES SECTION
# =========================================================================
elif nav_selection == "Product Sales":
    st.markdown("### 🛍️ Product Sales Performance")
    
    product_stats = (
        df_year.groupby("Description", as_index=False)
        .agg({"Revenue": "sum", "Quantity": "sum", "InvoiceNo": "nunique"})
        .rename(columns={"InvoiceNo": "Total Orders", "Quantity": "Units Sold"})
        .sort_values("Revenue", ascending=False)
    )

    p1, p2 = st.columns(2)
    with p1:
        st.markdown("#### Top 10 Products by Revenue")
        fig_pr = px.bar(
            product_stats.head(10).sort_values("Revenue", ascending=True),
            x="Revenue", y="Description", orientation="h", template="plotly_dark"
        )
        fig_pr.update_traces(marker_color="#22d3ee", hovertemplate="<b>%{y}</b><br>Revenue: £%{x:,.2f}<extra></extra>")
        fig_pr.update_layout(paper_bgcolor="#080d18", plot_bgcolor="#080d18", height=380)
        st.plotly_chart(fig_pr, use_container_width=True)

    with p2:
        st.markdown("#### Top 10 Products by Volume (Units Sold)")
        fig_pq = px.bar(
            product_stats.sort_values("Units Sold", ascending=False).head(10).sort_values("Units Sold", ascending=True),
            x="Units Sold", y="Description", orientation="h", template="plotly_dark"
        )
        fig_pq.update_traces(marker_color="#14b8a6", hovertemplate="<b>%{y}</b><br>Units Sold: %{x:,.0f}<extra></extra>")
        fig_pq.update_layout(paper_bgcolor="#080d18", plot_bgcolor="#080d18", height=380)
        st.plotly_chart(fig_pq, use_container_width=True)

    st.markdown("#### Complete Product Performance Catalog")
    formatted_prod = product_stats.copy()
    formatted_prod["Revenue"] = formatted_prod["Revenue"].apply(lambda x: f"£{x:,.2f}")
    formatted_prod["Units Sold"] = formatted_prod["Units Sold"].apply(lambda x: f"{x:,.0f}")
    st.dataframe(formatted_prod, use_container_width=True, hide_index=True)

    prod_csv = product_stats.to_csv(index=False).encode("utf-8")
    st.download_button("📥 Export Complete Product Catalog CSV", prod_csv, "product_performance_catalog.csv", "text/csv")


# =========================================================================
# 3. GEOGRAPHIC SALES SECTION
# =========================================================================
elif nav_selection == "Geographic Sales":
    st.markdown("### 🌍 Geographic & Country Sales Breakdown")

    country_stats = (
        df_year.groupby("Country", as_index=False)
        .agg({"Revenue": "sum", "Quantity": "sum", "InvoiceNo": "nunique", "CustomerID": "nunique"})
        .rename(columns={"InvoiceNo": "Orders", "Quantity": "Units Sold", "CustomerID": "Active Customers"})
        .sort_values("Revenue", ascending=False)
    )

    fig_geo = px.bar(
        country_stats.head(12).sort_values("Revenue", ascending=True),
        x="Revenue", y="Country", orientation="h",
        template="plotly_dark", title="Top 12 Revenue-Generating Markets", text_auto=".2s"
    )
    fig_geo.update_traces(marker_color="#22d3ee", hovertemplate="<b>%{y}</b><br>Revenue: £%{x:,.2f}<extra></extra>")
    fig_geo.update_layout(paper_bgcolor="#080d18", plot_bgcolor="#080d18", height=420)
    st.plotly_chart(fig_geo, use_container_width=True)

    st.markdown("#### Market Breakdown Summary Table")
    display_country = country_stats.copy()
    display_country["Revenue"] = display_country["Revenue"].apply(lambda x: f"£{x:,.2f}")
    display_country["Units Sold"] = display_country["Units Sold"].apply(lambda x: f"{x:,.0f}")
    st.dataframe(display_country, use_container_width=True, hide_index=True)

    geo_csv = country_stats.to_csv(index=False).encode("utf-8")
    st.download_button("📥 Export Geographic Summary CSV", geo_csv, "geographic_sales_summary.csv", "text/csv")


# =========================================================================
# 4. TRANSACTION DATA SECTION
# =========================================================================
elif nav_selection == "Transaction Data":
    st.markdown("### 📋 Filterable Sales Transaction Logs")
    
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        countries_list = sorted(df_year["Country"].dropna().unique().tolist())
        sel_countries = st.multiselect("Filter by Country", countries_list)
    with col_f2:
        search_query = st.text_input("Search Description or Stock Code", placeholder="e.g. HEART, BAG...")

    filtered_tx = df_year.copy()
    if sel_countries:
        filtered_tx = filtered_tx[filtered_tx["Country"].isin(sel_countries)]
    if search_query.strip():
        filtered_tx = filtered_tx[
            filtered_tx["Description"].str.contains(search_query, case=False, na=False) |
            filtered_tx["StockCode"].astype(str).str.contains(search_query, case=False, na=False)
        ]

    st.info(f"Showing **{min(len(filtered_tx), 1000):,}** of **{len(filtered_tx):,}** matching transaction records.")
    
    preview_df = filtered_tx.head(1000).copy()
    preview_df["Revenue"] = preview_df["Revenue"].apply(lambda x: f"£{x:,.2f}")
    preview_df["UnitPrice"] = preview_df["UnitPrice"].apply(lambda x: f"£{x:,.2f}")
    
    st.dataframe(preview_df[["InvoiceNo", "InvoiceDate", "StockCode", "Description", "Quantity", "UnitPrice", "Revenue", "CustomerID", "Country"]], use_container_width=True, hide_index=True)

    csv_data = filtered_tx.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Download Filtered Data as CSV",
        data=csv_data,
        file_name=f"sales_transactions_export_{selected_year}.csv",
        mime="text/csv",
        use_container_width=True
    )


# =========================================================================
# 5. SETTINGS SECTION
# =========================================================================
elif nav_selection == "Settings":
    st.markdown("### ⚙️ Dashboard Configuration")
    st.success("✅ Dashboard fully polished and synchronized with your project structure.")
    
    st.write(f"**Total Transaction Records in Dataset:** {len(df):,} rows")
    st.write(f"**Date Span:** {df['InvoiceDate'].min().strftime('%d %b %Y')} to {df['InvoiceDate'].max().strftime('%d %b %Y')}")
    st.write(f"**Total Countries:** {df['Country'].nunique()}")
    
    if st.button("🔄 Reset Application Data & Cache"):
        st.cache_data.clear()
        st.success("Cache cleared. Refreshing...")
        st.rerun()

# ---------------- FOOTER ----------------
st.markdown("---")
st.caption("Retail Sales Business Analytics Dashboard • Built with Python, Pandas, Plotly & Streamlit")