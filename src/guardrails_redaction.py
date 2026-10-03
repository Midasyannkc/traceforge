"""
PII redaction layer standing in for Amazon Bedrock Guardrails' PII filter
on agent output text (see data/bronze/SOURCE.md). Demonstrates Incident 4:
a naive regex pattern covers the dash- and space-separated US phone-number
formats but misses the dot-separated format (e.g. 214.690.1014), a real,
commonly occurring variant, so PII leaks through into stored agent output
text. The fix extends the pattern to cover the dot-separated variant too,
verified against real events from the synthetic generator where it is
deliberately present.
"""
import re

NAIVE_PHONE_PATTERN = re.compile(r"\b\d{3}[-\s]\d{3}[-\s]\d{4}\b")
FIXED_PHONE_PATTERN = re.compile(r"\b\d{3}[-.\s]\d{3}[-.\s]\d{4}\b")

REDACTED = "[REDACTED PHONE]"


def redact_naive(text):
    return NAIVE_PHONE_PATTERN.sub(REDACTED, text)



def scan_events_for_leaked_pii(events, redact_fn):
    """Returns the events whose output_text still contains an unredacted
    dot-separated phone number after running redact_fn."""
    dotted_phone = re.compile(r"\b\d{3}\.\d{3}\.\d{4}\b")
    leaked = []
    for e in events:
        text = e.get("output_text") or ""
        redacted = redact_fn(text)
        if dotted_phone.search(redacted):
            leaked.append(e)
    return leaked
