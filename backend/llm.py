import os
import re
from dataclasses import dataclass
from typing import List, Tuple

from dotenv import load_dotenv
from openai import OpenAI, RateLimitError

load_dotenv(dotenv_path="backend/.env")

API_KEY = os.getenv("OPENAI_API_KEY")
print("API KEY LOADED:", bool(API_KEY))

MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")

client = OpenAI(api_key=API_KEY) if API_KEY else None


SYSTEM_PROMPT = (
    "You are a supportive mental-health check-in assistant. "
    "Be calm, neutral, thoughtful, and non-judgmental. "
    "Do not diagnose and do not provide medical advice. "
    "Do not be overly agreeable, overly flattering, or mechanically validating. "
    "Avoid empty phrases like 'that sounds really hard' unless they add real value. "
    "Do not automatically assume the user's interpretation of events is fully correct. "
    "Instead, help the user explore their thoughts and emotions with gentle, specific questions. "
    "When appropriate, respectfully challenge black-and-white thinking, harsh self-judgment, "
    "mind-reading, catastrophizing, or avoidance. "
    "Use a tone that feels human, grounded, and emotionally intelligent. "
    "Usually respond in 2-4 sentences. "
    "Whenever possible, include one helpful follow-up question that encourages self-reflection."
)


@dataclass(frozen=True)
class SafetyResult:
    level: str  # "none" | "elevated" | "imminent"
    matched: List[str]


_IMMINENT_PATTERNS: List[Tuple[str, re.Pattern]] = [
    ("explicit_intent", re.compile(r"\b(i want to die|i[' ]?m going to kill myself|im going to kill myself|end my life)\b", re.I)),
    ("timeframe", re.compile(r"\b(tonight|today|right now)\b.*\b(kill myself|suicide|end my life)\b|\b(kill myself|suicide|end my life)\b.*\b(tonight|today|right now)\b", re.I)),
    ("plan", re.compile(r"\b(i have a plan|i planned it|my plan is to)\b.*\b(kill myself|suicide|end my life|overdose|od)\b", re.I)),
    ("method_overdose", re.compile(r"\b(overdose|od)\b", re.I)),
]

_ELEVATED_PATTERNS: List[Tuple[str, re.Pattern]] = [
    ("suicidal_terms", re.compile(r"\b(suicidal|suicide)\b", re.I)),
    ("self_harm", re.compile(r"\b(self[- ]?harm|cut myself|cutting)\b", re.I)),
    ("passive_death_wish", re.compile(r"\b(don[' ]?t want to live|dont want to live|wish i were dead|no reason to live|can[' ]?t go on|cant go on)\b", re.I)),
]


def _detect_crisis(user_text: str) -> SafetyResult:
    text = (user_text or "").strip()
    if not text:
        return SafetyResult(level="none", matched=[])

    matched: List[str] = []

    for name, pattern in _IMMINENT_PATTERNS:
        if pattern.search(text):
            matched.append(name)

    if matched:
        return SafetyResult(level="imminent", matched=matched)

    for name, pattern in _ELEVATED_PATTERNS:
        if pattern.search(text):
            matched.append(name)

    if matched:
        return SafetyResult(level="elevated", matched=matched)

    return SafetyResult(level="none", matched=[])


def _crisis_message(level: str) -> str:
    base = (
        "I’m really sorry you’re feeling this way — you don’t have to go through it alone.\n\n"
        "If you are in immediate danger or might hurt yourself, please call your local emergency number right now.\n"
        "If you’re in the U.S., you can call or text 988 (Suicide & Crisis Lifeline), or chat at 988lifeline.org.\n\n"
        "If you’re not in immediate danger, I’m here with you. Can you tell me: are you safe right now?"
    )

    if level == "imminent":
        return (
            "I’m really concerned about your safety.\n\n"
            + base
            + "\n\nIf you can, consider reaching out to someone nearby you trust right now."
        )

    return base


def _openai_reply(user_text: str) -> str:
    if not API_KEY or client is None:
        return "[Server misconfig] OPENAI_API_KEY is not set."

    try:
        resp = client.responses.create(
            model=MODEL,
            input=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_text},
            ],
        )
        return resp.output_text

    except RateLimitError as e:
        print("OPENAI RATE LIMIT ERROR:", e)
        return "The language model is temporarily unavailable right now. Please try again in a little while."

    except Exception as e:
        print("OPENAI GENERAL ERROR:", e)
        return "Something went wrong while generating a response. Please try again."

print("generate_reply() was called")
print("Using model:", MODEL)
print("Key loaded:", bool(API_KEY))

def generate_reply(user_text: str) -> tuple[str, str]:
    """
    Returns (reply, safety_level).
    safety_level is one of: "none" | "elevated" | "imminent"
    """
    safety = _detect_crisis(user_text)

    if safety.level != "none":
        return _crisis_message(safety.level), safety.level

    return _openai_reply(user_text), "none"