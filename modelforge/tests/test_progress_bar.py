import io
import logging
import sys
import unittest

from clint.textui import progress

from modelforge import progress_bar


class ProgressBarTests(unittest.TestCase):
    def test_progress_bar(self):
        logger = logging.getLogger("progress")
        logger.setLevel(logging.INFO)
        stream = io.StringIO()
        stream.isatty = lambda: True
        progress.STREAM = stream
        list(progress_bar.progress_bar(range(10), logger, expected_size=10))
        self.assertEqual(stream.getvalue().strip()[-51:],
                         "[################################] 10/10 - 00:00:00")
        progress.STREAM = sys.stderr

if __name__ == "__main__":
    unittest.main()
