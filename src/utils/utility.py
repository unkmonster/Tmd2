import os
import requests
import winshell
from pathlib import Path

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
    from exception import TWRequestError
    errors = response.json().get('errors')
    if errors != None:
        raise TWRequestError(errors)


def handle_title(full_text: str) -> str:
    import pattern
    full_text = pattern.url.sub('', full_text)
    full_text = pattern.at.sub('', full_text)
    full_text = pattern.tag.sub('', full_text)
    full_text = pattern.enter.sub(' ', full_text)
    full_text = pattern.nonsupport.sub('', full_text)
    return full_text.strip()

timeformat = '%a %b %d %H:%M:%S %z %Y'