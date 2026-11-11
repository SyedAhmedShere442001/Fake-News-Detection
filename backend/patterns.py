"""Heuristic detection of suspicious language patterns.

These signals are independent of the ML model and flag writing styles
commonly associated with misleading content. They are advisory only.
"""
import re

CLICKBAIT_PHRASES = [
    "you won't believe", "you wont believe", "shocking", "doctors hate",
    "this one weird trick", "the truth about", "they don't want you to know",
    "the real reason", "gone wrong", "will blow your mind", "blow your mind",
    "you'll never guess", "youll never guess", "what happens next",
    "is a hoax", "the government is hiding", "mainstream media won't",
    "wake up america", "share this before", "before it's deleted",
    "before its deleted", "spread the word before",
]

SENSATIONAL_WORDS = [
    "miracle", "cure", "cures", "cancer", "poison", "conspiracy",
    "cover-up", "coverup", "secret", "exposed", "bombshell", "chaos",
    "panic", "breakthrough", "destroyed", "banned", "censored",
]

UNVERIFIED_CLAIM_MARKERS = [
    "a study shows", "studies show", "researchers say", "experts say",
    "scientists discovered", "reportedly", "rumor has it", "it is said",
    "many people are saying", "insiders claim", "sources say",
]

DEFAULT_SOURCE_CUES = [
    "according to", "reuters", "ap news", "associated press", "afp",
    "bbc", "quoted", "in a statement", "the report said", "said in",
    "told reporters", "press release", "officials said",
]


def _count_caps_words(text):
    words = re.findall(r"\b[A-Z]{3,}\b", text)
    alpha_words = re.findall(r"\b[A-Za-z]+\b", text)
    if not alpha_words:
        return 0.0, []
    ratio = len(words) / len(alpha_words)
    return ratio, words[:10]


def _find_phrases(text, phrases):
    lower = text.lower()
    return [p for p in phrases if p in lower]


def analyze_patterns(text, source_cues=None):
    """Return a list of suspicious-pattern findings for a news text."""
    cues = source_cues if source_cues is not None else DEFAULT_SOURCE_CUES
    findings = []
    lower = text.lower()
    word_count = len(re.findall(r"\b\w+\b", text))

    clickbait = _find_phrases(lower, CLICKBAIT_PHRASES)
    if clickbait:
        findings.append({
            "type": "clickbait_language",
            "severity": "high" if len(clickbait) > 1 else "medium",
            "description": "Clickbait-style phrasing detected",
            "matches": clickbait[:5],
        })

    sensational = _find_phrases(lower, SENSATIONAL_WORDS)
    if sensational:
        findings.append({
            "type": "sensationalist_wording",
            "severity": "medium",
            "description": "Sensational or emotionally charged wording",
            "matches": sensational[:5],
        })

    unverified = _find_phrases(lower, UNVERIFIED_CLAIM_MARKERS)
    if unverified:
        findings.append({
            "type": "unverified_claims",
            "severity": "high",
            "description": "Claims attributed without a verifiable source",
            "matches": unverified[:5],
        })

    if word_count >= 30 and not _find_phrases(lower, cues):
        findings.append({
            "type": "missing_attribution",
            "severity": "medium",
            "description": "No source attribution cues found in the text",
            "matches": [],
        })

    caps_ratio, caps_words = _count_caps_words(text)
    if caps_ratio > 0.08 and caps_ratio < 1.0:
        findings.append({
            "type": "excessive_capitalization",
            "severity": "low",
            "description": f"Unusually high ratio of ALL-CAPS words ({caps_ratio:.0%})",
            "matches": caps_words,
        })

    if re.search(r"[!?]{3,}", text):
        findings.append({
            "type": "excessive_punctuation",
            "severity": "low",
            "description": "Repeated exclamation/question marks",
            "matches": re.findall(r"\S*[!?]{3,}\S*", text)[:5],
        })

    if word_count < 30:
        findings.append({
            "type": "insufficient_text",
            "severity": "info",
            "description": "Very short text — model confidence may be unreliable",
            "matches": [],
        })

    severity_rank = {"high": 0, "medium": 1, "low": 2, "info": 3}
    findings.sort(key=lambda f: severity_rank.get(f["severity"], 4))
    return findings
