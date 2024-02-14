import json
import os
from api import ListByRestId, ListMembers, Create

from src.utils.utility import raise_if_error, get_following, get_entries
from src.session import session
from src.settings import *

import concurrent.futures  

from src.twitter.user import TwitterUser

class TwitterList:
    """负数 ID 为非 Twitter 列表"""

    def __init__(self, *, rest_id=None, list:dict = None, name = None) -> None:
        if not rest_id and not list:
            raise TypeError('至少需要 rest_id 或 list')
        
        if rest_id:
            self._rest_id = str(rest_id)
        
        while name == None:
            # 非 Twitter 列表
            if rest_id and int(rest_id) < 0:
                listmap = json.loads(project.listj_dir.read_text('utf-8'))
                self._name = listmap[self._rest_id]['names'][-1]
                self._path = config.store_dir.joinpath(self._name)
                return
            if not list:
                ListByRestId.params['variables']['listId'] = self._rest_id
                params = {k: json.dumps(v) for k, v in ListByRestId.params.items()}              
                res = session.get(ListByRestId.api, params=params)
                raise_if_error(res)
                list = res.json()['data']['list']
                try:
                    name = list['name']
                except KeyError:
                    rest_id = -1    # 作为本地列表处理
             
        if not rest_id:
            self._rest_id = list['id_str']
        self._name = name
        self._path = config.store_dir.joinpath(self._name)

    
    def _create(self):
        if not self._is_exist():
            self._create_profile()
        else:
            self._update()


    def _is_exist(self) -> bool:
        return self._rest_id in json.loads(project.listj_dir.read_text('utf-8'))


    def _update(self):
        listmap = json.loads(project.listj_dir.read_text('utf-8'))
        if self._name != listmap[self._rest_id]['names'][-1]:
            if not config.store_dir.joinpath(listmap[self._rest_id]['names'][-1]).exists():
                config.store_dir.joinpath(listmap[self._rest_id]['names'][-1]).mkdir()
            config.store_dir.joinpath(listmap[self._rest_id]['names'][-1]).rename(self._path)
            listmap[self._rest_id]["names"].append(self._name)
            project.listj_dir.write_text(json.dumps(listmap, ensure_ascii=False, indent=4, separators=(',', ': ')), 'utf-8')


    def _create_profile(self):
        if not self._path.exists():
            self._path.mkdir(parents=True)

        listmap = json.loads(project.listj_dir.read_text('utf-8'))
        listmap[self._rest_id] = {
            'names': [self._name]
        }
        project.listj_dir.write_text(json.dumps(listmap, ensure_ascii=False, indent=4, separators=(',', ': ')), 'utf-8')

    
    def get_members(self):
        ListMembers.params['variables']['listId'] = self._rest_id
        ListMembers.params['variables']['count'] = 200

        entries = get_entries(
            ListMembers, 
            lambda j: j['data']['list']['members_timeline']['timeline']['instructions'][-1]['entries']
        )
        return [TwitterUser(result=entry['content']['itemContent']['user_results']['result']) for entry in entries]     