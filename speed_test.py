"""
speed_test.py — Compares models to find the fastest one for your key and network.
Run:  python speed_test.py   and copy the output (it never prints your key).
Each test gives up after 60 seconds.
"""

import os
import time

from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

from google import genai

PROMPT = "Reply with just the word OK."
MODELS = [
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite",
    "gemini-flash-lite-latest",
    "gemini-2.5-flash-lite",
    os.getenv("GEMINI_MODEL", "gemini-3.8-flash"),
]

client = genai.Client(http_options={"timeout": 60_000})  # milliseconds

# Quick network check: listing models is a small, simple request
start = time.time()
try:
    next(iter(client.models.list()))
    print(f"Network check (list models): {time.time() - start:.1f}s\n")
except Exception as err:
    print(f"Network check failed: {str(err)[:150]}\n")


def timed(label, fn):
    start = time.time()
    try:
        fn()
        result = "OK"
    except Exception as err:
        result = "ERROR: " + str(err)[:120]
    print(f"{label:<48} {time.time() - start:6.1f}s  {result}")


for model in dict.fromkeys(MODELS):  # removes duplicates, keeps order
    timed(f"{model}  [interactions]",
          lambda: client.interactions.create(model=model, input=PROMPT))
    timed(f"{model}  [generate_content]",
          lambda: client.models.generate_content(model=model, contents=PROMPT))
