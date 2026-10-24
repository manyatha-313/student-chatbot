"""Gemma 4 client (Google AI Studio). Adapted from the HackDay starter kit.

Loads GOOGLE_API_KEY from .env or the environment. With no key the app still
runs in DEMO_MODE: retrieval works and the passages are shown in place of a
written answer.
"""
import os

from dotenv import load_dotenv
from google import genai
from google.genai import types, errors

import config

load_dotenv()  # read GOOGLE_API_KEY from a local .env if present

GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
DEMO_MODE = not GOOGLE_API_KEY
_client = None if DEMO_MODE else genai.Client(api_key=GOOGLE_API_KEY)


def _friendly_error(e):
    code = getattr(e, "code", None)
    if code in (400, 401, 403) and "key" in str(e).lower():
        return "Error: the GOOGLE_API_KEY was rejected. Check the complete key is saved in .env, then try again."
    if code == 429:
        return "Error: the free-tier usage limit has been reached. Wait about one minute and try again."
    if code == 404:
        return f"Error: the model '{config.GEMMA_MODEL}' was not found. Check the GEMMA_MODEL setting."
    return f"Error: the request to Gemma failed ({e})."


def generate(user_text, system_text=None, temperature=config.TEMPERATURE,
             demo_reply="(Demonstration mode response)"):
    """Send one message to Gemma and return its reply as text.

    In demo mode returns `demo_reply`. On failure returns a string starting
    with "Error:".
    """
    if DEMO_MODE:
        return demo_reply
    try:
        response = _client.models.generate_content(
            model=config.GEMMA_MODEL,
            contents=user_text,
            config=types.GenerateContentConfig(
                system_instruction=system_text,
                temperature=temperature,
                thinking_config=types.ThinkingConfig(thinking_level="minimal"),  # faster replies
            ),
        )
        return (response.text or "").strip()
    except errors.APIError as e:
        return _friendly_error(e)
    except Exception as e:
        return f"Error: {e}"
