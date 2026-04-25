from pathlib import Path
profile_name = Path('username.txt').read_text(encoding="utf-8") if Path('username.txt').exists() else "".strip()
print(profile_name or "Guest")
