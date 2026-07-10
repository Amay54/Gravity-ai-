with open("backend/workflows/engine.py", encoding="utf-8") as f:
    lines = f.readlines()

for idx, line in enumerate(lines):
    if "def route_next_node" in line:
        print(f"route_next_node defined at L{idx + 1}")
    if "MAX_REVIEWER_LOOPS" in line:
        print(f"MAX_REVIEWER_LOOPS found at L{idx + 1}: {line.strip()}")
