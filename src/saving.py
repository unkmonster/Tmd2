import json
import core
import os
from twitter_list import TwitterList

def init():
    if not os.path.exists(core.path):
        os.mkdir(core.path)
    
    if not os.path.exists(core.path + '\\.lists.json'):
        with open(core.path + '\\.lists.json', 'w', encoding='utf-8') as f:
            json.dump(dict(), f)
            pass
    
    with open(core.path + '\\.lists.json', 'r', encoding='utf-8') as f:
        TwitterList.userlists = json.load(f)
        pass
    
    # single user
    path = core.path + '\\other'
    if not os.path.exists(path):
        os.mkdir(path)
    if not os.path.exists(path + '\\.users.json'):
        with open(path + '\\.users.json', 'w', encoding='utf-8') as f:
            json.dump(dict(), f)

def uninit():
    with open(core.path + '\\.lists.json', 'w', encoding='utf-8') as f:
        json.dump(TwitterList.userlists, f, ensure_ascii=False, indent=4, separators=(',', ': '))