import json
from urllib.parse import quote_plus

import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "en-CA,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

BED_CODE = {0: 1, 1: 2, 2: 3, 3: 4, 4: 5}


def build_url(filters: dict) -> str:
    base = "https://www.kijiji.ca/b-apartments-condos/city-of-vancouver/c37l1700287"
    params = []

    min_p = int(filters.get("min_price", 0) or 0)
    max_p = int(filters.get("max_price", 0) or 0)
    if max_p:
        params.append(f"price={min_p}__{max_p}" if min_p else f"price=__{max_p}")

    min_beds = filters.get("min_bedrooms")
    max_beds = filters.get("max_bedrooms")
    if min_beds is not None:
        min_code = BED_CODE.get(int(min_beds), 2)
        max_code = BED_CODE.get(int(max_beds), min_code) if max_beds is not None else min_code
        for code in range(min_code, max_code + 1):
            params.append(f"numBedrooms={code}")

    if filters.get("furnished"):
        params.append("isFurnished=1")

    if filters.get("pets"):
        params.append("petsAllowed=1")

    neighborhoods = filters.get("neighborhoods", [])
    if neighborhoods:
        params.append(f"keywords={quote_plus(' '.join(neighborhoods))}")

    return base + ("?" + "&".join(params) if params else "")


def _attr(attributes_list: list, name: str) -> str:
    for a in attributes_list:
        if a.get("canonicalName") == name:
            vals = a.get("canonicalValues", [])
            return vals[0] if vals else ""
    return ""


def _attr_int(attributes_list: list, name: str) -> int:
    try:
        return int(_attr(attributes_list, name) or 0)
    except (ValueError, TypeError):
        return 0


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
        apollo = data.get("props", {}).get("pageProps", {}).get("__APOLLO_STATE__", {})
        if not apollo:
            return []

        listings = []
        for key, item in apollo.items():
            if not key.startswith("RealEstateListing:"):
                continue

            # Price: stored in cents (e.g., 295000 = $2,950); may be "Not Available"
            price_obj = item.get("price", {})
            raw_amount = price_obj.get("amount", 0) if isinstance(price_obj, dict) else 0
            try:
                price = int(raw_amount) // 100 if raw_amount else 0
            except (TypeError, ValueError):
                price = 0

            # Image: upgrade thumbnail to larger size
            image_urls = item.get("imageUrls", [])
            image = None
            if image_urls:
                image = image_urls[0].replace("kijijica-200-jpg", "kijijica-640-jpg")

            # Location
            loc = item.get("location", {})
            address = ""
            if isinstance(loc, dict):
                address = loc.get("address") or loc.get("name") or ""

            # Attributes
            attrs_all = []
            attrs_obj = item.get("attributes", {})
            if isinstance(attrs_obj, dict):
                attrs_all = attrs_obj.get("all", [])

            listings.append({
                "title": item.get("title", ""),
                "price": price,
                "url": item.get("url", ""),
                "image": image,
                "address": address,
                "source": "Kijiji",
                "description": (item.get("description") or "")[:250],
                "posted": item.get("activationDate") or item.get("sortingDate") or "",
                "bedrooms": _attr(attrs_all, "numberbedrooms"),
                "pets": _attr(attrs_all, "petsallowed") == "1",
                "parking": _attr_int(attrs_all, "numberparkingspots") > 0,
                "laundry_in_suite": _attr(attrs_all, "laundryinunit") == "1",
            })

            if len(listings) >= 25:
                break

        return listings
    except Exception as e:
        print(f"[Kijiji] error: {e}")
        return []
