from api import ListManagementPageTimeline
from api import Settings
from session import ses
from logger import logger
from twitter.twitter_list import TwitterList
from twitter.twitter_user import TwitterUser
import core
import json
import os
from api import ListAddMember
from api import ListRemoveMember
import shutil
from requests import HTTPError
from utility import raise_if_error
from exception import *
from queue import Queue

class Manager:
    authorization: str
    screen_name: str
    spare: Queue

    def init(authorization: str) -> None:
        if not os.path.exists(core.path):
            os.mkdir(core.path)
        
        if not os.path.exists(core.path + '\\.lists.json'):
            with open(core.path + '\\.lists.json', 'w', encoding='utf-8') as f:
                json.dump(dict(), f)
                pass
        
        # TEMP
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
        
        Manager.authorization = authorization
        Manager.screen_name = None
        Manager.spare = Queue(-1)

    # TEMP
    def uninit():
        with open(core.path + '\\.lists.json', 'w', encoding='utf-8') as f:
            json.dump(TwitterList.userlists, f, ensure_ascii=False, indent=4, separators=(',', ': '))


    def login(cookie=None):
        msg = 'Current account has been switched to [{}]'
        if cookie == None:
            cookie = Manager.spare.get()
            msg = msg + '(from spare)'
        
        cookie = dict([i.split('=', 1) for i in cookie.split('; ')])

        header = {
            'X-Csrf-Token': cookie['ct0'],
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
            'Authorization': Manager.authorization
        }
        ses.cookies.update(cookie)
        ses.headers.update(header)

        res = ses.get(Settings.api)
        raise_if_error(res)
        Manager.screen_name = res.json()['screen_name']
        logger.debug(msg.format(Manager.screen_name))
        os.system('title ' + Manager.screen_name)


    def add_spare(cookie: str | list):
        if type(cookie) == str:
            Manager.spare.put(cookie)
        else:
            for c in cookie:
                Manager.spare.put(c)


    def get_lists() -> list:
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
    

    def download_list(rest_id: str | int):
        TwitterList(str(rest_id)).download_all()


    def download_user(screen_name: str):
        local = TwitterList(-1, 'other', 1)
        TwitterUser(screen_name, local).download()

        # path = core.path + '\\other'
        # with open(path + '\\.users.json', encoding='utf-8') as f:
        #     users = json.load(f)
        
        # try:
        #     if type(screen_name) == str:
        #         temp = screen_name
        #         screen_name = [temp]
        #         del temp

        #     for i in screen_name:
        #         try:
        #             TwitterUser(i, users, 'other').download()
        #         except TwUserError as err:
        #             logger.warning(err.fmt_msg())
        #             continue
        # finally:
        #     with open(path + '\\.users.json', 'w', encoding='utf-8') as f:
        #         json.dump(users, f, ensure_ascii=False, indent=4, separators=(',', ': '))


    def download_following():
        # TODO
        pass


    def move_user(screen_name: str, src_id: str, dst_id: str):
        try:
            user = TwitterUser(screen_name)
        except TwUserError as ex:
            logger.warning(ex.fmt_msg())
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


    def follow_user(screen_name: str | None, user_id = 0):
        from api import Create
        import utility
        from exception import TWRequestError

        if user_id == 0:
            user_id = int(TwitterUser(screen_name).rest_id)
        Create.params['user_id'] = user_id
        try:
            res = ses.post(Create.api, data=Create.params)
            utility.raise_if_error(res)
        except TWRequestError as err:
            logger.warning(err.msg())
            return False
        return True
 
 
    def user_to_list(user_id: str, list_id: str):
        ListAddMember.params['variables']['listId'] = list_id
        ListAddMember.params['variables']['userId'] = user_id
        res = ses.post(ListAddMember.api, json=ListAddMember.params)
        raise_if_error(res)