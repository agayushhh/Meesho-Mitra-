import streamlit as st
import pandas as pd
import numpy as np

# ----------------------------------------------------------------------------
# PAGE CONFIG
# ----------------------------------------------------------------------------
st.set_page_config(
    page_title="Meesho Mitra",
    page_icon="🤝",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ----------------------------------------------------------------------------
# THEME / STYLE
# ----------------------------------------------------------------------------
MEESHO_PURPLE = "#6A1B4D"
MEESHO_PINK = "#E91E63"
MEESHO_ORANGE = "#FF6F00"

st.markdown(f"""
<style>
    .main-header {{
        background: linear-gradient(90deg, {MEESHO_PURPLE} 0%, {MEESHO_PINK} 100%);
        padding: 1.5rem 2rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
    }}
    .main-header h1 {{
        color: white;
        margin: 0;
        font-size: 2rem;
    }}
    .main-header p {{
        color: #f0e0ea;
        margin: 0.2rem 0 0 0;
        font-size: 0.95rem;
    }}
    .metric-card {{
        background: #FAF5F8;
        border: 1px solid #E8D5E0;
        border-radius: 10px;
        padding: 1rem 1.2rem;
        margin-bottom: 0.6rem;
    }}
    .rationale-box {{
        background: #FFF8E1;
        border-left: 4px solid {MEESHO_ORANGE};
        padding: 0.9rem 1.1rem;
        border-radius: 6px;
        margin-top: 0.6rem;
    }}
    .stButton>button {{
        background-color: {MEESHO_PURPLE};
        color: white;
        border-radius: 8px;
        font-weight: 600;
        border: none;
        padding: 0.5rem 1.5rem;
    }}
    .stButton>button:hover {{
        background-color: {MEESHO_PINK};
        color: white;
    }}
</style>
""", unsafe_allow_html=True)

# ----------------------------------------------------------------------------
# SYNTHETIC MARKET-TREND DATA (backend "market trend" knowledge base)
# In production this would be pulled from live sales/commission/creator-supply data
# ----------------------------------------------------------------------------
CATEGORY_DATA = {
    "Skincare": {
        "subcategories": ["Face Wash", "Moisturizer", "Serum", "Sunscreen", "Face Mask"],
        "base_commission": 15.0,
        "demand_index": 82,       # 0-100, current market pull
        "competition_index": 70,  # 0-100, how saturated creator promotion already is
        "avg_price": 320,
    },
    "Makeup": {
        "subcategories": ["Lipstick", "Foundation", "Kajal/Eyeliner", "Compact", "Mascara"],
        "base_commission": 14.0,
        "demand_index": 78,
        "competition_index": 75,
        "avg_price": 280,
    },
    "Haircare": {
        "subcategories": ["Shampoo", "Hair Oil", "Hair Serum", "Conditioner", "Hair Mask"],
        "base_commission": 13.0,
        "demand_index": 65,
        "competition_index": 55,
        "avg_price": 250,
    },
    "Fragrance": {
        "subcategories": ["Perfume", "Deodorant", "Body Mist"],
        "base_commission": 12.0,
        "demand_index": 55,
        "competition_index": 40,
        "avg_price": 400,
    },
    "Bath & Body": {
        "subcategories": ["Body Lotion", "Body Wash", "Soap/Bar", "Scrub"],
        "base_commission": 11.0,
        "demand_index": 60,
        "competition_index": 45,
        "avg_price": 220,
    },
    "Men's Grooming": {
        "subcategories": ["Beard Oil", "Face Wash (Men)", "Trimmer Care", "Grooming Kit"],
        "base_commission": 13.0,
        "demand_index": 70,
        "competition_index": 50,
        "avg_price": 300,
    },
}

MIN_SELLER_MARGIN_PCT = 18.0  # floor margin % seller should retain after commission + est. costs

# ----------------------------------------------------------------------------
# RECOMMENDATION ENGINE
# ----------------------------------------------------------------------------
def recommend_commission(category, price, cogs, stock_units):
    cat = CATEGORY_DATA[category]
    base = cat["base_commission"]
    demand = cat["demand_index"]
    competition = cat["competition_index"]

    # 1. Saturation adjustment — more creators already promoting this category
    #    => seller needs to pay slightly more to stand out
    saturation_adj = (competition - 50) / 50 * 2.0   # range approx -2.0 to +2.0

    # 2. Demand adjustment — high organic demand means influencers are already
    #    inclined to promote it (product "sells itself"), so slightly less
    #    commission is needed to attract interest
    demand_adj = -(demand - 50) / 50 * 1.0            # range approx -1.0 to +1.0

    # 3. Price-band adjustment — very low-priced items need a slightly higher %
    #    to make the absolute payout meaningful to a creator; premium items
    #    already yield a large absolute commission at a lower %
    if price < 200:
        price_adj = 1.5
    elif price < 500:
        price_adj = 0.5
    elif price < 1000:
        price_adj = -0.5
    else:
        price_adj = -1.5

    # 4. Inventory urgency — high stock sellers benefit from faster clearing,
    #    small nudge upward to accelerate creator interest
    if stock_units > 500:
        urgency_adj = 0.8
    elif stock_units > 150:
        urgency_adj = 0.3
    else:
        urgency_adj = 0.0

    raw_recommendation = base + saturation_adj + demand_adj + price_adj + urgency_adj

    # 5. Margin safety cap — ensure seller retains minimum margin after commission
    if cogs and cogs > 0:
        gross_margin_pct = (price - cogs) / price * 100
        max_affordable_commission = max(0, gross_margin_pct - MIN_SELLER_MARGIN_PCT)
        capped = min(raw_recommendation, max_affordable_commission) if max_affordable_commission > 0 else raw_recommendation
        margin_capped = capped < raw_recommendation
        final_commission = max(6.0, capped)  # never recommend below a sane floor
    else:
        gross_margin_pct = None
        margin_capped = False
        final_commission = max(6.0, raw_recommendation)

    final_commission = round(final_commission, 1)
    low = round(final_commission - 1.2, 1)
    high = round(final_commission + 1.2, 1)

    rationale = []
    if saturation_adj > 0.3:
        rationale.append(f"📈 **{category}** is a high-competition category on the creator side — many influencers already promote similar products, so a slightly higher commission helps your listing stand out.")
    elif saturation_adj < -0.3:
        rationale.append(f"🟢 **{category}** has lower creator saturation right now — you don't need to overpay to get noticed.")

    if demand_adj < -0.2:
        rationale.append(f"🔥 Current market demand for **{category}** is strong — creators are naturally drawn to this category, so commission can stay moderate while still attracting interest.")
    elif demand_adj > 0.2:
        rationale.append(f"📉 Demand for **{category}** is comparatively softer right now — a touch higher commission helps compensate creators for the extra selling effort.")

    if price_adj > 0:
        rationale.append(f"💰 At ₹{price:.0f}, the absolute commission payout is small — a higher percentage keeps it worthwhile for creators to feature.")
    elif price_adj < 0:
        rationale.append(f"💰 At ₹{price:.0f}, even a lower percentage translates into a solid absolute payout for creators.")

    if urgency_adj > 0:
        rationale.append(f"📦 With {stock_units} units in stock, a small commission bump can help move inventory faster through creator-driven demand.")

    if margin_capped:
        rationale.append(f"⚠️ Recommendation was capped to protect your minimum margin of {MIN_SELLER_MARGIN_PCT:.0f}% after costs — paying more than this would erode your profitability.")

    return {
        "point": final_commission,
        "low": max(6.0, low),
        "high": high,
        "rationale": rationale,
        "gross_margin_pct": gross_margin_pct,
        "demand_index": demand,
        "competition_index": competition,
    }


def interest_score(chosen_commission, recommended_point):
    """Proxy score (0-100) estimating creator interest based on how the
    seller's chosen commission compares to the data-backed recommendation."""
    diff = chosen_commission - recommended_point
    if diff >= 1:
        return min(100, 80 + diff * 4)
    elif diff >= -0.5:
        return 75
    elif diff >= -2:
        return 55
    elif diff >= -4:
        return 35
    else:
        return 15


# ----------------------------------------------------------------------------
# SESSION STATE — seeded demo listings
# ----------------------------------------------------------------------------
if "listings" not in st.session_state:
    st.session_state.listings = pd.DataFrame([
        {"Product": "Herbal Glow Face Wash 100ml", "Category": "Skincare", "Price (₹)": 249,
         "Recommended %": 16.5, "Your Commission %": 12.0, "Interest Score": 35, "Status": "Live"},
        {"Product": "MatteFinish Liquid Lipstick", "Category": "Makeup", "Price (₹)": 199,
         "Recommended %": 17.0, "Your Commission %": 17.0, "Interest Score": 75, "Status": "Live"},
        {"Product": "Onion Hair Oil 200ml", "Category": "Haircare", "Price (₹)": 299,
         "Recommended %": 12.5, "Your Commission %": 13.5, "Interest Score": 80, "Status": "Live"},
    ])

# ----------------------------------------------------------------------------
# HEADER
# ----------------------------------------------------------------------------
st.markdown("""
<div class="main-header">
    <h1>🤝 Meesho Mitra</h1>
    <p>Seller Portal · Smart Commission Recommendations for Beauty & Personal Care</p>
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### Profile")
    profile = st.radio("I am a...", ["🏪 Seller", "🎥 Influencer (coming next)"], index=0)
    st.markdown("---")
    st.markdown("### About Meesho Mitra")
    st.caption(
        "One portal, two sides. Sellers get data-backed commission guidance "
        "to attract the right influencers. Influencers discover sellers and "
        "products matched to their niche and audience — without top-down "
        "brand assignment."
    )
    st.markdown("---")
    st.caption("Demo build · Season 3 DICE Challenge · Business Track")

if profile == "🎥 Influencer (coming next)":
    st.info("👋 Influencer side is coming up next — for now, explore the Seller experience below.")
    st.stop()

# ----------------------------------------------------------------------------
# SELLER SIDE
# ----------------------------------------------------------------------------
tab1, tab2 = st.tabs(["➕ List a New Product", "📦 My Listings"])

with tab1:
    st.subheader("List a new Beauty & Personal Care product")
    st.caption("Fill in the basics — we'll recommend a commission that maximizes interest from influencers while protecting your margin.")

    col1, col2 = st.columns([1, 1])

    with col1:
        product_name = st.text_input("Product Name", placeholder="e.g. Vitamin C Brightening Serum 30ml")
        category = st.selectbox("Category", list(CATEGORY_DATA.keys()))
        subcategory = st.selectbox("Sub-category", CATEGORY_DATA[category]["subcategories"])
        price = st.number_input("Selling Price (₹)", min_value=10, max_value=10000, value=int(CATEGORY_DATA[category]["avg_price"]), step=10)

    with col2:
        cogs = st.number_input("Your Cost per Unit / COGS (₹) — optional but improves accuracy", min_value=0, max_value=10000, value=int(price * 0.55), step=10)
        stock_units = st.number_input("Stock Available (units)", min_value=1, max_value=5000, value=200, step=10)
        st.markdown("")
        st.markdown("")
        get_rec = st.button("🔍 Get Commission Recommendation", use_container_width=True)

    if get_rec:
        if not product_name:
            st.warning("Please enter a product name to continue.")
        else:
            rec = recommend_commission(category, price, cogs, stock_units)
            st.session_state["last_rec"] = rec
            st.session_state["last_product"] = {
                "name": product_name, "category": category, "price": price,
                "cogs": cogs, "stock": stock_units
            }

    if "last_rec" in st.session_state and st.session_state.get("last_product", {}).get("name") == product_name and product_name:
        rec = st.session_state["last_rec"]
        st.markdown("---")
        st.markdown("### 💡 Recommendation")

        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.metric("Recommended Commission", f"{rec['point']}%", help="Data-backed point estimate")
        with m2:
            st.metric("Suggested Range", f"{rec['low']}% – {rec['high']}%")
        with m3:
            st.metric("Category Demand", f"{rec['demand_index']}/100", delta="High" if rec['demand_index'] > 65 else "Moderate")
        with m4:
            st.metric("Creator Saturation", f"{rec['competition_index']}/100", delta="High" if rec['competition_index'] > 65 else "Moderate", delta_color="inverse")

        payout = price * rec['point'] / 100
        st.markdown(f"**Estimated payout per sale to influencer:** ₹{payout:.0f} on a ₹{price:.0f} product")
        if rec['gross_margin_pct'] is not None:
            remaining_margin = rec['gross_margin_pct'] - rec['point']
            st.markdown(f"**Your estimated margin after this commission:** ~{remaining_margin:.1f}% (before platform fees & logistics)")

        st.markdown('<div class="rationale-box">', unsafe_allow_html=True)
        st.markdown("**Why this recommendation:**")
        for r in rec["rationale"]:
            st.markdown(f"- {r}")
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("#### Set your final commission")
        chosen = st.slider(
            "Your Commission % (drag to adjust — we'll show expected influencer interest)",
            min_value=5.0, max_value=25.0, value=float(rec['point']), step=0.5
        )
        score = interest_score(chosen, rec['point'])
        score_color = "🟢" if score >= 70 else ("🟡" if score >= 40 else "🔴")
        st.markdown(f"**{score_color} Estimated Influencer Interest Score: {score:.0f}/100**")
        if chosen < rec['point'] - 2:
            st.caption("Below-market commission typically means fewer influencers pick up your product, and slower initial traction.")
        elif chosen >= rec['point']:
            st.caption("At or above the recommended level — this should attract healthy influencer interest.")

        if st.button("✅ Confirm & List Product"):
            new_row = {
                "Product": product_name, "Category": category, "Price (₹)": price,
                "Recommended %": rec['point'], "Your Commission %": chosen,
                "Interest Score": round(score), "Status": "Live"
            }
            st.session_state.listings = pd.concat(
                [st.session_state.listings, pd.DataFrame([new_row])], ignore_index=True
            )
            st.success(f"'{product_name}' listed successfully! It's now visible to influencers browsing {category}.")
            del st.session_state["last_rec"]

with tab2:
    st.subheader("My Listings")
    st.caption("Track how your commission choices compare to market recommendations, and the resulting influencer interest.")

    df = st.session_state.listings.copy()
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Interest Score": st.column_config.ProgressColumn(
                "Interest Score", min_value=0, max_value=100, format="%d"
            )
        },
    )

    st.markdown("#### Commission vs. Market Recommendation")
    chart_df = df.set_index("Product")[["Recommended %", "Your Commission %"]]
    st.bar_chart(chart_df)

    below_market = df[df["Your Commission %"] < df["Recommended %"] - 1]
    if len(below_market) > 0:
        st.warning(f"⚠️ {len(below_market)} product(s) are priced below the recommended commission and may be getting less influencer traction than they could: " + ", ".join(below_market["Product"].tolist()))
