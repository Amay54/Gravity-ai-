import os
import re
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent

# Exclusions list
EXCLUDED_DIRS = {
    ".venv",
    ".git",
    ".pytest_cache",
    ".ruff_cache",
    "__pycache__",
    "node_modules",
    "dist",
    "build",
}

EXCLUDED_FILES = {
    "uv.lock",
    "package-lock.json",
    ".env",  # .env itself is verified separately for ignoring
}

# Regex to detect common API keys, passwords, and tokens
SECRET_PATTERNS = [
    # Gemini / Google API Key (typically AIzaSy followed by 35 alphanumeric/underscore/hyphen chars)
    r"AIzaSy[A-Za-z0-9_\-]{35}",
    # Supabase service role / anon keys or other high-entropy keys
    r"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9\.[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+",  # JWT tokens
]

# Suspect assignments
SUSPECT_KEYWORDS = [
    r"password\s*=\s*['\"][^'\"]+['\"]",
    r"api_key\s*=\s*['\"][^'\"]+['\"]",
    r"jwt_secret\s*=\s*['\"][^'\"]+['\"]",
    r"service_role\s*=\s*['\"][^'\"]+['\"]",
]


def scan_file(file_path: Path):
    """Scans a single file for sensitive keys or patterns."""
    try:
        with open(file_path, encoding="utf-8", errors="ignore") as f:
            content = f.read()
    except Exception:
        return []

    findings = []

    # 1. Regex check
    for pattern in SECRET_PATTERNS:
        matches = re.findall(pattern, content)
        if matches:
            for match in matches:
                # Exclude mock keys or dummy assignments
                if "mock" not in match.lower() and "your_" not in match.lower():
                    findings.append(f"Found sensitive pattern match: {match[:8]}...")

    # 2. Suspect assignments check
    for keyword in SUSPECT_KEYWORDS:
        matches = re.findall(keyword, content, re.IGNORECASE)
        for match in matches:
            # Exclude known mock values, default settings, or environment variable mappings
            lower_match = match.lower()
            if any(
                dummy in lower_match
                for dummy in [
                    "mock",
                    "your_",
                    "os.get",
                    "settings.",
                    "env.",
                    "default",
                    "none",
                    "false",
                    "true",
                    "self.",
                    "field",
                ]
            ):
                continue
            findings.append(f"Found suspect assignment: '{match}'")

    return findings


def scan_repository():
    """Recursively walks and scans the repository for secrets."""
    print("Initiating repository secret scanning...")
    all_findings = {}

    for root, dirs, files in os.walk(ROOT_DIR):
        # Apply directory filters in-place
        dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]

        for file in files:
            if file in EXCLUDED_FILES:
                continue
            file_path = Path(root) / file
            findings = scan_file(file_path)
            if findings:
                all_findings[str(file_path.relative_to(ROOT_DIR))] = findings

    if all_findings:
        print(
            "\n[CRITICAL] Secrets scan failed. Potential hardcoded credentials detected:",
            file=sys.stderr,
        )
        for rel_path, items in all_findings.items():
            print(f"\nFile: {rel_path}", file=sys.stderr)
            for item in items:
                print(f"  - {item}", file=sys.stderr)
        return False

    print("SUCCESS: Secrets scan completed. No active keys or passwords found.")
    return True


if __name__ == "__main__":
    if not scan_repository():
        sys.exit(1)
    sys.exit(0)
