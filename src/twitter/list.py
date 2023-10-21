import json
import os
from api import ListByRestId, ListMembers, Create

from utils.logger import logger
from utils.utility import raise_if_error
from src.session import session
from src.settings import *

import concurrent.futures  

class TwitterList:
    def __init__(self, rest_id, name = None, member_count = None) -> None:
        self.rest_id = str(rest_id)
        
        if name == None or member_count == None:
            ListByRestId.params['variables']['listId'] = self.rest_id
            params = {k: json.dumps(v) for k, v in ListByRestId.params.items()}              
            res = session.get(ListByRestId.api, params=params)
            raise_if_error(res)

            list = res.json()['data']['list']
            name = list['name']
            member_count = list['member_count']

        self.name = name
        self.member_count = member_count
        self.path = config.store_dir.joinpath(self.name)

        self.usermap_dir = project.lists_dir.joinpath('{}.json'.format(self.rest_id))
        self.users = {}
        """用户信息字典"""


        if not self.is_exist():
            self.create_profile()
        else:
            self.update()
    
        self.users = json.loads(self.usermap_dir.read_text('utf-8'))


    def __del__(self):
        self.usermap_dir.write_text(json.dumps(self.users, ensure_ascii=False, indent=4, separators=(',', ': ')), 'utf-8')
        logger.debug("Saved {}".format(self.usermap_dir))

    
    def is_exist(self) -> bool:
        return self.rest_id in json.loads(project.listj_dir.read_text('utf-8'))


    def update(self):
        listmap = json.loads(project.listj_dir.read_text('utf-8'))
        if self.name != listmap[self.rest_id]['names'][0]:
            config.store_dir.joinpath(listmap[self.rest_id]['names'][0]).rename(self.path)
            listmap[self.rest_id]["names"].insert(0, self.name)
            project.listj_dir.write_text(json.dumps(listmap, ensure_ascii=False, indent=4, separators=(',', ': ')), 'utf-8')
        if not self.path.exists():
            self.path.mkdir(parents=True)


    def create_profile(self):
        listmap = json.loads(project.listj_dir.read_text('utf-8'))
        listmap[self.rest_id] = {
            'names': [self.name]
        }
        project.listj_dir.write_text(json.dumps(listmap, ensure_ascii=False, indent=4, separators=(',', ': ')), 'utf-8')

        if not self.path.exists():
            self.path.mkdir(parents=True)
        
        # 以 rest_id 为文件名创建当前列表的 'users.json'
        if not self.usermap_dir.exists():
            self.usermap_dir.write_text(json.dumps(dict()))
    

    def user_exist(self, rest_id)->bool:
        return rest_id in self.users


    def get_members(self) -> list:
        if int(self.rest_id) < 0:
            logger.warning('本地列表不允许调用')
            return []

        members = []
        ListMembers.params['variables']['listId'] = self.rest_id
        ListMembers.params['variables']['count'] = 200
        ListMembers.params['variables']['cursor'] = ''

        while True:    
            res = session.get(ListMembers.api, json=ListMembers.params)
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
    
    
    def download(self):
        if int(self.rest_id) < 0:
            logger.warning('本地列表不允许调用')
            return
            
        from user import TwitterUser
        from utils.exception import TWRequestError, TwUserError
        

        entries = self.get_members()
        count = 1
        os.system("title {} {}/{}".format(self.name, count, self.member_count))
        
        def progress_update(f): # future callback
            nonlocal count
            count = count + 1
            os.system("title {} {}/{}".format(self.name, count, self.member_count))


        futures = [] 
        with concurrent.futures.ThreadPoolExecutor() as exc: 
            for entry in entries:
                content = entry['content']
                if content['entryType'] == 'TimelineTimelineItem':
                    result = content['itemContent']['user_results']['result']
                    os.system("title {} {}/{}".format(self.name, count, self.member_count))
                    
                    future = exc.submit(TwitterUser.download, TwitterUser(result['legacy']['screen_name'], 
                                                                            self,
                                                                            result['legacy']['name'],
                                                                            result['rest_id'])
                    )
                    future.add_done_callback(progress_update)
                    futures.append(future)
                    
        for res in concurrent.futures.as_completed(futures):
            try:
                res.exception()
            except TWRequestError as err:
                logger.warning(err)
            except TwUserError as err:
                logger.warning(err.fmt_msg())
                if err.reason == 'UserUnavailable':
                    print('需要关注')
                    pass
