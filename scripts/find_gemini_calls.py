import os
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"

for root, dirs, files in os.walk(BACKEND_DIR):
    for file in files:
        if file.endswith(".py"):
            file_path = Path(root) / file
            with open(file_path, encoding="utf-8") as f:
                content = f.read()
            if "GeminiLLM" in content or "generate_json" in content or "generate_text" in content:
                print(f"File: {file_path.relative_to(BACKEND_DIR)}")
                lines = content.splitlines()
                for idx, line in enumerate(lines):
                    if any(kw in line for kw in ["GeminiLLM", "generate_json", "generate_text"]):
                        print(f"  L{idx + 1}: {line.strip()}")
