from __future__ import annotations

from pathlib import Path

path = Path(
    r"C:\AI Folder\EasyChatBot-Hackathon\backend"
    r"\app\application\identity\authentication_email_service.py"
)

text = path.read_text(encoding="utf-8")

replacements = {
    "ðŸŽ“": "[EasyChatBot]",
    "ðŸ‘‹": "",
    "â€”": "-",
    "â™¥": "",
    "â³": "",
    "ðŸ›¡ï¸": "",
    "ðŸ’¡": "",
    "ðŸ“–": "",
    "ðŸ‘¥": "",
    "ðŸš€": "",
    "ðŸ”": "",
    "âœ¨": "",
    "âœ“": "OK",
    "Â©": "(c)",
    "â†’": "->",
    "ðŸŽ“": "[EasyChatBot]",
}

for bad, good in replacements.items():
    text = text.replace(bad, good)

# Remove leftover variation-selector / mojibake fragments that are known
# to appear in the current source. Do not perform a broad transliteration.
for bad in ("ï¸", "â", "ð", "Ÿ", "Ž"):
    # Only remove isolated fragments that are left after the exact
    # replacements above. This keeps normal ASCII email content stable.
    text = text.replace(bad, "")

path.write_text(text, encoding="utf-8")
print(f"Updated: {path}")
print("Encoding remediation applied.")
