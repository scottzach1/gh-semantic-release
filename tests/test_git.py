from collections.abc import Iterator
from unittest import mock

import pytest
from pydantic import BaseModel

from scottzach1.semantic_release.githelper import (
    LegacyMessage,
    SemanticMessage,
    parse_commit_msg,
    read_commit_log,
)

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
    (
        "feat(123): numeric scope",
        SemanticMessage(
            type="feat",
            scope="123",
            breaking=False,
            subject="numeric scope",
        ),
    ),
    (
        "feat(api): with trailing period.",
        SemanticMessage(
            type="feat",
            scope="api",
            breaking=False,
            subject="with trailing period.",
        ),
    ),
    (
        "release(uv): this is a release!",
        SemanticMessage(
            type="release",
            scope="uv",
            breaking=False,
            subject="this is a release!",
        ),
    ),
    (
        "feat(auth): add OAuth integration\n\nThis commit adds OAuth2 support with multiple providers.",
        SemanticMessage(
            type="feat",
            scope="auth",
            breaking=False,
            subject="add OAuth integration",
            body="This commit adds OAuth2 support with multiple providers.",
        ),
    ),
    (
        "fix: resolve memory leak\n\n"
        "Identified and fixed memory leak in the rendering pipeline.\n"
        "The issue was related to texture resources not being properly released.",
        SemanticMessage(
            type="fix",
            scope=None,
            breaking=False,
            subject="resolve memory leak",
            body=(
                "Identified and fixed memory leak in the rendering pipeline.\n"
                "The issue was related to texture resources not being properly released."
            ),
        ),
    ),
    (
        "refactor(core)!: change API response format\n\n"
        "BREAKING CHANGE: Response format has changed from XML to JSON.\n"
        "This affects all API consumers.",
        SemanticMessage(
            type="refactor",
            scope="core",
            breaking=True,
            subject="change API response format",
            body="BREAKING CHANGE: Response format has changed from XML to JSON.\nThis affects all API consumers.",
        ),
    ),
    (
        "docs(readme): update installation instructions\n\n"
        "Updated the installation guide with new dependency requirements.\n\n"
        "Also fixed formatting issues in the examples section.",
        SemanticMessage(
            type="docs",
            scope="readme",
            breaking=False,
            subject="update installation instructions",
            body=(
                "Updated the installation guide with new dependency requirements.\n\n"
                "Also fixed formatting issues in the examples section."
            ),
        ),
    ),
    (
        "feat(test): subject with unicode 🔥\n\nThis tests how unicode characters are handled.",
        SemanticMessage(
            type="feat",
            scope="test",
            subject="subject with unicode 🔥",
            body="This tests how unicode characters are handled.",
        ),
    ),
    (
        "feat(api)!: trailing whitespace  \n\nHas trailing whitespace in subject.",
        SemanticMessage(
            type="feat",
            scope="api",
            breaking=True,
            subject="trailing whitespace",
            body="Has trailing whitespace in subject.",
        ),
    ),
    (
        "feat(api)!: trailing whitespace\n\nHas trailing whitespace in body.  ",
        SemanticMessage(
            type="feat",
            scope="api",
            breaking=True,
            subject="trailing whitespace",
            body="Has trailing whitespace in body.",
        ),
    ),
    (
        "feat(api)!: leading whitespace\n\n  Has leading whitespace in body.",
        SemanticMessage(
            type="feat",
            scope="api",
            breaking=True,
            subject="leading whitespace",
            body="Has leading whitespace in body.",
        ),
    ),
    (
        "feat:   leading whitespace in subject",
        SemanticMessage(
            type="feat",
            scope=None,
            subject="leading whitespace in subject",
        ),
    ),
    (
        "feat(auth): add login page\r\n\r\nImplemented new login screen with password reset.",
        SemanticMessage(
            type="feat",
            scope="auth",
            breaking=False,
            subject="add login page",
            body="Implemented new login screen with password reset.",
        ),
    ),
    (
        "fix(core)!: change authentication flow\r\n\r\n"
        "BREAKING CHANGE: Users will need to re-authenticate.\r\n"
        "This improves security by requiring 2FA.",
        SemanticMessage(
            type="fix",
            scope="core",
            breaking=True,
            subject="change authentication flow",
            body="BREAKING CHANGE: Users will need to re-authenticate.\r\nThis improves security by requiring 2FA.",
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
    "fix(): empty scope\n\nThis has an empty scope which might be invalid.",
    "feature: invalid type\n\nCommit types should be standardized.",
    "chore[deps]: wrong scope delimiter\n\nUsing square brackets instead of parentheses.",
    "refactor!api: missing parentheses\n\nThe scope should be in parentheses.",
    "feat(ci)\n\nMissing subject line entirely.",
]


@pytest.mark.parametrize("commit_msg, expected_model", VALID_CASES)
def test_valid_commit(commit_msg: str, expected_model: SemanticMessage):
    assert SemanticMessage.parse(commit_msg) == expected_model
    assert parse_commit_msg(commit_msg) == expected_model


@pytest.mark.parametrize("commit_msg", INVALID_CASES)
def test_invalid_commit_msg(commit_msg: str):
    with pytest.raises(ValueError):
        SemanticMessage.parse(commit_msg)
    assert parse_commit_msg(commit_msg) == LegacyMessage(message=commit_msg)


def test_read_commit_log():
    class MockGitCommit(BaseModel):
        hexsha: str
        message: str

    with mock.patch("git.Repo") as repo:
        repo.iter_commits.return_value = iter(
            [
                MockGitCommit(hexsha="abc1234", message="feat: add user authentication"),
                MockGitCommit(hexsha="def5678", message="fix(api): resolve timeout issue"),
                MockGitCommit(hexsha="ghi9012", message="docs: update README"),
                MockGitCommit(hexsha="jkl3456", message="feat!: redesign UI"),
                MockGitCommit(hexsha="mno7890", message="chore: cleanup"),
                MockGitCommit(hexsha="pqr1234", message="not a semantic commit"),
                MockGitCommit(hexsha="stu5678", message="test(pytest): fix test_make_pancakes()"),
                MockGitCommit(hexsha="vwx9102", message="release(uv): this is a release!"),
                MockGitCommit(hexsha="yza3456", message="refactor: rewrite some logic"),
            ]
        )

        commits_iter = read_commit_log(repo)
        commits = list(commits_iter)
        assert isinstance(commits_iter, Iterator), "commits_iter should be an iterator"

    assert commits == [
        SemanticMessage(type="feat", scope=None, breaking=False, subject="add user authentication"),
        SemanticMessage(type="fix", scope="api", breaking=False, subject="resolve timeout issue"),
        SemanticMessage(type="docs", scope=None, breaking=False, subject="update README"),
        SemanticMessage(type="feat", scope=None, breaking=True, subject="redesign UI"),
        SemanticMessage(type="chore", scope=None, breaking=False, subject="cleanup"),
        LegacyMessage(message="not a semantic commit"),
        SemanticMessage(type="test", scope="pytest", breaking=False, subject="fix test_make_pancakes()"),
        SemanticMessage(type="release", scope="uv", breaking=False, subject="this is a release!"),
        SemanticMessage(type="refactor", scope=None, subject="rewrite some logic"),
    ]


def test_semantic_validation_breaking():
    with pytest.raises(ValueError):
        # noinspection PyTypeChecker
        SemanticMessage(
            type="feat",
            scope=None,
            breaking="Nope",
            subject="invalid breaking",
        )

    assert (
        SemanticMessage(
            type="feat",
            scope=None,
            breaking=False,
            subject="invalid breaking",
            body="BREAKING CHANGE: meepity moop",
        ).breaking
        is True
    ), "breaking should be true"
