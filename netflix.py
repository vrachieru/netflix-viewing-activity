#!/usr/bin/python3
# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup
import requests
import codecs
import json
import time
import re

class Netflix:
    headers = {'User-Agent': 'Mozilla/5.0'}
    session = requests.Session()
    context = None

    def __init__(self, email, password):
        self.login(email, password)

    def escape(self, string):
        string = re.sub(r'\\([^x])', r'\\\\\1', string)
        return codecs.decode(string, 'unicode_escape')

    def get_js_property(self, page, prop):
        pattern = re.compile('%s\s+=\s+({[\s\S]+?});' % prop)
        result = re.search(pattern, page.text)
        data = self.escape(result.group(1))
        return json.loads(data)

    def login(self, email, password):
        page = self.session.get('https://www.netflix.com/Login', headers=self.headers)
        soup = BeautifulSoup(page.text, 'lxml')
        self.authURL = soup.find('input', attrs={'name': 'authURL'})['value']

        parameters = {
            'email': email,
            'password': password,
            'rememberMe': False,
            'flow': 'websiteSignUp',
            'mode': 'login',
            'action': 'loginAction',
            'withFields': 'email,password,rememberMe,nextPage,showPassword',
            'authURL': self.authURL,
            'nextPage': '',
            'showPassword': ''
        }

        page = self.session.post('https://www.netflix.com/Login', data=parameters, headers=self.headers)
        self.context = self.get_js_property(page, 'reactContext')

    def get_profiles(self):
        return self.context['models']['profilesModel']['data']['profiles']

    def get_active_profile(self):
        return self.context['models']['profilesModel']['data']['active']

    def switch_profile(self, guid):
        self.session.get('https://www.netflix.com/SwitchProfile?tkn=%s' % guid, headers=self.headers)

    def get_viewing_activity(self):
        serverDefs = self.context['models']['serverDefs']['data']
        url = '/'.join([serverDefs['SHAKTI_API_ROOT'], serverDefs['BUILD_IDENTIFIER'], 'viewingactivity'])

        page = 0
        viewing_activity = []

        while True:
            parameters = {
                'pg': page,
                'pgSize': 100,
                '_': int(time.time() * 1000),
                'authURL': self.authURL
            }
            res = self.session.get(url, params=parameters).json()

            if len(res['viewedItems']) > 0:
                viewing_activity.extend(res['viewedItems'])
                page += 1
            else:
                break

        return viewing_activity


netflix = Netflix('email', 'password')
profiles = netflix.get_profiles()

for profile in profiles:
    netflix.switch_profile(profile['guid'])
    with open('%s.json' % profile['firstName'], 'w') as file:
            json.dump(netflix.get_viewing_activity(), file)