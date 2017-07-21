import codecs
import logging
import io
import re
import sys


class ColorFormatter(logging.Formatter):
    """
    logging Formatter which prints messages with colors.
    """
    GREEN_MARKERS = [' ok', "ok:", 'finished', 'completed', 'ready',
                     'done', 'running', 'success', 'saved']
    GREEN_RE = re.compile("|".join(GREEN_MARKERS))

    def formatMessage(self, record):
        level_color = "0"
        text_color = "0"
        fmt = ""
        if record.levelno <= logging.DEBUG:
            fmt = "\033[0;37m" + logging.BASIC_FORMAT + "\033[0m"
        elif record.levelno <= logging.INFO:
            level_color = "1;36"
            lmsg = record.message.lower()
            if self.GREEN_RE.search(lmsg):
                text_color = "1;32"
        elif record.levelno <= logging.WARNING:
            level_color = "1;33"
        elif record.levelno <= logging.CRITICAL:
            level_color = "1;31"
        if not fmt:
            fmt = "\033[" + level_color + \
                  "m%(levelname)s\033[0m:%(name)s:\033[" + text_color + \
                  "m%(message)s\033[0m"
        return fmt % record.__dict__


def setup_logging(level):
    """
    Makes stdout and stderr unicode friendly in case of misconfigured
    environments, initializes the logging and enables colored logs if it is
    appropriate.

    :param level: The logging level, can be either an int or a string.
    :return: None
    """
    if not isinstance(level, int):
        level = logging._nameToLevel[level]

    def ensure_utf8_stream(stream):
        if not isinstance(stream, io.StringIO) and hasattr(stream, "buffer"):
            stream = codecs.getwriter("utf-8")(stream.buffer)
            stream.encoding = "utf-8"
        return stream

    sys.stdout, sys.stderr = (ensure_utf8_stream(s)
                              for s in (sys.stdout, sys.stderr))
    logging.basicConfig(level=level)
    root = logging.getLogger()
    # In some cases root has handlers and basicConfig() is a no-op
    root.setLevel(level)
    if not sys.stdin.closed and sys.stdout.isatty():
        handler = root.handlers[0]
        handler.setFormatter(ColorFormatter())
