import json
import os
from api import ListByRestId, ListMembers, Create

from src.utils.logger import logger
from utils.utility import raise_if_error
from src.session import session
from src.settings import *

import concurrent.futures  

from src.twitter.user import TwitterUser
class TwitterList:
    def __init__(self, rest_id, name = None) -> None:
        self.rest_id = str(rest_id)
        
        if name == None:
            if int(rest_id) < 0:
                listmap = json.loads(project.listj_dir.read_text('utf-8'))
                self.name = listmap[self.rest_id]['names'][0]
                self.path = config.store_dir.joinpath(self.name)
                return
            else:
                ListByRestId.params['variables']['listId'] = self.rest_id
                params = {k: json.dumps(v) for k, v in ListByRestId.params.items()}              
                res = session.get(ListByRestId.api, params=params)
                raise_if_error(res)

                list = res.json()['data']['list']
                name = list['name']


        self.name = name
        self.path = config.store_dir.joinpath(self.name)

        if not self.is_exist():
            self.create_profile()
        else:
            self.update()

    
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
        if not self.path.exists():
            self.path.mkdir(parents=True)

        listmap = json.loads(project.listj_dir.read_text('utf-8'))
        listmap[self.rest_id] = {
            'names': [self.name]
        }
        project.listj_dir.write_text(json.dumps(listmap, ensure_ascii=False, indent=4, separators=(',', ': ')), 'utf-8')


    def get_members(self) -> list[TwitterUser]:
        if int(self.rest_id) == -2: # 关注中的
            from src.features import get_following
            from src.session import account
            members = get_following(account.rest_id)
            self.member_count = len(members)
            return members
        if int(self.rest_id) < 0:
            print('本地列表不允许调用')
            return []

        cursor = ''
        ListMembers.params['variables']['listId'] = self.rest_id
        ListMembers.params['variables']['count'] = 200

        entries = []
        while True:
            ListMembers.params['variables']['cursor'] = cursor
            res = session.get(ListMembers.api, json=ListMembers.params)
            raise_if_error(res)

            ets = res.json()['data']['list']['members_timeline']['timeline']['instructions'][-1]['entries']
            cursors = [ets.pop(), ets.pop()]

            if not len(ets):
                break
            entries.extend(ets)
            for cur in cursors:
                if cur['content']['cursorType'] == 'Bottom':
                    cursor = cur['content']['value']
                    break

        self.member_count = len(entries)
        return [TwitterUser(result=entry['content']['itemContent']['user_results']['result']) for entry in entries]
                
            
    def download(self):
        if int(self.rest_id) < 0 and int(self.rest_id) != -2:
            print('本地列表: {}, 不允许调用 "download"'.format(self.name))
            return
            
        from src.utils.exception import TWRequestError, TwUserError
        
        members = self.get_members()
        count = 0
        
        def progress_update(f: concurrent.futures.Future): # future callback
            nonlocal count
            count = count + 1
            os.system("title {} {}/{}".format(self.name, count, self.member_count))
            
        futures = [] 
        with concurrent.futures.ThreadPoolExecutor() as exc: 
            for member in members:
                future = exc.submit(TwitterUser.download, member, self)
                future.add_done_callback(progress_update)
                futures.append(future)
        
        from src.features import follow_user
        for f in concurrent.futures.as_completed(futures):
            exp = f.exception()
            try:
                if exp:
                    raise exp
            except TwUserError as err:
                logger.warning(err.fmt_msg)
                if err.reason == 'UserUnavailable':
                    if follow_user(rest_id=err.user.rest_id):
                        logger.info('Followed %s', err.user.title)
            except TWRequestError as err:
                logger.warning(err)