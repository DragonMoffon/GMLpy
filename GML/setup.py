from __future__ import annotations
from typing import TYPE_CHECKING

from GML.logging import setup_logging, get_logger

if TYPE_CHECKING:
    from arcade import Window


def setup_GMLpy() -> Window:
    setup_logging()
    logger = get_logger("setup")
    from arcade import Window

    window = Window(1, 1, "GML Headless Context")

    window.minimize()

    logger.debug("GML setup")

    return window
