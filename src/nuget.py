import urllib.error
import urllib.request
import xml.etree.ElementTree as ElementTree

from errors import RepositoryError

TIMEOUT = 15
NOT_FOUND = 404
ANY_FRAMEWORK = "any"


def local_name(tag):
    return tag.rsplit("}", 1)[-1]


class Dependency:

    def __init__(self, name, version, framework=ANY_FRAMEWORK):
        self.name = name
        self.version = version
        self.framework = framework

    def key(self):
        return self.name.lower(), self.version

    def __str__(self):
        return f"{self.name} {self.version}"


def make_dependency(element, framework):
    return Dependency(element.get("id"), element.get("version", ""),
                      framework)


def read_group(group):
    framework = group.get("targetFramework", ANY_FRAMEWORK)
    return [make_dependency(item, framework) for item in group
            if local_name(item.tag) == "dependency"]


def read_dependencies(element):
    result = []
    for child in element:
        name = local_name(child.tag)
        if name == "group":
            result.extend(read_group(child))
        elif name == "dependency":
            result.append(make_dependency(child, ANY_FRAMEWORK))
    return result


def parse_dependencies(data):
    try:
        root = ElementTree.fromstring(data)
    except ElementTree.ParseError as err:
        raise RepositoryError("Ошибка: неверный формат файла .nuspec") from err
    result = []
    for element in root.iter():
        if local_name(element.tag) == "dependencies":
            result.extend(read_dependencies(element))
    return result


def unique(dependencies):
    found = {}
    for dependency in dependencies:
        found.setdefault(dependency.key(), dependency)
    return [found[key] for key in sorted(found)]


class NuGetRepository:

    def __init__(self, url):
        self.url = url.rstrip("/")

    def nuspec_url(self, package, version):
        name = package.lower()
        return f"{self.url}/{name}/{version.lower()}/{name}.nuspec"

    @staticmethod
    def download(url):
        try:
            with urllib.request.urlopen(url, timeout=TIMEOUT) as response:
                return response.read()
        except urllib.error.HTTPError as err:
            if err.code == NOT_FOUND:
                raise RepositoryError(
                    "Ошибка: пакет или версия не найдены в репозитории"
                ) from err
            raise RepositoryError(
                f"Ошибка: репозиторий вернул код {err.code}") from err
        except (urllib.error.URLError, TimeoutError, ValueError) as err:
            reason = getattr(err, "reason", err)
            raise RepositoryError(
                f"Ошибка: не удалось подключиться к репозиторию: {reason}"
            ) from err

    def direct_dependencies(self, package, version):
        data = self.download(self.nuspec_url(package, version))
        return unique(parse_dependencies(data))
