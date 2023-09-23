import json
import os
import core
import requests
from api import ListByRestId, ListMembers
from progress import prog
from session import ses
from twitter.twitter_user import TwitterUser
from logger import logger
from utility import raise_if_error

class TwitterList:
    # TEMP
    userlists = {}

    def __init__(self, rest_id, name = None, member_count = None) -> None:
        self.rest_id = str(rest_id)
        
        if name == None or member_count == None:
            # Get infomation of the list
            ListByRestId.params['variables']['listId'] = self.rest_id
            params = {k: json.dumps(v) for k, v in ListByRestId.params.items()}              
            res = ses.get(ListByRestId.api, params=params)
            raise_if_error(res)

            list = res.json()['data']['list']
            name = list['name']
            member_count = list['member_count']

        self.name = name
        self.member_count = member_count
        self.path = core.path + f'\\{self.name}'
        self.users = {}

        if not self.is_exist():
            self.create_profile()
        else:
            self.update()
        
        with open(self.path + '\\.users.json',encoding='utf-8') as f:           
            self.users = json.load(f)


    def __del__(self):
        with open(self.path + '\\.users.json', 'w', encoding='utf-8') as f:
            json.dump(self.users, f, ensure_ascii=False, indent=4, separators=(',', ': '))
        logger.info("Saved {}".format(os.path.join(self.path, '.users.json')))

    
    def is_exist(self) -> bool:
        return self.rest_id in TwitterList.userlists

    def update(self):
        if self.name != TwitterList.userlists[self.rest_id]['names'][0]:
            os.rename(core.path + f'\\{TwitterList.userlists[self.rest_id]["names"][0]}', self.path)
            TwitterList.userlists[self.rest_id]["names"].insert(0, self.name)


    def create_profile(self):
        TwitterList.userlists[self.rest_id] = {'names': [self.name]}
        if not os.path.exists(self.path):
            os.mkdir(self.path)
        if not os.path.exists(self.path + f'\\.users.json'):
            with open(self.path + f'\\.users.json', 'w', encoding='utf-8') as f:
                json.dump(dict(), f)
                pass
        
    def get_members(self) -> list:
        members = []
        ListMembers.params['variables']['listId'] = self.rest_id
        ListMembers.params['variables']['count'] = 200
        ListMembers.params['variables']['cursor'] = ''

        while True:    
            res = ses.get(ListMembers.api, json=ListMembers.params)
            raise_if_error(res)

            for instruction in res.json()['data']['list']['members_timeline']['timeline']['instructions']:
                if instruction['type'] == "TimelineAddEntries":
                    if len(instruction['entries']) == 2:
                        return members
                    else:
                        cursors = [instruction['entries'].pop(), instruction['entries'].pop()]
                        members.extend(instruction['entries'])
                        
                        for cur in cursors:
                            if cur['content']['cursorType'] == 'Bottom':
                                ListMembers.params['variables']['cursor'] = cur['content']['value']
                                break
                    break
    
    
    def download_all(self):
        from exception import TWRequestError, TwUserError
        entries = self.get_members()
        t1 = prog.add_task(self.name, total=self.member_count)   
        for entry in entries:
            content = entry['content']
            if content['entryType'] == 'TimelineTimelineItem':
                result = content['itemContent']['user_results']['result']
                try:
                    TwitterUser(result['legacy']['screen_name'], 
                                self.users,
                                self.name, 
                                result['legacy']['name'],
                                result['rest_id']).download()
                except TWRequestError as err:
                    logger.warning(err.msg())
                except TwUserError as err:
                    logger.warning(err.fmt_msg())
                prog.advance(t1)                    