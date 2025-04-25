import hashlib
import logging
from collections.abc import Iterator
from pathlib import Path
from unittest.mock import MagicMock, call

import git
from git import Commit
from gitdb.util import hex_to_bin

from scottzach1.semantic_release.version_parser import Pep261, VersionCommit, VersionStrategy, iter_version_commits

PROJECT_ROOT = Path(__file__).parent.parent


def test_version_bumps():
    repo = git.Repo(PROJECT_ROOT)

    for bump in iter_version_commits(repo, strategy=Pep261):
        print(bump.commit.hexsha, bump.version, bump.commit.message)


class MockCommit(Commit):
    def __init__(self, repo, seed: str, **kwargs):
        hex_sha = hashlib.sha1(seed.encode("ascii")).hexdigest()
        bin_sha = hex_to_bin(hex_sha)

        self.seed = seed
        super().__init__(repo, bin_sha, **kwargs)

    def __repr__(self) -> str:
        return f"<MockCommit {self.seed}>"


def test_version_commits_logic(caplog):
    """
    Verity the toplevel behavior of iter_version_commits() with mocked repo and strategy.

    Validates expected behavior for None, str, and Exception results.
    """
    repo = MagicMock()  # spec=git.Repo)

    versions = [
        None,
        "1.1.1",
        "1.1.1",
        None,
        "1.1.0",
        "1.1.0",
        "1.1.0",
        "1.0.9",
        None,
        None,
        ValueError("MEEP"),
        "1.0.8",
    ]
    commits = [MockCommit(repo, f"commits[{i}]") for i, _ in enumerate(versions)]

    repo.working_dir = Path("/tmp/bogus")
    repo.iter_commits.return_value = commits

    strategy = MagicMock(spec=VersionStrategy)
    strategy.watch_path = "meep.txt"
    strategy.get_version.side_effect = versions

    # noinspection PyTypeChecker
    iterator = iter_version_commits(repo, strategy=strategy)
    assert isinstance(iterator, Iterator)

    with caplog.at_level(logging.WARNING):
        result = list(iterator)

    assert result == [
        VersionCommit(version="1.1.1", commit=commits[2]),
        VersionCommit(version="1.1.0", commit=commits[6]),
        VersionCommit(version="1.0.9", commit=commits[7]),
    ]
    assert "unexpected ValueError while parsing commit <MockCommit commits[10]>: MEEP" in caplog.text
    assert repo.iter_commits.mock_calls == [call(paths=Path("/tmp/bogus/meep.txt"))]
