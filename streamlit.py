import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# ----------------------------- PAGE CONFIG -----------------------------
st.set_page_config(
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ----------------------------- STYLES -----------------------------
st.markdown("""
    <style>    page_title="Online Shopping Analysis",

    .metric-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #4CAF50;
    }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px 8px 0 0;
        padding: 10px 16px;
    }
    </style>
""", unsafe_allow_html=True)

# ----------------------------- SAMPLE DATA GENERATOR -----------------------------
@st.cache_data
def generate_sample_data(n=1500, seed=42):
    rng = np.random.default_rng(seed)

    products = {
        "Wireless Mouse": ("Electronics", 25),
        "Bluetooth Headphones": ("Electronics", 60),
        "Smartphone Case": ("Electronics", 15),
        "Laptop Stand": ("Electronics", 35),
        "USB-C Cable": ("Electronics", 10),
        "Running Shoes": ("Footwear", 70),
        "Casual Sneakers": ("Footwear", 55),
        "Leather Sandals": ("Footwear", 40),
        "Cotton T-Shirt": ("Apparel", 20),
        "Denim Jeans": ("Apparel", 45),
        "Winter Jacket": ("Apparel", 90),
        "Yoga Mat": ("Fitness", 30),
        "Dumbbell Set": ("Fitness", 80),
        "Water Bottle": ("Fitness", 12),
        "Coffee Maker": ("Home & Kitchen", 65),
        "Non-stick Pan": ("Home & Kitchen", 28),
        "Bed Sheet Set": ("Home & Kitchen", 38),
        "Desk Lamp": ("Home & Kitchen", 22),
        "Notebook Set": ("Stationery", 8),
        "Backpack": ("Apparel", 50),
    }
    prod_names = list(products.keys())
    weights = rng.dirichlet(np.ones(len(prod_names)) * 1.5)

    start_date = datetime(2025, 1, 1)
    end_date = datetime(2025, 12, 31)
    date_range_days = (end_date - start_date).days

    customer_ids = [f"CUST{str(i).zfill(4)}" for i in range(1, 301)]

    rows = []
    for _ in range(n):
        product = rng.choice(prod_names, p=weights)
        category, base_price = products[product]
        price = round(base_price * rng.uniform(0.9, 1.15), 2)
        quantity = int(rng.choice([1, 1, 1, 2, 2, 3, 4], p=[0.35,0.2,0.15,0.15,0.07,0.05,0.03]))
        customer = rng.choice(customer_ids)
        date = start_date + timedelta(days=int(rng.integers(0, date_range_days)))
        rows.append({
            "Customer ID": customer,
            "Product": product,
            "Category": category,
            "Price": price,
            "Quantity": quantity,
            "Date": date
        })

    df = pd.DataFrame(rows)
    df["Date"] = pd.to_datetime(df["Date"])
    return df

# ----------------------------- DATA LOADING -----------------------------
def load_and_clean(df):
    df = df.copy()
    # Try to standardize column names
    col_map = {c.lower().strip(): c for c in df.columns}
    rename = {}
    for target in ["customer id", "product", "category", "price", "quantity", "date"]:
        for k in col_map:
            if target in k:
                rename[col_map[k]] = target.title().replace(" Id", " ID")
                break
    df = df.rename(columns=rename)

    required = ["Customer ID", "Product", "Price", "Quantity", "Date"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        st.error(f"Missing required columns: {missing}")
        st.stop()

    if "Category" not in df.columns:
        df["Category"] = "Uncategorized"

    df["Price"] = pd.to_numeric(df["Price"], errors="coerce")
    df["Quantity"] = pd.to_numeric(df["Quantity"], errors="coerce")
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df = df.dropna(subset=["Price", "Quantity", "Date"])
    df["Revenue"] = df["Price"] * df["Quantity"]
    df["Month"] = df["Date"].dt.to_period("M").astype(str)
    return df

# ----------------------------- SIDEBAR -----------------------------
st.sidebar.title("🛍️ Shopping Analysis")
st.sidebar.markdown("Upload your own dataset or explore using sample data.")

uploaded_file = st.sidebar.file_uploader("Upload CSV file", type=["csv"])

if uploaded_file is not None:
    raw_df = pd.read_csv(uploaded_file)
    st.sidebar.success("File uploaded successfully!")
else:
    st.sidebar.info("Using built-in sample dataset (no file uploaded).")
    raw_df = generate_sample_data()

df = load_and_clean(raw_df)

# Filters
st.sidebar.markdown("---")
st.sidebar.subheader("Filters")

min_date, max_date = df["Date"].min().date(), df["Date"].max().date()
date_range = st.sidebar.date_input("Date range", value=(min_date, max_date),
                                    min_value=min_date, max_value=max_date)

categories = sorted(df["Category"].dropna().unique().tolist())
selected_categories = st.sidebar.multiselect("Category", categories, default=categories)

if len(date_range) == 2:
    df = df[(df["Date"].dt.date >= date_range[0]) & (df["Date"].dt.date <= date_range[1])]
df = df[df["Category"].isin(selected_categories)]

if df.empty:
    st.warning("No data matches the selected filters. Please adjust filters.")
    st.stop()

# ----------------------------- HEADER -----------------------------
st.title("🛍️ Online Shopping Analysis Dashboard")
st.markdown("Analyze e-commerce purchase data: best sellers, customer spending, revenue trends, and category performance.")

# ----------------------------- KPI ROW -----------------------------
total_revenue = df["Revenue"].sum()
total_orders = len(df)
total_customers = df["Customer ID"].nunique()
avg_order_value = df["Revenue"].mean()

k1, k2, k3, k4 = st.columns(4)
k1.metric("💰 Total Revenue", f"${total_revenue:,.2f}")      #1
k2.metric("🧾 Total Orders", f"{total_orders:,}")
k3.metric("👥 Unique Customers", f"{total_customers:,}")
k4.metric("📦 Avg Order Value", f"${avg_order_value:,.2f}")  #2

st.markdown("---")

# ----------------------------- TABS -----------------------------
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🏆 Best-Selling Products",
    "👤 Customer Spending",
    "📈 Monthly Revenue",
    "🗂️ Category Analysis",
    "📋 Raw Data"
])

# --- TAB 1: BEST SELLING PRODUCTS ---
with tab1:
    st.subheader("Best-Selling Products")

    metric_choice = st.radio("Rank by:", ["Quantity Sold", "Revenue Generated"], horizontal=True)

    prod_summary = df.groupby("Product").agg(
        Quantity_Sold=("Quantity", "sum"),
        Revenue=("Revenue", "sum"),
        Orders=("Product", "count")
    ).reset_index().sort_values(
        "Quantity_Sold" if metric_choice == "Quantity Sold" else "Revenue",
        ascending=False
    )

    col1, col2 = st.columns([2, 1])
    with col1:
        top_n = st.slider("Show top N products", 5, min(20, len(prod_summary)), 10)
        sort_col = "Quantity_Sold" if metric_choice == "Quantity Sold" else "Revenue"
        fig = px.bar(
            prod_summary.head(top_n),
            x=sort_col, y="Product", orientation="h",
            color=sort_col, color_continuous_scale="Blues",
            text=sort_col
        )
        fig.update_layout(yaxis=dict(autorange="reversed"), showlegend=False)
        fig.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("**🥇 Top Product**")
        best = prod_summary.iloc[0]
        st.success(f"**{best['Product']}**\n\n"
                    f"Quantity Sold: {best['Quantity_Sold']:,.0f}\n\n"
                    f"Revenue: ${best['Revenue']:,.2f}\n\n"
                    f"Orders: {best['Orders']:,}")

    st.dataframe(prod_summary.style.format({"Revenue": "${:,.2f}"}), use_container_width=True)

# --- TAB 2: CUSTOMER SPENDING ---
with tab2:
    st.subheader("Customer Spending Analysis")

    cust_summary = df.groupby("Customer ID").agg(
        Total_Spent=("Revenue", "sum"),
        Orders=("Customer ID", "count"),
        Total_Items=("Quantity", "sum")
    ).reset_index().sort_values("Total_Spent", ascending=False)
    cust_summary["Avg_Order_Value"] = cust_summary["Total_Spent"] / cust_summary["Orders"]

    col1, col2 = st.columns(2)
    with col1:
        top_n_cust = st.slider("Show top N customers", 5, min(20, len(cust_summary)), 10)
        fig2 = px.bar(
            cust_summary.head(top_n_cust),
            x="Customer ID", y="Total_Spent",
            color="Total_Spent", color_continuous_scale="Greens",
            text="Total_Spent"
        )
        fig2.update_traces(texttemplate='$%{text:,.0f}', textposition='outside')
        fig2.update_layout(showlegend=False)
        st.plotly_chart(fig2, use_container_width=True)

    with col2:
        fig3 = px.histogram(
            cust_summary, x="Total_Spent", nbins=30,
            title="Distribution of Customer Spending",
            color_discrete_sequence=["#4CAF50"]
        )
        st.plotly_chart(fig3, use_container_width=True)

    st.markdown("**Top Customers**")
    st.dataframe(
        cust_summary.head(20).style.format({"Total_Spent": "${:,.2f}", "Avg_Order_Value": "${:,.2f}"}),
        use_container_width=True
    )

# --- TAB 3: MONTHLY REVENUE ---
with tab3:
    st.subheader("Monthly Revenue Trend")

    monthly = df.groupby("Month").agg(
        Revenue=("Revenue", "sum"),
        Orders=("Month", "count")
    ).reset_index().sort_values("Month")

    fig4 = go.Figure()
    fig4.add_trace(go.Scatter(
        x=monthly["Month"], y=monthly["Revenue"],
        mode="lines+markers", name="Revenue",
        line=dict(color="#4CAF50", width=3), fill="tozeroy"
    ))
    fig4.update_layout(title="Monthly Revenue Over Time", xaxis_title="Month", yaxis_title="Revenue ($)")
    st.plotly_chart(fig4, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        fig5 = px.bar(monthly, x="Month", y="Orders", color="Orders", color_continuous_scale="Oranges")
        fig5.update_layout(title="Monthly Order Count", showlegend=False)
        st.plotly_chart(fig5, use_container_width=True)
    with col2:
        best_month = monthly.loc[monthly["Revenue"].idxmax()]
        st.markdown("**📅 Best Month**")
        st.info(f"**{best_month['Month']}**\n\nRevenue: ${best_month['Revenue']:,.2f}\n\nOrders: {best_month['Orders']:,}")
        st.markdown("**Monthly Revenue Table**")
        st.dataframe(monthly.style.format({"Revenue": "${:,.2f}"}), use_container_width=True)

# --- TAB 4: CATEGORY ANALYSIS ---
with tab4:
    st.subheader("Category-wise Analysis")

    cat_summary = df.groupby("Category").agg(
        Revenue=("Revenue", "sum"),
        Quantity_Sold=("Quantity", "sum"),
        Orders=("Category", "count")
    ).reset_index().sort_values("Revenue", ascending=False)

    col1, col2 = st.columns(2)
    with col1:
        fig6 = px.pie(cat_summary, names="Category", values="Revenue", hole=0.4,
                       title="Revenue Share by Category")
        st.plotly_chart(fig6, use_container_width=True)
    with col2:
        fig7 = px.bar(cat_summary, x="Category", y="Quantity_Sold",
                       color="Category", title="Units Sold by Category")
        fig7.update_layout(showlegend=False)
        st.plotly_chart(fig7, use_container_width=True)

    st.markdown("**Category Summary Table**")
    st.dataframe(cat_summary.style.format({"Revenue": "${:,.2f}"}), use_container_width=True)

    st.markdown("**Category Revenue Trend Over Time**")
    cat_monthly = df.groupby(["Month", "Category"])["Revenue"].sum().reset_index()
    fig8 = px.line(cat_monthly, x="Month", y="Revenue", color="Category", markers=True)
    st.plotly_chart(fig8, use_container_width=True)

# --- TAB 5: RAW DATA ---
with tab5:
    st.subheader("Raw / Filtered Data")
    st.dataframe(df.sort_values("Date", ascending=False), use_container_width=True)
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Download filtered data as CSV", csv, "filtered_shopping_data.csv", "text/csv")

st.markdown("---")