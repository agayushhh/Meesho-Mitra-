# 🤝 Meesho Mitra — Seller × Influencer Commission Portal (Demo)

A demo built for **Meesho DICE Challenge Season 3 (Business Track)** — showing
how a data-backed commission recommendation system can help sellers attract
the right beauty & personal care (BPC) influencers, and how influencers can
discover sellers bottom-up instead of top-down brand assignment.

**Live demo:** _add your deployed Streamlit Cloud link here after deployment_

## Current scope
- ✅ Seller side — list products, get explainable commission recommendations, track listings
- 🔜 Influencer side — niche/region selection, seller discovery & matching, content idea generator

## Run locally
```bash
git clone https://github.com/<your-username>/meesho-mitra.git
cd meesho-mitra
pip install -r requirements.txt
streamlit run app.py
```
Opens at http://localhost:8501

## Deploy for free (Streamlit Community Cloud)
1. Push this folder to a **public GitHub repo** (steps below).
2. Go to https://share.streamlit.io and sign in with GitHub.
3. Click **"New app"** → select your repo → branch `main` → main file path `app.py`.
4. Click **Deploy**. You'll get a shareable URL like `https://meesho-mitra.streamlit.app`.
5. Any push to `main` auto-redeploys.

## Push this folder to GitHub
```bash
cd meesho-mitra
git init
git add .
git commit -m "Initial commit: Meesho Mitra seller-side demo"
git branch -M main
git remote add origin https://github.com/<your-username>/meesho-mitra.git
git push -u origin main
```
(Create the empty repo on github.com first, without a README, so there's no merge conflict.)

## Project structure
```
meesho-mitra/
├── app.py                  # Streamlit app (seller side)
├── requirements.txt        # Python dependencies
├── .streamlit/config.toml  # Theme config
├── .gitignore
├── LICENSE
└── README.md
```

## Tech notes
- Pure Streamlit + pandas/numpy — no external API keys or paid services required, so it deploys on Streamlit Community Cloud's free tier with zero config.
- Commission engine is rule-based and explainable by design (not a black-box model) so the rationale shown to sellers is always traceable.
