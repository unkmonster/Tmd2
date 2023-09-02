from api import ListManagementPageTimeline
from session import ses
from session import switch_account
from logger import logger
from twitter_list import TwitterList
from twitter_user import TwitterUser
import core
import json
import os

class Manager:
    def __init__(self) -> None:
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

        # 第一账号为主账号
        switch_account()
    
    def __del__(self):
        with open(core.path + '\\.lists.json', 'w', encoding='utf-8') as f:
            json.dump(TwitterList.userlists, f, ensure_ascii=False, indent=4, separators=(',', ': '))

    def get_lists(self) -> list:
        try:
            r = ses.get(ListManagementPageTimeline.api,json=ListManagementPageTimeline.params)
            r.raise_for_status()
        except Exception as ex:
            logger.error(ex)
        
        items = r.json()['data']['viewer']['list_management_timeline']['timeline']['instructions'][3]['entries'][2]['content']['items']
        results = []
        for item in items:
            result = {}
            list = item['item']['itemContent']['list']
            result['name'] = list['name']
            result['id_str'] = list['id_str']
            result['member_count'] = list['member_count']
            results.append(result)
        return results
    
    def download_list(self, rest_id: list | str | int):
        if type(rest_id) != list:
            temp = rest_id
            rest_id = [temp]
            del temp

        for r in rest_id:
            TwitterList(r).download_all()
        
    def single_user_download(self, screen_name: list | str):
        path = core.path + '\\other'
        with open(path + '\\.users.json', encoding='utf-8') as f:
            users = json.load(f)
        
        try:
            if type(screen_name) == str:
                temp = screen_name
                screen_name = [temp]
                del temp

            for i in screen_name:
                TwitterUser(i, users, 'other').download_all()
        finally:
            with open(path + '\\.users.json', 'w', encoding='utf-8') as f:
                json.dump(users, f, ensure_ascii=False, indent=4, separators=(',', ': '))


    def download_all_list(self):
        for list in self.get_lists():
            TwitterList(list['id_str'], list['name'], list['member_count']).download_all()
