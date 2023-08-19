from api import UserMedia
from api import UserByScreenName
from session import ses 
from session import switch_account
import json
import pattern
import core
import os
import pattern
import utility
import userlist
import requests
import time
from datetime import datetime

def handle_title(full_text: str) -> str:
    full_text = pattern.url.sub('', full_text)
    full_text = pattern.at.sub('', full_text)
    full_text = pattern.tag.sub('', full_text)
    full_text = pattern.enter.sub(' ', full_text)
    full_text = pattern.nonsupport.sub('', full_text)
    return full_text.strip()

# TODO
def get_bitrate(variant) -> int:
    bit = variant.get('bitrate')
    if bit == None:
        return 0
    return bit

class TwitterUser:
    users = {}
    def __init__(self, screen_name: str, relative_path = '', name = None, rest_id = None) -> None:       
        # Get 'name' and 'rest_id'
        if (name or rest_id) == None:
            UserByScreenName.params['variables']['screen_name'] = screen_name
            params = {k: json.dumps(v) for k, v in UserByScreenName.params.items()}
            res = ses.get(UserByScreenName.api, params=params)
            try:
                res.raise_for_status()
            except requests.exceptions.HTTPError as err:
                print(repr(err))

            name = res.json()['data']['user']['result']['legacy']['name']
            rest_id = res.json()['data']['user']['result']['rest_id']
        
        self.screen_name = screen_name
        self.name = name
        self.rest_id = rest_id
        self.title = f'{pattern.nonsupport.sub("", self.name)}({self.screen_name})'
        self.path = core.path + f'\\{relative_path}\\{self.title}'        
        
        if not self.is_exist():
            self.create_profile()
        else:
            self.update_info()

        self.latest = TwitterUser.users[self.rest_id]['latest']
        pass  

    def is_exist(self) -> bool:
        return self.rest_id in TwitterUser.users
    
    def update_info(self):
        # have changed name
        if self.title != TwitterUser.users[self.rest_id]['names'][0]:
            i = self.path.rfind('\\')
            os.rename(self.path[:i] + f'\\{TwitterUser.users[self.rest_id]["names"][0]}', self.path)        
            TwitterUser.users[self.rest_id]['names'].insert(0, self.title)
        pass
    
    def create_profile(self):
        TwitterUser.users[self.rest_id] = {'names': [self.title], 'latest': ''}

        if not os.path.exists(self.path):
            os.mkdir(self.path)

    def get_timeline(self, count=50, cursor="") -> list:
        """Return tweetlist of the user.
        """
        UserMedia.params['variables']['userId'] = self.rest_id
        UserMedia.params['variables']['count'] = count
        UserMedia.params['variables']['cursor'] = cursor
        params = {k: json.dumps(v) for k, v in UserMedia.params.items()}
        
        res = ses.get(UserMedia.api, params=params)     
        if res.status_code == requests.codes.TOO_MANY:
            if int(res.headers['x-rate-limit-remaining']) > 0:
                switch_account()           
            # 请求次数达到上限，挂起程序等待重新请求
            else:                            
                dt = datetime.datetime.fromtimestamp(int(res.headers['x-rate-limit-reset']))            
                print('Because reach rate-limit, wait until {}'.format(dt.strftime("%Y-%m-%d %H:%M:%S")))
                second = dt.timestamp() - datetime.datetime.now().timestamp()
                time.sleep(second)
            res = ses.get(UserMedia.api, params=params)
        
        if res.json()['data']['user']['result']['__typename'] == 'UserUnavailable':
            return list()
        return res.json()['data']['user']['result']['timeline_v2']['timeline']['instructions'][0]['entries']
    
    def get_entries(self) -> list:
        items = []
        last = self.latest
        if last != '':
            latest_timestamp = datetime.strptime(last, utility.timeformat).timestamp()
        
        entries = self.get_timeline()       
        while len(entries) > 2:
            # 遍历推文
            for entry in entries:
                content = entry['content']

                if content['entryType'] == 'TimelineTimelineItem':
                    result = dict(content['itemContent']['tweet_results']).get('result')
                    if result == None:
                        continue
                    if result['__typename'] == 'TweetWithVisibilityResults':
                        legacy = result['tweet']['legacy']
                    else:
                        legacy = result['legacy']

                    if last != '':                  
                        if (datetime.strptime(legacy['created_at'], utility.timeformat).timestamp() <= latest_timestamp):
                            entries.clear()
                            break
                    
                    if len(items) == 0:
                        self.latest = legacy['created_at']     

                    title = handle_title(legacy['full_text']) 
                    medias = legacy.get('extended_entities')
                    if medias == None:
                        # TODO NO MEDIA
                        continue
                    else:
                        medias = medias['media']

                    item = {}
                    urls = []
                    vurls = []
                    for m in medias:
                        match m['type']:
                            case 'photo':
                                urls.append(m['media_url_https'])                                                                      
                            case 'video':
                                variants = list(m['video_info']['variants'])
                                variants.sort(key=get_bitrate)      
                                vurl = [u['url'] for u in variants]
                                vurls.append(vurl)                      
                            case _:
                                pass  
                    item['title'] = title
                    item['urls'] = urls
                    item['vurls'] = vurls
                    items.append(item)                   
                # 翻页   
                elif content['entryType'] == 'TimelineTimelineCursor':
                    if content['cursorType'] == 'Bottom':   
                        entries = self.get_timeline(cursor=content['value'])  
        return items

    def download_all(self):    
        items = self.get_entries()
        if len(items):
            print(f"{self.name}({self.screen_name}) {len(items)}")
        for item in items:
            for p in item['urls']:
                utility.download(p, False, path=self.path, name=item['title'])
            for v in item['vurls']:
                while len(v):
                    try:
                        utility.download(v.pop(), False, path=self.path, name=item['title']) 
                    except requests.HTTPError as err:
                        if err.response.status_code == requests.codes.NOT_FOUND:                                    
                            continue
                    else:
                        break
        TwitterUser.users[self.rest_id]['latest'] = self.latest