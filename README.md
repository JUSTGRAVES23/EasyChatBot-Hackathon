# EasyChatBot — P0.2.9D.3 Secure Governance Package

## Objective
Secure the sensitive `internal_data_read` capability before P0.2.9E wires
the BetaUserReadService into the canonical Runtime.

## Changes
1. `BootstrapGovernance` fails closed for `internal_data_read` when:
   - no Runtime actor is present;
   - the actor has no `internal_data.read` permission;
   - the actor only has `beta_user` or an unknown role.
2. `operator` and `admin` are allowed according to the existing application
   permission contract.
3. The `/runtime/execute` API obtains the authenticated `Principal` through
   the existing identity dependency and converts it to the provider-neutral
   `RuntimeActorContext`.
4. Actor identity/roles come from the authenticated Principal, never from the
   request payload.
5. Existing non-sensitive hackathon capabilities retain the previous
   allow behavior.

## Files
- `P0.2.9D3_secure_governance_and_api_actor.patch`
- `tests/unit/application/test_bootstrap_governance.py`
- `tests/unit/api/test_runtime_route_actor_propagation.py`

## Apply
Run from:
`C:\AI Folder\EasyChatBot-Hackathon`

Inspect the patch first, then apply with:

```powershell
git apply .\P0.2.9D3_secure_governance_and_api_actor.patch
```

If the repository's existing working tree prevents a clean patch application,
STOP. Do not force, reset, or overwrite unrelated changes. Apply the two
small source edits manually using the exact diff as the change specification.

## Test
Use the project-local `.venv`:

```powershell
Set-Location "C:\AI Folder\EasyChatBot-Hackathon"
.\.venv\Scripts\python.exe -m pytest tests/unit/application/test_bootstrap_governance.py tests/unit/api/test_runtime_route_actor_propagation.py -q
```

Then run the relevant Runtime/auth regression suite already used for P0.2.9D.

## Acceptance
P0.2.9D.3 is NOT complete merely because the two new test files pass.
The existing relevant regression suite must also pass.

No commit is included or requested.
