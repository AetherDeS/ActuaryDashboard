"""Делает корень проекта импортируемым в тестах (config, data, utils)."""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
