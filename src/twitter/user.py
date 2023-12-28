import json
import os
import time
from datetime import datetime, timezone, timedelta

from api import UserByScreenName, UserMedia
from src.utils.exception import *
from src.utilitycpp import *
from src.utils.logger import logger

from src.settings import *
from readerwriterlock import rwlock


rwlock =  rwlock.RWLockFair()


class TwitterUser:
    def __init__(self, result =None, screen_name = None, rest_id = None) -> None:
        """ 账号不存在或账号被暂停,或受保护账号，抛出UserError
        """
        from src.utils import pattern
        from src.utils.utility import raise_if_error, get_user_result
        from src.session import session
        
        if not result and not screen_name and not rest_id:
            raise TypeError
        
        if not result:
            result = get_user_result(screen_name=screen_name) if screen_name else get_user_result(userId = rest_id)
            
        if 'UserUnavailable' == result['__typename']:
            if screen_name:
                result['screen_name'] = screen_name
            if rest_id and 'rest_id' not in result:
                result['rest_id'] = rest_id
            raise TwUserError(**result)

    
        self.screen_name = result['legacy']['screen_name']
        self.name = result['legacy']['name']
        self.rest_id = result['rest_id']
        self.title = f'{pattern.nonsupport.sub("", self.name)}({self.screen_name})'

        
    def _create(self, belong_to):
        self.belong_to = belong_to

        if self._is_exist():
            self._update()
        else:
            self._create_profile()


    def _is_exist(self) -> bool:
        lock = rwlock.gen_rlock()
        lock.acquire()
        users = json.loads(project.usersj_dir.read_text('utf-8'))
        lock.release()
        return self.rest_id in users


    # 异常安全
    def _update(self):
        from src.utils.utility import raise_if_error, create_shortcut
        from src.twitter.list import TwitterList
        lock = rwlock.gen_wlock()

        lock.acquire()
        try:
            users = json.loads(project.usersj_dir.read_text('utf-8'))
            creater = TwitterList(rest_id=users[self.rest_id]['belong_to'][0])

            # 更新用户名
            renamed = False
            latest_name = users[self.rest_id]['names'][-1]
            if self.title != latest_name:
                if not creater.path.joinpath(latest_name).exists():
                    creater.path.joinpath(latest_name).mkdir()
                creater.path.joinpath(latest_name).rename(creater.path.joinpath(self.title))
                users[self.rest_id]['names'].append(self.title)
                project.usersj_dir.write_text(json.dumps(users, indent=4, allow_nan=True, ensure_ascii=False), 'utf-8')
                logger.info('Renamed {} -> {}'.format(latest_name, self.title))
                renamed = True

            # 检查是否需要创建快捷方式
            if self.belong_to.rest_id not in users[self.rest_id]['belong_to']:
                create_shortcut(creater.path.joinpath(self.title), self.belong_to.path)
                users[self.rest_id]['belong_to'].append(self.belong_to.rest_id)
                project.usersj_dir.write_text(json.dumps(users, indent=4, allow_nan=True, ensure_ascii=False), 'utf-8')
                logger.info('Direct {1}/{0} -> {2}/{0}'.format(self.title, self.belong_to.name, creater.name))
            elif self.belong_to.rest_id != users[self.rest_id]['belong_to'][0] and renamed:
                """更改了用户名并且当前列表非首次创建者，更新快捷方式"""
                try:
                    self.belong_to.path.joinpath(latest_name).with_suffix('.lnk').unlink()
                except FileNotFoundError as err:
                    logger.warning(err)
                create_shortcut(creater.path.joinpath(self.title), self.belong_to.path)
                

            self.belong_to = creater
            self.latest = users[self.rest_id]['latest']
            self.path = self.belong_to.path.joinpath(self.title)
            self.prefix = '{}/{}'.format(self.belong_to.name, self.title)
        finally:
            lock.release()


    # 异常安全
    def _create_profile(self):
        self.latest = datetime.strftime(datetime.fromtimestamp(0, timezone(timedelta(hours=0))), '%a %b %d %H:%M:%S %z %Y')
        info = {
            'names': [self.title], 
            'latest': self.latest,
            'belong_to': [
                self.belong_to.rest_id
            ]
        }

        # 创建用户文件夹
        path = self.belong_to.path.joinpath(self.title)
        if not path.exists():
            path.mkdir()

        lock = rwlock.gen_wlock()
        lock.acquire()
        users = json.loads(project.usersj_dir.read_text('utf-8'))
        users[self.rest_id] = info
        project.usersj_dir.write_text(json.dumps(users, indent=4, allow_nan=True, ensure_ascii=False), 'utf-8')
        lock.release()
        
        self.path = path
        self.prefix = '{}/{}'.format(self.belong_to.name, self.title)
        logger.info('Created {}'.format(self.prefix))

    
    def get_tweets(self) -> list:
        """返回时间线(list)
        """
        
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
        
        from requests import HTTPError
        from src.utils.utility import raise_if_error, timeformat, handle_title
        from src.session import session
        after = datetime.strptime(self.latest, timeformat).timestamp()
        um = UserMedia()

        tweets = []
        cursor = ""
        um.params['variables']['userId'] = self.rest_id
        um.params['variables']['count'] = 20
        
        logger.debug('Getting timeline for %s', self.title)
        while True:
            um.params['variables']['cursor'] = cursor
            um.params['variables']['count'] = 200 if cursor != "" else 20
            try:
                res = session.get(um.api, json=um.params)
                res.raise_for_status()
                raise_if_error(res)
            except HTTPError:
                if res.status_code == 429 and int(res.headers['x-rate-limit-remaining']) <= 0:                
                    flush_time = datetime.fromtimestamp(int(res.headers['x-rate-limit-reset']))
                    print('Reached rate-limit, wait until {}'.format(flush_time.strftime("%Y-%m-%d %H:%M:%S")))

                    time.sleep(flush_time.timestamp() - datetime.now().timestamp())

                    res = session.get(um.api, json=um.params)
                    res.raise_for_status()
                    raise_if_error(res)
                else:
                    logger.error(res.text)
                    os._exit(1)

            if not len(tweets):
                try:
                    if res.json()['data']['user']['result']['__typename'] == 'UserUnavailable':
                        raise TwUserError(**res.json()['data']['user']['result'])
                except KeyError:
                    raise TwUserError('UserUnavailable', 'unknown', screen_name= self.screen_name, rid = self.rest_id)
            
            modules = []

            for ins in res.json()['data']['user']['result']['timeline_v2']['timeline']['instructions']:
                if ins['type'] == 'TimelineAddEntries':
                    for e in ins['entries']:
                        if e['content']['__typename'] == 'TimelineTimelineCursor' and e['content']['cursorType'] == 'Bottom':
                            cursor = e['content']['value']
                        elif e['content']['__typename'] == 'TimelineTimelineModule' and  um.params['variables']['cursor'] == '':
                            modules = e['content']['items']

                elif ins['type'] == 'TimelineAddToModule':
                    modules = ins['moduleItems']
            
            if not len(modules):
                return tweets
            
            for item in modules:
                result = item['item']['itemContent']['tweet_results'].get('result')
                if result == None or result['__typename'] == 'TweetTombstone':
                    continue
                if result['__typename'] == 'TweetWithVisibilityResults':
                    legacy = result['tweet']['legacy']
                else:
                    legacy = result['legacy']
                
                if (
                    datetime.strptime(legacy['created_at'], timeformat).timestamp() <= 
                    after
                ):
                    return tweets

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
                tweets.append(Tweet(title, urls, legacy['created_at']))


    def download(self, belong_to):
        import pythoncom
        from src.utils.utility import timeformat
        pythoncom.CoInitialize()

        try:
            self._create(belong_to)
            entries = self.get_tweets()
            if not len(entries):
                return
            #print(self.prefix, len(entries))
            latest = cdownload(entries, str(self.path))

            #print('calc time = %dms' % int((time.time() - start) * 1000))
            if latest:
                lock = rwlock.gen_wlock()
                lock.acquire()
                try:
                    users = json.loads(project.usersj_dir.read_text('utf-8'))
                    users[self.rest_id]['latest'] = datetime.strftime(datetime.fromtimestamp(latest, timezone(timedelta(hours=0))), timeformat)
                    project.usersj_dir.write_text(json.dumps(users, indent=4, allow_nan=True, ensure_ascii=False), 'utf-8')
                finally:
                    lock.release()
        finally:
            pythoncom.CoUninitialize()