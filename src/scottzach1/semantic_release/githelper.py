import re
from collections.abc import Iterator
from typing import Self

from git import Repo
from pydantic import BaseModel, ValidationError, field_validator

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
COMMIT_PAT = re.compile(r"^(?P<type>[a-z]+)(\((?P<scope>[a-z0-9-]+)\))?(?P<breaking>!)?: (?P<subject>.+)$")


class LegacyMessage(BaseModel):
    """
    Represents a not semantic commit message
    """

    commit_msg: str

    @classmethod
    def parse(cls, commit_msg: str) -> Self:
        return cls(commit_msg=commit_msg)


class SemanticMessage(BaseModel):
    """
    Represents a semantic commit message
    """

    type: str
    scope: str | None = None
    breaking: bool = False
    subject: str

    @field_validator("type")
    def _validate_type(cls, v: str):
        if v not in TYPES:
            raise ValueError(f"Invalid semver type: {v!r}")
        return v

    @field_validator("breaking", mode="before")
    def _validate_breaking(cls, v: str | None) -> bool:
        if v is True or v == "!":
            return True

        if v is False or v is None:
            return False

        raise ValueError(f"Unexpected value for breaking: {v!r}")

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

        if isinstance(message, SemanticMessage) and message.type == "release":
            break

        yield message
