import json
import core
import os
from userlist import UserList

def init():
    if not os.path.exists(core.path):
        os.mkdir(core.path)
    
    if not os.path.exists(core.path + '\\.lists.json'):
        with open(core.path + '\\.lists.json', 'w', encoding='utf-8') as f:
            json.dump(dict(), f)
            pass
    
    with open(core.path + '\\.lists.json', 'r', encoding='utf-8') as f:
        UserList.userlists = json.load(f)
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
        json.dump(UserList.userlists, f, ensure_ascii=False, indent=4, separators=(',', ': '))