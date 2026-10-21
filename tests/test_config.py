import pytest

from config import Config
from errors import ConfigError
from main import main

URL = "https://api.nuget.org/v3-flatcontainer/"


def make(**changes):
    params = {"package": "Serilog", "repo": URL, "version": "3.1.1",
              "max_depth": 3, "test_mode": False}
    params.update(changes)
    return Config(**params)


def test_from_args():
    config = Config.from_args([
        "--package", "Serilog", "--repo", URL,
        "--version", "3.1.1", "--max-depth", "5",
    ])
    assert config.package == "Serilog"
    assert config.repo == URL
    assert config.version == "3.1.1"
    assert config.max_depth == 5
    assert config.test_mode is False


def test_default_depth():
    config = Config.from_args(
        ["--package", "A", "--repo", URL, "--version", "1.0"])
    assert config.max_depth == 3


def test_show(capsys):
    make().show()
    assert capsys.readouterr().out == (
        "package=Serilog\n"
        f"repo={URL}\n"
        "test_mode=False\n"
        "version=3.1.1\n"
        "max_depth=3\n"
    )


def test_valid_config():
    make().validate()


def test_valid_test_mode(tmp_path):
    path = tmp_path / "graph.txt"
    path.write_text("A: B\n", encoding="utf-8")
    make(repo=str(path), test_mode=True).validate()


@pytest.mark.parametrize("changes, message", [
    ({"package": ""}, "не может быть пустым"),
    ({"package": "bad name"}, "недопустимое имя пакета"),
    ({"package": "A" * 101}, "слишком длинное"),
    ({"repo": "ftp://example.com"}, "должен начинаться с http"),
    ({"repo": "no_such.txt", "test_mode": True}, "не найден"),
    ({"version": "abc"}, "неверный формат версии"),
    ({"version": "1"}, "неверный формат версии"),
    ({"max_depth": 0}, "не меньше 1"),
])
def test_invalid(changes, message):
    with pytest.raises(ConfigError, match=message):
        make(**changes).validate()


def test_all_errors_at_once():
    config = make(package="", version="x", max_depth=-1)
    with pytest.raises(ConfigError) as info:
        config.validate()
    assert len(str(info.value).splitlines()) == 3


def test_depth_not_number():
    with pytest.raises(SystemExit):
        Config.from_args(["--package", "A", "--repo", URL,
                          "--version", "1.0", "--max-depth", "abc"])


def test_missing_required():
    with pytest.raises(SystemExit):
        Config.from_args(["--package", "A"])


def test_main_exit_codes(capsys):
    assert main(["--package", "A", "--repo", URL, "--version", "1.0"]) == 0
    assert main(["--package", "A", "--repo", "x", "--version", "1.0"]) == 1
    assert "Ошибка" in capsys.readouterr().out
