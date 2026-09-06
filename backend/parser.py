import json
import os
from pathlib import Path

from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

SYSTEM = """You are a friendly rental search assistant helping someone find apartments in Vancouver, BC.

Collect these preferences through natural conversation — ask 1-2 topics at a time, be warm and concise:
1. Preferred neighborhoods/areas (Kitsilano, Downtown, Mount Pleasant, Commercial Drive, East Van, West End, Burnaby, etc.)
2. Monthly budget (max rent, or range)
3. Number of bedrooms (studio/bachelor, 1 bed, 2 bed, 3 bed+)
4. Move-in date
5. Pets (what kind?)
6. Furnished or unfurnished?
7. Parking needed?
8. Laundry preference (in-suite, shared, no preference)?

When you have at minimum budget + bedrooms + at least one area preference (or "anywhere"), append this exact block at the very END of your message:

FILTERS_JSON:{"ready":true,"filters":{"min_price":0,"max_price":2500,"min_bedrooms":1,"max_bedrooms":1,"neighborhoods":["Kitsilano"],"pets":false,"furnished":false,"parking":false,"laundry_in_suite":false}}

Rules for the JSON:
- studio/bachelor → min_bedrooms:0, max_bedrooms:0
- 1 bed → min_bedrooms:1, max_bedrooms:1
- "1 or 2 beds" → min_bedrooms:1, max_bedrooms:2
- neighborhoods: empty array [] means anywhere in Vancouver
- pets: true if they have any pet
- If no min price given, use 0; if no max price, use 5000
- Do NOT append FILTERS_JSON if you still need more info — keep asking
- Today's date is 2026-09-06"""


def process_chat(messages: list[dict]) -> dict:
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=SYSTEM,
        messages=messages,
    )

    text = response.content[0].text
    filters = None

    if "FILTERS_JSON:" in text:
        try:
            json_str = text.split("FILTERS_JSON:")[1].strip()
            data = json.loads(json_str)
            if data.get("ready"):
                filters = data["filters"]
        except Exception:
            pass
        text = text.split("FILTERS_JSON:")[0].strip()

    return {"message": text, "filters": filters}
