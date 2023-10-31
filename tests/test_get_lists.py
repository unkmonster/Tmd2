import os
import sys
sys.path.append(os.getcwd())

from src.features import *
import json
import rich

for l in get_own_lists():
    rich.print_json(json.dumps(l))