import logging

_setup: bool = False


def setup_logging(
    file_level: int = logging.INFO,
    stream_level: int = logging.DEBUG,
    filename: str = "gmlid.log",
    include_stream: bool = True,
):
    # Early exit is setup already called
    global _setup
    if _setup:
        return

    # Locally needed imports
    import logging.handlers
    import queue

    # Queue handler for non-blocking logging
    log_queue = queue.Queue(-1)
    queue_handler = logging.handlers.QueueHandler(log_queue)

    # File and stream logging
    file_handler = logging.FileHandler(filename, "a", "utf-8")
    file_handler.setLevel(file_level)
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(stream_level)

    # Format stream output with colour and only immediately readable info
    stream_formatter = logging.Formatter(
        "\033[38;2;255;165;0m{asctime}\033[39m :\033[31m{levelname}\033[39m: [{name}] - {message}",
        style="{",
        datefmt="%Y-%m-%d %H:%M:%S UTC%z",
    )
    stream_handler.setFormatter(stream_formatter)

    # Format Log File without colour, and in easily splitable columns
    file_formatter = logging.Formatter(
        "{asctime} | {levelname:^8} | {name:^16} | {pathname:^60} | {funcName:^20} | {lineno:^4} | {message}",
        style="{",
        datefmt="%Y-%m-%d %H:%M:%S UTC%z",
    )
    file_handler.setFormatter(file_formatter)

    # Setup listener for non-blocking logging
    if include_stream:
        listener = logging.handlers.QueueListener(
            log_queue, file_handler, stream_handler, respect_handler_level=True
        )
    else:
        listener = logging.handlers.QueueListener(
            log_queue, file_handler, respect_handler_level=True
        )

    # Create parent logger and set level to DEBUG
    logger = logging.getLogger("GMLpy")
    logger.setLevel(logging.DEBUG)
    logger.addHandler(queue_handler)

    logger.debug("logger setup")

    _setup = True

    # Start QueueListener for non-blocking logging
    listener.start()

    # Return listener for early `listener.stop()`
    return listener


def get_logger(name: str):
    """
    Get a logging.Logger and setup GML logger with automatic name attachment
    """
    setup_logging()
    return logging.getLogger(f"GMLpy.{name}")
