import re

from pydantic import BaseModel, ValidationError, field_validator

TYPES = {"build", "chore", "ci", "docs", "feat", "fix", "perf", "refactor", "revert", "style", "test", "temp"}
COMMIT_PAT = re.compile(r"^(?P<type>[a-z]+)(\((?P<scope>[a-z0-9-]+)\))?(?P<breaking>!)?: (?P<subject>.+)$")


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


def parse_commit_msg(commit_msg: str) -> SemanticMessage:
    """
    Parse a commit message as a SemanticMessage model.

    :param commit_msg: Commit message to parse
    :return: parsed SemanticMessage if valid
    :raises: ValueError upon invalid message
    """

    if match := COMMIT_PAT.fullmatch(commit_msg):
        try:
            return SemanticMessage(**match.groupdict())
        except ValidationError as err:
            raise ValueError(f"Failed to parse commit message: {commit_msg=!r}") from err

    raise ValueError(f"Commit does not follow semantic syntax: {commit_msg=!r}")
