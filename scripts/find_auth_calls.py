import os
from pathlib import Path

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"

patterns = [".login(", ".register(", ".logout(", ".oauth("]

for root, dirs, files in os.walk(FRONTEND_DIR):
    for file in files:
        if file.endswith(".py") and file != "api_client.py":
            file_path = Path(root) / file
            with open(file_path, encoding="utf-8") as f:
                lines = f.readlines()
            for idx, line in enumerate(lines):
                for pattern in patterns:
                    if pattern in line:
                        print(f"{file_path.relative_to(FRONTEND_DIR)}:L{idx + 1}: {line.strip()}")
