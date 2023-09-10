import requests
import core
from api import Settings
from urllib3.util import Retry
from requests.adapters import HTTPAdapter
from logger import logger
from utility import raise_if_error
from exception import TWRequestError

ses = requests.session()
retries = Retry(
    backoff_factor=0.1,
    status_forcelist=[502, 503, 504],
    status=10,
    connect=10
)
ses.mount('https://', HTTPAdapter(max_retries=retries))

def switch_account():
    if bool(len(core.accounts)):
        header = core.accounts.popleft()
        cookie = dict([i.split('=', 1) for i in header['cookie'].split('; ')])
        header['X-Csrf-Token'] = cookie['ct0']
        header['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36'
        ses.headers.update(header)
  
        try:
            res = ses.get(Settings.api)
            raise_if_error(res)
        except TWRequestError as er:
            logger.error(er)
            return False
        logger.info(f"Current account has been switched to [{res.json()['screen_name']}]")
    else:
        raise RuntimeError('All of accounts have reached the limit for seeing posts today.')
    return True