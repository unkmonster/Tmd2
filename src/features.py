from twitter.api import *
from src.session import session
from twitter.user import TwitterUser
from twitter.list import TwitterList

from src.utils.logger import logger
from utils.exception import *
from utils.utility import raise_if_error

def download_user(screen_name: str, save_to = "other") -> bool:
    local = TwitterList(-1, save_to, -1)
    usr = TwitterUser(screen_name, local)
    try:
        usr.download()
    except TwUserError as err:
        logger.warning(err.fmt_msg)
        return False
    return True


def get_own_lists()-> list[dict]:
    res = session.get(ListManagementPageTimeline.api, json=ListManagementPageTimeline.params)
    raise_if_error(res)

    items = res.json()['data']['viewer']['list_management_timeline']['timeline']['instructions'][3]['entries'][2]['content']['items']
    results = []
    for item in items:
        result = {}
        list = item['item']['itemContent']['list']
        result['name'] = list['name']
        result['rest_id'] = list['id_str']
        result['member_count'] = list['member_count']
        results.append(result)
    return results


def follow_user(screen_name = None, rest_id = None) -> bool:
    if screen_name is None and rest_id is None:
        raise ValueError('参数错误，至少需要一个参数')
    if rest_id is None:
        rest_id = TwitterUser(screen_name).rest_id

    Create.params['user_id'] = rest_id
    try:
        res = session.post(Create.api, data=Create.params)
        raise_if_error(res)
    except TWRequestError as err:
        logger.warning(err)
        return False
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