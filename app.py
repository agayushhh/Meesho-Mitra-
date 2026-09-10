import streamlit as st
import pandas as pd
import numpy as np
import random

# ----------------------------------------------------------------------------
# PAGE CONFIG
# ----------------------------------------------------------------------------
st.set_page_config(
    page_title="Meesho Mitra",
    page_icon="🤝",
    layout="wide",
    initial_sidebar_state="collapsed",
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
    .rationale-box {{
        background: #FFF8E1;
        border-left: 4px solid {MEESHO_ORANGE};
        padding: 0.9rem 1.1rem;
        border-radius: 6px;
        margin-top: 0.6rem;
    }}
    .idea-card {{
        background: #F5F0FF;
        border: 1px solid #DED0F0;
        border-radius: 10px;
        padding: 0.9rem 1.1rem;
        margin-bottom: 0.7rem;
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
    .role-card {{
        border: 2px solid #E8D5E0;
        border-radius: 16px;
        padding: 2.2rem 1.5rem;
        text-align: center;
        background: #FAF5F8;
        height: 100%;
    }}
    .role-card h2 {{
        color: {MEESHO_PURPLE};
    }}
</style>
""", unsafe_allow_html=True)

# ----------------------------------------------------------------------------
# SHARED DATA — categories, market trend indices
# ----------------------------------------------------------------------------
CATEGORY_DATA = {
    "Skincare": {
        "subcategories": ["Face Wash", "Moisturizer", "Serum", "Sunscreen", "Face Mask"],
        "base_commission": 15.0, "demand_index": 82, "competition_index": 70, "avg_price": 320,
    },
    "Makeup": {
        "subcategories": ["Lipstick", "Foundation", "Kajal/Eyeliner", "Compact", "Mascara"],
        "base_commission": 14.0, "demand_index": 78, "competition_index": 75, "avg_price": 280,
    },
    "Haircare": {
        "subcategories": ["Shampoo", "Hair Oil", "Hair Serum", "Conditioner", "Hair Mask"],
        "base_commission": 13.0, "demand_index": 65, "competition_index": 55, "avg_price": 250,
    },
    "Fragrance": {
        "subcategories": ["Perfume", "Deodorant", "Body Mist"],
        "base_commission": 12.0, "demand_index": 55, "competition_index": 40, "avg_price": 400,
    },
    "Bath & Body": {
        "subcategories": ["Body Lotion", "Body Wash", "Soap/Bar", "Scrub"],
        "base_commission": 11.0, "demand_index": 60, "competition_index": 45, "avg_price": 220,
    },
    "Men's Grooming": {
        "subcategories": ["Beard Oil", "Face Wash (Men)", "Trimmer Care", "Grooming Kit"],
        "base_commission": 13.0, "demand_index": 70, "competition_index": 50, "avg_price": 300,
    },
}

MIN_SELLER_MARGIN_PCT = 18.0

STATE_ZONE = {
    "Delhi": "North", "Punjab": "North", "Haryana": "North", "Uttar Pradesh": "North",
    "Uttarakhand": "North", "Rajasthan": "North", "Himachal Pradesh": "North",
    "Maharashtra": "West", "Gujarat": "West", "Goa": "West", "Madhya Pradesh": "West",
    "Karnataka": "South", "Tamil Nadu": "South", "Kerala": "South",
    "Andhra Pradesh": "South", "Telangana": "South",
    "West Bengal": "East", "Odisha": "East", "Bihar": "East", "Jharkhand": "East",
    "Assam": "Northeast", "Meghalaya": "Northeast", "Manipur": "Northeast",
}
STATES = list(STATE_ZONE.keys())
LANGUAGES = ["Hindi", "English", "Bengali", "Tamil", "Telugu", "Marathi", "Gujarati",
             "Kannada", "Malayalam", "Punjabi", "Odia", "Assamese", "Bhojpuri"]

# ----------------------------------------------------------------------------
# COMMISSION RECOMMENDATION ENGINE (seller side)
# ----------------------------------------------------------------------------
def recommend_commission(category, price, cogs, stock_units):
    cat = CATEGORY_DATA[category]
    base = cat["base_commission"]
    demand = cat["demand_index"]
    competition = cat["competition_index"]

    saturation_adj = (competition - 50) / 50 * 2.0
    demand_adj = -(demand - 50) / 50 * 1.0

    if price < 200:
        price_adj = 1.5
    elif price < 500:
        price_adj = 0.5
    elif price < 1000:
        price_adj = -0.5
    else:
        price_adj = -1.5

    if stock_units > 500:
        urgency_adj = 0.8
    elif stock_units > 150:
        urgency_adj = 0.3
    else:
        urgency_adj = 0.0

    raw_recommendation = base + saturation_adj + demand_adj + price_adj + urgency_adj

    if cogs and cogs > 0:
        gross_margin_pct = (price - cogs) / price * 100
        max_affordable_commission = max(0, gross_margin_pct - MIN_SELLER_MARGIN_PCT)
        capped = min(raw_recommendation, max_affordable_commission) if max_affordable_commission > 0 else raw_recommendation
        margin_capped = capped < raw_recommendation
        final_commission = max(6.0, capped)
    else:
        gross_margin_pct = None
        margin_capped = False
        final_commission = max(6.0, raw_recommendation)

    final_commission = round(final_commission, 1)
    low = round(final_commission - 1.2, 1)
    high = round(final_commission + 1.2, 1)

    rationale = []
    if saturation_adj > 0.3:
        rationale.append(f"📈 **{category}** is a high-competition category on the creator side — a slightly higher commission helps your listing stand out.")
    elif saturation_adj < -0.3:
        rationale.append(f"🟢 **{category}** has lower creator saturation right now — you don't need to overpay to get noticed.")
    if demand_adj < -0.2:
        rationale.append(f"🔥 Current market demand for **{category}** is strong — commission can stay moderate while still attracting interest.")
    elif demand_adj > 0.2:
        rationale.append(f"📉 Demand for **{category}** is comparatively softer — a touch higher commission compensates for extra selling effort.")
    if price_adj > 0:
        rationale.append(f"💰 At ₹{price:.0f}, a higher percentage keeps the absolute payout worthwhile for creators.")
    elif price_adj < 0:
        rationale.append(f"💰 At ₹{price:.0f}, even a lower percentage translates into a solid absolute payout.")
    if urgency_adj > 0:
        rationale.append(f"📦 With {stock_units} units in stock, a small commission bump can help move inventory faster.")
    if margin_capped:
        rationale.append(f"⚠️ Capped to protect your minimum margin of {MIN_SELLER_MARGIN_PCT:.0f}% after costs.")

    return {
        "point": final_commission, "low": max(6.0, low), "high": high,
        "rationale": rationale, "gross_margin_pct": gross_margin_pct,
        "demand_index": demand, "competition_index": competition,
    }


def interest_score(chosen_commission, recommended_point):
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
# SYNTHETIC SELLER MARKETPLACE (for influencer discovery)
# ----------------------------------------------------------------------------
def build_marketplace():
    random.seed(7)
    raw_sellers = [
        ("GlowRoots Naturals", "Skincare", "Face Wash", 249, "Rajasthan", "Jaipur", "Tier-2"),
        ("Herbivore Basics", "Skincare", "Sunscreen", 349, "Maharashtra", "Pune", "Tier-1"),
        ("PureBlend Co.", "Skincare", "Serum", 599, "Karnataka", "Bengaluru", "Tier-1"),
        ("ColorPop Studio", "Makeup", "Lipstick", 199, "Delhi", "Delhi", "Tier-1"),
        ("MatteMuse", "Makeup", "Foundation", 449, "Uttar Pradesh", "Lucknow", "Tier-2"),
        ("KajalKraft", "Makeup", "Kajal/Eyeliner", 129, "Bihar", "Patna", "Tier-2"),
        ("RootRevive", "Haircare", "Hair Oil", 279, "West Bengal", "Kolkata", "Tier-1"),
        ("SilkStrand", "Haircare", "Shampoo", 259, "Tamil Nadu", "Coimbatore", "Tier-2"),
        ("CurlCare India", "Haircare", "Hair Serum", 349, "Kerala", "Kochi", "Tier-2"),
        ("MistyTrail", "Fragrance", "Body Mist", 299, "Gujarat", "Surat", "Tier-2"),
        ("EssenceHouse", "Fragrance", "Perfume", 599, "Maharashtra", "Mumbai", "Tier-1"),
        ("SoapBar Co.", "Bath & Body", "Soap/Bar", 149, "Madhya Pradesh", "Indore", "Tier-2"),
        ("BodyBliss", "Bath & Body", "Body Lotion", 229, "Odisha", "Bhubaneswar", "Tier-2"),
        ("BeardBro", "Men's Grooming", "Beard Oil", 249, "Punjab", "Ludhiana", "Tier-2"),
        ("GentCare", "Men's Grooming", "Grooming Kit", 499, "Telangana", "Hyderabad", "Tier-1"),
        ("NatureNourish", "Skincare", "Moisturizer", 299, "Assam", "Guwahati", "Tier-3"),
        ("BrightBloom", "Makeup", "Compact", 179, "Jharkhand", "Ranchi", "Tier-3"),
        ("TressTonic", "Haircare", "Conditioner", 239, "Haryana", "Karnal", "Tier-3"),
    ]
    rows = []
    for seller, category, subcat, price, state, city, tier in raw_sellers:
        cogs = round(price * 0.55)
        stock = random.choice([80, 150, 220, 400, 600])
        rec = recommend_commission(category, price, cogs, stock)
        rows.append({
            "Seller": seller, "Product": f"{seller} — {subcat}", "Category": category,
            "Sub-category": subcat, "Price (₹)": price, "Commission %": rec["point"],
            "State": state, "Zone": STATE_ZONE[state], "City": city, "City Tier": tier,
            "Source": "Marketplace",
        })
    return pd.DataFrame(rows)


def get_full_marketplace():
    base = build_marketplace()
    if "listings" in st.session_state and len(st.session_state.listings) > 0:
        own = st.session_state.listings.copy()
        own_rows = []
        for _, r in own.iterrows():
            own_rows.append({
                "Seller": "You (your listing)", "Product": r["Product"], "Category": r["Category"],
                "Sub-category": "-", "Price (₹)": r["Price (₹)"], "Commission %": r["Your Commission %"],
                "State": "Maharashtra", "Zone": "West", "City": "Mumbai", "City Tier": "Tier-1",
                "Source": "Your Listing",
            })
        if own_rows:
            base = pd.concat([base, pd.DataFrame(own_rows)], ignore_index=True)
    return base


def match_score(row, niches, state, zone, min_c, max_c):
    niche_score = 100 if row["Category"] in niches else 30
    if row["State"] == state:
        region_score = 100
    elif row["Zone"] == zone:
        region_score = 60
    else:
        region_score = 25
    if max_c > min_c:
        commission_score = (row["Commission %"] - min_c) / (max_c - min_c) * 100
    else:
        commission_score = 50
    total = niche_score * 0.40 + region_score * 0.30 + commission_score * 0.30
    return round(total), niche_score, region_score, round(commission_score)


# ----------------------------------------------------------------------------
# CONTENT IDEA GENERATOR
# ----------------------------------------------------------------------------
CONTENT_HOOKS = {
    "Skincare": [
        "\"My skin doubted me for 2 weeks — here's what happened\" (before/after arc)",
        "Answer a real comment: \"Will this suit oily/combination skin?\" on camera",
        "Morning routine in under 30 seconds — no talking, just text overlays",
        "\"I tried the viral vs. the budget version\" honest comparison",
        "React to a skincare myth your followers keep asking about",
    ],
    "Makeup": [
        "GRWM in your regional language with shade-matching commentary",
        "\"3 lipstick shades, 1 skin tone\" — swatch + honest verdict",
        "Festival-ready look using 3 products under ₹500",
        "\"Will it transfer?\" stress test — kiss test / rub test on camera",
        "Duet/react to a follower's makeup fail and fix it live",
    ],
    "Haircare": [
        "30-day hair oil challenge — weekly check-ins, no filters",
        "\"Why is my hair falling\" myth-busting with product tie-in",
        "Before/after blow-dry using the product, filmed handheld",
        "Regional recipe twist — e.g. \"how my nani used this ingredient\"",
        "\"Does this REALLY reduce frizz in humidity\" real-weather test",
    ],
    "Fragrance": [
        "\"Which perfume matches your personality\" quiz-style reel",
        "Longevity test — spray at 8am, update through the day",
        "\"Budget dupe vs. designer\" honest sniff-test comparison",
        "Gifting guide tied to an upcoming festival",
        "\"One scent, three occasions\" styling reel",
    ],
    "Bath & Body": [
        "\"Self-care Sunday\" routine featuring the product",
        "Unboxing + first impression, filmed in natural light",
        "\"Does this actually moisturize in winter\" real test over a week",
        "Gift-hamper styling idea using 3 products under a budget",
        "React to comments asking about fragrance/skin-feel",
    ],
    "Men's Grooming": [
        "\"5-minute grooming routine before work\" — fast cuts, no fluff",
        "Beard growth check-in series using the product",
        "\"Does this actually work or is it hype\" honest verdict video",
        "Before/after trim + product styling reel",
        "Answer follower Q&A on beard/skin concerns",
    ],
}

GENERAL_TACTICS = [
    "Post in your strongest regional language first, then caption in Hindi/English for reach — vernacular content consistently outperforms generic metro-style content.",
    "Try an honest 'this didn't work for me, but this did' format occasionally — audiences trust creators more after an honest 'no', not less.",
    "Raw, handheld, single-take content is currently outperforming studio-polished videos in engagement-per-view — don't over-produce.",
    "Tie content to an upcoming festival or seasonal moment (wedding season, Diwali, Holi) for a natural demand spike.",
    "Respond to your own comments with a follow-up mini-video — it signals authenticity and boosts the algorithm's reach.",
    "Batch-film 3-4 pieces of content in one sitting using the same product to reduce your weekly effort.",
]


# ----------------------------------------------------------------------------
# SESSION STATE INIT
# ----------------------------------------------------------------------------
if "role" not in st.session_state:
    st.session_state.role = None
if "listings" not in st.session_state:
    st.session_state.listings = pd.DataFrame([
        {"Product": "Herbal Glow Face Wash 100ml", "Category": "Skincare", "Price (₹)": 249,
         "Recommended %": 16.5, "Your Commission %": 12.0, "Interest Score": 35, "Status": "Live"},
        {"Product": "MatteFinish Liquid Lipstick", "Category": "Makeup", "Price (₹)": 199,
         "Recommended %": 17.0, "Your Commission %": 17.0, "Interest Score": 75, "Status": "Live"},
        {"Product": "Onion Hair Oil 200ml", "Category": "Haircare", "Price (₹)": 299,
         "Recommended %": 12.5, "Your Commission %": 13.5, "Interest Score": 80, "Status": "Live"},
    ])
if "influencer_profile" not in st.session_state:
    st.session_state.influencer_profile = None


# ----------------------------------------------------------------------------
# LANDING / PROFILE SELECTION PAGE
# ----------------------------------------------------------------------------
def render_landing():
    st.markdown("""
    <div class="main-header">
        <h1>🤝 Meesho Mitra</h1>
        <p>One portal, two sides — smart commission matching for Beauty & Personal Care</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### Continue as")
    st.write("")

    col1, col2 = st.columns(2, gap="large")
    with col1:
        st.markdown("""
        <div class="role-card">
            <h2>🏪 Seller</h2>
            <p>List your BPC products and get a data-backed commission recommendation
            to attract the right influencers — without guessing what to pay.</p>
        </div>
        """, unsafe_allow_html=True)
        st.write("")
        if st.button("Continue as Seller", use_container_width=True, key="pick_seller"):
            st.session_state.role = "seller"
            st.rerun()

    with col2:
        st.markdown("""
        <div class="role-card">
            <h2>🎥 Influencer</h2>
            <p>Pick your niche and region, discover sellers matched to you, and get
            ready-to-use content ideas — no top-down brand assignment.</p>
        </div>
        """, unsafe_allow_html=True)
        st.write("")
        if st.button("Continue as Influencer", use_container_width=True, key="pick_influencer"):
            st.session_state.role = "influencer"
            st.rerun()

    st.write("")
    st.caption("Demo build · Meesho DICE Challenge Season 3 · Business Track")


def render_top_bar(role_label):
    c1, c2 = st.columns([5, 1])
    with c1:
        st.markdown(f"""
        <div class="main-header">
            <h1>🤝 Meesho Mitra</h1>
            <p>{role_label}</p>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.write("")
        st.write("")
        if st.button("🔄 Switch Profile", use_container_width=True):
            st.session_state.role = None
            st.rerun()


# ----------------------------------------------------------------------------
# SELLER SIDE
# ----------------------------------------------------------------------------
def render_seller_side():
    render_top_bar("Seller Portal · Smart Commission Recommendations for Beauty & Personal Care")

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
            st.write("")
            st.write("")
            get_rec = st.button("🔍 Get Commission Recommendation", use_container_width=True)

        if get_rec:
            if not product_name:
                st.warning("Please enter a product name to continue.")
            else:
                rec = recommend_commission(category, price, cogs, stock_units)
                st.session_state["last_rec"] = rec
                st.session_state["last_product"] = {"name": product_name, "category": category, "price": price, "cogs": cogs, "stock": stock_units}

        if "last_rec" in st.session_state and st.session_state.get("last_product", {}).get("name") == product_name and product_name:
            rec = st.session_state["last_rec"]
            st.markdown("---")
            st.markdown("### 💡 Recommendation")

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Recommended Commission", f"{rec['point']}%")
            m2.metric("Suggested Range", f"{rec['low']}% – {rec['high']}%")
            m3.metric("Category Demand", f"{rec['demand_index']}/100", delta="High" if rec['demand_index'] > 65 else "Moderate")
            m4.metric("Creator Saturation", f"{rec['competition_index']}/100", delta="High" if rec['competition_index'] > 65 else "Moderate", delta_color="inverse")

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
            chosen = st.slider("Your Commission % (drag to adjust)", min_value=5.0, max_value=25.0, value=float(rec['point']), step=0.5)
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
                st.session_state.listings = pd.concat([st.session_state.listings, pd.DataFrame([new_row])], ignore_index=True)
                st.success(f"'{product_name}' listed successfully! It's now visible to influencers browsing {category}.")
                del st.session_state["last_rec"]

    with tab2:
        st.subheader("My Listings")
        st.caption("Track how your commission choices compare to market recommendations, and the resulting influencer interest.")
        df = st.session_state.listings.copy()
        st.dataframe(
            df, use_container_width=True, hide_index=True,
            column_config={"Interest Score": st.column_config.ProgressColumn("Interest Score", min_value=0, max_value=100, format="%d")},
        )
        st.markdown("#### Commission vs. Market Recommendation")
        chart_df = df.set_index("Product")[["Recommended %", "Your Commission %"]]
        st.bar_chart(chart_df)
        below_market = df[df["Your Commission %"] < df["Recommended %"] - 1]
        if len(below_market) > 0:
            st.warning(f"⚠️ {len(below_market)} product(s) are below the recommended commission and may be getting less influencer traction: " + ", ".join(below_market["Product"].tolist()))


# ----------------------------------------------------------------------------
# INFLUENCER SIDE
# ----------------------------------------------------------------------------
def render_influencer_side():
    render_top_bar("Influencer Portal · Discover sellers matched to your niche, region & reach")

    tab1, tab2, tab3 = st.tabs(["🧭 My Niche & Profile", "🔎 Recommended Sellers", "✨ Content Ideas"])

    with tab1:
        st.subheader("Tell us about you")
        st.caption("This is bottom-up by design — you choose what you want to brand for, we don't assign it to you.")

        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Your Name / Handle", placeholder="e.g. @glowwithria")
            state = st.selectbox("Home State", STATES, index=STATES.index("Maharashtra"))
            city = st.text_input("City", placeholder="e.g. Nagpur")
            followers = st.number_input("Follower / Subscriber Count", min_value=100, max_value=2_000_000, value=8000, step=100)
        with col2:
            niches = st.multiselect("Niches you want to brand for", list(CATEGORY_DATA.keys()), default=["Skincare", "Makeup"])
            languages = st.multiselect("Languages you create in", LANGUAGES, default=["Hindi", "English"])

        if followers < 10_000:
            tier = "Nano"
        elif followers < 50_000:
            tier = "Micro"
        elif followers < 200_000:
            tier = "Mid-tier"
        else:
            tier = "Macro"
        st.info(f"📊 Based on your reach, you're a **{tier} creator** ({followers:,} followers).")

        if st.button("💾 Save Profile", use_container_width=True):
            st.session_state.influencer_profile = {
                "name": name or "Creator", "state": state, "city": city, "followers": followers,
                "tier": tier, "niches": niches if niches else list(CATEGORY_DATA.keys()),
                "languages": languages,
            }
            st.success("Profile saved! Head to 'Recommended Sellers' to see your matches.")

    profile = st.session_state.influencer_profile

    with tab2:
        if not profile:
            st.info("👈 Save your profile in the 'My Niche & Profile' tab first to see personalized matches.")
        else:
            st.subheader(f"Sellers matched to {profile['name']}")
            st.caption(f"{profile['tier']} creator · {profile['city'] or profile['state']}, {profile['state']} · Niches: {', '.join(profile['niches'])}")

            marketplace = get_full_marketplace()
            zone = STATE_ZONE[profile["state"]]
            min_c, max_c = marketplace["Commission %"].min(), marketplace["Commission %"].max()

            scores = marketplace.apply(lambda r: match_score(r, profile["niches"], profile["state"], zone, min_c, max_c), axis=1)
            marketplace["Match Score"] = [s[0] for s in scores]
            marketplace["_niche"] = [s[1] for s in scores]
            marketplace["_region"] = [s[2] for s in scores]
            marketplace["_comm"] = [s[3] for s in scores]

            fc1, fc2, fc3 = st.columns(3)
            with fc1:
                cat_filter = st.multiselect("Filter by category", list(CATEGORY_DATA.keys()), default=profile["niches"])
            with fc2:
                region_filter = st.selectbox("Region scope", ["All India", f"Same zone ({zone})", f"Same state ({profile['state']})"])
            with fc3:
                sort_by = st.selectbox("Sort by", ["Best Match", "Highest Commission", "Nearest Region"])

            view = marketplace.copy()
            if cat_filter:
                view = view[view["Category"].isin(cat_filter)]
            if region_filter.startswith("Same zone"):
                view = view[view["Zone"] == zone]
            elif region_filter.startswith("Same state"):
                view = view[view["State"] == profile["state"]]

            if sort_by == "Best Match":
                view = view.sort_values("Match Score", ascending=False)
            elif sort_by == "Highest Commission":
                view = view.sort_values("Commission %", ascending=False)
            else:
                view = view.sort_values("_region", ascending=False)

            st.markdown(f"**{len(view)} sellers found**")
            display_cols = ["Seller", "Product", "Category", "Price (₹)", "Commission %", "State", "City Tier", "Match Score"]
            st.dataframe(
                view[display_cols], use_container_width=True, hide_index=True,
                column_config={"Match Score": st.column_config.ProgressColumn("Match Score", min_value=0, max_value=100, format="%d")},
            )

            if len(view) > 0:
                top = view.iloc[0]
                st.markdown('<div class="rationale-box">', unsafe_allow_html=True)
                st.markdown(f"**Why {top['Seller']} is your top match:**")
                st.markdown(f"- Niche alignment: {'✅ Direct category match' if top['_niche']==100 else '➖ Adjacent category'}")
                st.markdown(f"- Region: {'✅ Same state' if top['_region']==100 else ('🟡 Same zone' if top['_region']==60 else '🔴 Different region')}")
                st.markdown(f"- Commission: {top['Commission %']}% — {'above' if top['_comm']>50 else 'below'} average for similar sellers")
                st.markdown('</div>', unsafe_allow_html=True)

    with tab3:
        st.subheader("Content Ideas & Tactics")
        st.caption("Ready-to-use hooks and formats so you spend less time stuck on 'what do I post today'.")

        if profile and profile["niches"]:
            niche_choice = st.selectbox("Get ideas for", profile["niches"])
        else:
            niche_choice = st.selectbox("Get ideas for", list(CATEGORY_DATA.keys()))

        if st.button("✨ Generate Content Ideas", use_container_width=True):
            hooks = random.sample(CONTENT_HOOKS[niche_choice], k=min(3, len(CONTENT_HOOKS[niche_choice])))
            tactics = random.sample(GENERAL_TACTICS, k=3)

            st.markdown(f"#### 🎬 Hook ideas for {niche_choice}")
            for h in hooks:
                st.markdown(f'<div class="idea-card">💡 {h}</div>', unsafe_allow_html=True)

            st.markdown("#### 📌 General tactics to boost reach")
            for t in tactics:
                st.markdown(f'<div class="idea-card">📈 {t}</div>', unsafe_allow_html=True)
        else:
            st.info("Click 'Generate Content Ideas' to get a fresh set of hooks and tactics.")


# ----------------------------------------------------------------------------
# ROUTER
# ----------------------------------------------------------------------------
if st.session_state.role is None:
    render_landing()
elif st.session_state.role == "seller":
    render_seller_side()
elif st.session_state.role == "influencer":
    render_influencer_side()
