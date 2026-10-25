"""
assistant.py — The core of the Transwork Business Assistant v1.

Flow:  Python  ->  Gemini API  ->  AI model  ->  AI response  ->  Python application

Three business functions:
  1. draft_customer_response()  - Business writing
  2. summarise_document()       - Summarisation
  3. extract_enquiry()          - Information extraction (structured JSON output)
"""

import os
from enum import Enum
from typing import List, Optional

from dotenv import load_dotenv
from pydantic import BaseModel, Field, ValidationError

import prompts

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))  # reads GEMINI_API_KEY (and optional GEMINI_MODEL) from a .env file

MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
MAX_INPUT_CHARS = 20_000  # protects cost and keeps very long inputs manageable
THINKING_LEVEL = os.getenv("GEMINI_THINKING_LEVEL", "low")  # low = faster replies

_client = None
_low_thinking_supported = True


def get_client():
    """Create the Gemini client once and reuse it."""
    global _client
    if _client is None:
        from google import genai  # imported here so tests can run without the SDK

        if not os.getenv("GEMINI_API_KEY"):
            raise RuntimeError(
                "GEMINI_API_KEY is not set. Copy .env.example to .env and paste your key."
            )
        _client = genai.Client()
    return _client


def ask_model(prompt: str, json_schema: Optional[dict] = None) -> str:
    """
    Send one prompt to Gemini and return the text of the reply.
    If json_schema is given, the model is forced to reply with JSON matching it.
    """
    client = get_client()

    # Newer SDKs: Interactions API (current Gemini quickstart)
    if hasattr(client, "interactions"):
        global _low_thinking_supported
        kwargs = {"model": MODEL, "input": prompt}
        if json_schema:
            kwargs["response_format"] = {
                "type": "text",
                "mime_type": "application/json",
                "schema": json_schema,
            }
        # Speed-up: these are simple tasks, so ask the model to think less.
        if _low_thinking_supported:
            try:
                interaction = client.interactions.create(
                    **kwargs, generation_config={"thinking_level": THINKING_LEVEL}
                )
                return interaction.output_text or ""
            except Exception as err:
                if "thinking" not in str(err).lower() and "generation_config" not in str(err).lower():
                    raise  # a different problem (e.g. no internet) — show it
                _low_thinking_supported = False  # this model/SDK doesn't support it; stop trying
                print("(Note: low-thinking speed setting not supported here — using normal mode.)")
        interaction = client.interactions.create(**kwargs)
        return interaction.output_text or ""

    # Older SDKs: generate_content API (fallback)
    config = None
    if json_schema:
        config = {"response_mime_type": "application/json", "response_json_schema": json_schema}
    response = client.models.generate_content(model=MODEL, contents=prompt, config=config)
    return response.text or ""


def _clean_input(text: str) -> str:
    """Basic input checks before we spend an API call."""
    text = (text or "").strip()
    if not text:
        raise ValueError("Input is empty. Please provide some text.")
    if len(text) > MAX_INPUT_CHARS:
        text = text[:MAX_INPUT_CHARS] + "\n[...input truncated by Transwork Assistant...]"
    return text


# ===========================================================================
# Function 1 — Business Writing
# ===========================================================================
def draft_customer_response(
    situation: str,
    staff_notes: str = "Not provided",
    customer_name: str = "Not provided",
    tone: str = "Professional and empathetic",
) -> str:
    situation = _clean_input(situation)
    prompt = prompts.WRITING_SYSTEM + "\n\n" + prompts.WRITING_TEMPLATE.format(
        customer_name=customer_name or "Not provided",
        situation=situation,
        staff_notes=staff_notes or "Not provided",
        tone=tone,
    )
    return ask_model(prompt).strip()


# ===========================================================================
# Function 2 — Summarisation
# ===========================================================================
def summarise_document(document: str) -> str:
    document = _clean_input(document)
    prompt = prompts.SUMMARY_SYSTEM + "\n\nDOCUMENT:\n\"\"\"\n" + document + "\n\"\"\""
    return ask_model(prompt).strip()


# ===========================================================================
# Function 3 — Information Extraction (structured output)
# ===========================================================================
class Category(str, Enum):
    COMPLAINT = "Complaint"
    ENQUIRY = "Enquiry"
    REQUEST = "Request"
    BILLING = "Billing"
    FEEDBACK = "Feedback"
    OTHER = "Other"


class Level(str, Enum):
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class EnquiryExtraction(BaseModel):
    """The structure every extraction must follow — easy for another system to use."""

    customer_name: Optional[str] = Field(description="Customer's name, or null if not given.")
    issue: str = Field(description="Short description of the problem or request.")
    category: Category = Field(description="Type of enquiry.")
    urgency: Level = Field(description="How urgent the case is.")
    recommended_action: str = Field(description="One clear next step for staff.")
    missing_information: List[str] = Field(description="What staff still need to ask the customer.")
    confidence: Level = Field(description="How sure the AI is about this extraction.")


def needs_human_review(data: EnquiryExtraction) -> List[str]:
    """
    Business rules written in normal Python (not AI) that decide when a person
    must check the AI's work. Rules are predictable; the AI is not.
    """
    reasons = []
    if data.urgency == Level.HIGH:
        reasons.append("High urgency case")
    if data.confidence == Level.LOW:
        reasons.append("AI confidence is low")
    if data.customer_name is None:
        reasons.append("No customer name found")
    if data.missing_information:
        reasons.append("Information is missing")
    if data.category == Category.OTHER:
        reasons.append("Not a clear customer enquiry")
    return reasons


def extract_enquiry(enquiry: str) -> dict:
    """
    Returns a dictionary like:
    {
      "customer_name": "John Mensah", "issue": "...", "category": "Complaint",
      "urgency": "High", "recommended_action": "...", "missing_information": [],
      "confidence": "High", "human_review_required": true,
      "review_reasons": ["High urgency case"]
    }
    """
    enquiry = _clean_input(enquiry)
    prompt = prompts.EXTRACTION_SYSTEM + "\n\n" + prompts.EXTRACTION_TEMPLATE.format(enquiry=enquiry)
    raw = ask_model(prompt, json_schema=EnquiryExtraction.model_json_schema())

    try:
        data = EnquiryExtraction.model_validate_json(raw)
    except ValidationError as err:
        # The model returned something that does not fit our structure.
        # We never pass broken data on — we send it to a person instead.
        return {
            "error": "AI output did not match the required structure",
            "raw_output": raw,
            "details": str(err)[:500],
            "human_review_required": True,
            "review_reasons": ["Invalid AI output"],
        }

    result = data.model_dump(mode="json")
    reasons = needs_human_review(data)
    result["human_review_required"] = bool(reasons)
    result["review_reasons"] = reasons
    return result
