# llm.py
import re
from dataclasses import dataclass
from typing import List, Tuple


@dataclass(frozen=True)
class SafetyResult:
    level: str  # "none" | "elevated" | "imminent"
    matched: List[str]


# v1 patterns
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
    # keep it short and non judgemental
    base = (
        "I’m really sorry you’re feeling this way — you don’t have to go through it alone.\n\n"
        "If you are in immediate danger or might hurt yourself, please call your local emergency number right now.\n"
        "If you’re in the U.S., you can call or text **988** (Suicide & Crisis Lifeline), or chat at 988lifeline.org.\n\n"
        "If you’re not in immediate danger, I’m here with you. "
        "Can you tell me: **are you safe right now?**"
    )

    # slightly stronger wording for imminent signals
    if level == "imminent":
        return (
            "I’m really concerned about your safety.\n\n"
            + base
            + "\n\nIf you can, consider reaching out to someone nearby you trust right now."
        )

    return base


def generate_reply(user_text: str) -> str:
    """
    Phase 1 prototype response with a basic crisis safeguard.
    Later, replace the normal path with an OpenAI call,
    but KEEP the safeguard checks before any model response.
    """
    safety = _detect_crisis(user_text)

    if safety.level != "none":
        return _crisis_message(safety.level)

    # normal prototype response
    return (
        "I hear you. Thanks for sharing that. "
        "If you want to talk more about it, I'm here to listen."
    )

