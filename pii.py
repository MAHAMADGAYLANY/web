import re
from typing import Dict, List, Tuple

from cryptography.fernet import Fernet


EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE_RE = re.compile(r"^\+?[\d\s().-]{7,}$")
PII_NAME_HINTS = ("name", "email", "phone", "address")


def detect_pii(record: Dict[str, str]) -> List[str]:
    detected = []
    for field, value in record.items():
        normalized_field = field.lower()
        text = str(value or "").strip()
        if any(hint in normalized_field for hint in PII_NAME_HINTS):
            detected.append(field)
        elif EMAIL_RE.fullmatch(text) or PHONE_RE.fullmatch(text):
            detected.append(field)
    return detected


def mask_value(value: str) -> str:
    text = str(value or "")
    if "@" in text and EMAIL_RE.fullmatch(text):
        name, domain = text.split("@", 1)
        return f"{name[:1]}***@{domain}"
    if len(text) > 3:
        return "*" * (len(text) - 3) + text[-3:]
    return "*" * len(text)


def protect_record(record: Dict[str, str], cipher: Fernet) -> Tuple[Dict[str, str], List[str]]:
    protected = {}
    pii_fields = detect_pii(record)
    for field, value in record.items():
        if field in pii_fields:
            protected[field] = mask_value(value)
            protected[f"{field}_encrypted"] = cipher.encrypt(str(value).encode()).decode()
        else:
            protected[field] = value
    protected["pii_fields"] = ",".join(pii_fields)
    return protected, pii_fields
