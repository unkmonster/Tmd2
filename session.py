import requests
import core
from api import Settings
from urllib3.util import Retry
from requests.adapters import HTTPAdapter

ses = requests.session()
retries = Retry(
    backoff_factor=0.1,
    status_forcelist=[502, 503, 504],
    status=10
)
ses.mount('https://', HTTPAdapter(max_retries=retries))

def switch_account():
    if bool(len(core.accounts)):
        account = core.accounts.popleft()
        cookie = dict([i.split('=', 1) for i in account['cookie'].split('; ')])
        account['X-Csrf-Token'] = cookie['ct0']
        ses.headers.update(account)

        res = ses.get(Settings.api)
        res.raise_for_status()
        print(f"Current account has been switched to [{res.json()['screen_name']}]")
    else:
        raise RuntimeError('All of accounts have reached the limit for seeing posts today.')

switch_account()
pass