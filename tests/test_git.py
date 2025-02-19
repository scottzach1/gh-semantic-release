import pytest

from scottzach1.semantic_release.githelper import SemanticMessage, parse_commit_msg

VALID_CASES = [
    (
        "feat: add user authentication",
        SemanticMessage(
            type="feat",
            scope=None,
            breaking=False,
            subject="add user authentication",
        ),
    ),
    (
        "fix(api): resolve timeout issue on large requests",
        SemanticMessage(
            type="fix",
            scope="api",
            breaking=False,
            subject="resolve timeout issue on large requests",
        ),
    ),
    (
        "docs: update README with new installation steps",
        SemanticMessage(
            type="docs",
            scope=None,
            breaking=False,
            subject="update README with new installation steps",
        ),
    ),
    (
        "feat!: completely redesign user interface",
        SemanticMessage(
            type="feat",
            scope=None,
            breaking=True,
            subject="completely redesign user interface",
        ),
    ),
    (
        "chore(deps): update dependencies to latest versions",
        SemanticMessage(
            type="chore",
            scope="deps",
            breaking=False,
            subject="update dependencies to latest versions",
        ),
    ),
    (
        "fix: correct typo in error message",
        SemanticMessage(
            type="fix",
            scope=None,
            breaking=False,
            subject="correct typo in error message",
        ),
    ),
    (
        "style(css): fix indentation in main stylesheet",
        SemanticMessage(
            type="style",
            scope="css",
            breaking=False,
            subject="fix indentation in main stylesheet",
        ),
    ),
    (
        "test(auth): add unit tests for login flow",
        SemanticMessage(
            type="test",
            scope="auth",
            breaking=False,
            subject="add unit tests for login flow",
        ),
    ),
    (
        "refactor: simplify payment processing logic",
        SemanticMessage(
            type="refactor",
            scope=None,
            breaking=False,
            subject="simplify payment processing logic",
        ),
    ),
    (
        "perf(db): optimize database queries for dashboard",
        SemanticMessage(
            type="perf",
            scope="db",
            breaking=False,
            subject="optimize database queries for dashboard",
        ),
    ),
    (
        "build: update build pipeline configuration",
        SemanticMessage(
            type="build",
            scope=None,
            breaking=False,
            subject="update build pipeline configuration",
        ),
    ),
    (
        "ci: add GitHub Actions workflow",
        SemanticMessage(
            type="ci",
            scope=None,
            breaking=False,
            subject="add GitHub Actions workflow",
        ),
    ),
    (
        "feat(user): add profile picture upload",
        SemanticMessage(
            type="feat",
            scope="user",
            breaking=False,
            subject="add profile picture upload",
        ),
    ),
    (
        "fix(api)!: change API response format",
        SemanticMessage(
            type="fix",
            scope="api",
            breaking=True,
            subject="change API response format",
        ),
    ),
    (
        'revert: revert "feat: add dark mode support"',
        SemanticMessage(
            type="revert",
            scope=None,
            breaking=False,
            subject='revert "feat: add dark mode support"',
        ),
    ),
    (
        "docs(api): update API documentation",
        SemanticMessage(
            type="docs",
            scope="api",
            breaking=False,
            subject="update API documentation",
        ),
    ),
    (
        "fix(security): patch XSS vulnerability",
        SemanticMessage(
            type="fix",
            scope="security",
            breaking=False,
            subject="patch XSS vulnerability",
        ),
    ),
    (
        "feat(auth): add 2FA support",
        SemanticMessage(
            type="feat",
            scope="auth",
            breaking=False,
            subject="add 2FA support",
        ),
    ),
    (
        "chore: remove deprecated functions",
        SemanticMessage(
            type="chore",
            scope=None,
            breaking=False,
            subject="remove deprecated functions",
        ),
    ),
    (
        "refactor(core): split monolithic service into microservices",
        SemanticMessage(
            type="refactor", scope="core", breaking=False, subject="split monolithic service into microservices"
        ),
    ),
    (
        "test: improve test coverage",
        SemanticMessage(
            type="test",
            scope=None,
            breaking=False,
            subject="improve test coverage",
        ),
    ),
    (
        "perf!: completely rewrite rendering engine",
        SemanticMessage(
            type="perf",
            scope=None,
            breaking=True,
            subject="completely rewrite rendering engine",
        ),
    ),
    (
        "feat(ui): implement responsive design",
        SemanticMessage(
            type="feat",
            scope="ui",
            breaking=False,
            subject="implement responsive design",
        ),
    ),
    (
        "fix(ios): resolve crash on iOS 15",
        SemanticMessage(
            type="fix",
            scope="ios",
            breaking=False,
            subject="resolve crash on iOS 15",
        ),
    ),
    (
        "build(docker): update Dockerfile",
        SemanticMessage(
            type="build",
            scope="docker",
            breaking=False,
            subject="update Dockerfile",
        ),
    ),
    ("feat(123): numeric scope", SemanticMessage(type="feat", scope="123", breaking=False, subject="numeric scope")),
    (
        "feat(api): with trailing period.",
        SemanticMessage(
            type="feat",
            scope="api",
            breaking=False,
            subject="with trailing period.",
        ),
    ),
]


INVALID_CASES = [
    "feature: add new login page",
    "FIX: correct calculation error",
    "feat(api) missing colon before subject",
    "feat:missing space after colon",
    ": empty type",
    "feat(): empty scope",
    "FEAT: uppercase type",
    "fix[ui]: incorrect scope delimiter",
    "feat(ui: missing closing parenthesis",
    "(ui)fix: wrong order",
    "feat(UI): uppercase scope",
    "feat(api)!missing colon after breaking indicator",
    "feat!!: double breaking indicator",
    "chore(dep-update, security): multiple scopes",
    ": just a subject",
    "feat(): : empty scope with empty subject",
    "feat: ",
    "refactor(): ",
    "@feat: invalid character",
    "fix-typo: invalid type",
    "feature(auth): non-standard type",
]


@pytest.mark.parametrize("commit_msg, expected_model", VALID_CASES)
def test_valid_commit(commit_msg: str, expected_model: SemanticMessage):
    assert parse_commit_msg(commit_msg) == expected_model


@pytest.mark.parametrize("commit_msg", INVALID_CASES)
def test_invalid_commit_msg(commit_msg: str):
    with pytest.raises(ValueError):
        parse_commit_msg(commit_msg)
