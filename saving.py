import json
import core
import os

users = dict()

def init():
    if not os.path.exists(core.path):
        os.mkdir(core.path)
    
    if not os.path.exists(core.path + '\\.users.json'):
        with open(core.path + '\\.users.json', 'w', encoding='utf-8') as f:
            json.dump(dict(), f)
            pass
    
    # 读取已存在用户列表
    with open(core.path + '\\.users.json', 'r', encoding='utf-8') as f:
        global users
        users = json.load(f)
        pass

def uninit():
    with open(core.path + '\\.users.json', 'w', encoding='utf-8') as f:
        json.dump(users, f, ensure_ascii=False)