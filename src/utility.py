import os
import requests
import winshell

def download(url: str, overwrite: bool, *, path = '.', name = None, change_suffix = False) -> bool:
    res = requests.get(url, stream=True)

    origin = get_filename_from_path(url)
    if name == None:
        name = origin
    elif change_suffix == False:
        name = name + '.' + origin.split('.')[-1]
    
    if not overwrite:
        # 处理重复文件  
        count = 1
        i = name.rfind('.')
        if i != -1:
            pre, suf = name[:i], name[i+1:]
        else:
            pre, suf = name, '\b'

        while os.path.exists(path + f'\\{name}'):
            name = pre + '_' + str(count) + '.' + suf
            count = count + 1
    
    #print(name) 
    with open(path + f'\\{name}', 'wb') as f:
        for chunk in res.iter_content(chunk_size=1024):
            f.write(chunk)

def get_filename_from_path(path : str) -> str:
    i = path.find('?')
    if i != -1:
        path = path[:i]
    return path.split('/')[-1]

def create_shortcut(target: str, saveto):
    name = target[target.rfind('\\') + 1:]
    
    # remove suffix
    index = name.find('.')
    if index != -1:
        name = name[index+1:]

    shortcut = os.path.join(saveto, name + '.lnk')
    winshell.CreateShortcut(Path=shortcut, Target=target)  

def raise_if_error(response):
    from exception import TWRequestError
    errors = response.json().get('errors')
    if errors != None:
        raise TWRequestError(*errors)
    
timeformat = '%a %b %d %H:%M:%S %z %Y'