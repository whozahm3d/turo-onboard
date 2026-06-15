"""
app.py — Phase 3: TURO_ONBOARD Onboarding Generator
Streamlit UI that ties scraper.py and pipeline.py together.

Run:
    streamlit run app.py

From Jupyter:
    import subprocess
    subprocess.Popen(["streamlit", "run", "app.py"])
    # Then open http://localhost:8501
"""

import json
import os
import sys
import subprocess
from pathlib import Path
import concurrent.futures
import traceback

try:
    import streamlit as st
except Exception:
    print("Error: streamlit not installed. Run: pip install streamlit")
    sys.exit(1)

try:
    from pipeline import call_openrouter
except ImportError:
    st.error("pipeline.py not found in the same directory as app.py.")
    st.stop()

OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

# ─────────────────────────────────────────────
#  PAGE CONFIG + CSS
# ─────────────────────────────────────────────

st.set_page_config(
    page_title="TURO_ONBOARD · Onboarding Generator",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
[data-testid="stAppViewContainer"] { background: #FAF7F5; }
[data-testid="stHeader"]           { background: #FAF7F5; border-bottom: 1px solid #F0E8E2; }
[data-testid="stSidebar"]          { background: #1A1A1A; }
[data-testid="stSidebar"] * { color: #F0E8E2 !important; }
[data-testid="stSidebar"] input { background: #2A2A2A !important; color: white !important; border: 1px solid #444 !important; }
[data-testid="stSidebar"] label { color: #AAA !important; font-size: 0.8rem !important; text-transform: uppercase; letter-spacing: 0.08em; }
.main .block-container { padding-top: 2rem; padding-bottom: 4rem; max-width: 1080px; }
.card {
    background: #FFFFFF;
    border-radius: 14px;
    padding: 1.5rem 1.75rem;
    margin-bottom: 1rem;
    border: 1px solid #F0E8E2;
    box-shadow: 0 1px 6px rgba(0,0,0,0.04);
    color: #1A1A1A;
}
.card-dark {
    background: #1A1A1A;
    border-radius: 14px;
    padding: 1.5rem 1.75rem;
    margin-bottom: 1rem;
    color: #F0E8E2;
}
.revenue-big {
    font-size: 3.2rem;
    font-weight: 800;
    color: #1E7D50;
    letter-spacing: -2px;
    line-height: 1;
    margin: 0;
}
.revenue-label {
    font-size: 0.78rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: #8B7D75;
    margin-top: 4px;
}
.eyebrow {
    font-size: 0.72rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: #1B3A7A;
    margin-bottom: 4px;
}
.opening-pitch {
    font-size: 1.25rem;
    font-weight: 600;
    color: #1A1A1A;
    font-style: italic;
    border-left: 4px solid #1B3A7A;
    padding: 0.75rem 1.25rem;
    background: #FFF8F5;
    border-radius: 0 10px 10px 0;
    margin: 1rem 0;
}
.step-card {
    display: flex;
    gap: 1rem;
    padding: 1rem 1.25rem;
    background: white;
    border-radius: 10px;
    border: 1px solid #F0E8E2;
    margin-bottom: 0.75rem;
}
.step-num { font-size: 1.4rem; font-weight: 800; color: #E5501A; min-width: 2rem; line-height: 1.2; }
.step-body { flex: 1; }
.step-topic { font-weight: 700; font-size: 0.95rem; color: #1A1A1A; }
.step-msg { font-size: 0.85rem; color: #6B6B6B; margin-top: 2px; }
.step-quote {
    font-size: 0.85rem;
    font-style: italic;
    color: #4A4A4A;
    background: #FAF7F5;
    border-left: 3px solid #1B3A7A;
    padding: 6px 12px;
    border-radius: 0 6px 6px 0;
    margin-top: 8px;
}
.badge {
    display: inline-block;
    background: #F4EDE8;
    color: #8B3A1A;
    font-size: 0.78rem;
    font-weight: 500;
    padding: 3px 11px;
    border-radius: 100px;
    margin: 2px 3px;
}
.flag {
    background: #FFF5F5;
    border-left: 3px solid #D94040;
    padding: 0.65rem 1rem;
    border-radius: 0 8px 8px 0;
    margin: 6px 0;
    font-size: 0.88rem;
    color: #4A1A1A;
}
.vp-title { font-weight: 700; font-size: 0.92rem; color: #1A1A1A; }
.vp-desc  { font-size: 0.85rem; color: #6B6B6B; margin-top: 2px; }
.feat-row { padding: 0.75rem 1rem; background: #F8F5F2; border-radius: 8px; margin: 6px 0; }
.feat-name { font-weight: 700; font-size: 0.9rem; color: #1A1A1A; }
.feat-why  { font-size: 0.83rem; color: #6B6B6B; margin-top: 2px; }
.trust { font-size: 0.83rem; color: #2D6A4F; padding: 4px 0; }
div[data-testid="stTabs"] button { font-size: 0.9rem; font-weight: 600; color: #1A1A1A !important; }
.stTextInput input { 
    border-radius: 10px !important; 
    border: 1.5px solid #DDD !important; 
    font-size: 0.95rem !important;
    background: #FFFFFF !important;
    color: #1A1A1A !important;
}
.stTextInput input::placeholder { color: #AAAAAA !important; }
.stButton button {
    background: #1B3A7A !important;
    color: white !important;
    border-radius: 10px !important;
    font-weight: 700 !important;
    border: none !important;
    padding: 0.5rem 1.75rem !important;
}
.stDownloadButton button {
    background: #1B3A7A !important;
    color: white !important;
    border-radius: 10px !important;
    font-weight: 700 !important;
    border: none !important;
    padding: 0.5rem 1.75rem !important;
}
.stDownloadButton button:hover { background: #142E6E !important; }
.main [data-testid="stMarkdownContainer"] p,
.main [data-testid="stMarkdownContainer"] li,
.main [data-testid="stMarkdownContainer"] strong,
.main [data-testid="stMarkdownContainer"] em { color: #1A1A1A !important; }
.stCaption p { color: #6B6B6B !important; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
#  SESSION STATE
# ─────────────────────────────────────────────

if "package" not in st.session_state: st.session_state.package = None
if "listing" not in st.session_state: st.session_state.listing = None
if "error"   not in st.session_state: st.session_state.error   = None


# ─────────────────────────────────────────────
#  SIDEBAR
# ─────────────────────────────────────────────

with st.sidebar:
    st.markdown("### 🚗 TURO_ONBOARD")
    st.markdown("**Onboarding Generator**")
    st.markdown("---")

    api_key = st.text_input(
        "COHERE API Key",
        type="password",
        placeholder="sk-or-v1-...",
        value=os.environ.get("COHERE_API_KEY", ""),
    )
    if api_key:
        os.environ["COHERE_API_KEY"] = api_key.strip()

    st.markdown("---")
    st.markdown("**How it works**")
    st.markdown("1. Paste a Turo listing URL\n2. We scrape the listing\n3. Cohere builds the package\n4. Use it on your onboarding call")

    st.markdown("---")
    if st.session_state.package:
        if st.button("↩ Start Over"):
            st.session_state.package = None
            st.session_state.listing = None
            st.session_state.error   = None
            st.rerun()


# ─────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────

def eyebrow(text: str):
    st.markdown(f'<div class="eyebrow">{text}</div>', unsafe_allow_html=True)

def badges(items: list):
    html = " ".join(f'<span class="badge">{i}</span>' for i in items)
    st.markdown(html, unsafe_allow_html=True)

def run_scraper(url: str) -> tuple[bool, str, str]:
    result = subprocess.run(
        [sys.executable, "scraper.py", url],
        capture_output=True,
        text=True,
        timeout=120,
    )
    return result.returncode == 0, result.stdout, result.stderr


# ─────────────────────────────────────────────
#  RESULT RENDERERS
# ─────────────────────────────────────────────

def render_revenue(pkg: dict):
    ps = pkg["pricing_strategy"]
    fs = pkg["fleet_summary"]

    st.markdown(f'<div class="opening-pitch">"{pkg["opening_pitch"]}"</div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    revenue_num = ps["estimated_extra_monthly_revenue"].split("(")[0].strip()
    with col1:
        st.markdown(f"""
        <div class="card">
            <div class="eyebrow">Extra Revenue / Month</div>
            <p class="revenue-big">{revenue_num}</p>
            <p class="revenue-label">{ps["estimated_extra_monthly_revenue"]}</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="card">
            <div class="eyebrow">Current Turo Rate</div>
            <h2 style='margin:0;color:#6B6B6B'>{ps['current_turo_price_per_day']}</h2>
            <p class="revenue-label">after marketplace fees</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="card">
            <div class="eyebrow">Recommended Direct Rate</div>
            <h2 style='margin:0;color:#E5501A'>{ps['recommended_direct_price_per_day']}</h2>
            <p class="revenue-label">on their own booking site</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="card">
        <div class="eyebrow">Pricing Rationale</div>
        <p style="color:#4A4A4A;margin-top:6px">{ps["reasoning"]}</p>
    </div>
    """, unsafe_allow_html=True)

    col_a, col_b = st.columns(2)
    with col_a:
        strengths_html = "".join(f'<li style="color:#4A4A4A;margin:4px 0">{s}</li>' for s in fs["current_turo_strengths"])
        st.markdown(f"""
        <div class="card">
            <div class="eyebrow">Fleet Position</div>
            <p style="color:#1A1A1A;margin:4px 0"><strong>Tier:</strong> {fs['quality_tier'].title()}</p>
            <p style="color:#4A4A4A;margin:8px 0">{fs['market_position']}</p>
            <p style="color:#1A1A1A;margin:8px 0"><strong>Current Strengths:</strong></p>
            <ul style="margin:0;padding-left:1.2rem">{strengths_html}</ul>
        </div>
        """, unsafe_allow_html=True)

    with col_b:
        badges_html = " ".join(f'<span class="badge">{i}</span>' for i in ps.get("upsell_opportunities", []))
        st.markdown(f"""
        <div class="card">
            <div class="eyebrow">Upsell Opportunities</div>
            <div style="margin-top:8px">{badges_html}</div>
        </div>
        """, unsafe_allow_html=True)

def render_persona(pkg: dict):
    cp = pkg["customer_persona"]

    st.markdown(f"""
    <div class="card">
        <div class="eyebrow">Customer Persona</div>
        <h2 style="color:#1A1A1A;margin:8px 0">Meet {cp['persona_name']}</h2>
        <p style="color:#4A4A4A;margin:4px 0"><strong>{cp['age_range']}</strong> · {cp['likely_use_case']}</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        motivations_html = "".join(f'<p style="color:#4A4A4A;margin:4px 0">✓ {m}</p>' for m in cp.get("booking_motivations", []))
        st.markdown(f"""
        <div class="card">
            <div class="eyebrow">Booking Motivations</div>
            {motivations_html}
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="card">
            <div class="eyebrow">Why Direct Booking Wins</div>
            <p style="color:#4A4A4A;margin-top:6px">{cp.get("why_direct_booking_wins", "")}</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        frustrations_html = "".join(f'<p style="color:#4A4A4A;margin:4px 0">✗ {f}</p>' for f in cp.get("frustrations_with_turo", []))
        st.markdown(f"""
        <div class="card">
            <div class="eyebrow">Frustrations with Turo</div>
            {frustrations_html}
        </div>
        """, unsafe_allow_html=True)

def render_copy(pkg: dict):
    wc = pkg["website_copy"]

    st.markdown(f"""
    <div class="card-dark">
        <div class="eyebrow" style="color:#AAA">Hero Headline</div>
        <h2 style="color:white;margin:8px 0">{wc['hero_headline']}</h2>
        <p style="color:#CCC;margin:0">{wc['hero_subheadline']}</p>
        <button style="margin-top:1rem;background:#E5501A;color:white;border:none;padding:10px 24px;border-radius:8px;font-weight:700;cursor:default">{wc.get('primary_cta','Book Now')}</button>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="eyebrow" style="margin:12px 0 8px">Value Propositions</div>', unsafe_allow_html=True)
    vps = wc.get("value_propositions", [])
    cols = st.columns(len(vps) or 1)
    for i, vp in enumerate(vps):
        with cols[i]:
            st.markdown(f"""
            <div class="card">
                <p class="vp-title">{vp['title']}</p>
                <p class="vp-desc">{vp['description']}</p>
            </div>
            """, unsafe_allow_html=True)

    trust_html = "".join(f'<div class="trust">✓ {ts}</div>' for ts in wc.get("trust_signals", []))
    st.markdown(f"""
    <div class="card">
        <div class="eyebrow">Trust Signals</div>
        {trust_html}
    </div>
    """, unsafe_allow_html=True)


def render_call(pkg: dict):
    st.markdown(f"""
    <div class="card">
        <div class="eyebrow">Opening Pitch</div>
        <div class="opening-pitch">"{pkg['opening_pitch']}"</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="eyebrow" style="margin:12px 0 8px">5-Step Agenda</div>', unsafe_allow_html=True)
    for step in pkg.get("onboarding_call_agenda", []):
        st.markdown(f"""
        <div class="step-card">
            <div class="step-num">{step['step']}</div>
            <div class="step-body">
                <div class="step-topic">{step['topic']}</div>
                <div class="step-msg">{step['key_message']}</div>
                <div class="step-quote">"{step['suggested_opener']}"</div>
            </div>
        </div>
        """, unsafe_allow_html=True)


def render_features(pkg: dict):
    col1, col2 = st.columns(2)

    with col1:
        features = pkg.get("recommended_turo_onboard_features", pkg.get("recommended_1now_features", []))
        features_html = "".join(
            f'<div class="feat-row"><div class="feat-name">{f["feature"]}</div><div class="feat-why">{f["why_relevant"]}</div></div>'
            for f in features
        )
        st.markdown(f"""
        <div class="card">
            <div class="eyebrow">Recommended 1Now Features</div>
            {features_html}
        </div>
        """, unsafe_allow_html=True)

    with col2:
        flags = pkg.get("red_flags", [])
        if flags and flags != ["N/A"]:
            flags_html = "".join(f'<div class="flag">{rf}</div>' for rf in flags)
            st.markdown(f"""
            <div class="card">
                <div class="eyebrow">⚠ Red Flags to Address</div>
                {flags_html}
            </div>
            """, unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  MAIN UI
# ─────────────────────────────────────────────

st.markdown("""
<div style='margin-bottom:1.5rem'>
    <span style='font-size:1.6rem;font-weight:800;color:#1A1A1A;letter-spacing:-0.5px'>TURO_ONBOARD</span>
    <span style='font-size:1rem;color:#8B7D75;margin-left:10px;font-weight:400'>Onboarding Generator</span>
</div>
""", unsafe_allow_html=True)

if not st.session_state.package:
    st.markdown("""
    <div class="card">
        <div class="eyebrow">Generate Onboarding Package</div>
        <p style="color:#4A4A4A;margin-top:6px">Paste any Turo listing URL. We'll scrape it, run it through Cohere AI, and build a full onboarding package in under 60 seconds.</p>
    </div>
    """, unsafe_allow_html=True)

    url = st.text_input(
        "Turo listing URL",
        placeholder="https://turo.com/us/en/suv-rental/...",
        label_visibility="collapsed",
    )

    go = st.button("Generate Package →", use_container_width=False)

    if go:
        if not url.strip():
            st.warning("Paste a Turo listing URL first.")
            st.stop()
        if not os.environ.get("COHERE_API_KEY"):
            st.warning("Add your Cohere API key in the sidebar.")
            st.stop()

        with st.status("Loading Turo listing...", expanded=True) as status:
            st.write("Launching browser...")
            success, stdout, stderr = run_scraper(url.strip())

            if not success:
                status.update(label="Scraping failed", state="error")
                st.error(f"Scraper error:\n\n{stderr}")
                st.info("Check `output/screenshot.png` to see what the browser loaded.")
                st.stop()

            listing_path = OUTPUT_DIR / "listing_data.json"
            if not listing_path.exists():
                status.update(label="No output file found", state="error")
                st.stop()

            listing = json.loads(listing_path.read_text())
            vehicle = listing.get("vehicle", {}).get("name", "vehicle")
            status.update(label=f"✓ Loaded: {vehicle}", state="complete")

        with st.status("Analyzing with Cohere...", expanded=True) as status:
            st.write("Building onboarding package...")
            try:
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(call_openrouter, listing)
                    package = future.result()
            except json.JSONDecodeError as e:
                status.update(label="Cohere returned invalid JSON", state="error")
                st.error(str(e))
                st.stop()
            except Exception as e:
                status.update(label="Cohere call failed", state="error")
                st.error(str(e))
                st.code(traceback.format_exc())
                st.stop()

            (OUTPUT_DIR / "onboarding_package.json").write_text(
                json.dumps(package, indent=2, ensure_ascii=False)
            )
            status.update(label="✓ Package ready", state="complete")

        st.session_state.package = package
        st.session_state.listing = listing
        st.rerun()

if st.session_state.package:
    pkg     = st.session_state.package
    listing = st.session_state.listing

    vehicle_name = pkg["fleet_summary"]["vehicle_name"]
    st.markdown(f"<h3 style='margin-bottom:0.25rem;color:#1A1A1A'>{vehicle_name}</h3>", unsafe_allow_html=True)
    st.caption(f"Hosted by {listing.get('host', {}).get('name', 'N/A')}  ·  {listing.get('details', {}).get('location', 'N/A')}")

    tabs = st.tabs([
        "💰 Revenue Impact",
        "👤 Customer Persona",
        "🌐 Website Copy",
        "📞 Onboarding Call",
        "⚙️ Features & Flags",
    ])

    with tabs[0]:
        try:
            render_revenue(pkg)
        except Exception as e:
            st.error(f"Render error: {e}")
            st.code(traceback.format_exc())
    with tabs[1]: render_persona(pkg)
    with tabs[2]: render_copy(pkg)
    with tabs[3]: render_call(pkg)
    with tabs[4]: render_features(pkg)

    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        pkg_json = json.dumps(pkg, indent=2)
        st.download_button(
            "⬇ Download JSON",
            data=pkg_json,
            file_name=f"onboarding_{vehicle_name.replace(' ', '_')}.json",
            mime="application/json",
        )
    with col2:
        md_path = OUTPUT_DIR / "onboarding_package.md"
        if md_path.exists():
            st.download_button(
                "⬇ Download Markdown",
                data=md_path.read_text(),
                file_name=f"onboarding_{vehicle_name.replace(' ', '_')}.md",
                mime="text/markdown",
            )