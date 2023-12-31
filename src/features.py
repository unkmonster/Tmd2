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
    usr.download(local)


def get_own_lists()-> list[TwitterList]:
    entries = get_entries(
        ListManagementPageTimeline, 
        lambda j: j['data']['viewer']['list_management_timeline']['timeline']['instructions'][-1]['entries']
    )

    for entry in entries:
        if entry['entryId'] == 'owned-subscribed-list-module-0':
            items = entry['content']['items']
            return [TwitterList(list=i['item']['itemContent']['list']) for i in items]


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


def download_following(usr: TwitterUser):
    tl = TwitterList(rest_id= '-' + usr.rest_id, name= 'Following of ' + usr.screen_name)
    download(tl, get_following(usr.rest_id))


def download(t: TwitterList, members: list[TwitterUser]):
    import concurrent.futures

    t._create()

    count = 0    
    def progress_update(f: concurrent.futures.Future): # future callback
        nonlocal count
        count = count + 1
        os.system("title {}/{} {}".format(count, len(members), t.name))

    futures = [] 
    with concurrent.futures.ThreadPoolExecutor() as exc: 
        for member in members:
            future = exc.submit(TwitterUser.download, member, t)
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
        except TWRequestError as err:
            logger.warning(err)
