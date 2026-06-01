"""
Online Retail — Streamlit dashboard (Business Overview + RFM).
Run: streamlit run app.py
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from data_utils import SEGMENT_RECOMMENDATIONS, load_analytics

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Online Retail Analytics",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    /* Soft aurora background */
    .stApp {
        background: linear-gradient(
            165deg,
            #eef2ff 0%,
            #f5f3ff 38%,
            #ecfeff 72%,
            #f0fdfa 100%
        ) !important;
    }
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #e0e7ff 0%, #ddd6fe 100%) !important;
        border-right: 1px solid #c7d2fe;
    }
    section[data-testid="stSidebar"] * {
        color: #312e81 !important;
    }
    section[data-testid="stSidebar"] .stRadio label {
        color: #3730a3 !important;
        font-weight: 500;
    }
    hr { border-color: #c7d2fe !important; }

    .main-header {
        font-size: 1.85rem; font-weight: 800;
        color: #4338ca !important;
        margin-bottom: 0.25rem;
    }
    .sub-header {
        color: #5b6280 !important; font-size: 0.95rem; margin-bottom: 1.25rem;
    }
    h3 {
        color: #4338ca !important;
        font-weight: 700 !important;
        padding-bottom: 0.35rem;
        border-bottom: 2px solid #c7d2fe;
    }

    /* KPI cards — alternating soft tints per column */
    div[data-testid="stMetric"] {
        padding: 1rem 1.25rem;
        border-radius: 14px;
        box-shadow: 0 4px 14px rgba(99, 102, 241, 0.12);
        border: 1px solid rgba(255, 255, 255, 0.8);
    }
    div[data-testid="column"]:nth-child(4n+1) div[data-testid="stMetric"] {
        background: linear-gradient(145deg, #ffffff 0%, #e0e7ff 100%) !important;
        border-left: 4px solid #6366f1 !important;
    }
    div[data-testid="column"]:nth-child(4n+2) div[data-testid="stMetric"] {
        background: linear-gradient(145deg, #ffffff 0%, #ccfbf1 100%) !important;
        border-left: 4px solid #14b8a6 !important;
    }
    div[data-testid="column"]:nth-child(4n+3) div[data-testid="stMetric"] {
        background: linear-gradient(145deg, #ffffff 0%, #ede9fe 100%) !important;
        border-left: 4px solid #8b5cf6 !important;
    }
    div[data-testid="column"]:nth-child(4n+4) div[data-testid="stMetric"] {
        background: linear-gradient(145deg, #ffffff 0%, #fce7f3 100%) !important;
        border-left: 4px solid #ec4899 !important;
    }
    div[data-testid="stMetric"] label {
        color: #5b6280 !important;
        font-weight: 600 !important;
    }
    div[data-testid="stMetric"] [data-testid="stMetricValue"],
    div[data-testid="stMetric"] [data-testid="stMetricValue"] > div {
        color: #1e1b4b !important;
        font-size: 1.7rem !important;
        font-weight: 700 !important;
    }
    div[data-testid="stMetric"] [data-testid="stMetricDelta"] { color: #4338ca !important; }
    div[data-testid="stMetric"] svg { fill: #6366f1 !important; }

    /* Chart panels */
    div[data-testid="stPlotlyChart"] {
        background: rgba(255, 255, 255, 0.72);
        border-radius: 14px;
        padding: 0.35rem;
        border: 1px solid #e0e7ff;
        box-shadow: 0 2px 12px rgba(99, 102, 241, 0.08);
    }

    .segment-pill {
        display: inline-block;
        padding: 0.4rem 1.1rem;
        border-radius: 999px;
        font-weight: 600;
        font-size: 0.95rem;
        margin: 0.5rem 0 1rem 0;
    }
    .rec-box {
        background: linear-gradient(135deg, #f0fdfa 0%, #eef2ff 100%);
        border-left: 4px solid #14b8a6;
        padding: 1rem 1.25rem;
        border-radius: 0 12px 12px 0;
        margin: 1rem 0;
        color: #1e1b4b !important;
        box-shadow: 0 2px 10px rgba(20, 184, 166, 0.12);
    }
    .rec-box b { color: #0f766e !important; }

    /* Inputs */
    div[data-testid="stTextInput"] input,
    div[data-baseweb="select"] > div {
        background-color: rgba(255, 255, 255, 0.85) !important;
        border-color: #c7d2fe !important;
        color: #1e1b4b !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Cohesive chart palette (indigo → teal → violet → rose)
CHART_COLORS = ["#6366f1", "#14b8a6", "#8b5cf6", "#f472b6", "#38bdf8", "#a78bfa"]
CHART_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(255,255,255,0.45)",
    font=dict(color="#475569", size=12),
    title_font=dict(size=15, color="#4338ca"),
    margin=dict(l=10, r=10, t=50, b=10),
)


def style_fig(fig):
    """Apply shared layout theme to Plotly figures."""
    fig.update_layout(**CHART_LAYOUT)
    return fig

SEGMENT_COLORS = {
    "Champions": "#16a34a",
    "Loyal Customers": "#2563eb",
    "Potential Loyalists": "#7c3aed",
    "Recent Customers": "#0891b2",
    "Promising": "#ca8a04",
    "Need Attention": "#ea580c",
    "Cant Lose Them": "#dc2626",
    "At Risk": "#e11d48",
    "Hibernating": "#64748b",
    "Lost": "#94a3b8",
    "Others": "#475569",
}


@st.cache_data(show_spinner="Loading and preparing data…")
def get_data():
    return load_analytics()


data = get_data()
clean = data["clean"]
orders = data["orders"]
rfm = data["rfm"]
returns = data["returns"]

total_revenue = clean["Revenue"].sum()
total_customers = clean["CustomerID"].nunique()
total_orders = len(orders)
overall_aov = orders["Order_Revenue"].mean()

# ── Sidebar navigation ───────────────────────────────────────────────────────
st.sidebar.markdown(
    '<p style="font-size:1.15rem;font-weight:800;color:#4338ca !important;">'
    "🛒 Retail Analytics</p>",
    unsafe_allow_html=True,
)
st.sidebar.markdown("**Navigation**")
page = st.sidebar.radio(
    "Go to",
    ["Business Overview", "Customer RFM"],
    label_visibility="collapsed",
)
st.sidebar.markdown("---")
st.sidebar.caption(
    f"Data: Dec 2010 – Dec 2011 · {len(clean):,} line items · "
    f"{total_customers:,} customers"
)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 1 — Business Overview
# ══════════════════════════════════════════════════════════════════════════════
if page == "Business Overview":
    st.markdown('<p class="main-header">Business Overview</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="sub-header">Sales performance, geography, and product insights (cleaned dataset)</p>',
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Revenue", f"£{total_revenue:,.0f}")
    c2.metric("Customers", f"{total_customers:,}")
    c3.metric("Orders", f"{total_orders:,}")
    c4.metric("Avg Order Value", f"£{overall_aov:.2f}")

    c5, c6, c7 = st.columns(3)
    c5.metric(
        "Return / credit rate (lines)",
        f"{returns['return_line_pct']}%",
        help=f"{returns['credit_lines']:,} credit-note lines of {returns['total_lines']:,} raw lines",
    )
    c6.metric("Credit orders (share)", f"{returns['credit_order_pct']}%")
    c7.metric("Units sold", f"{clean['Quantity'].sum():,.0f}")

    st.markdown("---")

    # Revenue trends
    st.subheader("Revenue & order trends")
    monthly = (
        clean.assign(YearMonth=clean["InvoiceDate"].dt.to_period("M").astype(str))
        .groupby("YearMonth", as_index=False)
        .agg(
            Revenue=("Revenue", "sum"),
            Orders=("InvoiceNo", "nunique"),
            Units=("Quantity", "sum"),
        )
    )

    col_a, col_b = st.columns(2)
    with col_a:
        fig_rev = px.bar(
            monthly,
            x="YearMonth",
            y="Revenue",
            title="Monthly revenue",
            color_discrete_sequence=[CHART_COLORS[0]],
        )
        fig_rev.update_layout(xaxis_title="", yaxis_title="Revenue (£)", height=380)
        st.plotly_chart(style_fig(fig_rev), use_container_width=True)

    with col_b:
        fig_ord = px.line(
            monthly,
            x="YearMonth",
            y="Orders",
            markers=True,
            title="Monthly orders",
            color_discrete_sequence=[CHART_COLORS[1]],
        )
        fig_ord.update_layout(xaxis_title="", yaxis_title="Orders", height=380)
        st.plotly_chart(style_fig(fig_ord), use_container_width=True)

    # Geography
    st.subheader("Geographic distribution")
    geo = (
        clean.groupby("Country", as_index=False)
        .agg(
            Revenue=("Revenue", "sum"),
            Orders=("InvoiceNo", "nunique"),
            Units=("Quantity", "sum"),
        )
        .sort_values("Revenue", ascending=False)
    )
    geo["Revenue_Pct"] = (geo["Revenue"] / geo["Revenue"].sum() * 100).round(1)

    col_g1, col_g2 = st.columns([1.2, 1])
    with col_g1:
        top_geo = geo.head(12)
        fig_geo = px.bar(
            top_geo.sort_values("Revenue"),
            y="Country",
            x="Revenue",
            orientation="h",
            title="Top 12 countries by revenue",
            color="Revenue",
            color_continuous_scale=[[0, "#e0e7ff"], [0.5, "#818cf8"], [1, "#4338ca"]],
        )
        fig_geo.update_layout(height=420, coloraxis_showscale=False)
        st.plotly_chart(style_fig(fig_geo), use_container_width=True)

    with col_g2:
        fig_pie = px.pie(
            geo.head(8),
            values="Revenue",
            names="Country",
            title="Revenue share (top 8)",
            hole=0.45,
            color_discrete_sequence=CHART_COLORS,
        )
        fig_pie.update_layout(height=420)
        fig_pie = style_fig(fig_pie)
        fig_pie.update_traces(marker=dict(line=dict(color="#eef2ff", width=2)))
        st.plotly_chart(fig_pie, use_container_width=True)

    st.subheader("Product performance")
    products = (
        clean.groupby(["StockCode", "Description"], as_index=False)
        .agg(Revenue=("Revenue", "sum"), Units=("Quantity", "sum"), Orders=("InvoiceNo", "nunique"))
        .sort_values("Revenue", ascending=False)
    )
    categories = (
        clean.groupby("Category", as_index=False)
        .agg(Revenue=("Revenue", "sum"))
        .sort_values("Revenue", ascending=False)
    )

    col_p1, col_p2 = st.columns(2)
    with col_p1:
        top_p = products.head(12).copy()
        top_p["Label"] = top_p["Description"].str.slice(0, 40)
        fig_prod = px.bar(
            top_p.sort_values("Revenue"),
            y="Label",
            x="Revenue",
            orientation="h",
            title="Top 12 products by revenue",
            color_discrete_sequence=[CHART_COLORS[2]],
        )
        fig_prod.update_layout(height=440, yaxis_title="")
        st.plotly_chart(style_fig(fig_prod), use_container_width=True)

    with col_p2:
        fig_cat = px.treemap(
            categories,
            path=["Category"],
            values="Revenue",
            title="Revenue by product category",
            color="Revenue",
            color_continuous_scale=[[0, "#ccfbf1"], [0.5, "#2dd4bf"], [1, "#0f766e"]],
        )
        fig_cat.update_layout(height=440)
        st.plotly_chart(style_fig(fig_cat), use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 2 — Customer RFM
# ══════════════════════════════════════════════════════════════════════════════
else:
    st.markdown('<p class="main-header">Customer RFM Analysis</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="sub-header">Segment lookup, profile, and personalised recommendations</p>',
        unsafe_allow_html=True,
    )

    # Segment overview row
    seg_summary = (
        rfm.groupby("Segment", observed=False)
        .agg(Customers=("CustomerID", "count"), Revenue=("Monetary", "sum"))
        .reset_index()
    )
    seg_summary = seg_summary[seg_summary["Customers"] > 0]

    col_s1, col_s2 = st.columns([1, 1])
    with col_s1:
        fig_seg = px.bar(
            seg_summary.sort_values("Revenue", ascending=True),
            y="Segment",
            x="Revenue",
            orientation="h",
            color="Segment",
            color_discrete_map=SEGMENT_COLORS,
            title="Revenue by RFM segment",
        )
        fig_seg.update_layout(showlegend=False, height=360)
        st.plotly_chart(style_fig(fig_seg), use_container_width=True)

    with col_s2:
        fig_cnt = px.pie(
            seg_summary,
            values="Customers",
            names="Segment",
            title="Customers by segment",
            color="Segment",
            color_discrete_map=SEGMENT_COLORS,
            hole=0.4,
        )
        fig_cnt.update_layout(height=360)
        st.plotly_chart(style_fig(fig_cnt), use_container_width=True)

    st.markdown("---")

    # Customer lookup
    st.subheader("Customer lookup")
    customer_options = rfm.sort_values("Monetary", ascending=False)
    id_list = customer_options["CustomerID"].astype(int).tolist()
    monetary_map = rfm.set_index("CustomerID")["Monetary"].to_dict()

    filt_col1, filt_col2 = st.columns([1, 2])
    with filt_col1:
        id_filter = st.text_input("Filter by customer ID", placeholder="e.g. 17850")
    with filt_col2:
        filtered_ids = (
            [i for i in id_list if id_filter in str(i)]
            if id_filter.strip()
            else id_list[:500]
        )

    cust_id = st.selectbox(
        "Select customer",
        options=filtered_ids if filtered_ids else id_list[:1],
        format_func=lambda x: (
            f"ID {x} · {rfm.loc[rfm['CustomerID'] == x, 'Segment'].iloc[0]} · "
            f"£{monetary_map.get(x, 0):,.0f}"
        ),
    )
    cust_id = int(cust_id)
    cust_rfm = rfm[rfm["CustomerID"] == cust_id].iloc[0]
    cust_lines = clean[clean["CustomerID"] == cust_id]
    segment = str(cust_rfm["Segment"])
    seg_color = SEGMENT_COLORS.get(segment, "#475569")

    st.markdown(
        f'<span class="segment-pill" style="background:{seg_color}22;color:{seg_color};'
        f'border:1px solid {seg_color};">{segment}</span>',
        unsafe_allow_html=True,
    )

    rec_text = SEGMENT_RECOMMENDATIONS.get(segment, SEGMENT_RECOMMENDATIONS["Others"])
    st.markdown(f'<div class="rec-box"><b>Recommendation:</b> {rec_text}</div>', unsafe_allow_html=True)

    # Profile cards
    st.subheader("Customer profile")
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Country", str(cust_rfm.get("Country", cust_lines["Country"].mode().iloc[0])))
    m2.metric("RFM score", cust_rfm["RFM_Score"])
    m3.metric("Total revenue", f"£{cust_rfm['Monetary']:,.2f}")
    m4.metric("AOV", f"£{cust_rfm['Avg_Order_Value']:,.2f}")
    m5.metric("Transactions", int(cust_rfm["Frequency"]))

    p1, p2, p3 = st.columns(3)
    p1.metric("First purchase", pd.Timestamp(cust_rfm["First_Purchase"]).strftime("%d %b %Y"))
    p2.metric("Last purchase", pd.Timestamp(cust_rfm["Last_Purchase"]).strftime("%d %b %Y"))
    p3.metric("Recency (days)", int(cust_rfm["Recency"]))

    # RFM score gauge-style
    score_cols = st.columns(3)
    for col, label, val in zip(score_cols, ["Recency", "Frequency", "Monetary"], ["R_Score", "F_Score", "M_Score"]):
        with col:
            fig_g = go.Figure(
                go.Indicator(
                    mode="gauge+number",
                    value=int(cust_rfm[val]),
                    title={"text": f"{label} score"},
                    gauge={
                        "axis": {"range": [1, 5]},
                        "bar": {"color": seg_color},
                        "steps": [
                            {"range": [1, 2], "color": "#fee2e2"},
                            {"range": [2, 4], "color": "#fef9c3"},
                            {"range": [4, 5], "color": "#dcfce7"},
                        ],
                    },
                )
            )
            fig_g.update_layout(height=200, margin=dict(l=20, r=20, t=50, b=10))
            st.plotly_chart(style_fig(fig_g), use_container_width=True)

    # Product charts
    st.subheader("Purchase behaviour")
    top_prod = (
        cust_lines.groupby(["Description"], as_index=False)["Revenue"]
        .sum()
        .sort_values("Revenue", ascending=False)
        .head(8)
    )
    cat_rev = (
        cust_lines.groupby("Category", as_index=False)["Revenue"]
        .sum()
        .sort_values("Revenue", ascending=False)
    )

    ch1, ch2 = st.columns(2)
    with ch1:
        if len(top_prod):
            fig_tp = px.bar(
                top_prod.sort_values("Revenue"),
                y="Description",
                x="Revenue",
                orientation="h",
                title="Top products purchased",
                color_discrete_sequence=[seg_color],
            )
            fig_tp.update_layout(height=360, yaxis_title="")
            st.plotly_chart(style_fig(fig_tp), use_container_width=True)
        else:
            st.info("No product history for this customer.")

    with ch2:
        if len(cat_rev):
            fig_tc = px.pie(
                cat_rev,
                values="Revenue",
                names="Category",
                title="Spend by category",
                hole=0.35,
            )
            fig_tc.update_layout(height=360)
            st.plotly_chart(style_fig(fig_tc), use_container_width=True)

    # Purchase timeline
    cust_orders = (
        cust_lines.groupby("InvoiceNo", as_index=False)
        .agg(Order_Date=("InvoiceDate", "min"), Order_Revenue=("Revenue", "sum"))
        .sort_values("Order_Date")
    )
    if len(cust_orders) > 1:
        fig_tl = px.scatter(
            cust_orders,
            x="Order_Date",
            y="Order_Revenue",
            size="Order_Revenue",
            title="Order history over time",
            color_discrete_sequence=[seg_color],
        )
        fig_tl.update_layout(height=300)
        st.plotly_chart(style_fig(fig_tl), use_container_width=True)
