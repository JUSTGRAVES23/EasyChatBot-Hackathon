from pathlib import Path
import ast

domain_path = Path(r".\backend\app\domain\identity\transaction_authorization.py")
test_path = Path(r".\backend\tests\security\test_transaction_authorization.py")

domain = domain_path.read_text(encoding="utf-8")
tests = test_path.read_text(encoding="utf-8")


def replace_function(source: str, function_name: str, replacement: str) -> str:
    tree = ast.parse(source)
    lines = source.splitlines(keepends=True)

    matches = []

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name == function_name:
                matches.append(node)

    if len(matches) != 1:
        raise RuntimeError(
            f"Expected exactly one function named {function_name!r}; "
            f"found {len(matches)}"
        )

    node = matches[0]

    start = node.lineno - 1
    end = node.end_lineno

    original_indent = len(lines[start]) - len(lines[start].lstrip())

    replacement_lines = replacement.splitlines(keepends=True)

    if not replacement.endswith("\n"):
        replacement_lines.append("\n")

    if original_indent:
        prefix = " " * original_indent
        replacement_lines = [
            (prefix + line if line.strip() else line)
            for line in replacement_lines
        ]

    return "".join(lines[:start] + replacement_lines + lines[end:])


# ------------------------------------------------------------------
# TEST 1
#
# The production boundary intentionally rejects an assurance context
# whose principal does not match the transaction. The old test tried
# to construct TrustedApprovalEvidence first and expected a later
# failure. The correct assertion is at construction time.
# ------------------------------------------------------------------

test1 = r'''def test_assurance_is_bound_to_transaction_principal(
    authorization: TransactionAuthorization,
    clock: FixedClock,
) -> None:
    pending = transition(
        authorization,
        TransactionAuthorizationState.PENDING_USER_APPROVAL,
    )

    with pytest.raises(ValueError, match="principal binding mismatch"):
        TrustedApprovalEvidence(
            authorization_id=pending.authorization_id,
            transaction=pending.transaction,
            approved_at=clock.now(),
            evidence_id="approval",
            assurance_context=assurance_context(
                principal_id="different-user",
            ),
        )
'''


# ------------------------------------------------------------------
# TEST 2
#
# Future-dated assurance must fail closed against trusted application
# time. We exercise attach_approval, which is the first point at which
# the assurance context crosses into transaction authorization.
# ------------------------------------------------------------------

test2 = r'''def test_future_dated_assurance_does_not_bypass_trusted_time(
    authorization: TransactionAuthorization,
    clock: FixedClock,
) -> None:
    pending = transition(
        authorization,
        TransactionAuthorizationState.PENDING_USER_APPROVAL,
    )

    approval = TrustedApprovalEvidence(
        authorization_id=pending.authorization_id,
        transaction=pending.transaction,
        approved_at=clock.now(),
        evidence_id="future-assurance",
        assurance_context=assurance_context(
            level=AuthenticationAssuranceLevel.A3,
            assurance_time=clock.now() + timedelta(hours=1),
        ),
    )

    with pytest.raises(ValueError, match="future"):
        attach_approval(
            pending,
            approval,
            clock=clock,
        )
'''


tests = replace_function(
    tests,
    "test_assurance_is_bound_to_transaction_principal",
    test1,
)

tests = replace_function(
    tests,
    "test_future_dated_assurance_does_not_bypass_trusted_time",
    test2,
)


# ------------------------------------------------------------------
# DOMAIN TRUSTED-TIME CHECK
#
# Do not derive current time from caller data.
# The transaction authorization boundary receives TrustedClock and
# must reject assurance_context timestamps that are in the future.
#
# We insert one helper only if the current source does not already
# contain it.
# ------------------------------------------------------------------

helper_name = "_validate_assurance_context_time"

if helper_name not in domain:
    marker = "\ndef _trusted_now(clock: TrustedClock) -> datetime:\n"

    if marker not in domain:
        raise RuntimeError(
            "Could not locate _trusted_now marker; "
            "refusing to patch production source."
        )

    helper = r'''

def _validate_assurance_context_time(
    assurance_context: AuthenticationAssuranceContext,
    clock: TrustedClock,
) -> None:
    now = _trusted_now(clock)

    if assurance_context.authentication_time > now:
        raise ValueError(
            "authentication assurance authentication_time is future-dated"
        )

    if assurance_context.assurance_time > now:
        raise ValueError(
            "authentication assurance assurance_time is future-dated"
        )

    if assurance_context.authentication_time > assurance_context.assurance_time:
        raise ValueError(
            "authentication_time must not be later than assurance_time"
        )
'''

    domain = domain.replace(marker, helper + marker, 1)


# ------------------------------------------------------------------
# Inject the trusted-time validation into attach_approval.
# ------------------------------------------------------------------

def inject_after_assurance_binding(source: str, function_name: str) -> str:
    tree = ast.parse(source)
    lines = source.splitlines(keepends=True)

    matches = [
        n for n in ast.walk(tree)
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
        and n.name == function_name
    ]

    if len(matches) != 1:
        raise RuntimeError(
            f"Expected exactly one {function_name} function; found {len(matches)}"
        )

    node = matches[0]

    start = node.lineno - 1
    end = node.end_lineno

    block = "".join(lines[start:end])

    call = "    _validate_assurance_context_time(approval.assurance_context, clock)\n"

    if call in block:
        return source

    needle = (
        "    if approval.assurance_context.principal_id != "
        "authorization.transaction.principal_id:\n"
    )

    if needle not in block:
        raise RuntimeError(
            f"Could not find assurance principal-binding check in {function_name}"
        )

    # Find the end of the principal-binding if block.
    block_lines = block.splitlines(keepends=True)

    needle_index = None

    for i, line in enumerate(block_lines):
        if line == needle:
            needle_index = i
            break

    if needle_index is None:
        raise RuntimeError(
            f"Could not locate principal-binding line in {function_name}"
        )

    insert_index = needle_index

    # Walk until after the indented raise block.
    i = needle_index + 1

    while i < len(block_lines):
        stripped = block_lines[i].strip()

        if stripped and not block_lines[i].startswith(" " * 8):
            break

        i += 1

    block_lines.insert(i, call)

    new_block = "".join(block_lines)

    return "".join(lines[:start] + [new_block] + lines[end:])


domain = inject_after_assurance_binding(domain, "attach_approval")


# Also protect the consuming paths.
domain = inject_after_assurance_binding(domain, "consume_once")
domain = inject_after_assurance_binding(domain, "consume")


domain_path.write_text(domain, encoding="utf-8")
test_path.write_text(tests, encoding="utf-8")

print("PATCH_SUCCESS")
print("Updated test_assurance_is_bound_to_transaction_principal")
print("Updated test_future_dated_assurance_does_not_bypass_trusted_time")
print("Ensured trusted assurance-time validation helper exists")
print("Injected trusted assurance-time validation into attach_approval/consume_once/consume")
print("W15.6 assurance authority remains external")
print("No ZITADEL/Keycloak/WebAuthn changes")
