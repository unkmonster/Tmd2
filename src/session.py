import requests
from urllib3.util import Retry
from requests.adapters import HTTPAdapter
from src.settings import config, project

from twitter.api import Settings

session = requests.session()
retries = Retry(
    backoff_factor=0.1,
    status_forcelist=[502, 503, 504],
    status=10,
    connect=10
)
session.mount('https://', HTTPAdapter(max_retries=retries))
info = {}

def login(cookie = config.cookie[0]):
    global session
    global info
    cookie = dict([i.split('=', 1) for i in cookie.split('; ')])
    header = {
        'X-Csrf-Token': cookie['ct0'],
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
        'Authorization': config.authorization
    }
    session.headers.update(header)
    session.cookies.update(cookie)

    if 'screen_name' in info:
        print('已退出:', info['screen_name'])
    r = session.get(Settings.api, timeout=10)
    info = r.json()
    print('已登录:', info['screen_name'])


def add_cookie(cookie: str) -> bool:
    if cookie not in config.cookie:
        config.cookie.append(cookie)
        with project.cookie_dir.open('w') as f:
            for ck in config.cookie:
                f.write(ck + '\n')
        return True
    print('cookie 已存在')
    return False


login()