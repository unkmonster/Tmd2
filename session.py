import requests
import core

cookie = dict([i.split('=', 1) for i in core.cookie.split('; ')])

header = {
    'cookie': core.cookie,
    'Authorization': core.Authorization,
    'X-Csrf-Token': cookie['ct0']
}

ses = requests.session()
ses.headers.update(header)