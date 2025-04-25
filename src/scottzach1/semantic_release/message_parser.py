import re
from collections.abc import Iterator
from typing import Any, Self

from git import Repo
from pydantic import BaseModel, ValidationError, field_validator, model_validator

TYPES = {
    "build",
    "chore",
    "ci",
    "docs",
    "feat",
    "fix",
    "perf",
    "refactor",
    "release",
    "revert",
    "style",
    "test",
    "temp",
}
COMMIT_PAT = re.compile(
    r"^(?P<type>[a-z]+)(\((?P<scope>[a-z0-9-]+)\))?(?P<breaking>!)?: (?P<subject>.+)(?:\r?\n\r?\n(?P<body>[\s\S]*))?$"
)
__UNSET__ = object()


class LegacyMessage(BaseModel):
    """
    Represents a not semantic commit message
    """

    message: str

    @classmethod
    def parse(cls, commit_msg: str) -> Self:
        return cls(message=commit_msg)


class SemanticMessage(BaseModel):
    """
    Represents a semantic commit message
    """

    type: str
    scope: str | None = None
    breaking: bool = False
    subject: str
    body: str | None = None

    @field_validator("type", "scope", "subject", "body")
    def _trim_whitespace(cls, v: str):
        if isinstance(v, str):
            return v.strip()
        return v

    @field_validator("type")
    def _validate_type(cls, v: str):
        if v not in TYPES:
            raise ValueError(f"Invalid semver type: {v!r}")
        return v

    @model_validator(mode="before")
    def _validate_breaking(cls, data: Any):
        if isinstance(data, dict):
            # Case 1: Check if breaking specified via ! ("refactor!: redesign interface", "fix(user)!: rem field", etc.)
            if (breaking := data.get("breaking", __UNSET__)) is not __UNSET__:
                if breaking == "!" or breaking is True:
                    data["breaking"] = True
                    return data
                elif breaking is not None and breaking is not False:
                    raise ValueError(f"Invalid breaking mode: {breaking!r}")

            # Case 2: Check for BREAKING CHANGE: in commit body.
            if (body := data.get("body")) and "BREAKING CHANGE" in body:
                data["breaking"] = True
                return data

            # Case 3: Default is False
            data["breaking"] = False
        return data

    @classmethod
    def parse(cls, commit_msg: str) -> Self:
        if match := COMMIT_PAT.fullmatch(commit_msg.strip()):
            try:
                return SemanticMessage(**match.groupdict())
            except ValidationError as err:
                raise ValueError(f"Failed to parse commit message: {commit_msg=!r}") from err

        raise ValueError(f"Commit does not follow semantic syntax: {commit_msg=!r}")


def parse_commit_msg(commit_msg: str) -> SemanticMessage | LegacyMessage:
    """
    Parse a commit message as a SemanticMessage model.

    :param commit_msg: Commit message to parse
    :return: parsed SemanticMessage if valid, LegacyMessage if not.
    """

    try:
        return SemanticMessage.parse(commit_msg)
    except (ValidationError, ValueError):
        return LegacyMessage.parse(commit_msg)


def read_commit_log(repo: Repo) -> Iterator[SemanticMessage | LegacyMessage]:
    """
    Create an iterator of parsed messages from a git repo up until the previous release.

    :param repo: the git repo to read from.
    :return: iterator of parsed SemanticMessages/LegacyMessages
    """
    for commit in repo.iter_commits():
        message = parse_commit_msg(commit.message)

        yield message
