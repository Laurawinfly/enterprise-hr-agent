"""Small teaching redactor for traces/audit. Replace with enterprise DLP in production."""
import re
PATTERNS = [
    (re.compile(r"\b1[3-9]\d{9}\b"), "[PHONE]"),
    (re.compile(r"\b\d{17}[\dXx]\b"), "[CN_ID]"),
    (re.compile(r"(?i)(api[_-]?key|access[_-]?token|authorization)\s*[:=]\s*\S+"), r"\1=[SECRET]"),
]

def redact(value):
    if isinstance(value, str):
        for pattern, replacement in PATTERNS:
            value = pattern.sub(replacement, value)
        return value
    if isinstance(value, dict):
        return {
            key: ("[SECRET]" if any(x in key.lower() for x in ["token", "secret", "api_key", "authorization"]) else redact(val))
            for key, val in value.items()
        }
    if isinstance(value, list):
        return [redact(x) for x in value]
    return value
