from twitter_user import TwitterUser
from twitter_list import TwitterList
import core
import json
import saving
from logger import logger


def single_user_download(screen_name: list | str):
    path = core.path + '\\other'
    with open(path + '\\.users.json', encoding='utf-8') as f:
        users = json.load(f)

    try:
        if type(screen_name) == str:
            temp = screen_name
            screen_name = [temp]
            del temp

        for i in screen_name:
            TwitterUser(i, users, 'other').download_all()
    finally:
        with open(path + '\\.users.json', 'w', encoding='utf-8') as f:
            json.dump(users, f, ensure_ascii=False, indent=4, separators=(',', ': '))


def list_download(rest_id: list | str | int):
    if type(rest_id) != list:
        temp = rest_id
        rest_id = [temp]
        del temp

    for r in rest_id:
        TwitterList(r).download_all()

if __name__ == "__main__":
    saving.init()
    try:
        name = ['taozi994', 'yueyue31415926']
        single_user_download(name)

        # rid = 1560060739372535809
        # list_download(rid)
    except BaseException as ex:
        logger.error('Unexcepted error: {}'.format(ex))
    finally:
        saving.uninit()
