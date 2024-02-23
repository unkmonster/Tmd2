import os
import sys
sys.path.append(os.getcwd())

from src.twitter.list import TwitterList
import rich

if __name__ == '__main__':
    members = TwitterList(rest_id=sys.argv[1]).get_members()
    for i, m in enumerate(members):
        rich.print(F'[{i+1}] {m._name}(@{m._screen_name})')
