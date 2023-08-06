from api import UserMedia
from api import UserByScreenName
from session import ses 
import json
import pattern
import core
import os
import saving
import pattern
import utility

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
        if name or rest_id == None:
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
            #os.mkdir(core.path + '\\')
        pass
    
    def is_exist(self) -> bool:
        # TODO
        if self.rest_id in saving.users:          
            return True
        else:
            return False
    
    def create_profile(self):
        saving.users[self.rest_id] = self.title

        os.mkdir(self.path)
        with open(self.path + f'\\.{self.rest_id}', 'w'):
            pass

    def get_timeline(self, count=50, cursor="") -> list:
        """Return tweetlist of the user.
        """
        UserMedia.params['variables']['userId'] = self.rest_id
        UserMedia.params['variables']['count'] = count
        UserMedia.params['variables']['cursor'] = cursor

        # 格式化词典
        params = {k: json.dumps(v) for k, v in UserMedia.params.items()}
        
        res = ses.get(UserMedia.api, params=params)
        res.raise_for_status()

        return res.json()['data']['user']['result']['timeline_v2']['timeline']['instructions'][0]['entries']

    def download_all(self):
        # 读取已下载推文列表
        with open(self.path + f'\\.{self.rest_id}') as f: 
            tlist = [l.strip() for l in f]
          
        try:
            entries = self.get_timeline() 
            # len <= 2 意味着到达底部
            while len(entries) > 2:
                # 遍历推文
                for entry in entries:
                    content = entry['content']
                    
                    if content['entryType'] == 'TimelineTimelineItem':
                        if 'legacy' in content['itemContent']['tweet_results']['result']:
                            legacy = content['itemContent']['tweet_results']['result']['legacy']
                        else:
                            legacy = content['itemContent']['tweet_results']['result']['tweet']['legacy'] 
                       
                        title = handle_title(legacy['full_text'])
                        print(title)
                       
                        # 遍历推文媒体并下载
                        medias = legacy.get('extended_entities')['media']
                        for m in medias:
                            # 利用媒体ID判断此媒体本地是否已存在
                            if m['id_str'] in tlist:
                                continue
                            try:
                                if m['type'] == 'photo':
                                    utility.download(m['media_url_https'], False, path=self.path, name=title)
                                elif m['type'] == 'video':
                                    variants = list(m['video_info']['variants'])
                                    variants.sort(key=get_bitrate)                                  
                                    utility.download(variants[-1]['url'], False, path=self.path, name=title)
                                else:
                                    # TODO 
                                    print(m['type'])
                            except:
                                raise
                            else:
                                tlist.append(m['id_str'])
                       
                    elif content['entryType'] == 'TimelineTimelineCursor':
                        if content['cursorType'] == 'Bottom':   # 翻页
                            entries = self.get_timeline(cursor=content['value'])
        finally:
            with open(self.path + f'\\.{self.rest_id}', 'w') as f: 
                for id in tlist:
                    f.write(id + '\n')
