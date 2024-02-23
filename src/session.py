import requests
import rich
import os

from urllib3.util import Retry
from requests.adapters import HTTPAdapter
from src.settings import *

from twitter.api import Settings
from dataclasses import dataclass

@dataclass
class Account:
    session: requests.Session
    screen_name: str
    rest_id: str

    @classmethod
    def login(cls, cookie):
        from src.utils.utility import raise_if_error
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
        raise_if_error(r)

        return cls(session, r.json()['screen_name'], cookie['twid'][4:]) # u%3d


while True:
    from src.utils.exception import TWRequestError
    try:
        account = Account.login(config.cookie)
        break
    except TWRequestError as error:
        rich.print(str(error))
        os.remove(project.cookie_dir)
        config = Config.load(project)

session = account.session
rich.print(F"Login successfully: '@{account.screen_name}'")
