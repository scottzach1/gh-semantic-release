import logging
from collections.abc import Iterator
from os import PathLike
from pathlib import Path
from typing import Protocol

import toml
from git import Commit, Repo
from pydantic import BaseModel, ConfigDict


class VersionCommit(BaseModel):
    """
    Model abstraction
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    commit: Commit
    version: str


log = logging.getLogger("scottzach1").getChild("semantic_release").getChild("version_parser")


class VersionStrategy(Protocol):
    watch_path: PathLike

    @staticmethod
    def get_version(commit: Commit) -> str | None: ...


class Pep261:
    """
    Strategy to extract version from pyproject.toml following PEP 261 standard.

    ```toml
    [project]
    name = "project-name"
    version = "0.0.1"
    ```

    https://peps.python.org/pep-0621/
    """

    watch_path = "pyproject.toml"

    @staticmethod
    def get_version(commit: Commit) -> str | None:
        try:
            toml_content = (commit.tree / "pyproject.toml").data_stream.read().decode("utf-8")
        except KeyError:
            return None  # File missing for commit

        try:
            toml_dict = toml.loads(toml_content)
        except toml.TomlDecodeError:
            return None  # Malformed pyproject.toml file

        try:
            version = toml_dict["project"]["version"]

            if not isinstance(version, str):
                raise TypeError(f"Version must be a string (found {type(version)})")

            return version
        except (KeyError, TypeError):
            return None  # TOML data missing key(s) or malformed (e.g. is None or str)


class Uv(Pep261):
    """
    Callback strategy to extract version for an astral-sh/uv project (follows PEP 261).

    https://github.com/astral-sh/uv
    """


class PoetryV2(Pep261):
    """
    Callback strategy to extract version for a python-poetry/poetry (version 2) project (follows PEP 261).

    https://github.com/python-poetry/poetry
    """


class PoetryV1(Pep261):
    """
    Callback strategy to extract version for a python-poetry/poetry (version < 2) project.

    https://github.com/python-poetry/poetry/tree/1.8 (latest minor version as of 25/05/2025).
    """

    watch_path = "pyproject.toml"

    @staticmethod
    def get_version(commit: Commit) -> str | None:
        try:
            toml_content = (commit.tree / "pyproject.toml").data_stream.read().decode("utf-8")
        except KeyError:
            return None  # File missing for commit

        try:
            toml_dict = toml.loads(toml_content)
        except toml.TomlDecodeError:
            return None  # Malformed pyproject.toml file

        try:
            version = toml_dict["tool"]["poetry"]["version"]

            if not isinstance(version, str):
                raise TypeError(f"Version must be a string (found {type(version)})")

            return version
        except (KeyError, TypeError):
            return None  # TOML data missing key(s) or malformed (e.g. is None or str)


def iter_version_commits(repo: Repo, *, strategy: VersionStrategy) -> Iterator[VersionCommit]:
    """
    Extract commits containing version bumps based on user provided strategy.

    Args:
        repo: the repo to parse commits from.
        strategy: callback to extract version string from commit.

    Returns:
        iterator of commits where the version string is present and has changed (newest to oldest).
    """

    nxt_version = None  # version for previous iteration (we are recursing newest to oldest)
    nxt_commit = None

    for cur_commit in repo.iter_commits(paths=Path(repo.working_dir, strategy.watch_path)):
        cur_version = None
        try:
            cur_version = strategy.get_version(cur_commit)
        except Exception as e:
            log.warning("unexpected %s while parsing commit %s: %s", type(e).__name__, repr(cur_commit), str(e))

        if cur_version != nxt_version and nxt_commit is not None and nxt_version is not None:
            yield VersionCommit(commit=nxt_commit, version=nxt_version)

        nxt_commit = cur_commit
        nxt_version = cur_version
