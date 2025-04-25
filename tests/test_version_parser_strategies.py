from collections.abc import Callable
from unittest.mock import MagicMock, PropertyMock

import pytest
from git import Commit

from scottzach1.semantic_release.version_parser import (
    Pep261,
    PoetryV1,
    PoetryV2,
    Uv,
    VersionStrategy,
)

# --- Mock Fixtures ---


@pytest.fixture
def mock_commit() -> MagicMock:
    return MagicMock(spec=Commit)


@pytest.fixture
def mock_tree(mock_commit: MagicMock) -> MagicMock:
    """Creates a mock gitpython Tree object and attaches it to the mock commit."""
    tree = MagicMock()
    mock_commit.tree = tree
    return tree


@pytest.fixture
def mock_blob() -> tuple[MagicMock, MagicMock]:
    """Creates a mock gitpython Blob object."""
    blob = MagicMock()
    data_stream_mock = MagicMock()
    # We use PropertyMock because data_stream is accessed as an attribute
    type(blob).data_stream = PropertyMock(return_value=data_stream_mock)
    return blob, data_stream_mock  # Return both for easier access


# --- Helper Function ---


def setup_commit_file(
    mock_tree: MagicMock,
    mock_blob_data_stream: tuple[MagicMock, MagicMock],
    filename: str,
    content: str | None = None,
    exists: bool = True,
    read_error: Exception | None = None,
):
    """
    Configures the mock tree and blob for a specific file.
    """
    mock_blob_obj, mock_stream = mock_blob_data_stream

    def tree_truediv_side_effect(path):
        if str(path) == filename and exists:
            return mock_blob_obj
        else:
            # Simulate file not found
            raise KeyError(f"File '{path}' not found in commit")

    mock_tree.__truediv__.side_effect = tree_truediv_side_effect

    if exists and content is not None:
        mock_stream.read.return_value = content.encode("utf-8")
    elif read_error:
        mock_stream.read.side_effect = read_error
    else:
        # Ensure read isn't called if the file doesn't exist via KeyError
        pass


# --- Test Cases ---


class StrategyTest:
    """
    Base class for testing all Strategy implementations.
    """

    STRATEGY = VersionStrategy

    def test_strategy_implements_protocol(self):
        assert hasattr(self.STRATEGY, "watch_path")
        assert isinstance(self.STRATEGY.watch_path, str)
        assert hasattr(self.STRATEGY, "get_version")
        assert isinstance(self.STRATEGY.get_version, Callable)


class TestPep261(StrategyTest):
    """
    Tests for the Pep261 strategy.
    """

    STRATEGY = Pep261
    FILENAME = "pyproject.toml"
    VALID_CONTENT = """
[project]
name = "my-package"
version = "1.2.3"
description = "A test package"
"""
    MISSING_VERSION_CONTENT = """
[project]
name = "my-package"
description = "A test package"
"""
    MISSING_PROJECT_CONTENT = """
[tool.other]
value = "something"
"""
    INVALID_TOML_CONTENT = """
[project]
name = "my-package"
version = "1.2.3"
invalid = [ key = "no"
"""
    INVALID_STRUCTURE_CONTENT_PROJECT_STR = """
project = "not a table"
"""
    INVALID_STRUCTURE_CONTENT_VERSION_INT = """
[project]
name = "my-package"
version = 456
"""

    def test_watch_path(self):
        assert self.STRATEGY.watch_path == self.FILENAME

    def test_get_version_success(self, mock_commit, mock_tree, mock_blob):
        """
        Test successful version extraction.
        """
        blob_obj, stream_mock = mock_blob
        setup_commit_file(mock_tree, (blob_obj, stream_mock), self.FILENAME, self.VALID_CONTENT)
        version = self.STRATEGY.get_version(mock_commit)
        assert version == "1.2.3"
        mock_tree.__truediv__.assert_called_once_with(self.FILENAME)
        stream_mock.read.assert_called_once()

    def test_get_version_file_missing(self, mock_commit, mock_tree, mock_blob):
        """
        Test when pyproject.toml is missing.
        """
        blob_obj, stream_mock = mock_blob
        setup_commit_file(mock_tree, (blob_obj, stream_mock), self.FILENAME, exists=False)
        version = self.STRATEGY.get_version(mock_commit)
        assert version is None
        mock_tree.__truediv__.assert_called_once_with(self.FILENAME)
        stream_mock.read.assert_not_called()  # Read shouldn't be called if KeyError

    def test_get_version_malformed_toml(self, mock_commit, mock_tree, mock_blob):
        """
        Test with invalid TOML content.
        """
        blob_obj, stream_mock = mock_blob
        setup_commit_file(mock_tree, (blob_obj, stream_mock), self.FILENAME, self.INVALID_TOML_CONTENT)
        version = self.STRATEGY.get_version(mock_commit)
        assert version is None
        mock_tree.__truediv__.assert_called_once_with(self.FILENAME)
        stream_mock.read.assert_called_once()

    @pytest.mark.parametrize(
        "content, description",
        [
            (MISSING_VERSION_CONTENT, "missing version key"),
            (MISSING_PROJECT_CONTENT, "missing project table"),
            (INVALID_STRUCTURE_CONTENT_PROJECT_STR, "project key is not a table"),
            (INVALID_STRUCTURE_CONTENT_VERSION_INT, "version key is not a string"),
            ("", "empty file"),  # Also causes TomlDecodeError or KeyError
        ],
    )
    def test_get_version_invalid_structure(self, mock_commit, mock_tree, mock_blob, content, description):
        """
        Test various invalid structures within the TOML file.
        """
        blob_obj, stream_mock = mock_blob
        setup_commit_file(mock_tree, (blob_obj, stream_mock), self.FILENAME, content)
        version = self.STRATEGY.get_version(mock_commit)
        assert version is None, f"Failed for case: {description}"
        mock_tree.__truediv__.assert_called_once_with(self.FILENAME)
        # Read might be called or not depending on when the error occurs (parsing vs lookup)
        # So we don't assert read count strictly here, just that the outcome is None.


class TestUv(TestPep261):
    """
    Tests for the Uv strategy (inherits from Pep261).
    """

    STRATEGY = Uv

    def test_inheritance(self):
        assert issubclass(Uv, Pep261)
        assert Uv.get_version is Pep261.get_version


class TestPoetryV2(TestPep261):
    """
    Tests for the PoetryV2 strategy (inherits from Pep261).
    """

    STRATEGY = PoetryV2

    def test_inheritance(self):
        assert issubclass(PoetryV2, Pep261)
        assert PoetryV2.get_version is Pep261.get_version


class TestPoetryV1(StrategyTest):
    """
    Tests for the PoetryV1 strategy.
    """

    STRATEGY = PoetryV1
    FILENAME = "pyproject.toml"
    VALID_CONTENT = """
[tool.poetry]
name = "my-poetry-package"
version = "0.5.0"
description = ""
authors = ["Your Name <you@example.com>"]

[build-system]
requires = ["poetry-core>=1.0.0"]
build-backend = "poetry.core.masonry.api"
"""
    MISSING_VERSION_CONTENT = """
[tool.poetry]
name = "my-poetry-package"
"""
    MISSING_POETRY_CONTENT = """
[tool.other]
value = "something"
"""
    MISSING_TOOL_CONTENT = """
[project]
name = "test"
"""
    INVALID_TOML_CONTENT = TestPep261.INVALID_TOML_CONTENT  # Re-use invalid toml
    INVALID_STRUCTURE_CONTENT_TOOL_STR = """
tool = "not a table"
"""
    INVALID_STRUCTURE_CONTENT_POETRY_STR = """
[tool]
poetry = "not a table"
"""
    INVALID_STRUCTURE_CONTENT_VERSION_INT = """
[tool.poetry]
name = "my-poetry-package"
version = 123
"""

    def test_watch_path(self):
        assert self.STRATEGY.watch_path == self.FILENAME

    def test_get_version_success(self, mock_commit, mock_tree, mock_blob):
        """
        Test successful version extraction for Poetry v1.
        """
        blob_obj, stream_mock = mock_blob
        setup_commit_file(mock_tree, (blob_obj, stream_mock), self.FILENAME, self.VALID_CONTENT)
        version = self.STRATEGY.get_version(mock_commit)
        assert version == "0.5.0"
        mock_tree.__truediv__.assert_called_once_with(self.FILENAME)
        stream_mock.read.assert_called_once()

    def test_get_version_file_missing(self, mock_commit, mock_tree, mock_blob):
        """
        Test when pyproject.toml is missing for Poetry v1.
        """
        blob_obj, stream_mock = mock_blob
        setup_commit_file(mock_tree, (blob_obj, stream_mock), self.FILENAME, exists=False)
        version = self.STRATEGY.get_version(mock_commit)
        assert version is None
        mock_tree.__truediv__.assert_called_once_with(self.FILENAME)
        stream_mock.read.assert_not_called()

    def test_get_version_malformed_toml(self, mock_commit, mock_tree, mock_blob):
        """
        Test with invalid TOML content for Poetry v1.
        """
        blob_obj, stream_mock = mock_blob
        setup_commit_file(mock_tree, (blob_obj, stream_mock), self.FILENAME, self.INVALID_TOML_CONTENT)
        version = self.STRATEGY.get_version(mock_commit)
        assert version is None
        mock_tree.__truediv__.assert_called_once_with(self.FILENAME)
        stream_mock.read.assert_called_once()

    @pytest.mark.parametrize(
        "content, description",
        [
            (MISSING_VERSION_CONTENT, "missing version key"),
            (MISSING_POETRY_CONTENT, "missing poetry table"),
            (MISSING_TOOL_CONTENT, "missing tool table"),
            (INVALID_STRUCTURE_CONTENT_TOOL_STR, "tool key is not a table"),
            (INVALID_STRUCTURE_CONTENT_POETRY_STR, "poetry key is not a table"),
            (INVALID_STRUCTURE_CONTENT_VERSION_INT, "version key is not a string"),
            ("", "empty file"),  # Also causes TomlDecodeError or KeyError
        ],
    )
    def test_get_version_invalid_structure(self, mock_commit, mock_tree, mock_blob, content, description):
        """
        Test various invalid structures within the TOML file for Poetry v1.
        """
        blob_obj, stream_mock = mock_blob
        setup_commit_file(mock_tree, (blob_obj, stream_mock), self.FILENAME, content)
        version = self.STRATEGY.get_version(mock_commit)
        assert version is None, f"Failed for case: {description}"
        mock_tree.__truediv__.assert_called_once_with(self.FILENAME)
        # Read might be called or not depending on when the error occurs (parsing vs lookup)
