import json
import os

import core
import saving
from api import ListByRestId, ListMembers
from session import ses
import user

users = list()

class TweeterList:
    def __init__(self, rest_id) -> None:
        self.rest_id = str(rest_id)
        
        # Get info of the list
        ListByRestId.params['variables']['listId'] = self.rest_id
        params = {k: json.dumps(v) for k, v in ListByRestId.params.items()}
        
        res = ses.get(ListByRestId.api, params=params)
        res.raise_for_status()

        list = res.json()['data']['list']
        self.name = list['name']
        self.member_count = list['member_count']
        self.path = core.path + f'\\{self.name}'

        if not self.is_exist():
            self.create_profile()

        global users
        with open(self.path + '\\.users.json',encoding='utf-8') as f:           
            users = json.load(f)
        pass
    
    def is_exist(self) -> bool:
        return self.rest_id in saving.j_lists

    def update_info(self):
        if self.name != saving.j_lists[self.rest_id]:
            os.rename(core.path + f'\\{saving.j_lists[self.rest_id]}', self.path)

            if os.path.exists(self.path + '\\.history.ini'):
                with open(self.path + '\\.history.ini', 'w', encoding='utf-8'):
                    pass
            with open(self.path + '\\.history.ini', 'a', encoding='utf-8') as f:
                f.write(saving.j_lists[self.rest_id] + '\n')
            saving.j_lists[self.rest_id] = self.name

    def create_profile(self):
        saving.j_lists[self.rest_id] = self.name
        if not os.path.exists(self.path):
            os.mkdir(self.path)
        if not os.path.exists(self.path + f'\\.users.json'):
            with open(self.path + f'\\.users.json', 'w', encoding='utf-8') as f:
                json.dump(dict(), f)
                pass
        
    def get_members(self, count=50, cursor="") -> list:
        ListMembers.params['variables']['listId'] = self.rest_id
        ListMembers.params['variables']['count'] = count
        ListMembers.params['variables']['cursor'] = cursor

        params = {k: json.dumps(v) for k, v in ListMembers.params.items()}

        res = ses.get(ListMembers.api, params=params)
        res.raise_for_status()

        for instruction in res.json()['data']['list']['members_timeline']['timeline']['instructions']:
            if instruction['type'] == "TimelineAddEntries":
                return instruction['entries']
    
    def download_all(self):   
        count = 1
        entries = self.get_members()
        try:
            while len(entries) > 2:
                for entry in entries:
                    content = entry['content']
                    if content['entryType'] == 'TimelineTimelineItem':
                        result = content['itemContent']['user_results']['result']
                        
                        print(f"[{result['legacy']['name']}]", f"{count}/{self.member_count}")
                        user.TwitterUser(result['legacy']['screen_name'], 
                                    self.name, 
                                    result['legacy']['name'],
                                    result['rest_id']).download_all()
                        count = count + 1
                   
                    elif content['entryType'] == 'TimelineTimelineCursor':
                        if content['cursorType'] == 'Bottom':
                            entries = self.get_members(cursor=content['value'])
                            break
                    pass
        finally:
            self.close()
    
    def close(self):
        with open(self.path + '\\.users.json', 'w', encoding='utf-8') as f:
            json.dump(users, f, ensure_ascii=False, indent=4, separators=(',', ': '))
        users.clear()
    