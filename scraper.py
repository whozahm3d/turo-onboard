"""
scraper.py — Phase 1: Turo Listing Scraper
Extracts vehicle, host, pricing, features, and reviews from a Turo listing.

Run:
    python scraper.py <turo_listing_url>
    python scraper.py https://turo.com/us/en/car-rental/...

Output:
    output/listing_data.json   ← structured data for Phase 2
    output/raw.html            ← full HTML for debugging
    output/screenshot.png      ← visual snapshot of the page
"""

import json
import re
import sys
import time
from pathlib import Path

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)


# ─────────────────────────────────────────────
#  BROWSER
# ─────────────────────────────────────────────

def load_page(url: str) -> tuple[str, bytes]:
    """
    Launch headless Chromium, navigate to the Turo listing,
    scroll to trigger lazy loads, then return (html, screenshot).
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,  # Set to True to run headless
            args=[
                "--no-sandbox",
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
            ],
        )
        ctx = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 900},
        )
        page = ctx.new_page()

        # Mask automation flag — reduces bot-detection hits
        page.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )

        print(f"[*] Navigating → {url}")
        page.goto(url, wait_until="load", timeout=45_000)

        # Scroll in steps to trigger lazy-loaded content
        print("[*] Scrolling to load dynamic content...")
        for fraction in [0.25, 0.5, 0.75, 1.0]:
            page.evaluate(f"window.scrollTo(0, document.body.scrollHeight * {fraction})")
            time.sleep(0.8)

        page.evaluate("window.scrollTo(0, 0)")
        time.sleep(1.5)

        # Add these lines right before html = page.content()
        try:
            page.wait_for_selector("h1", timeout=60000)
        except:
            pass
        time.sleep(4)  # extra buffer for dynamic content

        html = page.content()
        screenshot = page.screenshot(full_page=True)
        browser.close()

    return html, screenshot


# ─────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────

def clean(text: str | None) -> str:
    """Collapse whitespace and strip."""
    return " ".join(text.split()).strip() if text else "N/A"


def find_text(soup: BeautifulSoup, pattern: re.Pattern) -> str | None:
    """Return the first string node matching regex pattern."""
    el = soup.find(string=pattern)
    return clean(el) if el else None


# ─────────────────────────────────────────────
#  JSON-LD  (most reliable when present)
# ─────────────────────────────────────────────

def extract_jsonld(soup: BeautifulSoup) -> dict:
    """
    Turo embeds structured data as JSON-LD in <script> tags.
    Pull what we can from there before touching the DOM.
    """
    result = {}
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "")
            if not isinstance(data, dict):
                continue

            # Product / Vehicle listing
            if data.get("@type") in ("Product", "Car", "Vehicle"):
                result["name"]          = data.get("name")
                result["description"]   = data.get("description")
                result["rating"]        = (data.get("aggregateRating") or {}).get("ratingValue")
                result["review_count"]  = (data.get("aggregateRating") or {}).get("reviewCount")
                offers = data.get("offers") or {}
                result["price"]         = offers.get("price")
                result["currency"]      = offers.get("priceCurrency", "USD")

            # Local business / location
            if "address" in data:
                addr = data["address"]
                if isinstance(addr, dict):
                    city  = addr.get("addressLocality", "")
                    state = addr.get("addressRegion", "")
                    result["location"] = f"{city}, {state}".strip(", ") or None

            # Reviews
            if "review" in data:
                reviews_raw = data["review"]
                if isinstance(reviews_raw, dict):
                    reviews_raw = [reviews_raw]
                result["jsonld_reviews"] = [
                    {
                        "author": (r.get("author") or {}).get("name", "Unknown"),
                        "rating": (r.get("reviewRating") or {}).get("ratingValue", "N/A"),
                        "text":   clean(r.get("reviewBody", "")),
                        "date":   r.get("datePublished", "N/A"),
                    }
                    for r in reviews_raw
                    if isinstance(r, dict)
                ]
        except (json.JSONDecodeError, AttributeError):
            continue

    return result


# ─────────────────────────────────────────────
#  VEHICLE
# ─────────────────────────────────────────────

def parse_vehicle(soup: BeautifulSoup, jsonld: dict) -> dict:
    v = {}

    # Name — prefer JSON-LD, fall back to h1
    v["name"] = jsonld.get("name") or clean(
        (soup.find("h1") or BeautifulSoup("", "html.parser")).get_text()
    )

    # Price — prefer JSON-LD
    if jsonld.get("price"):
        v["price_per_day"] = f"${jsonld['price']}/day"
    else:
        match = re.search(
            r"\$[\d,]+(?:\.\d{2})?\s*/?\s*day",
            soup.get_text(),
            re.IGNORECASE,
        )
        v["price_per_day"] = match.group() if match else "N/A"

    # Rating + trip count — prefer JSON-LD
    if jsonld.get("rating"):
        v["rating"]      = str(jsonld["rating"])
        v["trip_count"]  = str(jsonld.get("review_count", "N/A"))
    else:
        trip_match = re.search(
            r"(\d+\.?\d*)\s*[•·(]\s*(\d+)\s*trip",
            soup.get_text(),
            re.IGNORECASE,
        )
        if trip_match:
            v["rating"]     = trip_match.group(1)
            v["trip_count"] = trip_match.group(2)
        else:
            v["rating"]     = "N/A"
            v["trip_count"] = "N/A"

    return v


# ─────────────────────────────────────────────
#  HOST
# ─────────────────────────────────────────────

def parse_host(soup: BeautifulSoup) -> dict:
    h = {}
    page_text = soup.get_text(" ", strip=True)

    # Host name — "Hosted by X"
    name_match = re.search(
        r"[Hh]osted\s+by\s+([A-Z][a-zA-Z\s'-]{1,40}?)(?:\s+\d|\s*[·•]|\s*$)",
        page_text,
    )
    h["name"] = name_match.group(1).strip() if name_match else "N/A"

    # Trips hosted
    trips_match = re.search(r"(\d[\d,]*)\s+trips?\s+hosted", page_text, re.IGNORECASE)
    h["trips_hosted"] = trips_match.group(1).replace(",", "") if trips_match else "N/A"

    # Response rate
    resp_match = re.search(r"(\d+)%\s*response\s*rate", page_text, re.IGNORECASE)
    h["response_rate"] = f"{resp_match.group(1)}%" if resp_match else "N/A"

    # Member since
    since_match = re.search(r"[Mm]ember\s+since\s+(\w+\s+\d{4}|\d{4})", page_text)
    h["member_since"] = since_match.group(1) if since_match else "N/A"

    return h


# ─────────────────────────────────────────────
#  LISTING DETAILS
# ─────────────────────────────────────────────

def parse_details(soup: BeautifulSoup, jsonld: dict) -> dict:
    d = {}

    # Location
    d["location"] = jsonld.get("location") or _extract_location(soup)

    # Description — prefer JSON-LD
    if jsonld.get("description") and len(jsonld["description"]) > 50:
        d["description"] = clean(jsonld["description"])
    else:
        paras = [
            clean(p.get_text())
            for p in soup.find_all("p")
            if len(clean(p.get_text())) > 80
        ]
        d["description"] = paras[0] if paras else "N/A"
        d["additional_descriptions"] = paras[1:4]

    # Features — deduplicated li items of plausible length
    seen, features = set(), []
    for li in soup.find_all("li"):
        text = clean(li.get_text())
        if 4 < len(text) < 80 and text not in seen:
            seen.add(text)
            features.append(text)
    d["features"] = features[:30]

    # Vehicle specs via regex (MPG, seats, doors, transmission etc.)
    page_text = soup.get_text(" ")
    spec_patterns = {
        "mpg":          r"(\d+\s*(?:–|-)\s*\d+|\d+)\s*MPG",
        "seats":        r"(\d+)\s*seats?",
        "doors":        r"(\d+)\s*doors?",
        "transmission": r"(Automatic|Manual)\s*transmission",
        "fuel_type":    r"(Gasoline|Electric|Hybrid|Diesel)",
    }
    specs = {}
    for key, pat in spec_patterns.items():
        m = re.search(pat, page_text, re.IGNORECASE)
        if m:
            specs[key] = m.group(1) if m.lastindex else m.group()
    d["specs"] = specs

    return d


def _extract_location(soup: BeautifulSoup) -> str:
    # City, State pattern (e.g. "Los Angeles, CA")
    match = re.search(
        r"\b([A-Z][a-zA-Z\s]{2,20}),\s*([A-Z]{2})\b",
        soup.get_text(),
    )
    return f"{match.group(1)}, {match.group(2)}" if match else "N/A"


# ─────────────────────────────────────────────
#  REVIEWS
# ─────────────────────────────────────────────

def parse_reviews(soup: BeautifulSoup, jsonld: dict) -> list:
    # JSON-LD reviews are cleanest — use if available
    if jsonld.get("jsonld_reviews"):
        return jsonld["jsonld_reviews"]

    reviews = []

    # Try data-testid, class, or article containers
    containers = (
        soup.find_all(attrs={"data-testid": re.compile(r"review", re.I)})
        or soup.find_all(class_=re.compile(r"review", re.I))
        or soup.find_all("article")
    )

    for el in containers[:10]:
        text = clean(el.get_text())
        if 40 < len(text) < 1500:
            reviews.append({"text": text})

    # Last resort — blockquote / q tags
    if not reviews:
        for el in soup.find_all(["blockquote", "q"])[:10]:
            text = clean(el.get_text())
            if len(text) > 40:
                reviews.append({"text": text})

    return reviews


# ─────────────────────────────────────────────
#  ORCHESTRATOR
# ─────────────────────────────────────────────

def parse_listing(html: str) -> dict:
    soup   = BeautifulSoup(html, "lxml")
    jsonld = extract_jsonld(soup)

    return {
        "vehicle": parse_vehicle(soup, jsonld),
        "host":    parse_host(soup),
        "details": parse_details(soup, jsonld),
        "reviews": parse_reviews(soup, jsonld),
    }


# ─────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────

def main():
    url = sys.argv[1] if len(sys.argv) > 1 else input("Turo listing URL: ").strip()

    print("\n" + "=" * 55)
    print("  1Now — Phase 1: Turo Scraper")
    print("=" * 55 + "\n")

    # Step 1: load page
    html, screenshot = load_page(url)

    # Step 2: save raw outputs for debugging
    (OUTPUT_DIR / "raw.html").write_text(html, encoding="utf-8")
    (OUTPUT_DIR / "screenshot.png").write_bytes(screenshot)
    print("[✓] Saved → output/raw.html")
    print("[✓] Saved → output/screenshot.png")

    # Step 3: parse
    print("[*] Parsing listing data...")
    data = parse_listing(html)

    # Step 4: save JSON
    out_path = OUTPUT_DIR / "listing_data.json"
    out_path.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    print(f"[✓] Saved → {out_path}\n")

    # Step 5: preview
    v = data["vehicle"]
    h = data["host"]
    d = data["details"]
    r = data["reviews"]

    print("─" * 40)
    print(f"  Vehicle  : {v.get('name')}")
    print(f"  Price    : {v.get('price_per_day')}")
    print(f"  Rating   : {v.get('rating')}  ({v.get('trip_count')} trips)")
    print(f"  Host     : {h.get('name')}  [{h.get('trips_hosted')} trips hosted]")
    print(f"  Location : {d.get('location')}")
    print(f"  Specs    : {d.get('specs')}")
    print(f"  Features : {len(d.get('features', []))} items")
    print(f"  Reviews  : {len(r)} found")
    print(f"  Desc len : {len(d.get('description', ''))} chars")
    print("─" * 40)
    print("\nPhase 1 done. Feed output/listing_data.json into pipeline.py next.")


if __name__ == "__main__":
    main()
