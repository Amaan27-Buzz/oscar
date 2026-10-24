"""Synthetic child that keeps its working directory until transport teardown."""

import os
import sys
import time
from pathlib import Path

Path(sys.argv[1]).write_text(str(os.getpid()))
while True:
    time.sleep(1)
