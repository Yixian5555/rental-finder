import re
from urllib.parse import quote_plus

import feedparser
import requests
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}


def build_url(filters: dict) -> str:
    params = ["format=rss"]

    if filters.get("min_price") is not None:
        params.append(f"min_price={int(filters['min_price'])}")
    if filters.get("max_price") is not None:
        params.append(f"max_price={int(filters['max_price'])}")

    min_beds = filters.get("min_bedrooms", 0)
    if min_beds and min_beds > 0:
        params.append(f"min_bedrooms={min_beds}")

    max_beds = filters.get("max_bedrooms")
    if max_beds is not None and max_beds >= 0:
        params.append(f"max_bedrooms={max_beds}")

    if filters.get("pets"):
        params.append("pets_cat=1&pets_dog=1")

    if filters.get("furnished"):
        params.append("is_furnished=1")

    neighborhoods = filters.get("neighborhoods", [])
    if neighborhoods:
        query = " ".join(neighborhoods)
        params.append(f"query={quote_plus(query)}")

    return "https://vancouver.craigslist.org/search/apa?" + "&".join(params)


def extract_image(html: str) -> str | None:
    try:
        soup = BeautifulSoup(html, "html.parser")
        img = soup.find("img")
        if img:
            src = img.get("src", "")
            return src.replace("_300x300", "_600x450").replace("_50x50c", "_600x450")
    except Exception:
        pass
    return None


def parse_price(title: str) -> int:
    match = re.search(r"\$(\d[\d,]*)", title)
    if match:
        return int(match.group(1).replace(",", ""))
    return 0


def scrape(filters: dict) -> list[dict]:
    try:
        url = build_url(filters)
        resp = requests.get(url, headers=HEADERS, timeout=15)
        feed = feedparser.parse(resp.content)
        listings = []

        for entry in feed.entries[:25]:
            title = entry.get("title", "")
            image = extract_image(entry.get("summary", ""))
            description = BeautifulSoup(entry.get("summary", ""), "html.parser").get_text()[:250]

            # Extract address from title "(address)" pattern
            address = ""
            addr_match = re.search(r"\(([^)]+)\)\s*$", title)
            if addr_match:
                address = addr_match.group(1)

            listings.append({
                "title": title,
                "url": entry.get("link", ""),
                "price": parse_price(title),
                "image": image,
                "address": address,
                "source": "Craigslist",
                "description": description.strip(),
                "posted": entry.get("published", ""),
            })

        return listings
    except Exception as e:
        print(f"[Craigslist] error: {e}")
        return []
