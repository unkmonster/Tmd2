import json
import core
import os

j_lists = dict()

def init():
    if not os.path.exists(core.path):
        os.mkdir(core.path)
    
    # TODO
    if not os.path.exists(core.path + '\\.lists.json'):
        with open(core.path + '\\.lists.json', 'w', encoding='utf-8') as f:
            json.dump(dict(), f)
            pass
    
    # 读取已存在'列表'
    with open(core.path + '\\.lists.json', 'r', encoding='utf-8') as f:
        global j_lists
        j_lists = json.load(f)
        pass

def uninit():
    with open(core.path + '\\.lists.json', 'w', encoding='utf-8') as f:
        json.dump(j_lists, f, ensure_ascii=False, indent=4, separators=(',', ': '))