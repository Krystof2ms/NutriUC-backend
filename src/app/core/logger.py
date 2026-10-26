import copy
import logging
from typing import ClassVar, override

from colorama import Fore, Style


class ColorFormatter(logging.Formatter):
    LEVEL_COLORS: ClassVar[dict[int, str]] = {
        logging.DEBUG: Fore.CYAN,
        logging.INFO: Fore.GREEN,
        logging.WARNING: Fore.YELLOW,
        logging.ERROR: Fore.RED,
        logging.CRITICAL: Fore.MAGENTA,
    }

    @override
    def format(self, record: logging.LogRecord):
        record_copy = copy.copy(record)

        color = self.LEVEL_COLORS.get(record.levelno, "")

        level_name = f"{record.levelname}:"
        padding = f"{level_name:<10}"

        record_copy.levelname = (
            f"{color}{record.levelname}{Style.RESET_ALL}"
            f"{padding[len(record.levelname):]}"
        )

        record_copy.name = f"{Fore.BLUE}{record.name}{Style.RESET_ALL}"

        return super().format(record_copy)


def init_logger(name: str):
    handler = logging.StreamHandler()
    handler.setFormatter(ColorFormatter(f"%(levelname)s%(name)s:{' ' * 2}%(message)s"))

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.propagate = False
    logger.addHandler(handler)

    return logger

logging.basicConfig()

logger = init_logger("app")
