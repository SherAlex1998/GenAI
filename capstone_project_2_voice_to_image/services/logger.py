import sys
from collections import deque
from typing import Deque, Iterable, List, Optional


class Logger:

    def __init__(self, max_entries: int = 500) -> None:
        self._buffer: Deque[str] = deque(maxlen=max_entries)

    def log(self, message: str) -> None:
        self._buffer.append(message)
        print(message, file=sys.stdout, flush=True)

    def history(self) -> List[str]:
        return list(self._buffer)

    def clear(self) -> None:
        self._buffer.clear()


LOGGER = Logger()


def log(message: str) -> None:
    LOGGER.log(message)


def get_logs() -> List[str]:
    return LOGGER.history()

