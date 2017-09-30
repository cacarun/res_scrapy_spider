# -*- coding: utf-8 -*-
import scrapy

from scrapy.http import Request, FormRequest

import urllib
import urllib2
import cookielib
import re
import time
import random

class BeautySpider(scrapy.Spider):
    name = 'beauty'
    allowed_domains = ['douban.com']
    # start_urls = ['http://beauty.com/']

    def __init__(self):
        # 初始化一些变量
        self.douban_header = {
            "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36"}
        # self.douban_cookie = {}

        self.login_url = 'https://accounts.douban.com/login'
        self.login_form_data = {
            # 'redir': 'https://www.douban.com',
            'form_email': '',
            'form_password': '',
            'login': u'登陆'
        }

        self.cj = cookielib.CookieJar()

    def replace_all(self, text, dic):
        for i, j in dic.iteritems():
            text = text.replace(i, j)
        return text

    def browse(self, url, cj):
        try:
            req = urllib2.Request(url)
            opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
            response = opener.open(req)
            print ('BROSWE_REQUEST:\n' + url)
            # print ('BROSWE_RESPONSE:\n' + response.read())
            return response.read()
        except:
            return ''

    def downImg(url, name):
        fr = urllib.urlopen(url)
        stream = fr.read(-1)
        fr.close()
        print ("save:" + url + "\r")
        fw = open('results/' + name, 'w')
        fw.write(stream)
        fw.close()

    def parse(self, response):
        du = 'http://m.douban.com'
        # set refresh_interval
        refresh_interval = 1

        if response.status == 200:
            replace_dict = {'\n': '', '\t': '', ' ': '', '　': ''}
            group_content = self.replace_all(response, replace_dict)
            # print (group_content)
            items = re.findall(
                '<ahref="\/group\/topic\/(\d+)\/"title="(.*?)"><.*?<divclass="info">(\d+)回应', group_content)
            if not items.__len__() == 0:
                for i in items:
                    item_title = i[1]
                    item_title = item_title.replace('/', '')
                    item_ID = i[0]
                    item_comm = i[2]
                    if int(item_comm) > 1:
                        print (item_title + ' | ' + item_comm)
                        item_url = du + '/group/topic/' + item_ID + '/'
                        item_content = self.browse(item_url, self.cj)
                        img_content = self.replace_all(item_content, replace_dict)
                        imgs = re.findall(
                            '<divclass="content_img"><imgsrc="(.*?)"/>', img_content)
                        if not imgs.__len__() == 0:
                            num = 0
                            for img_url in imgs:
                                num = num + 1
                                filename = str(item_title) + str(num) + '.jpg'
                                try:
                                    self.downImg(img_url, filename)
                                except:
                                    pass
                        time.sleep(refresh_interval * random.randint(1, 3))

            time.sleep(refresh_interval)


        else:
            print 'request list page error %s -status code: %s:' % (response.url, response.status)

    def start_requests(self):
        return [Request(
            url=self.login_url,
            meta={"cookiejar": 1},
            headers=self.douban_header,
            callback=self.post_login)]

    def post_login(self, response):
        if response.status == 200:
            captcha_url = response.xpath('//*[@id="captcha_image"]/@src').extract()  # 获取验证码图片的链接
            if len(captcha_url) > 0:
                print 'manual input captcha，link url is：%s' % captcha_url
                captcha_text = raw_input('Please input the captcha:')
                self.login_form_data['captcha-solution'] = captcha_text
            else:
                print 'no captcha'
            print 'login processing......'

            return [
                FormRequest.from_response(
                    response,
                    meta={"cookiejar": response.meta["cookiejar"]},
                    headers=self.douban_header,
                    formdata=self.login_form_data,
                    callback=self.after_login
                )
            ]

        else:
            print 'request login page error %s -status code: %s:' % (self.login_url, response.status)

    def after_login(self, response):
        if response.status == 200:
            title = response.xpath('//title/text()').extract()[0]
            if u'登录豆瓣' in title:
                print 'login failed，please retry!'
            else:
                print 'login success!'

                # 分页查找（豆瓣当前是按每页 25 条显示的）
                # hangzhou: 1
                # shanghai: 2
                list_urls = ['https://www.douban.com/group/haixiuzu/discussion?start=' + str(i) for i in range(0, 100, 25)]
                # list_urls_2 = ['https://www.douban.com/group/467221/discussion?start=' + str(i) for i in range(0, 250, 25)]
                # list_urls_sh = ['https://www.douban.com/group/homeatshanghai/discussion?start=' + str(i) for i in
                #                 range(0, 250, 25)]
                # list_urls.extend(list_urls_2)
                # list_urls.extend(list_urls_sh)

                for i in range(len(list_urls)):
                    url = list_urls[i]
                    print 'list page url: %s' % url
                    yield Request(url=url, headers=self.douban_header, callback=self.parse)

        else:
            print 'request post login error %s -status code: %s:' % (self.login_url, response.status)

