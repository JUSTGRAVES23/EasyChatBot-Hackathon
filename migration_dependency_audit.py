from pathlib import Path
import ast
import re

academy = Path(r"C:\AI Folder\easychatbot_academy_backend\migrations\versions")
hackathon = Path(r"C:\AI Folder\EasyChatBot-Hackathon\backend\alembic\versions")

targets = {
    "20260901_cmp_monitoring_plan_items",
    "20260902_m2_3_world_catalogue",
    "20260903_m4_2_r4_user_role",
    "20260907_provider_usage_events",
    "20260910_functionality_operational_control",
}

def parse_file(path):
    text = path.read_text(encoding="utf-8")
    tree = ast.parse(text, filename=str(path))

    revision = None
    down_revision = None
    branch_labels = None

    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    if target.id == "revision":
                        revision = ast.literal_eval(node.value)
                    elif target.id == "down_revision":
                        down_revision = ast.literal_eval(node.value)
                    elif target.id == "branch_labels":
                        branch_labels = ast.literal_eval(node.value)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if node.value is None:
                continue
            if node.target.id == "revision":
                revision = ast.literal_eval(node.value)
            elif node.target.id == "down_revision":
                down_revision = ast.literal_eval(node.value)
            elif node.target.id == "branch_labels":
                branch_labels = ast.literal_eval(node.value)

    return revision, down_revision, branch_labels

def normalise(value):
    if value is None:
        return []
    if isinstance(value, (tuple, list)):
        return [str(x) for x in value if x is not None]
    return [str(value)]

def build_index(root):
    index = {}
    errors = []

    for path in sorted(root.glob("*.py")):
        try:
            revision, down_revision, branch_labels = parse_file(path)
            if revision:
                index[str(revision)] = {
                    "file": path.name,
                    "down_revision": normalise(down_revision),
                    "branch_labels": branch_labels,
                }
        except Exception as exc:
            errors.append((path.name, str(exc)))

    return index, errors

academy_index, academy_errors = build_index(academy)
hackathon_index, hackathon_errors = build_index(hackathon)

print("=" * 80)
print("EASYCHATBOT BULK MIGRATION DEPENDENCY AUDIT")
print("=" * 80)

print("\nDB TARGETS:")
for target in sorted(targets):
    print("  ", target)

print("\nACADEMY MIGRATION COUNT:", len(academy_index))
print("HACKATHON MIGRATION COUNT:", len(hackathon_index))

if academy_errors:
    print("\nACADEMY PARSE ERRORS:")
    for item in academy_errors:
        print("  ", item)

if hackathon_errors:
    print("\nHACKATHON PARSE ERRORS:")
    for item in hackathon_errors:
        print("  ", item)

required = set()
queue = list(targets)

while queue:
    revision = queue.pop()
    if revision in required:
        continue

    required.add(revision)

    node = academy_index.get(revision)
    if not node:
        continue

    for parent in node["down_revision"]:
        if parent not in required:
            queue.append(parent)

print("\n" + "-" * 80)
print("REQUIRED ACADEMY GRAPH CLOSURE")
print("-" * 80)

for revision in sorted(required):
    node = academy_index.get(revision)

    if node:
        print(
            f"{revision}\n"
            f"  file: {node['file']}\n"
            f"  down_revision: {node['down_revision']}\n"
            f"  branch_labels: {node['branch_labels']}"
        )
    else:
        print(f"{revision}\n  *** NOT FOUND IN ACADEMY SOURCE ***")

missing = sorted(
    revision
    for revision in required
    if revision not in hackathon_index
)

print("\n" + "-" * 80)
print("REQUIRED REVISIONS MISSING FROM HACKATHON")
print("-" * 80)

if missing:
    for revision in missing:
        node = academy_index.get(revision)
        print(
            f"{revision} -> "
            f"{node['file'] if node else 'ACADEMY SOURCE MISSING'}"
        )
else:
    print("NONE")

print("\n" + "-" * 80)
print("REQUIRED REVISIONS ALREADY PRESENT IN HACKATHON")
print("-" * 80)

for revision in sorted(required & set(hackathon_index)):
    print(revision)

print("\n" + "-" * 80)
print("ACADEMY PROVIDER VS HACKATHON PROVIDER")
print("-" * 80)

for revision in sorted(
    r for r in academy_index
    if "provider_usage" in r
):
    print(
        revision,
        "=>",
        academy_index[revision]["file"],
        "down=",
        academy_index[revision]["down_revision"],
        "branch=",
        academy_index[revision]["branch_labels"],
    )

for revision in sorted(
    r for r in hackathon_index
    if "provider_usage" in r
):
    print(
        revision,
        "=>",
        hackathon_index[revision]["file"],
        "down=",
        hackathon_index[revision]["down_revision"],
        "branch=",
        hackathon_index[revision]["branch_labels"],
    )

print("\n" + "=" * 80)
print("END AUDIT")
print("=" * 80)
