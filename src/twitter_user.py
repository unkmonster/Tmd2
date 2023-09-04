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
import requests
import time
from datetime import datetime
from logger import logger
from collections import deque

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
    def __init__(self, screen_name: str, belong_to: dict = None,relative_path = '', name = None, rest_id = None) -> None:       
        self.external = False

        # Get 'name' and 'rest_id'
        if (name or rest_id) == None:
            UserByScreenName.params['variables']['screen_name'] = screen_name           
            try:
                res = ses.get(UserByScreenName.api, json=UserByScreenName.params)
                res.raise_for_status()
            except:
                logger.error(res)
                raise

            if 'user' in res.json()['data']:
                result = res.json()['data']['user']['result']
                if 'UserUnavailable' == result['__typename']:
                    raise RuntimeError(screen_name, 'UserUnavailable')
                name = res.json()['data']['user']['result']['legacy']['name']
                rest_id = res.json()['data']['user']['result']['rest_id']
            else:
                raise RuntimeError(screen_name, "Account doesn't exist")
        
        self.screen_name = screen_name
        self.name = name
        self.rest_id = rest_id
        self.title = f'{pattern.nonsupport.sub("", self.name)}({self.screen_name})'
        self.path = core.path + f'\\{relative_path}\\{self.title}'       
        self.belong_to = belong_to 
        self.latest = ''

        # TODO
        if self.belong_to != None:
            if not self.is_exist():
                self.create_profile()
            else:
                self.update_info()
            
        if self.external:
            utility.create_shortcut(self.path, core.path + f'\\{relative_path}')

        self.failure = []
        pass  
    
    def __del__(self):
        if self.external:
            path = self.path[:self.path.rfind('\\')] + '\\.users.json'
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(self.belong_to, f, ensure_ascii=False, indent=4, separators=(',', ': '))
        pass

    def is_exist(self) -> bool:
        if self.rest_id in self.belong_to:
            return True
        else:    
            with open(os.path.join(core.path, '.lists.json'), encoding='utf-8') as f:
                for v in json.load(f).values():
                    with open(core.path + '\\' + v['names'][0] + '\\.users.json', encoding='utf-8') as f:
                        users = json.load(f)
                        if self.rest_id in users:
                            self.external = True
                            self.path = core.path + f'\\{v["names"][0]}\\{self.title}'
                            self.belong_to = users
                            return True
        return False
    
    def update_info(self):
        # has changed name
        if self.title != self.belong_to[self.rest_id]['names'][0]:
            i = self.path.rfind('\\')
            os.rename(self.path[:i] + f'\\{self.belong_to[self.rest_id]["names"][0]}', self.path)        
            self.belong_to[self.rest_id]['names'].insert(0, self.title)

        self.latest = self.belong_to[self.rest_id]['latest']
        pass
    
    def create_profile(self):
        self.belong_to[self.rest_id] = {'names': [self.title], 'latest': ''}

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
                logger.warning('Because reach rate-limit, wait until {}'.format(dt.strftime("%Y-%m-%d %H:%M:%S")))
                second = dt.timestamp() - datetime.datetime.now().timestamp()
                time.sleep(second)
            res = ses.get(UserMedia.api, params=params)
        
        if res.json()['data']['user']['result']['__typename'] == 'UserUnavailable':
            return list()
        return res.json()['data']['user']['result']['timeline_v2']['timeline']['instructions'][0]['entries']
    
    def get_entries(self) -> deque:
        items = deque()
        if self.latest != '':
            latest_timestamp = datetime.strptime(self.latest, utility.timeformat).timestamp()
        
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

                    if self.latest != '':                  
                        if (datetime.strptime(legacy['created_at'], utility.timeformat).timestamp() <= latest_timestamp):
                            entries.clear()
                            break

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
                    item['created_at'] = legacy['created_at']
                    items.appendleft(item)
                # 翻页   
                elif content['entryType'] == 'TimelineTimelineCursor':
                    if content['cursorType'] == 'Bottom':   
                        entries = self.get_timeline(cursor=content['value'])  
        return items

    def download_tweets(self, entries, overwrite: bool) -> str:
        created_at = self.latest

        for i, tweet in enumerate(entries):
            try:
                for p in tweet['urls']:
                    utility.download(p, overwrite, path=self.path, name=tweet['title'])

                for v in tweet['vurls']:
                    while len(v):
                        try:
                            utility.download(v.pop(), overwrite, path=self.path, name=tweet['title']) 
                        except requests.HTTPError as err:
                            if err.response.status_code == requests.codes.NOT_FOUND:                                    
                                continue
                        else:
                            break
            except requests.RequestException as ex:
                self.failure.append(tweet)
                logger.error('Failed to download: {}'.format(repr(ex)))
                continue
            else:
                logger.info("{}(@{}) {}/{} > {}".format(self.name, self.screen_name, i+1, len(entries), tweet['title']))
                created_at = tweet['created_at']
        return created_at

    def retry(self):
        entries = self.failure
        self.failure.clear()
        latest = self.download_tweets(entries, True)

        # 判断失败列表的最新推文发布日期是否晚于已成功的推文
        if latest != '' and self.belong_to[self.rest_id]['latest'] != '':
            ts_saved = datetime.strptime(self.belong_to[self.rest_id]['latest'], utility.timeformat).timestamp()
            ts_latest = datetime.strptime(latest, utility.timeformat).timestamp()
            if ts_latest  > ts_saved:
                self.belong_to[self.rest_id]['latest'] = latest
        
        for i, t in enumerate(self.failure):
            logger.error(f'{self.name}(@{self.screen_name}) > Failed to download[{i+1}]: {t["title"]}')
        
    def download_all(self):    
        latest = self.download_tweets(self.get_entries(), False)
        self.belong_to[self.rest_id]['latest'] = latest

        l = len(self.failure)
        if l > 0:
            logger.debug(f'{self.name}(@{self.screen_name}) > failures: {l}')
            self.retry()
