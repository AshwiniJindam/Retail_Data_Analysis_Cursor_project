"""Shared data loading, cleaning, and analytics for retail dashboards."""

from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd

DATA_FILE = Path(__file__).parent / "Online Retail.xlsx"


def load_raw() -> pd.DataFrame:
    return pd.read_excel(DATA_FILE)


def clean_sales(df: pd.DataFrame) -> pd.DataFrame:
    out = (
        df.drop_duplicates()
        .dropna(subset=["CustomerID", "Description"])
        .loc[lambda d: ~d["InvoiceNo"].astype(str).str.startswith("C")]
        .loc[lambda d: d["Quantity"] > 0]
        .loc[lambda d: d["UnitPrice"] > 0]
        .copy()
    )
    out["Revenue"] = out["Quantity"] * out["UnitPrice"]
    out["CustomerID"] = out["CustomerID"].astype("Int64")
    return out.reset_index(drop=True)


def compute_return_rate(df_raw: pd.DataFrame) -> dict:
    """Return metrics from raw data (before sales-only cleaning)."""
    inv = df_raw["InvoiceNo"].astype(str)
    credit_lines = inv.str.startswith("C").sum()
    neg_qty_lines = (df_raw["Quantity"] < 0).sum()
    total_lines = len(df_raw)
    total_orders = df_raw["InvoiceNo"].nunique()
    credit_orders = df_raw.loc[inv.str.startswith("C"), "InvoiceNo"].nunique()

    return {
        "return_line_pct": round(credit_lines / total_lines * 100, 2),
        "negative_qty_line_pct": round(neg_qty_lines / total_lines * 100, 2),
        "credit_order_pct": round(credit_orders / total_orders * 100, 2),
        "credit_lines": int(credit_lines),
        "total_lines": int(total_lines),
    }


def assign_category(description: str) -> str:
    d = str(description).upper()
    if re.search(r"POSTAGE|^POST$|MANUAL|BANK CHARGES|DOTCOM", d):
        return "Fees & Admin"
    if re.search(r"CHRISTMAS|XMAS|SNOWMAN|SANTA|ADVENT", d):
        return "Seasonal & Christmas"
    if re.search(r"BAG|SHOPPER", d) and not re.search(r"PAPER", d[:25]):
        return "Bags & Carriers"
    if re.search(r"LIGHT|CANDLE|T-LIGHT|NIGHT LIGHT|LAMP|CHILLI", d):
        return "Lighting & Candles"
    if re.search(
        r"CAKE|TIN|JAM|KITCHEN|MUG|LUNCH|PLATE|CUP|FOOD|BAKING|PANTRY|TEAPOT|CUTLERY|TEA SET|BOWL",
        d,
    ):
        return "Kitchen, Cake & Dining"
    if re.search(r"NECKLACE|BRACELET|RING|EARRING|JEWEL|BROOCH", d):
        return "Jewelry & Accessories"
    if re.search(
        r"CARD|WRAP|GIFT TAG|STATIONERY|PAPER CHAIN|PAPER CRAFT|NOTEBOOK|PEN |PAINT SET|RIBBON",
        d,
    ):
        return "Cards, Paper & Crafts"
    if re.search(r"GARDEN|PLANT|GNOME|PARASOL", d):
        return "Garden & Outdoor"
    if re.search(r"PARTY|BUNTING|BALLOON|FLAG|BUNNY|TOY|GAME|POPCORN", d):
        return "Party & Novelty"
    if re.search(
        r"DOORMAT|ORNAMENT|FRAME|CLOCK|WICKER|BOARD|CUSHION|VASE|DECORATION|HANGING|METAL SIGN|COAT RACK|SIGN",
        d,
    ):
        return "Home Decor"
    if re.search(r"BOX|STORAGE|JAR|BASKET|DRAWER", d):
        return "Storage & Organisation"
    if re.search(r"HOT WATER BOTTLE|HAND WARMER", d):
        return "Comfort & Homeware"
    if re.search(r"SOAP|BATH|COSMETIC|CREAM|TOWEL", d):
        return "Bath & Body"
    if re.search(r"CLOTH|SCARF|APRON|TEXTILE|FELT|WOOL|FAN", d):
        return "Textiles & Fabric"
    return "Other"


def assign_rfm_segment(row: pd.Series) -> str:
    r, f, m = int(row["R_Score"]), int(row["F_Score"]), int(row["M_Score"])
    if r >= 4 and f >= 4 and m >= 4:
        return "Champions"
    if r >= 3 and f >= 3 and m >= 3:
        return "Loyal Customers"
    if r >= 4 and f <= 2:
        return "Recent Customers"
    if r >= 3 and f <= 2 and m >= 3:
        return "Potential Loyalists"
    if r >= 3 and f <= 2 and m <= 2:
        return "Promising"
    if r == 3 and f <= 2:
        return "Need Attention"
    if r <= 2 and f >= 3 and m >= 3:
        return "At Risk"
    if r <= 2 and f >= 4 and m >= 4:
        return "Cant Lose Them"
    if r <= 2 and f <= 2 and m >= 3:
        return "Hibernating"
    if r <= 2 and f <= 2 and m <= 2:
        return "Lost"
    return "Others"


SEGMENT_ORDER = [
    "Champions",
    "Loyal Customers",
    "Potential Loyalists",
    "Recent Customers",
    "Promising",
    "Need Attention",
    "Cant Lose Them",
    "At Risk",
    "Hibernating",
    "Lost",
    "Others",
]

SEGMENT_RECOMMENDATIONS = {
    "Champions": "VIP rewards, early access to new products, and referral incentives.",
    "Loyal Customers": "Cross-sell hero categories (Kitchen, Home Decor, Bags) and loyalty points.",
    "Potential Loyalists": "Offer a second-purchase discount within 30–60 days.",
    "Recent Customers": "Welcome series and product recommendations based on first order.",
    "Promising": "Checkout upsells and bundles from core categories.",
    "Need Attention": "Re-engagement email highlighting bestsellers and limited-time offers.",
    "Cant Lose Them": "Personal outreach before churn; avoid mass discount blasts.",
    "At Risk": "Urgent win-back campaign — time-limited offer on favourites.",
    "Hibernating": "Seasonal reactivation email with gift-ready bundles.",
    "Lost": "Low-cost reactivation only; avoid expensive paid ads.",
    "Others": "Review purchase history and tailor offers by top category purchased.",
}


def build_rfm(df_clean: pd.DataFrame) -> pd.DataFrame:
    snapshot_date = df_clean["InvoiceDate"].max() + pd.Timedelta(days=1)
    orders = (
        df_clean.groupby(["CustomerID", "InvoiceNo"], as_index=False)
        .agg(
            Order_Date=("InvoiceDate", "max"),
            Order_Revenue=("Revenue", "sum"),
        )
    )
    rfm = (
        orders.groupby("CustomerID")
        .agg(
            Recency=("Order_Date", lambda x: (snapshot_date - x.max()).days),
            Frequency=("InvoiceNo", "nunique"),
            Monetary=("Order_Revenue", "sum"),
            First_Purchase=("Order_Date", "min"),
            Last_Purchase=("Order_Date", "max"),
        )
        .reset_index()
    )
    rfm["Avg_Order_Value"] = rfm["Monetary"] / rfm["Frequency"]

    scored = rfm.copy()
    scored["R_Score"] = pd.qcut(
        scored["Recency"], q=5, labels=[5, 4, 3, 2, 1]
    ).astype(int)
    scored["F_Score"] = pd.qcut(
        scored["Frequency"].rank(method="first"), q=5, labels=[1, 2, 3, 4, 5]
    ).astype(int)
    scored["M_Score"] = pd.qcut(
        scored["Monetary"].rank(method="first"), q=5, labels=[1, 2, 3, 4, 5]
    ).astype(int)
    scored["RFM_Score"] = (
        scored["R_Score"].astype(str)
        + scored["F_Score"].astype(str)
        + scored["M_Score"].astype(str)
    )
    scored["Segment"] = scored.apply(assign_rfm_segment, axis=1)
    scored["Segment"] = pd.Categorical(
        scored["Segment"], categories=SEGMENT_ORDER, ordered=True
    )
    return scored


def load_analytics() -> dict:
    raw = load_raw()
    clean = clean_sales(raw)
    returns = compute_return_rate(raw)
    clean["Category"] = clean["Description"].apply(assign_category)

    orders = (
        clean.groupby("InvoiceNo", as_index=False)
        .agg(
            Order_Revenue=("Revenue", "sum"),
            Order_Date=("InvoiceDate", "min"),
            CustomerID=("CustomerID", "first"),
            Country=("Country", "first"),
        )
    )

    rfm = build_rfm(clean)
    country_lookup = (
        clean.groupby("CustomerID")["Country"]
        .agg(lambda x: x.mode().iloc[0] if len(x) else "Unknown")
        .reset_index()
    )
    rfm = rfm.merge(country_lookup, on="CustomerID", how="left")

    return {
        "raw": raw,
        "clean": clean,
        "orders": orders,
        "rfm": rfm,
        "returns": returns,
    }
