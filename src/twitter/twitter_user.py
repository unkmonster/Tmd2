import json
import os
import time
from collections import deque
from datetime import datetime, timezone, timedelta

import requests

import core
import pattern
import utility
from api import UserByScreenName, UserMedia
from exception import TWRequestError, TwUserError
from logger import logger
from session import ses
from utility import raise_if_error
from src.utilitycpp import *

def handle_title(full_text: str) -> str:
    full_text = pattern.url.sub('', full_text)
    full_text = pattern.at.sub('', full_text)
    full_text = pattern.tag.sub('', full_text)
    full_text = pattern.enter.sub(' ', full_text)
    full_text = pattern.nonsupport.sub('', full_text)
    return full_text.strip()


class TwitterUser:
    from twitter.twitter_list import TwitterList
    def __init__(self, screen_name: str, belong_to: TwitterList= None, name=None, rest_id=None) -> None:
        """ 账号不存在或账号被暂停,或受保护账号，抛出UserError
        """
        self.external = False

        # Get 'name' and 'rest_id'
        if (name or rest_id) == None:
            UserByScreenName.params['variables']['screen_name'] = screen_name
            res = ses.get(UserByScreenName.api, json=UserByScreenName.params)
            raise_if_error(res)

            if 'user' in res.json()['data']:
                result = res.json()['data']['user']['result']
                if 'UserUnavailable' == result['__typename']:
                    raise TwUserError(self, 'UserUnavailable')
                if 'protected' in result['legacy'] and result['legacy']['protected'] == True:
                    raise TwUserError(self, 'These Tweets are protected')
                name = res.json()['data']['user']['result']['legacy']['name']
                rest_id = res.json()['data']['user']['result']['rest_id']
            else:
                raise TwUserError(screen_name, "Account doesn't exist")

        self.screen_name = screen_name
        self.name = name
        self.rest_id = rest_id
        self.title = f'{pattern.nonsupport.sub("", self.name)}({self.screen_name})'
        self.belong_to = belong_to
        self.path = os.path.join(self.belong_to.path, self.title)
        self.latest = ''

        # TODO
        # 目前的情况是，如果此用户隶属于某个列表，或本地列表。我们才创建为其创建配置。
        # 但没有配置的用户是无法下载的，所以此用户只用于获取信息。
        if self.belong_to != None:
            exist = self.is_exist()
            if exist:
                self.update()
            self.prefix = '{}/{}'.format(self.belong_to.name, self.title)
            if not exist:
                self.create_profile()
       

        if self.external:
            utility.create_shortcut(self.path, self.origin_path)  
        
        self.failures = []
        pass


    # def __del__(self):
    #     if self.external:
    #         path = os.path.join(self.belong_to.path, '.users.json')
    #         with open(path, 'w', encoding='utf-8') as f:
    #             json.dump(self.belong_to.users, f, ensure_ascii=False, indent=4, separators=(',', ': '))
    #     pass


    def is_exist(self) -> bool:
        if self.belong_to.user_exist(self.rest_id):
            return True
        else:
            # 判断此用户是否已存在于本地其他列表
            from twitter.twitter_list import TwitterList
            with open(os.path.join(core.path, '.lists.json'), encoding='utf-8') as f:
                lists = json.load(f)
                del lists[self.belong_to.rest_id]
                for k in lists:
                    if k != '-1':
                        tl = TwitterList(k)
                        if tl.user_exist(self.rest_id):
                            self.external = True
                            self.origin_path = self.belong_to.path
                            self.belong_to = tl
                            self.path = os.path.join(self.belong_to.path, self.title)
                            return True
        return False


    def update(self):
        if self.title != self.belong_to.users[self.rest_id]['names'][0]:
            root = self.path[:self.path.rfind('\\')]    
            os.rename(os.path.join(root, self.belong_to.users[self.rest_id]["names"][0]), self.path)
            self.belong_to.users[self.rest_id]['names'].insert(0, self.title)
            logger.info('Renamed: {} -> {}'.format(self.belong_to.users[self.rest_id]["names"][1], 
                                                  self.belong_to.users[self.rest_id]["names"][0]))
        self.latest = self.belong_to.users[self.rest_id]['latest']
        pass


    def create_profile(self):
        self.belong_to.users[self.rest_id] = {
            'names': [self.title], 
            'latest': ''
        }

        if not os.path.exists(self.path):
            os.mkdir(self.path)
        logger.info('Created {}'.format(self.prefix))


    def get_timeline(self, count=50, cursor="") -> list:
        """返回时间线上的所有推文(list)
        """
        UserMedia.params['variables']['userId'] = self.rest_id
        UserMedia.params['variables']['count'] = count
        UserMedia.params['variables']['cursor'] = cursor
        params = {k: json.dumps(v) for k, v in UserMedia.params.items()}

        try:
            res = ses.get(UserMedia.api, params=params)
            raise_if_error(res)
        except TWRequestError as er:
            if res.status_code == requests.codes.TOO_MANY:
                if int(res.headers['x-rate-limit-remaining']) > 0:
                    from manager import Manager
                    if Manager.spare.empty():
                        raise RuntimeError(er.msg())
                    Manager.login()
                else:                
                    limit_time = datetime.datetime.fromtimestamp(int(res.headers['x-rate-limit-reset']))
                    logger.warning(
                        'Reached rate-limit, have been waiting until {}'.format(limit_time.strftime("%Y-%m-%d %H:%M:%S")))

                    time.sleep(limit_time.timestamp() - datetime.datetime.now().timestamp())

                res = ses.get(UserMedia.api, params=params)
                raise_if_error(res)
            else:
                raise
        try:
            if res.json()['data']['user']['result']['__typename'] == 'UserUnavailable':
                raise TwUserError(self, 'User has been protected')
            return res.json()['data']['user']['result']['timeline_v2']['timeline']['instructions'][0]['entries']
        except KeyError:
            raise TwUserError(self, 'UserUnavailable')


    def get_entries(self) -> deque:
        def max_bitrate(variants)->str:
            max = [0, '']
            for v in variants:
                br = int(v.get("bitrate") or 0)
                if br > max[0]:
                    max[0] = br
                    max[1] = v['url']
            return max[1]
        
        
        items = []
        if self.latest != '':
            latest_timestamp = datetime.strptime(self.latest, utility.timeformat).timestamp()

        entries = self.get_timeline()
        while len(entries) > 2:
            # 遍历推文
            for entry in entries:
                content = entry['content']

                if content['entryType'] == 'TimelineTimelineItem':
                    result = content['itemContent']['tweet_results'].get('result')
                    if result == None or result['__typename'] == 'TweetTombstone':
                        continue
                    if result['__typename'] == 'TweetWithVisibilityResults':
                        legacy = result['tweet']['legacy']
                    else:
                        legacy = result['legacy']

                    if self.latest != '':
                        if (datetime.strptime(legacy['created_at'],
                                              utility.timeformat).timestamp() <= latest_timestamp):
                            entries.clear()
                            break

                    title = handle_title(legacy['full_text'])
                    medias = legacy.get('extended_entities')
                    if medias == None:
                        # TODO NO MEDIA
                        continue
                    else:
                        medias = medias['media']

                    urls = []
                    for m in medias:
                        match m['type']:
                            case 'photo':
                                urls.append(m['media_url_https'])
                            case 'video':
                                variants = list(m['video_info']['variants'])
                                urls.append(max_bitrate(variants))
                            case _:
                                pass
                    items.append(Tweet(title, urls, legacy['created_at']))
                    pass
                # 翻页   
                elif content['entryType'] == 'TimelineTimelineCursor':
                    if content['cursorType'] == 'Bottom':
                        entries = self.get_timeline(cursor=content['value'])
        return items


    def download_tweets(self, entries, overwrite: bool) -> tuple:
        created_at = self.latest
        need_failed_created_at = False
        for i, tweet in enumerate(entries):
            try:
                for p in tweet.pic_url:
                    utility.download(p, overwrite, path=self.path, name=tweet.text)

                for v in tweet.vid_url:
                    while len(v):
                        try:
                            utility.download(v.pop(), overwrite, path=self.path, name=tweet.text)
                        except requests.HTTPError as err:
                            if err.response.status_code == requests.codes.NOT_FOUND:
                                continue
                        else:
                            break
            except requests.RequestException as ex:
                self.failures.append(tweet)
                logger.warning(repr(ex))
                need_failed_created_at = True
                continue
            else:
                print('{} [{}/{}] {}'.format(self.prefix, i + 1, len(entries), tweet.text))
                created_at = tweet.created_at
                need_failed_created_at = False
        return (need_failed_created_at, created_at)


    def retry(self, update_latest: bool):
        entries = self.failures
        self.failures.clear()
        result = self.download_tweets(entries, True)

        if update_latest:
            self.belong_to.users[self.rest_id]['latest'] = result[1]

        if len(self.failures):
            logger.warning("There are tweets with failed downloads by {})", self.title)
        for i, t in enumerate(self.failures):
            logger.warning(t.text)


    def download(self):
        entries = self.get_entries()
        latest = cdownload(entries, self.path)

        #print('calc time = %dms' % int((time.time() - start) * 1000))
        if latest:
            self.belong_to.users[self.rest_id]['latest'] = datetime.strftime(datetime.fromtimestamp(latest, timezone(timedelta(hours=0))), utility.timeformat)