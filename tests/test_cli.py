from typer.testing import CliRunner

from scottzach1.semantic_release.cli import app

runner = CliRunner()


def test_cli_main():
    result = runner.invoke(app)
    assert result.exit_code == 0
    assert result.output == "Hello world!\n"
