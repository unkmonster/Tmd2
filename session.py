import requests
import core
from api import Settings

ses = requests.session()

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