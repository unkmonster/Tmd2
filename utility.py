import os
import session

def download(url: str, overwrite: bool, *, path = '.', name = None, change_suffix = False):
    res = session.ses.get(url, stream=True)
    res.raise_for_status()

    origin = get_filename_from_path(url)
    if name == None:
        name = origin
    elif change_suffix == False:
        name = name + '.' + origin.split('.')[-1]
    
    if not overwrite:
        # 处理重复文件  
        count = 1
        i = name.rfind('.')
        pre, suf = name[:i], name[i:]
        while os.path.exists(path + f'\\{name}'):
            name = pre + '_' + str(count) + '.' + suf
            count = count + 1
        
    with open(path + f'\\{name}', 'wb') as f:
        for chunk in res.iter_content(chunk_size=1024):
            f.write(chunk)

def get_filename_from_path(path : str) -> str:
    i = path.find('?')
    if i != -1:
        path = path[:i]
    return path.split('/')[-1]


