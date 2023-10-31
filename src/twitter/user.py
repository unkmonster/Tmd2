import json
import os
import time
from datetime import datetime, timezone, timedelta

from api import UserByScreenName, UserMedia
from src.utils.exception import *
from src.utils.utility import *
from src.utilitycpp import *
from src.utils.logger import logger

from src.session import session
from src.settings import *
from readerwriterlock import rwlock


rwlock =  rwlock.RWLockFair()


class TwitterUser:
    from twitter.list import TwitterList
    def __init__(self, screen_name: str, belong_to: TwitterList=None, name=None, rest_id=None) -> None:
        """ 账号不存在或账号被暂停,或受保护账号，抛出UserError
        """
        from src.utils import pattern

        # 如果 name 或 rest_id 未指定，则利用 screen_name 获取
        if (name or rest_id) == None:
            UserByScreenName.params['variables']['screen_name'] = screen_name
            res = session.get(UserByScreenName.api, json=UserByScreenName.params)
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

        exist = self.is_exist()
        if exist:
            #self.tmp()
            self.update()
        self.prefix = '{}/{}'.format(self.belong_to.name, self.title)
        if not exist:
            self.create_profile()
        self.path = self.belong_to.path.joinpath(self.title)


    def is_exist(self) -> bool:
        lock = rwlock.gen_rlock()
        lock.acquire()
        users = json.loads(project.usersj_dir.read_text('utf-8'))
        lock.release()
        return self.rest_id in users


    def update(self):
        from twitter.list import TwitterList
        
        lock = rwlock.gen_wlock()
        lock.acquire()
        users = json.loads(project.usersj_dir.read_text('utf-8'))
        
        belong_to = TwitterList(users[self.rest_id]['belong_to'][0])

        # 更新用户名
        renamed = False
        latest_name = users[self.rest_id]['names'][-1]
        if self.title != latest_name:
            belong_to.path.joinpath(latest_name).rename(belong_to.path.joinpath(self.title))
            users[self.rest_id]['names'].append(self.title)
            logger.info('Renamed {} -> {}'.format(latest_name, self.title))
            renamed = True

        # 检查是否需要创建快捷方式
        if self.belong_to.rest_id not in users[self.rest_id]['belong_to']:
            users[self.rest_id]['belong_to'].append(self.belong_to.rest_id)
            create_shortcut(belong_to.path.joinpath(self.title), self.belong_to.path)
            logger.info('Direct {1}/{0} -> {2}/{0}'.format(self.title, self.belong_to.name, belong_to.name))
        elif self.belong_to.rest_id != users[self.rest_id]['belong_to'][0] and renamed:
            """更改了用户名并且当前列表非首次创建者，更新快捷方式"""
            try:
                self.belong_to.path.joinpath(latest_name).with_suffix('.lnk').unlink()
            except FileNotFoundError as err:
                logger.warning(err)
            create_shortcut(belong_to.path.joinpath(self.title), self.belong_to.path)
            

        self.belong_to = belong_to
        self.latest = users[self.rest_id]['latest']
        project.usersj_dir.write_text(json.dumps(users, indent=4, allow_nan=True, ensure_ascii=False), 'utf-8')
        lock.release()


    # def tmp(self):
    #     users = json.loads(project.usersj_dir.read_text('utf-8'))
    #     users[self.rest_id]['belong_to'] = [self.belong_to.rest_id]
    #     project.usersj_dir.write_text(json.dumps(users, indent=4, allow_nan=True, ensure_ascii=False), 'utf-8')


    def create_profile(self):
        self.latest = datetime.strftime(datetime.fromtimestamp(0, timezone(timedelta(hours=0))), '%a %b %d %H:%M:%S %z %Y')
        info = {
            'names': [self.title], 
            'latest': self.latest,
            'belong_to': [
                self.belong_to.rest_id
            ]
        }
        lock = rwlock.gen_wlock()
        lock.acquire()
        users = json.loads(project.usersj_dir.read_text('utf-8'))
        users[self.rest_id] = info
        project.usersj_dir.write_text(json.dumps(users, indent=4, allow_nan=True, ensure_ascii=False), 'utf-8')
        lock.release()
        
        self.path = self.belong_to.path.joinpath(self.title)
        if not self.path.exists():
            self.path.mkdir()
        logger.info('Created {}'.format(self.prefix))


    def get_timeline(self, count=50, cursor="") -> list:
        """返回时间线(list)
        """
        UserMedia.params['variables']['userId'] = self.rest_id
        UserMedia.params['variables']['count'] = count
        UserMedia.params['variables']['cursor'] = cursor
        params = {k: json.dumps(v) for k, v in UserMedia.params.items()}

        try:
            res = session.get(UserMedia.api, params=params)
            raise_if_error(res)
        except TWRequestError as er:
            if res.status_code == requests.codes.TOO_MANY:
                if int(res.headers['x-rate-limit-remaining']) > 0:
                    logger.warning('此账号已被限制')
                else:                
                    limit_time = datetime.datetime.fromtimestamp(int(res.headers['x-rate-limit-reset']))
                    logger.warning(
                        'Reached rate-limit, have been waiting until {}'.format(limit_time.strftime("%Y-%m-%d %H:%M:%S")))

                    time.sleep(limit_time.timestamp() - datetime.datetime.now().timestamp())

                res = session.get(UserMedia.api, params=params)
                raise_if_error(res)
            else:
                raise
        try:
            if res.json()['data']['user']['result']['__typename'] == 'UserUnavailable':
                raise TwUserError(self, 'User has been protected')
            return res.json()['data']['user']['result']['timeline_v2']['timeline']['instructions'][0]['entries']
        except KeyError:
            raise TwUserError(self, 'UserUnavailable')


    def get_entries(self) -> list[Tweet]:
        def max_bitrate(variants)->str:
            """ 用于获取最高比特率的视频
            """
            max = [0, '']
            for v in variants:
                br = int(v.get("bitrate") or 0)
                if br > max[0]:
                    max[0] = br
                    max[1] = v['url']
            return max[1]
        
        
        items = []
        latest_timestamp = datetime.strptime(self.latest, timeformat).timestamp()

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

                    if (
                        datetime.strptime(legacy['created_at'], timeformat).timestamp() <= 
                        latest_timestamp
                    ):
                        entries.clear()
                        break
                    
                    title = handle_title(legacy['full_text'])
                    medias = legacy.get('extended_entities')
                    if medias == None:
                        continue
                    else:
                        medias = medias['media']

                    urls = []
                    for m in medias:
                        match m['type']:
                            case 'photo':
                                urls.append(m['media_url_https'])
                            case 'video':
                                urls.append(max_bitrate(m['video_info']['variants']))
                    items.append(Tweet(title, urls, legacy['created_at']))
                    pass
                # 翻页   
                elif content['entryType'] == 'TimelineTimelineCursor':
                    if content['cursorType'] == 'Bottom':
                        entries = self.get_timeline(cursor=content['value'])
        return items


    def download(self):
        entries = self.get_entries()
        latest = cdownload(entries, str(self.path))

        #print('calc time = %dms' % int((time.time() - start) * 1000))
        if latest:
            lock = rwlock.gen_wlock()
            lock.acquire()
            users = json.loads(project.usersj_dir.read_text('utf-8'))
            users[self.rest_id]['latest'] = datetime.strftime(datetime.fromtimestamp(latest, timezone(timedelta(hours=0))), timeformat)
            project.usersj_dir.write_text(json.dumps(users, indent=4, allow_nan=True, ensure_ascii=False), 'utf-8')
            lock.release()