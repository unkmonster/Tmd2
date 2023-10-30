import requests
from urllib3.util import Retry
from requests.adapters import HTTPAdapter
from src.settings import *

from twitter.api import Settings
from dataclasses import dataclass

@dataclass
class Account:
    session: requests.Session
    screen_name: str

    @classmethod
    def login(cls, cookie):
        session = requests.session()
        retries = Retry(
            backoff_factor=0.1,
            status_forcelist=[502, 503, 504],
            status=10,
            connect=10
        )
        session.mount('https://', HTTPAdapter(max_retries=retries))

        cookie = dict([i.split('=', 1) for i in cookie.split('; ')])
        header = {
            'X-Csrf-Token': cookie['ct0'],
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
            'Authorization': config.authorization
        }
        session.headers.update(header)
        session.cookies.update(cookie)

        r = session.get(Settings.api, timeout=10)
        return cls(session, r.json()['screen_name'])


def add_cookie(cookie: str) -> bool:
    if cookie not in config.cookie:
        config.cookie.append(cookie)
        with project.cookie_dir.open('w') as f:
            for ck in config.cookie:
                f.write(ck + '\n')
        return True
    print('cookie 已存在')
    return False


account = Account.login(config.cookie[0])
session = account.session
print('已登录:', account.screen_name)
