import sys

from config import Config
from errors import ConfigError


def main(argv=None):
    config = Config.from_args(argv)
    config.show()
    try:
        config.validate()
    except ConfigError as err:
        print(err)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
