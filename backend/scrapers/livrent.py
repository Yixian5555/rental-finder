import json

import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "en-CA,en;q=0.9",
}

BED_PARAM = {0: "bachelor", 1: "one_bedroom", 2: "two_bedrooms", 3: "three_plus_bedrooms"}


def build_url(filters: dict) -> str:
    base = "https://liv.rent/rental-listings/canada/british-columbia/vancouver"
    params = []

    if filters.get("min_price") is not None:
        params.append(f"price_min={int(filters['min_price'])}")
    if filters.get("max_price") is not None:
        params.append(f"price_max={int(filters['max_price'])}")

    min_beds = filters.get("min_bedrooms")
    if min_beds is not None:
        bed_type = BED_PARAM.get(int(min_beds), "one_bedroom")
        params.append(f"bedroom_types={bed_type}")

    if filters.get("furnished"):
        params.append("furnished=true")
    if filters.get("pets"):
        params.append("pets_allowed=true")
    if filters.get("parking"):
        params.append("parking=true")
    if filters.get("laundry_in_suite"):
        params.append("laundry=in_suite")

    return base + ("?" + "&".join(params) if params else "")


def _dig(data: dict, *keys):
    for key in keys:
        if isinstance(data, dict):
            data = data.get(key)
        else:
            return None
    return data


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
        page_props = _dig(data, "props", "pageProps") or {}

        raw = []
        for key in ("listings", "rentals", "units", "data", "items"):
            candidate = page_props.get(key)
            if isinstance(candidate, list) and candidate:
                raw = candidate
                break
            if isinstance(candidate, dict):
                for sub in ("listings", "rentals", "data", "items"):
                    sub_list = candidate.get(sub)
                    if isinstance(sub_list, list) and sub_list:
                        raw = sub_list
                        break
            if raw:
                break

        listings = []
        for item in raw[:25]:
            price = item.get("price") or item.get("monthly_rent") or 0
            if isinstance(price, dict):
                price = price.get("amount", 0)

            photos = item.get("photos") or item.get("images") or item.get("media") or []
            image = None
            if isinstance(photos, list) and photos:
                first = photos[0]
                if isinstance(first, str):
                    image = first
                elif isinstance(first, dict):
                    image = first.get("url") or first.get("src") or first.get("thumb")

            slug = item.get("slug") or item.get("id") or ""
            listing_url = f"https://liv.rent/rental-listings/canada/british-columbia/vancouver/{slug}" if slug else url

            loc = item.get("location") or {}
            if isinstance(loc, dict):
                address = loc.get("full_address") or loc.get("address") or loc.get("city") or ""
            else:
                address = item.get("address", "")

            listings.append({
                "title": item.get("title") or item.get("name") or "",
                "price": int(price) if price else 0,
                "url": listing_url,
                "image": image,
                "address": address,
                "source": "liv.rent",
                "description": (item.get("description") or "")[:250],
                "posted": item.get("created_at") or item.get("listed_at") or "",
            })

        return listings
    except Exception as e:
        print(f"[liv.rent] error: {e}")
        return []
