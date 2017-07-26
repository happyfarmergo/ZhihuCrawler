# -*- coding: utf-8 -*-
import os
import pickle
import re
import sys
import time
import requests
from bs4 import BeautifulSoup
from PIL import Image

class AccountPool:
    def __init__(self):
        self.base_url = 'https://www.zhihu.com'
        self.headers = {
            "User-Agent": 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.10; rv:41.0) Gecko/20100101 Firefox/41.0',
            "Referer": 'http://www.zhihu.com/',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Host': 'www.zhihu.com',
        }
        self.cookies = []
        self.cookie_cnt = 0
        self.cookie_path = 'zhihu.cookie'
        self.login_all()

    '''
    一次登录所有账号，并存储到cookie文件中
    '''
    def login_all(self):
        if os.path.exists(self.cookie_path):
            with open(self.cookie_path) as f:
                self.cookies = pickle.load(f)
        else:
            number = int(raw_input('账户数量: '))
            while number > 0:
                session = requests.session()
                sys.stdout.flush()
                username = raw_input('用户名: ')
                password = raw_input('密码: ')
                captcha = self.get_captcha(session)

                if re.search(r'^1\d{10}$', username):
                    user_type = 'phone_num'
                    login_suffix = 'login/phone_num'
                elif re.search(r'(.+)@(.+)', username):
                    user_type = 'email'
                    login_suffix = 'login/email'
                else:
                    print('invalid username')
                    sys.exit(1)

                req = session.get(self.base_url, headers=self.headers, verify=True)
                soup = BeautifulSoup(req.text, 'html.parser')
                xsrf = soup.find('input', {'name': '_xsrf', 'type': 'hidden'}).get('value')

                login_data = {
                    user_type: username,
                    'password': password,
                    'rememberme': "true",
                    'captcha': captcha,
                    '_xsrf': xsrf
                }

                login_page = session.post(self.base_url + '/' + login_suffix, headers=self.headers, data=login_data,
                                         verify=True)
                if not login_page.json()['r']:
                    print(session.cookies.get_dict())
                    self.cookies.append(session.cookies)

                else:
                    print('login fail...')

                number -= 1

            with open(self.cookie_path, 'wb') as f:
                pickle.dump(self.cookies, file=f)

    def get_captcha(self, session):
        timestamp = int(time.time() * 1000)
        captcha_url = self.base_url + '/captcha.gif?r=' + str(timestamp) + '&type=login'

        with open('zhihucaptcha.gif', 'wb') as f:
            captcha = session.get(captcha_url, headers=self.headers, verify=True)
            f.write(captcha.content)
        try:
            img = Image.open('zhihucaptcha.gif')
            img.show()
        except:
            print('open image failed...')

        captcha = raw_input('请输入验证码: ').strip()
        return captcha

    '''
    切换账号    
    '''
    def get(self):
        if len(self.cookies) > 0:
            cookie = self.cookies[self.cookie_cnt]
            self.cookie_cnt = (self.cookie_cnt + 1) % len(self.cookies)
            return cookie
        return None
