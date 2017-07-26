# -*- coding: utf-8 -*-
from __future__ import print_function

import datetime
import json
import logging
import logging.config

import time

import requests
from bs4 import BeautifulSoup
from account_pool import AccountPool
from redis_util import RedisUtil
from mongo_util import Mongo


class ZhihuCrawler:
    def __init__(self):
        self.base_url = 'https://www.zhihu.com'
        self.settings = 'https://www.zhihu.com/settings/profile'
        self.headers = {
            "User-Agent": 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.10; rv:41.0) Gecko/20100101 Firefox/41.0',
            "Referer": 'http://www.zhihu.com/',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Host': 'www.zhihu.com',
        }
        # 爬虫起点
        self.start_user = None
        # 已爬取用户ID的Redis Set Key
        self.pass_key = 'zhihu:pass'
        # 爬取失败用户ID的Redis Set Key
        self.fail_key = 'zhihu:fail'
        # 待爬取用户ID的Redis List Key
        self.queue_key = 'user'
        # 知乎账号池
        self.pool = AccountPool()
        # 采用requests库保存会话信息
        self.session = requests.session()
        # mongodb存储爬取的用户信息
        self.mongo = Mongo(database='zhihu')
        # redis存储爬取状态信息
        self.redis = RedisUtil(host='localhost', port=6379, namespace='zhihu')
        # logger配置
        logging.config.fileConfig("./Log/zhihu.conf")
        self.logger = logging.getLogger('zhihu')

        self.use_account()

    '''
    切换账号
    '''

    def use_account(self):
        cookie = self.pool.get()
        if cookie is None:
            self.logger.error('NO ACCOUNT')
            return False
        self.session.cookies.update(cookie)
        return self.is_login()

    '''
    验证是否处于登录状态
    '''

    def is_login(self):
        login_code = self.session.get(self.settings, headers=self.headers, allow_redirects=False).status_code
        return True if login_code == 200 else False

    '''
    获取用户基本信息
    包括其关注者列表
    '''

    def get_user_basic(self, username):
        home_url = self.base_url + '/people/' + username + '/following'
        req = self.session.get(url=home_url, headers=self.headers, verify=True)
        soup = BeautifulSoup(req.text, 'lxml')

        user_info = dict()
        data = soup.find('div', id='data')['data-state']
        data = json.loads(data, encoding='utf-8')
        user = data['entities']['users'][username]
        followings = list(data['entities']['users'])
        followings.remove(username)

        img = soup.find('img', class_='Avatar Avatar--large UserAvatar-inner')
        user_info['avatar'] = img['src'] if img is not None else ''
        user_info['name'] = user['name']
        user_info['headline'] = user['headline']
        user_info['gender'] = 'Male' if user['gender'] else 'Female'
        user_info['description'] = user['description']
        user_info['business'] = user['business']['name'] if 'business' in user.keys() else ''
        user_info['answerCount'] = int(user['answerCount'])
        user_info['favoriteCount'] = int(user['favoriteCount'])
        user_info['thankedCount'] = int(user['thankedCount'])
        user_info['followerCount'] = int(user['followerCount'])
        user_info['followingCount'] = int(user['followingCount'])
        user_info['educations'] = list()
        user_info['employments'] = list()
        user_info['locations'] = list()

        for edu in user['educations']:
            info = dict()
            info['school'] = edu['school']['name'] if 'school' in edu.keys() else ''
            info['major'] = edu['major']['name'] if 'major' in edu.keys() else ''
            user_info['educations'].append(info)
        for loc in user['locations']:
            info = dict()
            info['name'] = loc['name']
            user_info['locations'].append(info)
        for em in user['employments']:
            info = dict()
            info['name'] = em['company']['name'] if 'name' in em.keys() else ''
            info['job'] = em['job']['name'] if 'job' in em.keys() else ''
            user_info['employments'].append(info)

        user_info['create_time'] = datetime.datetime.now()
        user_info['following'] = followings

        return user_info, followings

    '''
    采用BFS沿着关注链爬取用户
    depth: 当前层数
    max_depth: 最大层数
    '''

    def following_crawler(self, depth, max_depth=5):
        if depth > max_depth:
            return
        depths = ['#{}'.format(i) for i in range(max_depth)]
        index = 0
        s_cnt = self.redis.ssize(self.pass_key)
        f_cnt = self.redis.ssize(self.fail_key)
        if self.redis.get(self.queue_key) is None:
            self.start_user = raw_input('从谁开始爬? ') .strip()
            self.redis.put(self.start_user)
            self.redis.put('#0')

        while index <= max_depth:
            while not self.redis.empty(self.queue_key):
                username = self.redis.get(self.queue_key)
                try:
                    index = depths.index(username)
                    break
                except Exception as e:
                    pass

                if self.redis.sismem(self.pass_key, username) or self.redis.sismem(self.fail_key, username):
                    continue

                self.logger.info('[{}]'.format(username))
                try:
                    basic, followings = self.get_user_basic(username)
                    self.redis.sadd_items(self.pass_key, username)
                    self.redis.put(self.queue_key, *tuple(followings))
                    self.mongo.save_user(basic)
                    s_cnt += 1
                except Exception as e:
                    self.logger.info(e.message)
                    self.logger.info('--------{}--------failed'.format(username))
                    self.redis.sadd_items(self.fail_key, username)
                    f_cnt += 1

                # 知乎反爬虫力度太大，由于只有俩账号，只好放慢速度
                if (f_cnt + s_cnt + 1) % 5 == 0:
                    self.logger.info('---------\nsleep at {}\n---------'.format(datetime.datetime.now()))
                    time.sleep(5)
                if (f_cnt + s_cnt + 1) % 50 == 0:
                    self.logger.info('---------\nsleep at {}\n---------'.format(datetime.datetime.now()))
                    time.sleep(15)
                if (f_cnt + s_cnt + 1) % 25 == 0:
                    if not self.use_account():
                        self.logger.error('Account Error')
                        raise Exception('Account Error')
                    else:
                        self.logger.info('--------\nchange account\n--------')

            self.redis.put(self.queue_key, depths[index + 1])
            self.logger.info(
                '---------\nDepth {} crawled.\t Fail/Success: {}/{} got\n----------'.format(index, f_cnt, s_cnt))
            index = index + 1


if __name__ == '__main__':
    zhihu = ZhihuCrawler()
    zhihu.following_crawler(0, max_depth=5)
