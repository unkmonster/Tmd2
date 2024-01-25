from src.twitter.api import *
from src.session import session
from src.twitter.user import TwitterUser
from src.twitter.list import TwitterList

from src.utils.logger import logger
from src.utils.exception import *
from src.utils.utility import *


def download_user(screen_name: str, save_to = ".OTHER", listid = -1):
    local = TwitterList(rest_id=listid, name=save_to)
    usr = TwitterUser(screen_name=screen_name)
    usr.fetch(local)


def get_own_lists()-> list[TwitterList]:
    entries = get_entries(
        ListManagementPageTimeline, 
        lambda j: j['data']['viewer']['list_management_timeline']['timeline']['instructions'][-1]['entries']
    )

    for entry in entries:
        if entry['entryId'] == 'owned-subscribed-list-module-0':
            items = entry['content']['items']
            return [TwitterList(list=i['item']['itemContent']['list']) for i in items]


def follow_user(rest_id) -> bool:
    Create.params['user_id'] = rest_id
    res = session.post(Create.api, data=Create.params)
    raise_if_error(res)
    return True
 
    
def user_to_list(user_id: str, list_id: str) -> bool:
        ListAddMember.params['variables']['listId'] = list_id
        ListAddMember.params['variables']['userId'] = user_id
        try:
            res = session.post(ListAddMember.api, json=ListAddMember.params)
            raise_if_error(res)
        except TWRequestError as err:
            logger.warning(err)
            return False
        return True


def download_following(usr: TwitterUser, exclude: list[TwitterUser] = []):
    tl = TwitterList(rest_id= '-' + usr._rest_id, name= 'Following of ' + usr._screen_name)
    download(tl, usr.get_following(), exclude)


def download(owner: TwitterList, members: list[TwitterUser], exclude: list[TwitterUser] = []):
    owner._create()
    index = 0
    members = set(members).difference(exclude)
    
    for member in members:
        if exclude and member in exclude:
            continue
        index = index + 1
        os.system("title {}/{} {}".format(index, len(members), member._name))
        member.fetch(owner)


def destory_user(rest_id: str) -> str:
    destory = Destory()
    r = session.post(destory.api, data={'user_id': rest_id})
    raise_if_error(r)
    return r.json()['screen_name']