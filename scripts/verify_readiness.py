import sys
from pathlib import Path

from backend.core.config.base import BaseSettingsConfig

ROOT_DIR = Path(__file__).resolve().parent.parent


def verify_env_example():
    """Checks if .env.example contains all defined settings parameters."""
    print("Checking if .env.example contains all parameters from BaseSettingsConfig...")
    env_example_path = ROOT_DIR / ".env.example"

    if not env_example_path.exists():
        print("ERROR: .env.example file is missing!", file=sys.stderr)
        return False

    with open(env_example_path, encoding="utf-8") as f:
        content = f.read()

    # List of settings fields to verify in example config
    required_keys = [
        "APP_ENV",
        "DEBUG",
        "API_HOST",
        "API_PORT",
        "API_VERSION",
        "LOG_LEVEL",
        "JSON_LOGS",
        "GEMINI_API_KEY",
        "SUPABASE_URL",
        "SUPABASE_ANON_KEY",
        "SUPABASE_SERVICE_ROLE_KEY",
        "SUPABASE_SERVICE_KEY",
        "JWT_SECRET",
        "STREAMLIT_PORT",
        "BACKEND_API_URL",
        "API_BASE_URL",
    ]

    missing = []
    for key in required_keys:
        if f"{key}=" not in content:
            missing.append(key)

    if missing:
        print(f"ERROR: .env.example is missing settings variables: {missing}", file=sys.stderr)
        return False

    print("SUCCESS: .env.example contains all settings variables.")
    return True


def verify_folder_structure():
    """Validates that necessary folders exist in the workspace."""
    print("Verifying folder structure...")
    required_dirs = ["backend", "frontend", "tests", "docs", "portfolio", "docker"]

    for folder in required_dirs:
        dir_path = ROOT_DIR / folder
        if not dir_path.is_dir():
            print(f"ERROR: Directory '{folder}' is missing!", file=sys.stderr)
            return False

    print("SUCCESS: All required directories are present.")
    return True


if __name__ == "__main__":
    success = verify_env_example() and verify_folder_structure()
    if not success:
        sys.exit(1)
    print("SUCCESS: Deploy readiness validation completed successfully.")
    sys.exit(0)
