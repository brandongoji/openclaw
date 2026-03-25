#!/usr/bin/env python3
import runpy
from pathlib import Path

TARGET = Path('/Users/hagios/Documents/Hagios 1/workspace/skills/response-delivery-monitor/scripts/check_response_delivery.py')
runpy.run_path(str(TARGET), run_name='__main__')
