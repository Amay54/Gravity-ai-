with open("backend/workflows/engine.py", encoding="utf-8") as f:
    lines = f.readlines()

for idx, line in enumerate(lines):
    if line.strip().startswith("async def "):
        print(f"L{idx + 1}: {line.strip()}")
