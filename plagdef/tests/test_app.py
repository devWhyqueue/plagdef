from click.testing import CliRunner

from plagdef.app import cli, gui


def test_cli_version():
    runner = CliRunner()
    result = runner.invoke(cli, ['--version'])
    assert result.exit_code == 0


def test_gui_version():
    runner = CliRunner()
    result = runner.invoke(gui, ['--version'])
    assert result.exit_code == 0
