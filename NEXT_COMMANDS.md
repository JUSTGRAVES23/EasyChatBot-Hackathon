# Next repository steps

Run from `C:\AI Folder\ai_agents`.

## 1. Apply safe Skill prompt loading

Back up the existing loader:

```powershell
cd "C:\AI Folder\ai_agents"; Copy-Item "runtime\capabilities\loaders\skill_loader.py" "runtime\capabilities\loaders\skill_loader.py.pi1b.bak"
```

Apply the `load_prompt()` implementation from the package, preserving the
existing manifest contract.

## 2. Run focused Skill tests

```powershell
cd "C:\AI Folder\ai_agents"; pytest -q tests/unit/runtime/capabilities tests/unit/runtime/agents/services --disable-warnings --maxfail=1
```

## 3. Wire the loader/resource into PI

The PI agent should resolve the configured Skill resource through the
Runtime-controlled Skill infrastructure. Do not read `prompt.md` directly
from `PlatformIntelligenceAgent`.

## 4. Replace placeholder confidence

Remove the unconditional `0.80 / HIGH` assessment. If no
evidence-producing Skill has executed, use an explicit insufficient-evidence
state.

## 5. Reconcile PI default Skill

The observed PI profile referenced `platform_investigation`, while the
current structured Skill inventory contains `architecture_review`. Verify the
local profile before changing it.

## 6. Full validation

Focused → runtime unit → integration → security → build → smoke → review.
