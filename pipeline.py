"""
pipeline.py — Phase 2: Claude Onboarding Analysis Pipeline
Reads output/listing_data.json → sends to Claude → writes onboarding package.

Run:
    # Set your API key first (in Jupyter cell, before subprocess call):
    # import os; os.environ["ANTHROPIC_API_KEY"] = "sk-ant-..."

    python pipeline.py

Output:
    output/onboarding_package.json   ← structured analysis
    output/onboarding_package.md     ← human-readable report for the call
"""

import json
import os
import sys
from pathlib import Path
import types
import requests

INPUT_FILE  = Path("output/listing_data.json")
OUTPUT_JSON = Path("output/onboarding_package.json")
OUTPUT_MD   = Path("output/onboarding_package.md")

MODEL = "command-a-03-2025"

#  PROMPTS

SYSTEM_PROMPT = """You are a senior onboarding specialist at TURO-ONBOARD — a platform that helps \
independent car rental operators and Turo hosts build direct-booking businesses without \
paying 20–25% marketplace fees.

Your job: analyze a scraped Turo listing and produce a tailored onboarding package.
The output is used on a live call with the fleet operator to show them exactly how \
switching to TURO-ONBOARD would change their business.

Rules:
- Respond ONLY with valid JSON matching the exact schema requested.
- No preamble, no explanation, no markdown fences.
- Use concrete numbers and specific language — avoid vague phrases like "great opportunity".
- If a field cannot be determined from the data, write a plausible inference and note "(inferred)".
- Never leave a field blank."""


def build_user_prompt(data: dict) -> str:
    return f"""Analyze this Turo listing and return the onboarding package JSON.

LISTING DATA:
{json.dumps(data, indent=2)}

Return ONLY this JSON structure. Every field must be filled:

{{
  "fleet_summary": {{
    "vehicle_name": "year make model",
    "quality_tier": "budget | mid-range | premium | luxury",
    "market_position": "one sharp sentence on where this operator sits",
    "current_turo_strengths": ["strength 1", "strength 2", "strength 3"]
  }},

  "pricing_strategy": {{
    "current_turo_price_per_day": "$XX/day",
    "recommended_direct_price_per_day": "$XX/day",
    "reasoning": "specific explanation — reference the marketplace cut and what the operator actually nets",
    "estimated_extra_monthly_revenue": "$X,XXX (assuming Y trips/month at Z days avg)",
    "upsell_opportunities": ["airport delivery", "prepaid fuel", "car seat add-on", "etc"]
  }},

  "customer_persona": {{
    "persona_name": "give them a realistic first name",
    "age_range": "25–35 | 35–50 | etc",
    "likely_use_case": "e.g. weekend road trip, business travel, local replacement car",
    "booking_motivations": ["motivation 1", "motivation 2", "motivation 3"],
    "frustrations_with_turo": ["friction 1", "friction 2"],
    "why_direct_booking_wins": "one sentence on why this persona would prefer direct"
  }},

  "website_copy": {{
    "hero_headline": "punchy, specific headline for their direct booking site",
    "hero_subheadline": "one sentence that expands the headline with a concrete benefit",
    "value_propositions": [
      {{"title": "short label", "description": "one sentence benefit statement"}},
      {{"title": "short label", "description": "one sentence benefit statement"}},
      {{"title": "short label", "description": "one sentence benefit statement"}}
    ],
    "trust_signals": ["signal 1 — use real data from listing", "signal 2", "signal 3"],
    "primary_cta": "Book Direct — Save 15%"
  }},

  "onboarding_call_agenda": [
    {{
      "step": 1,
      "topic": "topic title",
      "key_message": "what you want the operator to walk away believing",
      "suggested_opener": "exact sentence to say out loud"
    }},
    {{
      "step": 2,
      "topic": "topic title",
      "key_message": "...",
      "suggested_opener": "..."
    }},
    {{
      "step": 3,
      "topic": "topic title",
      "key_message": "...",
      "suggested_opener": "..."
    }},
    {{
      "step": 4,
      "topic": "topic title",
      "key_message": "...",
      "suggested_opener": "..."
    }},
    {{
      "step": 5,
      "topic": "topic title",
      "key_message": "...",
      "suggested_opener": "..."
    }}
  ],

  "recommended_turo_onboard_features": [
    {{"feature": "feature name", "why_relevant": "tie it to something specific in this listing"}},
    {{"feature": "feature name", "why_relevant": "..."}},
    {{"feature": "feature name", "why_relevant": "..."}}
  ],

  "red_flags": [
    "specific concern from the listing data — e.g. low review count, high cancellation signals, pricing issues"
  ],

  "opening_pitch": "The single most compelling sentence to open the onboarding call — reference their actual vehicle and numbers"
}}"""
    
#  OPENROUTER CALL
def call_openrouter(data: dict) -> dict:

    response = requests.post(
        "https://api.cohere.com/v2/chat",
        headers={
            "Authorization": f"Bearer {os.environ['COHERE_API_KEY']}",
            "Content-Type": "application/json"
        },
        json={
            "model": MODEL,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": build_user_prompt(data)}
            ]
        },
        timeout=120
    )
    response.raise_for_status()

    raw = response.json()["message"]["content"][0]["text"].strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[-1]
    if raw.endswith("```"):
        raw = raw.rsplit("```", 1)[0]
    return json.loads(raw.strip())

#  MARKDOWN RENDERER

def to_markdown(listing: dict, pkg: dict) -> str:
    lines = []

    def h(level: int, text: str):
        lines.append(f"\n{'#' * level} {text}")

    def line(text: str = ""):
        lines.append(text)

    # Title
    h(1, f"TURO-ONBOARD - Onboarding Package")
    h(2, pkg["fleet_summary"]["vehicle_name"])
    line(f"_{pkg['opening_pitch']}_")
    line("\n---")

    # Fleet Summary
    h(2, "Fleet Summary")
    fs = pkg["fleet_summary"]
    line(f"**Quality Tier:** {fs['quality_tier'].title()}")
    line(f"**Market Position:** {fs['market_position']}")
    line(f"\n**Current Strengths on Turo:**")
    for s in fs["current_turo_strengths"]:
        line(f"- {s}")

    # Pricing
    h(2, "Pricing Strategy")
    ps = pkg["pricing_strategy"]
    line(f"| | Price |")
    line(f"|---|---|")
    line(f"| Current Turo rate | {ps['current_turo_price_per_day']} |")
    line(f"| Recommended direct rate | {ps['recommended_direct_price_per_day']} |")
    line(f"\n**Reasoning:** {ps['reasoning']}")
    line(f"\n**Estimated extra revenue per month:** {ps['estimated_extra_monthly_revenue']}")
    line(f"\n**Upsell opportunities:** {', '.join(ps['upsell_opportunities'])}")

    # Customer Persona
    h(2, f"Customer Persona — Meet {pkg['customer_persona']['persona_name']}")
    cp = pkg["customer_persona"]
    line(f"**Age:** {cp['age_range']}  **Use Case:** {cp['likely_use_case']}")
    line(f"\n**Why they book:**")
    for m in cp["booking_motivations"]:
        line(f"- {m}")
    line(f"\n**Turo frustrations:**")
    for f in cp["frustrations_with_turo"]:
        line(f"- {f}")
    line(f"\n**Why direct booking wins for them:** {cp['why_direct_booking_wins']}")

    # Website Copy
    h(2, "Direct Booking Website Copy")
    wc = pkg["website_copy"]
    line(f"**Headline:** {wc['hero_headline']}")
    line(f"\n**Subheadline:** {wc['hero_subheadline']}")
    line(f"\n**Value Props:**")
    for vp in wc["value_propositions"]:
        line(f"- **{vp['title']}:** {vp['description']}")
    line(f"\n**Trust Signals:**")
    for ts in wc["trust_signals"]:
        line(f"- {ts}")
    line(f"\n**CTA Button:** {wc['primary_cta']}")

    # Onboarding Agenda
    h(2, "Onboarding Call Agenda")
    for step in pkg["onboarding_call_agenda"]:
        h(3, f"Step {step['step']}: {step['topic']}")
        line(f"**Key message:** {step['key_message']}")
        line(f"\n> _{step['suggested_opener']}_")

    # TURO-ONBOARD Features
    h(2, "Recommended TURO-ONBOARD Features")
    for f in pkg["recommended_turo_onboard_features"]:
        line(f"- **{f['feature']}:** {f['why_relevant']}")

    # Red Flags
    if pkg.get("red_flags"):
        h(2, "Red Flags to Address Before Call")
        for rf in pkg["red_flags"]:
            line(f"- {rf}")

    return "\n".join(lines)


# ─────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────

def main():
    print("\n" + "=" * 55)
    print(" Phase 2:  COHERE Onboarding Pipeline")
    print("=" * 55 + "\n")

    # Guard: input file
    if not INPUT_FILE.exists():
        print(f"[✗] {INPUT_FILE} not found — run scraper.py first.")
        sys.exit(1)

    # Guard: API key
    if not os.getenv("COHERE_API_KEY"):
        print("[✗] COHERE_API_KEY not set.")
        print('    In Jupyter, run this first:')    
        print('    import os; os.environ["COHERE_API_KEY"] = "sk-or-v1-..."')
        sys.exit(1)

    # Load
    listing = json.loads(INPUT_FILE.read_text())
    vehicle_name = listing.get("vehicle", {}).get("name", "Unknown vehicle")
    print(f"[✓] Loaded: {vehicle_name}")

    # Call Cohere
    package = call_openrouter(listing)
    print("[✓] Analysis complete")

    # Save JSON
    OUTPUT_JSON.write_text(json.dumps(package, indent=2, ensure_ascii=False))
    print(f"[✓] Saved → {OUTPUT_JSON}")

    # Save Markdown
    md = to_markdown(listing, package)
    OUTPUT_MD.write_text(md, encoding="utf-8")
    print(f"[✓] Saved → {OUTPUT_MD}")

    # Preview
    print("\n" + "─" * 40)
    print(f"  Vehicle    : {package['fleet_summary']['vehicle_name']}")
    print(f"  Tier       : {package['fleet_summary']['quality_tier']}")
    print(f"  Direct $   : {package['pricing_strategy']['recommended_direct_price_per_day']}")
    print(f"  Extra/mo   : {package['pricing_strategy']['estimated_extra_monthly_revenue']}")
    print(f"  Persona    : {package['customer_persona']['persona_name']}")
    print(f"  Headline   : {package['website_copy']['hero_headline']}")
    print(f"  Pitch      : {package['opening_pitch']}")
    print("─" * 40)
    print("\nPhase 2 done. Run app.py next for the Streamlit UI.")


if __name__ == "__main__":
    main()
