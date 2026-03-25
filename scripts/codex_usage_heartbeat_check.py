#!/usr/bin/env python3
import runpy
from pathlib import Path

TARGET = Path('/Users/hagios/Documents/Hagios 1/workspace/scripts/api_limit_heartbeat_check.py')
runpy.run_path(str(TARGET), run_name='__main__')
