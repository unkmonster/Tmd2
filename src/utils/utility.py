import os
import requests
import winshell
from pathlib import Path


timeformat = '%a %b %d %H:%M:%S %z %Y'
# def download(url: str, overwrite: bool, *, path = '.', name = None, change_suffix = False) -> bool:
#     res = requests.get(url, stream=True)

#     origin = get_filename_from_path(url)
#     if name == None:
#         name = origin
#     elif change_suffix == False:
#         name = name + '.' + origin.split('.')[-1]
    
#     if not overwrite:
#         # 处理重复文件  
#         count = 1
#         i = name.rfind('.')
#         if i != -1:
#             pre, suf = name[:i], name[i+1:]
#         else:
#             pre, suf = name, '\b'

#         while os.path.exists(path + f'\\{name}'):
#             name = pre + '_' + str(count) + '.' + suf
#             count = count + 1
    
#     #print(name) 
#     with open(path + f'\\{name}', 'wb') as f:
#         for chunk in res.iter_content(chunk_size=1024):
#             f.write(chunk)


def create_shortcut(target: Path, saveto: Path):
    shortcut = saveto.joinpath(target.stem).with_suffix('.lnk')
    winshell.CreateShortcut(Path=str(shortcut), Target=str(target))  


def raise_if_error(response):
    from src.utils.exception import TWRequestError
    try:
        errors = response.json().get('errors')
    except:
        if response.status_code != 200:
            raise TWRequestError(response.text)
    if errors != None:
        raise TWRequestError(*errors)


def handle_title(full_text: str) -> str:
    from src.utils import pattern
    full_text = pattern.url.sub('', full_text)
    full_text = pattern.at.sub('', full_text)
    full_text = pattern.tag.sub('', full_text)
    full_text = pattern.enter.sub(' ', full_text)
    full_text = pattern.nonsupport.sub('', full_text)
    return full_text.strip()


def get_entries(timeline_api, handler):
    """可调用对象接受一个词典，返回提取出的 entries 列表"""
    from src.session import session

    cursor = ''
    entries = []

    while True:
        timeline_api.params['variables']['cursor'] = cursor
        res = session.get(
            url=timeline_api.api,
            json=timeline_api.params    
        )
        raise_if_error(res)
        ets = handler(res.json())
        
        for i in range(len(ets) - 1, -1, -1):
            if ets[i]['content']['__typename'] == 'TimelineTimelineCursor':
                if 'Bottom' == ets[i]['content']['cursorType']:
                    cursor = ets[i]['content']['value']
                del ets[i]
            else:
                break

        if not len(ets):
            break
        entries.extend(ets)
    return entries

from src.twitter.user import TwitterUser
def get_following(rest_id: str) -> list[TwitterUser]:
    from src.twitter.api import Following
    Following.params['variables']['userId'] = rest_id
    
    entries = get_entries(
        Following, 
        lambda j: j['data']['user']['result']['timeline']['timeline']['instructions'][-1]['entries']
    )
    return [TwitterUser(result=entry['content']['itemContent']['user_results']['result']) for entry in entries]
