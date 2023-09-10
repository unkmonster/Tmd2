from api import ListManagementPageTimeline
from session import ses
from session import switch_account
from logger import logger
from twitter_list import TwitterList
from twitter_user import TwitterUser
import core
import json
import os
from api import ListAddMember
from api import ListRemoveMember
import shutil
from requests import HTTPError
from utility import raise_if_error
from exception import TWRequestError

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
        if not switch_account():
            logger.critical('Account is invalid')
    
    def __del__(self):
        with open(core.path + '\\.lists.json', 'w', encoding='utf-8') as f:
            json.dump(TwitterList.userlists, f, ensure_ascii=False, indent=4, separators=(',', ': '))

    def get_lists(self) -> list:
        try:
            r = ses.get(ListManagementPageTimeline.api, json=ListManagementPageTimeline.params)
            r.raise_for_status()
        except:
            logger.error(r.text)
        
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
                try:
                    TwitterUser(i, users, 'other').download_all()
                except HTTPError:
                    continue
        finally:
            with open(path + '\\.users.json', 'w', encoding='utf-8') as f:
                json.dump(users, f, ensure_ascii=False, indent=4, separators=(',', ': '))


    def download_all_list(self):
        for list in self.get_lists():
            TwitterList(list['id_str'], list['name'], list['member_count']).download_all()

    def download_following(self):
        # TODO
        pass

    def move_user(self, screen_name: str, src_id: str, dst_id: str):
        try:
            user = TwitterUser(screen_name)
        except RuntimeError as ex:
            msg = ex.args[0] + ': ' + ex.args[1]    
            logger.error(msg)
            return
        except HTTPError:
            return
       
        ListAddMember.params['variables']['userId'] = ListRemoveMember.params['variables']['userId'] = user.rest_id    
        ListAddMember.params['variables']['listId'] = dst_id
        ListRemoveMember.params['variables']['listId'] = src_id
        
        try:
            r = ses.post(ListRemoveMember.api, json=ListRemoveMember.params)
            r.raise_for_status()
            r = ses.post(ListAddMember.api, json=ListAddMember.params)
            r.raise_for_status()
        except:
            logger.error(r.content)
            return

        # json
        src = TwitterList(src_id)
        dst = TwitterList(dst_id)
        dst.users[user.rest_id] = src.users[user.rest_id]
        del src.users[user.rest_id]

        # file
        logger.debug(shutil.move(os.path.join(src.path, user.title), dst.path))

    def follow_user(self, screen_name: str, user_id = 0):
        from api import Create
        import utility
        from exception import TWRequestError

        if user_id == 0:
            user_id = int(TwitterUser(screen_name).rest_id)
        Create.params['user_id'] = user_id
        
        res = ses.post(Create.api, data=Create.params)
        utility.raise_if_error(res)
 
    def user_to_list(self, user_id: str, list_id: str):
        ListAddMember.params['variables']['listId'] = list_id
        ListAddMember.params['variables']['userId'] = user_id
        res = ses.post(ListAddMember.api, json=ListAddMember.params)
        raise_if_error(res)