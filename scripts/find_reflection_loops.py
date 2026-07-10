with open("backend/workflows/engine.py", encoding="utf-8") as f:
    content = f.read()

lines = content.splitlines()
for idx, line in enumerate(lines):
    if "reflect" in line or "Reflection" in line:
        print(f"L{idx + 1}: {line.strip()}")
