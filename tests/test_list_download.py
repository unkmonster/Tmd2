import os
import sys
sys.path.append(os.getcwd())

from src.twitter.list import TwitterList
from src.features import download


lst = TwitterList(rest_id=sys.argv[1])
download(lst, lst.get_members(lst._rest_id))