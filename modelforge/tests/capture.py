from io import StringIO
from contextlib import contextmanager
import logging
import sys


@contextmanager
def captured_output():
    log = StringIO()
    log_handler = logging.StreamHandler(log)
    logging.getLogger().addHandler(log_handler)
    new_out, new_err = StringIO(), StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    new_out.isatty = lambda: True
    try:
        sys.stdout, sys.stderr = new_out, new_err
        yield new_out, new_err, log
    finally:
        sys.stdout, sys.stderr = old_out, old_err
        logging.getLogger().removeHandler(log_handler)
