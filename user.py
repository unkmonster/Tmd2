from api import UserMedia
from api import UserByScreenName
from session import ses 
from session import switch_account
from progress import prog
import json
import pattern
import core
import os
import pattern
import utility
import tlist
import requests
import time
import datetime

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
    def __init__(self, screen_name: str, relative_path = '', name = None, rest_id = None) -> None:       
        # Get 'name' and 'rest_id'
        if (name or rest_id) == None:
            UserByScreenName.params['variables']['screen_name'] = screen_name
            params = {k: json.dumps(v) for k, v in UserByScreenName.params.items()}
            res = ses.get(UserByScreenName.api, params=params)
            res.raise_for_status()

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
            #os.mkdir(core.path + '\\')
        pass
    
    def update_info(self):
        # 用户已更改用户名
        if self.title != tlist.users[self.rest_id]:
            i = self.path.rfind('\\')
            os.rename(self.path[:i] + f'\\{tlist.users[self.rest_id]}', self.path)

            # Save history of username
            
            # Create
            if os.path.exists(self.path + '\\.history.ini'):
                with open(self.path + '\\.history.ini', 'w', encoding='utf-8'):
                    pass
            # Read
            with open(self.path + '\\.history.ini', 'a', encoding='utf-8') as f:
                f.write(tlist.users[self.rest_id] + '\n')
            
            tlist.users[self.rest_id] = self.title
        pass

    def is_exist(self) -> bool:
        return self.rest_id in tlist.users
    
    def create_profile(self):
        tlist.users[self.rest_id] = self.title

        if not os.path.exists(self.path):
            os.mkdir(self.path)
        
        if not os.path.exists(self.path + f'\\.{self.rest_id}'):          
            with open(self.path + f'\\.{self.rest_id}', 'w'):
                pass

    def get_timeline(self, count=50, cursor="") -> list:
        """Return tweetlist of the user.
        """
        UserMedia.params['variables']['userId'] = self.rest_id
        UserMedia.params['variables']['count'] = count
        UserMedia.params['variables']['cursor'] = cursor
        params = {k: json.dumps(v) for k, v in UserMedia.params.items()}
        
        res = ses.get(UserMedia.api, params=params)
        # print('Before {}, {}/{}'.format(utility.timestamp_to_time(res.headers['x-rate-limit-reset']),
        #                                 res.headers['x-rate-limit-remaining'],
        #                                 res.headers['x-rate-limit-limit']))       
        if res.status_code == requests.codes.TOO_MANY:
            if int(res.headers['x-rate-limit-remaining']) > 0:
                switch_account()           
            # 请求次数达到上限，挂起程序等待重新请求
            else:                            
                dt = datetime.datetime.fromtimestamp(int(res.headers['x-rate-limit-reset']))            
                print('Reaching rate-limit wait until {}'.format(dt.strftime("%Y-%m-%d %H:%M:%S")))

                second = dt.timestamp() - datetime.datetime.now().timestamp()
                time.sleep(second)
            res = ses.get(UserMedia.api, params=params)
        
        if res.json()['data']['user']['result']['__typename'] == 'UserUnavailable':
            return list()
        return res.json()['data']['user']['result']['timeline_v2']['timeline']['instructions'][0]['entries']

    def download_all(self):
        # 读取已下载推文列表
        with open(self.path + f'\\.{self.rest_id}') as f: 
            tweets = [l.strip() for l in f]
                  
        try:     
            entries = self.get_timeline()   
            while len(entries) > 2:
                # 遍历推文
                for entry in entries:
                    content = entry['content']
                    
                    # TODO
                    if content['entryType'] == 'TimelineTimelineItem':
                        if 'result' not in content['itemContent']['tweet_results']:
                            continue
                        if 'legacy' in content['itemContent']['tweet_results']['result']:
                            legacy = content['itemContent']['tweet_results']['result']['legacy']
                        else:
                            legacy = content['itemContent']['tweet_results']['result']['tweet']['legacy'] 
                                                              
                        # 遍历推文媒体并下载
                        title = handle_title(legacy['full_text']) 
                        medias = legacy.get('extended_entities')
                        if medias == None:
                            # TODO NO MEDIA
                            continue
                        else:
                            medias = medias['media']

                        for m in medias:
                            # 利用媒体ID判断此媒体本地是否已存在
                            if m['id_str'] in tweets:
                                continue
                            try:
                                match m['type']:
                                    case 'photo':
                                        utility.download(m['media_url_https'], False, path=self.path, name=title)                                       
                                    case 'video':
                                        variants = list(m['video_info']['variants'])
                                        variants.sort(key=get_bitrate) 
                                        while len(variants):
                                            try:    
                                                url = variants.pop()['url']                            
                                                utility.download(url, False, path=self.path, name=title)
                                            except requests.HTTPError as err:
                                                if err.response.status_code == requests.codes.NOT_FOUND:                                    
                                                    continue
                                            else:
                                                break
                                        else:
                                            raise FileNotFoundError('No available resources')
                                    case _:
                                        pass  
                            except Exception as err:
                                print(repr(err))
                            else:
                                tweets.append(m['id_str'])
                    # 翻页   
                    elif content['entryType'] == 'TimelineTimelineCursor':
                        if content['cursorType'] == 'Bottom':   
                            entries = self.get_timeline(cursor=content['value'])         
        finally:
            with open(self.path + f'\\.{self.rest_id}', 'w') as f: 
                for id in tweets:
                    f.write(id + '\n')