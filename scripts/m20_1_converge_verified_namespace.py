from pathlib import Path
import ast
import re

ROOT = Path("backend/app")

def target_exists(module: str) -> bool:
    if not module.startswith("app."):
        return False

    relative = module[len("app."):]
    parts = relative.split(".")

    py = ROOT.joinpath(*parts).with_suffix(".py")
    init = ROOT.joinpath(*parts, "__init__.py")

    return py.exists() or init.exists()

def extract_imports(text: str):
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return []

    modules = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith("app."):
                    modules.append(alias.name)

        elif isinstance(node, ast.ImportFrom):
            if node.level == 0 and node.module and node.module.startswith("app."):
                modules.append(node.module)

    return sorted(set(modules))

changed_files = 0
changed_imports = 0
unresolved = set()

for path in ROOT.rglob("*.py"):
    text = path.read_text(encoding="utf-8-sig")

    modules = extract_imports(text)

    for module in modules:
        if not target_exists(module):
            unresolved.add(module)
            continue

        old_prefix = module
        new_prefix = "backend." + module

        pattern = rf"(?<![\w.]){re.escape(old_prefix)}(?=\.|\s|$)"

        updated, count = re.subn(
            pattern,
            new_prefix,
            text,
        )

        if count:
            text = updated
            changed_imports += count

    if text != path.read_text(encoding="utf-8-sig"):
        path.write_text(text, encoding="utf-8")
        changed_files += 1
        print(f"CHANGED|{path}")

print()
print("=" * 90)
print(f"FILES CHANGED: {changed_files}")
print(f"IMPORT REFERENCES CHANGED: {changed_imports}")
print("=" * 90)

print()
print("UNRESOLVED app.* MODULES — LEFT UNCHANGED")

for module in sorted(unresolved):
    print(f"UNRESOLVED|{module}")
