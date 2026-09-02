import sys
import os

UTF8_PATCH = (
    "\n\nimport sys\n"
    "if hasattr(sys.stdout, 'reconfigure'):\n"
    "    sys.stdout.reconfigure(encoding='utf-8')\n"
    "if hasattr(sys.stderr, 'reconfigure'):\n"
    "    sys.stderr.reconfigure(encoding='utf-8')\n"
)

files = [
    "01_data_wrangling.py",
    "02_database_crud.py",
    "03_data_cleaning.py",
    "04_data_analysis.py",
    "05_visualizations.py",
    "06_insights.py",
    "generate_datasets.py",
]

for fname in files:
    if not os.path.exists(fname):
        print(f"SKIP (not found): {fname}")
        continue
    with open(fname, "r", encoding="utf-8") as f:
        content = f.read()
    if "reconfigure" in content:
        print(f"Already patched: {fname}")
        continue
    # Find end of opening docstring
    first = content.find('"""')
    second = content.find('"""', first + 3) if first != -1 else -1
    insert_pos = second + 3 if second != -1 else 0
    new_content = content[:insert_pos] + UTF8_PATCH + content[insert_pos:]
    with open(fname, "w", encoding="utf-8") as f:
        f.write(new_content)
    print(f"Patched: {fname}")

print("Done.")
