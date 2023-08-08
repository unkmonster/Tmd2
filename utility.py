import os
import requests
import time

def download(url: str, overwrite: bool, *, path = '.', name = None, change_suffix = False) -> bool:
    count = 1
    while True:
        try:
            res = requests.get(url, stream=True)
        except (requests.exceptions.ProxyError, requests.exceptions.SSLError) as err:
            if count > 5:
                raise
            print(repr(err))
            print(f'[{count}] Attempting to retry...')
            time.sleep(10)
            count = count + 1
        else:
            res.raise_for_status()
            break

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
    
    print(name) 
    with open(path + f'\\{name}', 'wb') as f:
        for chunk in res.iter_content(chunk_size=1024):
            f.write(chunk)

def get_filename_from_path(path : str) -> str:
    i = path.find('?')
    if i != -1:
        path = path[:i]
    return path.split('/')[-1]

# TEMP
def timestamp_to_time(timestamp) -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(timestamp)))