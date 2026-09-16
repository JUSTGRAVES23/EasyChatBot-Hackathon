import ast
from pathlib import Path

ROOT = Path("backend/app").resolve()
ENTRY = ROOT / "main.py"

def module_to_file(module: str):
    if not module.startswith("backend.app."):
        return None

    relative = module[len("backend.app."):]
    py = ROOT / Path(relative.replace(".", "/")).with_suffix(".py")
    init = ROOT / Path(relative.replace(".", "/")) / "__init__.py"

    if py.exists():
        return py
    if init.exists():
        return init
    return None

def imports_from_file(path: Path):
    try:
        tree = ast.parse(path.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        print(f"PARSE_ERROR|{path}|{exc}")
        return []

    result = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                result.append(alias.name)

        elif isinstance(node, ast.ImportFrom):
            if node.level != 0 or not node.module:
                continue

            result.append(node.module)

    return result

def resolve_backend_import(module):
    if module == "backend.app":
        return ROOT / "__init__.py"

    if module.startswith("backend.app."):
        return module_to_file(module)

    return None

queue = ["backend.app.main"]
visited = set()
edges = []

while queue:
    module = queue.pop(0)

    if module in visited:
        continue

    visited.add(module)

    path = resolve_backend_import(module)

    if path is None:
        continue

    for imported in imports_from_file(path):
        edges.append((module, imported))

        if imported.startswith("backend.app.") and imported not in visited:
            queue.append(imported)

        # Relative imports are intentionally omitted from this first pass.
        # They remain internal to the canonical package and are not namespace
        # migration candidates.

reachable_stale = sorted({
    imported
    for _, imported in edges
    if imported.startswith("app.")
})

print()
print("=" * 90)
print("REACHABLE STALE app.* IMPORTS from app.main")
print("=" * 90)

for item in reachable_stale:
    target = "backend." + item

    relative = item[len("app."):]
    target_path = ROOT / Path(relative.replace(".", "/")).with_suffix(".py")
    target_init = ROOT / Path(relative.replace(".", "/")) / "__init__.py"

    if target_path.exists():
        status = "VERIFIED"
        location = str(target_path)
    elif target_init.exists():
        status = "VERIFIED_PACKAGE"
        location = str(target_init)
    else:
        status = "UNRESOLVED"
        location = ""

    print(f"{status}|{item}|{target}|{location}")

print()
print("=" * 90)
print(f"REACHABLE backend.app MODULES: {len(visited)}")
print(f"REACHABLE STALE app.* MODULES: {len(reachable_stale)}")
print("=" * 90)

