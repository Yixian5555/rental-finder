import re
from urllib.parse import quote_plus

import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "en-CA,en;q=0.9",
}


def build_url(filters: dict) -> str:
    params = []

    if filters.get("min_price"):
        params.append(f"min_price={int(filters['min_price'])}")
    if filters.get("max_price"):
        params.append(f"max_price={int(filters['max_price'])}")

    # Craigslist bedroom values: 0=studio, 1=1BR, 2=2BR, 3=3BR, 4=4BR+
    min_beds = filters.get("min_bedrooms")
    max_beds = filters.get("max_bedrooms")
    if min_beds is not None:
        params.append(f"min_bedrooms={int(min_beds)}")
    if max_beds is not None:
        params.append(f"max_bedrooms={int(max_beds)}")

    if filters.get("pets"):
        params.append("pets_cat=1&pets_dog=1")
    if filters.get("furnished"):
        params.append("is_furnished=1")

    neighborhoods = filters.get("neighborhoods", [])
    if neighborhoods:
        params.append(f"query={quote_plus(' '.join(neighborhoods))}")

    return "https://vancouver.craigslist.org/search/apa?" + "&".join(params)


def _parse_price(text: str) -> int:
    m = re.search(r"\$(\d[\d,]*)", text)
    return int(m.group(1).replace(",", "")) if m else 0


def scrape(filters: dict) -> list[dict]:
    try:
        url = build_url(filters)
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")
        items = soup.select("li.cl-static-search-result")

        listings = []
        for item in items[:25]:
            a = item.find("a")
            if not a:
                continue

            title = item.get("title") or item.select_one(".title")
            title = title.get_text(strip=True) if hasattr(title, "get_text") else str(title)

            price_el = item.select_one(".price")
            price = _parse_price(price_el.get_text()) if price_el else 0

            loc_el = item.select_one(".location")
            address = loc_el.get_text(strip=True) if loc_el else ""

            listing_url = a.get("href", "")

            listings.append({
                "title": title,
                "price": price,
                "url": listing_url,
                "image": None,
                "address": address,
                "source": "Craigslist",
                "description": "",
                "posted": "",
            })

        return listings
    except Exception as e:
        print(f"[Craigslist] error: {e}")
        return []
