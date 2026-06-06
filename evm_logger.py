import logging
from datetime import datetime
from typing import Callable, Optional, List

_log_callbacks: List[Callable] = []


def add_log_callback(cb: Callable):
    if cb not in _log_callbacks:
        _log_callbacks.append(cb)


def remove_log_callback(cb: Callable):
    if cb in _log_callbacks:
        _log_callbacks.remove(cb)


class _UIHandler(logging.Handler):
    def emit(self, record: logging.LogRecord):
        if not _log_callbacks:
            return
        try:
            from kivy.clock import Clock
            ts = datetime.fromtimestamp(record.created).strftime("%H:%M:%S")
            full_line = f"[{ts}] [{record.levelname}]  {record.getMessage()}"
            level = record.levelname

            def _dispatch(dt):
                for cb in list(_log_callbacks):
                    try:
                        cb(level, full_line)
                    except Exception:
                        pass

            Clock.schedule_once(_dispatch, 0)
        except Exception:
            pass


_root_logger = logging.getLogger("smart_evm")
_root_logger.setLevel(logging.DEBUG)

_handler = _UIHandler()
_root_logger.addHandler(_handler)

_console = logging.StreamHandler()
_console.setLevel(logging.DEBUG)
_root_logger.addHandler(_console)


def get_logger(name: str = "smart_evm") -> logging.Logger:
    return logging.getLogger(name)
