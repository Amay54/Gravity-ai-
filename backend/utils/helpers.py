import re


def normalize_string(text: str) -> str:
    """
    Trims and strips whitespace, and removes duplicate spaces.
    """
    if not text:
        return ""
    return re.sub(r"\s+", " ", text.strip())


def sanitize_domain(domain: str) -> str:
    """
    Cleans domain urls removing http protocols and trailing directories.
    """
    if not domain:
        return ""

    cleaned = domain.strip().lower()
    # Strip protocols
    cleaned = re.sub(r"^https?://(www\.)?", "", cleaned)
    cleaned = re.sub(r"^www\.", "", cleaned)
    # Strip paths
    cleaned = cleaned.split("/")[0]
    return cleaned
