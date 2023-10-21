import requests
from urllib3.util import Retry
from requests.adapters import HTTPAdapter
from settings import config

from twitter.api import Settings

session = requests.session()
retries = Retry(
    backoff_factor=0.1,
    status_forcelist=[502, 503, 504],
    status=10,
    connect=10
)
session.mount('https://', HTTPAdapter(max_retries=retries))

cookie = dict([i.split('=', 1) for i in config.cookie.split('; ')])
header = {
    'X-Csrf-Token': cookie['ct0'],
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
    'Authorization': config.authorization
}

session.headers.update(header)
session.cookies.update(cookie)


r = session.get(Settings.api)
info = r.json()
import rich
rich.print('已登录：', info['screen_name'])