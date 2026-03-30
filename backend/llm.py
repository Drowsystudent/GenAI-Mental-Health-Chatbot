import os
import re
import random
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

ELEVATION_PROMPT = (
    "The user may be in an elevated emotional state. "
    "Respond more carefully than usual. "
    "Stay calm, grounding, and supportive. "
    "Help slow things down. "
    "If helpful, encourage the user to focus on the next few minutes instead of everything at once. "
    "You may gently ask whether they are safe right now, but do not jump straight into an emergency-style response "
    "unless the message clearly suggests immediate danger. "
    "You may use simple grounding ideas like slow breathing, noticing physical surroundings, "
    "or focusing on one immediate next step. "
    "Keep the response human and natural, not robotic or overly scripted."
)


@dataclass(frozen=True)
class SafetyResult:
    level: str  # "none" | "elevated" | "imminent"
    matched: List[str]


_IMMINENT_PATTERNS: List[Tuple[str, re.Pattern]] = [
    # Direct intent
    ("explicit_intent", re.compile(
        r"\b(i want to die|i want to kill myself|i'm going to kill myself|im going to kill myself|end my life)\b",
        re.I
    )),

    # Time + intent combined
    ("timeframe", re.compile(
        r"\b(tonight|today|right now|soon)\b.*\b(kill myself|suicide|end my life|hurt myself)\b|"
        r"\b(kill myself|suicide|end my life|hurt myself)\b.*\b(tonight|today|right now|soon)\b",
        re.I
    )),

    # Planning / preparation
    ("plan", re.compile(
        r"\b(i have a plan|i planned it|my plan is|i wrote a note|i said goodbye)\b",
        re.I
    )),

    # Means / method
    ("means", re.compile(
        r"\b(overdose|od|pills|gun|knife|rope|razor)\b",
        re.I
    )),

    # Harm to others
    ("harm_to_others", re.compile(
        r"\b(i want to hurt someone|i want to kill someone|i'm going to hurt someone|attack someone)\b",
        re.I
    )),
]


_ELEVATED_PATTERNS: List[Tuple[str, re.Pattern]] = [
    # Passive death / giving up
    ("passive_death_wish", re.compile(
        r"\b(i don't want to be here|i dont want to be here|wish i were dead|don't want to wake up|dont want to wake up)\b",
        re.I
    )),

    # Hopelessness
    ("hopelessness", re.compile(
        r"\b(no reason to live|can't go on|cant go on|everyone would be better off without me|there is no point|i can't do this anymore|i cant do this anymore)\b",
        re.I
    )),

    # Self harm
    ("self_harm", re.compile(
        r"\b(self[- ]?harm|cut myself|cutting|burn myself|hurt myself)\b",
        re.I
    )),

    # General suicidal language
    ("suicidal_terms", re.compile(
        r"\b(suicidal|suicide)\b",
        re.I
    )),
]


def _detect_crisis(user_text: str) -> SafetyResult:
    text = (user_text or "").strip()
    if not text:
        return SafetyResult(level="none", matched=[])

    matched: List[str] = []

    # Check strong signals first
    for name, pattern in _IMMINENT_PATTERNS:
        if pattern.search(text):
            matched.append(name)

    # If we have strong intent + plan/means/time → definitely imminent
    if "explicit_intent" in matched and (
        "timeframe" in matched or "plan" in matched or "means" in matched
    ):
        return SafetyResult(level="imminent", matched=matched)

    # Harm to others should always be taken seriously
    if "harm_to_others" in matched:
        return SafetyResult(level="imminent", matched=matched)

    # Multiple strong signals → escalate
    if len(matched) >= 2:
        return SafetyResult(level="imminent", matched=matched)

    # Now check softer signals
    for name, pattern in _ELEVATED_PATTERNS:
        if pattern.search(text):
            matched.append(name)

    if matched:
        # If there's any strong + soft combo → escalate harder
        strong = {"explicit_intent", "timeframe", "plan", "means", "harm_to_others"}
        if any(m in strong for m in matched) and len(matched) >= 2:
            return SafetyResult(level="imminent", matched=matched)

        return SafetyResult(level="elevated", matched=matched)

    return SafetyResult(level="none", matched=matched)


def _crisis_message(level: str) -> str:
    imminent_templates = [
        (
            "I'm really concerned about your safety right now.\n\n"
            "You matter, and I don't want to treat this like a normal conversation.\n\n"
            "If you are in immediate danger or think you may hurt yourself, call your local emergency number right now. "
            "If you're in the U.S., call or text 988 (Suicide & Crisis Lifeline), or chat at 988lifeline.org.\n\n"
            "If you can, please reach out to someone nearby you trust and tell them you need support right now.\n\n"
            "Are you safe right now?"
        ),
        (
            "I'm glad you said that out loud, because this sounds serious and I want to respond carefully.\n\n"
            "If you're in immediate danger or may act on this, call your local emergency number right now. "
            "If you're in the U.S., call or text 988, or use 988lifeline.org for immediate support.\n\n"
            "If there is anyone near you that you trust, please contact them now and let them know you should not be alone.\n\n"
            "Can you tell me whether you are safe right now?"
        ),
        (
            "I'm really sorry you're carrying this right now, and I need to take your safety seriously.\n\n"
            "If you might hurt yourself or are in immediate danger, call your local emergency number right now. "
            "If you're in the U.S., call or text 988, or chat at 988lifeline.org.\n\n"
            "If possible, reach out to someone close to you and let them know you need support right now.\n\n"
            "Are you safe right now?"
        ),
    ]

    if level == "imminent":
        return random.choice(imminent_templates)


def _openai_reply(user_text: str, history: list[dict] | None = None, elevated: bool = False) -> str:
    if not API_KEY or client is None:
        return "[Server misconfig] OPENAI_API_KEY is not set."

    prompt = SYSTEM_PROMPT
    if elevated:
        prompt += "\n\n" + ELEVATION_PROMPT
        print("openai_reply elevated section")

    messages = [
        {"role": "system", "content": prompt}
    ]

    if history:
        for msg in history:
            role = msg.get("role")
            content = msg.get("content")

            if role in {"user", "assistant"} and isinstance(content, str):
                messages.append({
                    "role": role,
                    "content": content
                })

    messages.append({
        "role": "user",
        "content": user_text
    })

    try:
        resp = client.responses.create(
            model=MODEL,
            input=messages,
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

def generate_reply(user_text: str, history: list[dict] | None = None) -> tuple[str, str]:
    """
    Returns (reply, safety_level).
    safety_level is one of: "none" | "elevated" | "imminent"
    """
    safety = _detect_crisis(user_text)

    if safety.level == "imminent":
        return _crisis_message(safety.level), safety.level

    if safety.level == "elevated":
        return _openai_reply(user_text, history, elevated=True), "elevated"

    return _openai_reply(user_text, history, elevated=False), "none"