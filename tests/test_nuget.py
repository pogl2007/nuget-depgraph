import urllib.error

import pytest

import nuget
from errors import RepositoryError
from main import main
from nuget import NuGetRepository, parse_dependencies, unique

URL = "https://api.nuget.org/v3-flatcontainer/"

NUSPEC = b"""<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://schemas.microsoft.com/packaging/2013/05/nuspec.xsd">
  <metadata>
    <id>Demo</id>
    <version>1.0.0</version>
    <dependencies>
      <group targetFramework="net462">
        <dependency id="B.Lib" version="2.0.0" />
        <dependency id="A.Lib" version="[1.0, 2.0)" />
      </group>
      <group targetFramework="netstandard2.0">
        <dependency id="B.Lib" version="2.0.0" />
      </group>
      <group targetFramework="net8.0" />
    </dependencies>
  </metadata>
</package>
"""

OLD_NUSPEC = b"""<?xml version="1.0"?>
<package>
  <metadata>
    <dependencies>
      <dependency id="Old.Lib" version="1.2" />
    </dependencies>
  </metadata>
</package>
"""


def test_nuspec_url():
    repository = NuGetRepository(URL)
    assert repository.nuspec_url("Serilog", "3.1.1") == (
        URL + "serilog/3.1.1/serilog.nuspec")


def test_parse_groups():
    dependencies = parse_dependencies(NUSPEC)
    assert [str(d) for d in dependencies] == [
        "B.Lib 2.0.0", "A.Lib [1.0, 2.0)", "B.Lib 2.0.0"]
    assert dependencies[0].framework == "net462"


def test_unique_and_sorted():
    names = [str(d) for d in unique(parse_dependencies(NUSPEC))]
    assert names == ["A.Lib [1.0, 2.0)", "B.Lib 2.0.0"]


def test_parse_without_groups():
    dependencies = parse_dependencies(OLD_NUSPEC)
    assert [str(d) for d in dependencies] == ["Old.Lib 1.2"]
    assert dependencies[0].framework == "any"


def test_parse_no_dependencies():
    assert parse_dependencies(b"<package><metadata/></package>") == []


def test_parse_bad_xml():
    with pytest.raises(RepositoryError, match="неверный формат"):
        parse_dependencies(b"<package><metadata>")


def raise_error(error):
    def fake_urlopen(url, timeout):
        raise error
    return fake_urlopen


@pytest.mark.parametrize("error, message", [
    (urllib.error.HTTPError(URL, 404, "Not Found", None, None),
     "не найдены"),
    (urllib.error.HTTPError(URL, 500, "Server Error", None, None),
     "код 500"),
    (urllib.error.URLError("no host"), "не удалось подключиться"),
    (TimeoutError("timed out"), "не удалось подключиться"),
])
def test_download_errors(monkeypatch, error, message):
    monkeypatch.setattr(nuget.urllib.request, "urlopen", raise_error(error))
    with pytest.raises(RepositoryError, match=message):
        NuGetRepository(URL).download(URL)


def test_direct_dependencies(monkeypatch):
    monkeypatch.setattr(NuGetRepository, "download",
                        staticmethod(lambda url: NUSPEC))
    dependencies = NuGetRepository(URL).direct_dependencies("Demo", "1.0.0")
    assert [d.name for d in dependencies] == ["A.Lib", "B.Lib"]


def test_main_prints_dependencies(monkeypatch, capsys):
    monkeypatch.setattr(NuGetRepository, "download",
                        staticmethod(lambda url: NUSPEC))
    code = main(["--package", "Demo", "--repo", URL, "--version", "1.0.0"])
    assert code == 0
    assert capsys.readouterr().out == (
        "Прямые зависимости Demo 1.0.0:\n"
        "  A.Lib [1.0, 2.0)\n"
        "  B.Lib 2.0.0\n"
        "Всего: 2\n"
    )


def test_main_no_dependencies(monkeypatch, capsys):
    monkeypatch.setattr(NuGetRepository, "download",
                        staticmethod(lambda url: OLD_NUSPEC.replace(
                            b"<dependency id=\"Old.Lib\" version=\"1.2\" />",
                            b"")))
    main(["--package", "Old", "--repo", URL, "--version", "1.0"])
    assert "  нет" in capsys.readouterr().out


def test_main_test_mode_not_ready(tmp_path, capsys):
    path = tmp_path / "graph.txt"
    path.write_text("A: B\n", encoding="utf-8")
    code = main(["--package", "A", "--repo", str(path),
                 "--test-mode", "--version", "1.0"])
    assert code == 1
    assert "этапе 3" in capsys.readouterr().out
