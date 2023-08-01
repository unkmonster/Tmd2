import requests
import core

header = {
    'cookie': core.cookie,
    'Authorization': core.Authorization,
    'X-Csrf-Token': core.csrf
}

ses = requests.session()
ses.headers.update(header)