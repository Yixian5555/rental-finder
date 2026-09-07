import json
import os
import re
from datetime import date
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

SYSTEM_TEMPLATE = """You are a friendly rental search assistant helping someone find apartments in Vancouver, BC.

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

FILTERS_JSON:{{"ready":true,"filters":{{"min_price":0,"max_price":2500,"min_bedrooms":1,"max_bedrooms":1,"neighborhoods":["Kitsilano"],"pets":false,"furnished":false,"parking":false,"laundry_in_suite":false}}}}

Rules for the JSON:
- studio/bachelor → min_bedrooms:0, max_bedrooms:0
- 1 bed → min_bedrooms:1, max_bedrooms:1
- "1 or 2 beds" → min_bedrooms:1, max_bedrooms:2
- neighborhoods: empty array [] means anywhere in Vancouver
- pets: true if they have any pet
- If no min price given, use 0; if no max price, use 5000
- Do NOT append FILTERS_JSON if you still need more info — keep asking
- Today's date is {today}"""


def _extract_filters(text: str) -> dict:
    filters = None
    if "FILTERS_JSON:" in text:
        try:
            m = re.search(r"FILTERS_JSON:\s*(\{.*\})\s*$", text, re.DOTALL)
            if m:
                data = json.loads(m.group(1))
                if data.get("ready"):
                    filters = data["filters"]
        except Exception:
            pass
        text = text.split("FILTERS_JSON:")[0].strip()
    return {"message": text, "filters": filters}


def _chat_claude(messages: list[dict]) -> dict:
    from anthropic import Anthropic
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY is not set.")
    client = Anthropic(api_key=api_key)
    system = SYSTEM_TEMPLATE.format(today=date.today().isoformat())
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=system,
        messages=messages,
    )
    return _extract_filters(response.content[0].text)


def _chat_openai(messages: list[dict]) -> dict:
    from openai import OpenAI
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set.")
    client = OpenAI(api_key=api_key)
    system = SYSTEM_TEMPLATE.format(today=date.today().isoformat())
    oai_messages = [{"role": "system", "content": system}] + messages
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        max_tokens=1024,
        messages=oai_messages,
    )
    return _extract_filters(response.choices[0].message.content)


def _chat_gemini(messages: list[dict]) -> dict:
    from google import genai
    from google.genai import types
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set.")
    client = genai.Client(api_key=api_key)
    system = SYSTEM_TEMPLATE.format(today=date.today().isoformat())

    contents = []
    for msg in messages:
        role = "user" if msg["role"] == "user" else "model"
        contents.append(types.Content(role=role, parts=[types.Part(text=msg["content"])]))

    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=contents,
        config=types.GenerateContentConfig(system_instruction=system, max_output_tokens=1024),
    )
    return _extract_filters(response.text)


def process_chat(messages: list[dict], provider: str = "claude") -> dict:
    if provider == "openai":
        return _chat_openai(messages)
    if provider == "gemini":
        return _chat_gemini(messages)
    return _chat_claude(messages)


def available_providers() -> list[str]:
    providers = []
    if os.environ.get("ANTHROPIC_API_KEY"):
        providers.append("claude")
    if os.environ.get("OPENAI_API_KEY"):
        providers.append("openai")
    if os.environ.get("GEMINI_API_KEY"):
        providers.append("gemini")
    return providers
