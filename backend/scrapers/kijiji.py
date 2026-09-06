import json
from urllib.parse import quote_plus

import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "en-CA,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# Kijiji bedroom filter codes
BED_CODE = {0: 1, 1: 2, 2: 3, 3: 4, 4: 5}


def build_url(filters: dict) -> str:
    base = "https://www.kijiji.ca/b-apartments-condos/city-of-vancouver/c37l1700287"
    params = []

    min_p = int(filters.get("min_price", 0) or 0)
    max_p = int(filters.get("max_price", 0) or 0)
    if max_p:
        params.append(f"price={min_p}__{max_p}" if min_p else f"price=__{max_p}")

    min_beds = filters.get("min_bedrooms")
    if min_beds is not None:
        code = BED_CODE.get(int(min_beds), 2)
        params.append(f"numBedrooms={code}")

    if filters.get("furnished"):
        params.append("isFurnished=1")

    if filters.get("pets"):
        params.append("petsAllowed=1")

    neighborhoods = filters.get("neighborhoods", [])
    if neighborhoods:
        params.append(f"keywords={quote_plus(' '.join(neighborhoods))}")

    return base + ("?" + "&".join(params) if params else "")


def scrape(filters: dict) -> list[dict]:
    try:
        url = build_url(filters)
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")
        script = soup.find("script", id="__NEXT_DATA__")
        if not script:
            return []

        data = json.loads(script.string)
        page_props = data.get("props", {}).get("pageProps", {})

        raw = []
        for key in ("listings", "ads", "searchResults"):
            candidate = page_props.get(key)
            if isinstance(candidate, list) and candidate:
                raw = candidate
                break

        listings = []
        for item in raw[:25]:
            # Price
            price_raw = item.get("price", {})
            if isinstance(price_raw, dict):
                price = int(price_raw.get("amount", 0)) // 100
            elif isinstance(price_raw, (int, float)):
                price = int(price_raw)
            else:
                price = 0

            # Image
            images = item.get("images") or item.get("thumbnails") or []
            image = None
            if isinstance(images, list) and images:
                first = images[0]
                image = first if isinstance(first, str) else first.get("src") or first.get("url")

            # URL
            ad_id = item.get("id") or item.get("adId", "")
            slug = item.get("seoUrl") or item.get("url") or ""
            if slug and not slug.startswith("http"):
                listing_url = f"https://www.kijiji.ca{slug}"
            elif slug:
                listing_url = slug
            else:
                listing_url = f"https://www.kijiji.ca/v-apartments-condos/city-of-vancouver/a/{ad_id}"

            # Address
            loc = item.get("location") or {}
            address = loc.get("name") or loc.get("city") or "" if isinstance(loc, dict) else str(loc)

            listings.append({
                "title": item.get("title", ""),
                "price": price,
                "url": listing_url,
                "image": image,
                "address": address,
                "source": "Kijiji",
                "description": (item.get("description") or "")[:250],
                "posted": item.get("activationDate") or item.get("sortingDate") or "",
            })

        return listings
    except Exception as e:
        print(f"[Kijiji] error: {e}")
        return []
