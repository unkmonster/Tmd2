import json
import os
import time
from collections import deque
from datetime import datetime

import requests

import core
import pattern
import utility
from api import UserByScreenName, UserMedia
from exception import TWRequestError, TwUserError
from logger import logger
from session import ses
from twitter.tweet import Tweet
from utility import raise_if_error


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
    def __init__(self, screen_name: str, belong_to: dict = None, relative_path='', name=None, rest_id=None) -> None:
        """ 账号不存在或账号被暂停，抛出RuntimeError
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
        self.path = core.path + f'\\{relative_path}\\{self.title}'
        self.belong_to = belong_to
        self.latest = ''

        # TODO
        # 目前的情况是，如果此用户隶属于某个列表，或本地列表。我们才创建为其创建配置。
        # 但没有配置的用户是无法下载的，所以此用户只用于获取信息。
        if self.belong_to != None:
            if not self.is_exist():
                self.create_profile()
            else:
                self.update()

        if self.external:
            utility.create_shortcut(self.path, core.path + f'\\{relative_path}')

        self.failures = []
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


    def update(self):
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
        """返回时间线上的所有推文(list)
        """
        UserMedia.params['variables']['userId'] = self.rest_id
        UserMedia.params['variables']['count'] = count
        UserMedia.params['variables']['cursor'] = cursor
        params = {k: json.dumps(v) for k, v in UserMedia.params.items()}

        try:
            res = ses.get(UserMedia.api, params=params)
            raise_if_error(res)
        except TWRequestError:
            #logger.error(res.text)
            if res.status_code == requests.codes.TOO_MANY:
                if int(res.headers['x-rate-limit-remaining']) > 0:
                    raise RuntimeError('Reached rate-limit')
                else:
                    # Reach rate limit                    
                    limit_time = datetime.datetime.fromtimestamp(int(res.headers['x-rate-limit-reset']))
                    logger.warning(
                        'Reached rate-limit, have been waiting until {}'.format(limit_time.strftime("%Y-%m-%d %H:%M:%S")))

                    second = limit_time.timestamp() - datetime.datetime.now().timestamp()
                    time.sleep(second)
                    res = ses.get(UserMedia.api, params=params)
                    raise_if_error(res)
            raise
        if res.json()['data']['user']['result']['__typename'] == 'UserUnavailable':
            raise TwUserError(self, 'User has been protected')
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
                    items.appendleft(Tweet(title, urls, vurls, legacy['created_at']))
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
                logger.info("{} {}/{} > {}".format(self.title, i + 1, len(entries), tweet.text))
                created_at = tweet.created_at
                need_failed_created_at = False
        return (need_failed_created_at, created_at)


    def retry(self, update_latest: bool):
        entries = self.failures
        self.failures.clear()
        result = self.download_tweets(entries, True)

        if update_latest:
            self.belong_to[self.rest_id]['latest'] = result[1]

        if len(self.failures):
            logger.warning("There are tweets with failed downloads by {})", self.title)
        for i, t in enumerate(self.failures):
            logger.warning(t.text)


    def download(self):
        result = self.download_tweets(self.get_entries(), False)
        self.belong_to[self.rest_id]['latest'] = result[1]

        if len(self.failures) > 0:
            self.retry(result[0])