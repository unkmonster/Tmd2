import os
import sys
sys.path.append(os.getcwd())

from src.twitter.list import TwitterList



lst = TwitterList(rest_id=sys.argv[1])
lst.download()