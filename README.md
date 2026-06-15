# turo-onboard

Paste a Turo listing URL. Get a full operator onboarding package in under 60 seconds.

Built for independent fleet operators and Turo hosts evaluating [turo-onboard](https://1Now.ai) — the platform that replaces marketplace fees with direct bookings and AI automation.

---

## What it generates

From a single Turo URL, the tool produces:

- **Revenue impact** — exact extra monthly revenue if the operator switches to direct booking
- **Customer persona** — who books this car, why they book, what frustrates them about Turo
- **Direct booking website copy** — hero headline, subheadline, value props, trust signals, CTA
- **Onboarding call agenda** — 5-step script with the exact opening sentence for each step
- **1Now feature recommendations** — tied to specifics of that listing
- **Red flags** — what to address before the call

---

## Sample output — 2024 GMC Terrain, Rogers AR

> *"By switching to direct bookings, you can increase your earnings by over $1,200/month while offering renters a seamless, fee-free experience with your 2024 GMC Terrain."*

**Pricing**

| | Price |
|---|---|
| Current Turo rate | $66.5/day |
| Recommended direct rate | $75/day |
| Estimated extra revenue/month | $1,200 (10 trips/month at 3 days avg) |

**Customer Persona — Emily, 35–50**

Emily books for family weekend getaways in Northwest Arkansas. She values transparent pricing and direct communication with the host. Her biggest frustration with Turo: hidden fees and no direct line to the owner.

**Onboarding Call Opener**

> *"Hi Ryan, thanks for taking the time to chat. I've analyzed your Turo listing and see a great opportunity to boost your earnings by switching to direct bookings."*

**Website Headline**

> *Rent the 2024 GMC Terrain Directly in Rogers — Save on fees and enjoy a seamless rental experience.*

---

## Stack

| Layer | Tool |
|---|---|
| Scraping | Playwright + BeautifulSoup + JSON-LD extraction |
| Analysis | Cohere `command-a-03-2025` via Cohere API |
| UI | Streamlit |

---

## Setup

**1. Clone and install**

```bash
git clone https://github.com/whozahm3d/turo-onboard
cd turo-onboard
pip install -r requirements.txt
playwright install chromium
```

Or use the included setup script:

```bash
python setup.py
```

**2. Create your `.env` file**

```bash
cp .env.example .env
```

Then paste your Cohere API key into `.env`. Get a free key at [dashboard.cohere.com](https://dashboard.cohere.com).

```
COHERE_API_KEY=your-cohere-key-here
```

---

## Usage

### Option A — Streamlit UI (recommended for demo)

```bash
streamlit run app.py
```

Open `http://localhost:8501`, paste a Turo listing URL, click Generate.

### Option B — CLI (step by step)

```bash
# Phase 1: scrape the listing
python scraper.py https://turo.com/us/en/car-rental/...

# Phase 2: run AI analysis
python pipeline.py
```

### Option C — From Jupyter

```python
import subprocess, os
from dotenv import load_dotenv

load_dotenv()

# Scrape
subprocess.run(["python", "scraper.py", "https://turo.com/..."])

# Analyze
subprocess.run(["python", "pipeline.py"])

# Launch UI
subprocess.Popen(["streamlit", "run", "app.py"])
```

---

## Output files

All outputs land in `output/` after each run:

| File | Description |
|---|---|
| `listing_data.json` | Raw scraped listing data |
| `onboarding_package.json` | Full AI analysis (structured) |
| `onboarding_package.md` | Human-readable report |
| `raw.html` | Full page HTML (debugging) |
| `screenshot.png` | Browser snapshot of the listing |

---

## Project structure

```
turo-onboard/
├── app.py              # Streamlit UI
├── scraper.py          # Playwright + BS4 Turo scraper
├── pipeline.py         # Cohere onboarding analysis pipeline
├── setup.py            # One-time install script
├── requirements.txt    # Dependencies
├── .env.example        # Environment variable template
└── output/             # Generated at runtime (gitignored)
```

---

## How the scraper works

Two-layer extraction:

1. **JSON-LD structured data** — Turo embeds machine-readable listing data in `<script type="application/ld+json">` tags. Cleanest source for vehicle name, rating, price, reviews, and location.
2. **BeautifulSoup + regex fallbacks** — catches host name, trips hosted, response rate, specs (MPG, seats, doors, transmission), and features that JSON-LD misses.

Runs with a visible browser (`headless=False`) to bypass Cloudflare bot detection. A full-page screenshot is saved on every run for debugging.

---

## How the AI pipeline works

Scraped listing data is sent to Cohere's `command-a-03-2025` model with a structured system prompt framing it as a 1Now onboarding specialist task. The model returns strict JSON — parsed directly into the Streamlit UI.

The prompt engineers for specificity: prices reference the actual listing data, the persona is named and grounded in the reviews, and the onboarding agenda includes verbatim opening sentences rather than generic talking points.

---

## Notes

- Turo occasionally serves a Cloudflare challenge on first load. When the browser opens, complete the verification manually — it stays open for 60 seconds.
- `COHERE_API_KEY` is read from `.env` automatically via `python-dotenv`. Never hardcode it.
- `output/` is gitignored — scraped data and generated packages stay local.
