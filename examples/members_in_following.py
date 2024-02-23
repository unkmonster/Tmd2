import os
import sys
sys.path.append(os.getcwd())

from src.twitter.list import TwitterUser
from rich.console import Console

if __name__ == '__main__':
    console = Console()
    members = TwitterUser(screen_name=sys.argv[1]).get_following()
    with open(F'{sys.argv[1]}.txt', 'w', encoding='utf-8') as f:
        for i, m in enumerate(members):
            console.out(F'[{i+1}] {m._rest_id} {m._name}(@{m._screen_name})')
            f.write(F'[{i+1}] {m._rest_id} {m._name}(@{m._screen_name})\n')