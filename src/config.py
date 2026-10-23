import argparse
import os
import re

from errors import ConfigError

NAME_PATTERN = re.compile(r"[A-Za-z0-9_][A-Za-z0-9_.-]*")
VERSION_PATTERN = re.compile(r"\d+(\.\d+){1,3}(-[0-9A-Za-z.-]+)?")
URL_PREFIXES = ("http://", "https://")
MAX_NAME_LENGTH = 100
MIN_DEPTH = 1
DEFAULT_DEPTH = 3


class Config:

    def __init__(self, package, repo, version,
                 max_depth=DEFAULT_DEPTH, test_mode=False):
        self.package = package
        self.repo = repo
        self.test_mode = test_mode
        self.version = version
        self.max_depth = max_depth

    @classmethod
    def from_args(cls, argv=None):
        parser = argparse.ArgumentParser(
            description="Граф зависимостей пакетов NuGet")
        parser.add_argument("--package", required=True,
                            help="имя анализируемого пакета")
        parser.add_argument("--repo", required=True,
                            help="URL репозитория или путь к файлу "
                                 "тестового репозитория")
        parser.add_argument("--test-mode", action="store_true",
                            help="работать с тестовым репозиторием")
        parser.add_argument("--version", required=True,
                            help="версия пакета")
        parser.add_argument("--max-depth", type=int, default=DEFAULT_DEPTH,
                            help="максимальная глубина анализа")
        args = parser.parse_args(argv)
        return cls(args.package, args.repo, args.version,
                   args.max_depth, args.test_mode)

    def check_package(self):
        if not self.package:
            return "Ошибка: имя пакета не может быть пустым"
        if len(self.package) > MAX_NAME_LENGTH:
            return "Ошибка: имя пакета слишком длинное"
        if not NAME_PATTERN.fullmatch(self.package):
            return f"Ошибка: недопустимое имя пакета: {self.package}"
        return None

    def check_repo(self):
        if self.test_mode:
            if not os.path.isfile(self.repo):
                return f"Ошибка: файл тестового репозитория не найден: " \
                       f"{self.repo}"
            return None
        if not self.repo.startswith(URL_PREFIXES):
            return f"Ошибка: URL репозитория должен начинаться с " \
                   f"http:// или https://: {self.repo}"
        return None

    def check_version(self):
        if not VERSION_PATTERN.fullmatch(self.version):
            return f"Ошибка: неверный формат версии: {self.version}"
        return None

    def check_depth(self):
        if self.max_depth < MIN_DEPTH:
            return f"Ошибка: глубина должна быть не меньше {MIN_DEPTH}: " \
                   f"{self.max_depth}"
        return None

    def validate(self):
        checks = (self.check_package(), self.check_repo(),
                  self.check_version(), self.check_depth())
        errors = [error for error in checks if error]
        if errors:
            raise ConfigError("\n".join(errors))
