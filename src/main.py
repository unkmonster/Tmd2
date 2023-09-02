from user import TwitterUser
from userlist import UserList
import core
import json
import saving
from logger import logger


def single_user_download(screen_name: list | str):
    path = core.path + '\\other'

    # TODO: 不能和列表下载同时使用
    with open(path + '\\.users.json', encoding='utf-8') as f:
        TwitterUser.users = json.load(f)

    try:
        if type(screen_name) == str:
            temp = screen_name
            screen_name = [temp]
            del temp

        for i in screen_name:
            TwitterUser(i, 'other').download_all()
    finally:
        with open(path + '\\.users.json', 'w', encoding='utf-8') as f:
            json.dump(TwitterUser.users, f, ensure_ascii=False, indent=4, separators=(',', ': '))
        TwitterUser.users.clear()


def list_download(rest_id: list | str | int):
    if type(rest_id) != list:
        temp = rest_id
        rest_id = [temp]
        del temp

    for r in rest_id:
        UserList(r).download_all()

if __name__ == "__main__":
    saving.init()
    try:
        # name = 'IDlucky89757'
        # single_user_download(name)

        rid = 1560060739372535809
        list_download(rid)
    except BaseException as ex:
        logger.error('Unexcepted error: {}'.format(ex))
    finally:
        saving.uninit()
