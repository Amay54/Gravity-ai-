import re
from typing import Any

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


def normalize_url(url: str) -> str:
    """
    Cleans up any URL to make it a valid absolute URL.
    Removes duplicate prefixes such as https://https:// or http://https://
    """
    if not url:
        return ""
    cleaned = url.strip()
    
    # Check if it starts with protocol or www, or has double prefix
    lower_cleaned = cleaned.lower()
    has_protocol = lower_cleaned.startswith("http://") or lower_cleaned.startswith("https://") or "://" in lower_cleaned
    has_www = lower_cleaned.startswith("www.")
    
    if not (has_protocol or has_www):
        # Not a URL, return as is
        return cleaned
        
    # It is a URL. Let's normalize it.
    is_http = "http://" in lower_cleaned and "https://" not in lower_cleaned
    
    no_proto = cleaned
    while True:
        prev = no_proto
        no_proto = re.sub(r"^(https?://|www\.)+", "", no_proto, flags=re.IGNORECASE)
        if no_proto == prev:
            break
            
    protocol = "http://" if is_http else "https://"
    return f"{protocol}{no_proto}"


def normalize_all_urls_in_dict(data: Any) -> Any:
    """
    Recursively traverses a dictionary, list, or primitive value, and normalizes any strings that are URLs.
    """
    if isinstance(data, dict):
        return {k: normalize_all_urls_in_dict(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [normalize_all_urls_in_dict(item) for item in data]
    elif isinstance(data, str):
        return normalize_url(data)
    return data
