import json
import os
import core
import requests
from api import ListByRestId, ListMembers
from progress import prog
from session import ses
from user import TwitterUser
from logger import logger

class UserList:
    userlists = []

    def __init__(self, rest_id) -> None:
        self.rest_id = str(rest_id)
        
        # Get info of the list
        ListByRestId.params['variables']['listId'] = self.rest_id
        params = {k: json.dumps(v) for k, v in ListByRestId.params.items()}
        
        res = ses.get(ListByRestId.api, params=params)
        try:
            res.raise_for_status()
        except requests.exceptions.HTTPError as err:
            print(err)

        list = res.json()['data']['list']
        self.name = list['name']
        self.member_count = list['member_count']
        self.path = core.path + f'\\{self.name}'

        if not self.is_exist():
            self.create_profile()
        else:
            self.update_info()
        
        with open(self.path + '\\.users.json',encoding='utf-8') as f:           
            TwitterUser.users = json.load(f)
        pass

    def __del__(self):
        with open(self.path + '\\.users.json', 'w', encoding='utf-8') as f:
            json.dump(TwitterUser.users, f, ensure_ascii=False, indent=4, separators=(',', ': '))
        TwitterUser.users.clear()
        logger.debug("saved {}".format(self.path + '\\.users.json'))
    
    def is_exist(self) -> bool:
        return self.rest_id in UserList.userlists

    def update_info(self):
        if self.name != UserList.userlists[self.rest_id]['names'][0]:
            os.rename(core.path + f'\\{UserList.userlists[self.rest_id]["names"][0]}', self.path)
            list(UserList.userlists[self.rest_id]["names"]).insert(0, self.name)


    def create_profile(self):
        UserList.userlists[self.rest_id] = {'names': [self.name]}
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
        try:
            res.raise_for_status()
        except requests.exceptions.HTTPError as err:
            print(err)

        for instruction in res.json()['data']['list']['members_timeline']['timeline']['instructions']:
            if instruction['type'] == "TimelineAddEntries":
                return instruction['entries']
    
    def download_all(self):   
        entries = self.get_members()
        with prog:
            t1 = prog.add_task(self.name, total=self.member_count)   
            while len(entries) > 2:
                for entry in entries:
                    content = entry['content']
                    if content['entryType'] == 'TimelineTimelineItem':
                        result = content['itemContent']['user_results']['result']
                        
                        TwitterUser(result['legacy']['screen_name'], 
                                    self.name, 
                                    result['legacy']['name'],
                                    result['rest_id']).download_all()
                        prog.advance(t1)
                    elif content['entryType'] == 'TimelineTimelineCursor':
                        if content['cursorType'] == 'Bottom':
                            entries = self.get_members(cursor=content['value'])
                            break                       
    