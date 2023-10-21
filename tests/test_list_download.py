import os
import sys
sys.path.append(os.getcwd())

from src.twitter.list import TwitterList

tmp = 1408996658352848904

lst = TwitterList(tmp)
print(f'{lst.name=}')
lst.download()