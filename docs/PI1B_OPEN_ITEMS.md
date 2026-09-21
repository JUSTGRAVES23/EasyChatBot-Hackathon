# PI-1B Open Items

## 1. Skill resource loading

`SkillManifest.prompt` is a resource reference such as `prompt.md`, not prompt
text. Add safe `SkillLoader.load_prompt()` before filesystem resources enter
execution.

## 2. Skill selection

The PI agent currently has no general Skill-selection policy. The first slice
should select an explicitly configured Skill rather than allow arbitrary
model-generated Skill IDs.

## 3. Evidence

`architecture_review` is a reasoning/review Skill. It does not itself retrieve
authoritative external evidence. Do not label model output as external evidence.

## 4. Confidence

Until evidence-producing Skills are connected, use an explicit
`INSUFFICIENT_EVIDENCE` quality state rather than HIGH confidence.

## 5. Profile default Skill

The PI profile was previously observed to reference `platform_investigation`,
which does not exist in the current Skill inventory. Reconcile this before
automatic default Skill selection.

## 6. Composition

The per-agent execution-service mapping is an intermediate scalable solution.
If agent count grows materially, introduce a typed execution-policy catalogue
only when real duplication justifies it.

## 7. Screen intelligence

Reading all platform screens requires a governed screen inventory and read-only
page/data Skills. It should not be unrestricted UI scraping.
