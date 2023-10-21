from twitter.api import *
from src.session import session
from utils.utility import raise_if_error

def get_mylists()-> list[dict]:
    res = session.get(ListManagementPageTimeline.api, json=ListManagementPageTimeline.params)
    raise_if_error(res)

    items = res.json()['data']['viewer']['list_management_timeline']['timeline']['instructions'][3]['entries'][2]['content']['items']
    results = []
    for item in items:
        result = {}
        list = item['item']['itemContent']['list']
        result['name'] = list['name']
        result['rest_id'] = list['id_str']
        result['member_count'] = list['member_count']
        results.append(result)
    return results


