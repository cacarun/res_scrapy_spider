# -*- coding: utf-8 -*-
import scrapy
import time

from scrapy.http import Request, FormRequest
from scrapy import Selector

from bs4 import BeautifulSoup

from items import ResScrapySpiderItem


class BeautySpider(scrapy.Spider):
    name = 'beauty'
    allowed_domains = ['douban.com']

    custom_settings = {
        'IMAGES_STORE': './result_beauty/' + time.strftime('%Y%m%d_%X', time.localtime()).replace(':', ''),
    }

    def __init__(self):
        # 初始化一些变量
        self.douban_header = {
            "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36"}

        self.login_retry = 3
        self.login_account = 'https://accounts.douban.com'
        self.login_url = 'https://accounts.douban.com/login'
        self.login_form_data = {
            # 'redir': 'https://www.douban.com',
            'form_email': '',
            'form_password': '',
            'login': u'登陆'
        }
        # https://www.douban.com/group/topic/{image_name}/

        self.list_urls = self.get_urls()

    @staticmethod
    def get_urls():
        # 分页查找（豆瓣当前是按每页 25 条显示的）
        # haixiuzu, 515085, 481977, 516876, 569879, 582663, jiatuizu, 368701
        count = 160
        list_urls_1 = ['https://www.douban.com/group/haixiuzu/discussion?start=' + str(i) for i in range(0, count, 25)]
        return list_urls_1

    def start_requests(self):
        print '=================== start_requests ===================='
        return [Request(
            url=self.login_account,
            meta={"cookiejar": 1},
            headers=self.douban_header,
            callback=self.check_login)]

    def login(self):
        print '[login] login retry: ' + str(self.login_retry)
        if self.login_retry > 0:
            return [Request(
                url=self.login_url,
                meta={"cookiejar": 1},
                headers=self.douban_header,
                callback=self.check_login)]
        else:
            print '[login] login try max!'

    def check_login(self, response):
        if response.status == 200:
            title = response.xpath('//title/text()').extract()[0]
            if u'登录豆瓣' in title:
                print '[check_login] cookie empty, need to login'
                return [Request(
                    url=self.login_url,
                    meta={"cookiejar": 1},
                    headers=self.douban_header,
                    callback=self.post_login)]
            else:
                print '[check_login] cookie exist, direct go'
                self.crawl()
        else:
            print '[check_login] error %s, status code: %s' % (response.url, response.status)

    def post_login(self, response):
        if response.status == 200:
            captcha_url = response.xpath('//*[@id="captcha_image"]/@src').extract()  # 获取验证码图片的链接
            if len(captcha_url) > 0:
                print '[post_login] manual input captcha, link url is: %s' % captcha_url
                captcha_text = raw_input('Please input the captcha:')
                self.login_form_data['captcha-solution'] = captcha_text
            else:
                print '[post_login] no captcha'
            print '[post_login] login processing......'

            return [FormRequest.from_response(
                    response,
                    meta={"cookiejar": response.meta["cookiejar"]},
                    headers=self.douban_header,
                    formdata=self.login_form_data,
                    callback=self.after_login)]

        else:
            print '[post_login] error %s, status code: %s' % (response.url, response.status)

    def after_login(self, response):
        if response.status == 200:
            title = response.xpath('//title/text()').extract()[0]
            if u'登录豆瓣' in title:
                print '[after_login] login failed, retry'
                self.login_retry -= 1
                self.login()
            else:
                print '[after_login] login success!'
                return self.crawl()
        else:
            print '[after_login] error %s, status code: %s' % (response.url, response.status)

    def crawl(self):
        for i in range(len(self.list_urls)):
            url = self.list_urls[i]
            print '[crawl] list page url: %s' % url
            yield Request(url=url, headers=self.douban_header, callback=self.parse)

    def parse(self, response):
        if response.status == 200:
            sel = Selector(response)
            sites = sel.xpath('//table[@class="olt"]/tr[@class=""]')
            for site in sites:
                title = site.xpath('td[@class="title"]/a')
                if title:
                    detail_url = title.xpath('@href').extract()[0]
                    if detail_url:
                        # 请求详情页
                        yield Request(url=detail_url, headers=self.douban_header, callback=self.parse_detail)

        else:
            print '[parse] error %s, status code: %s' % (response.url, response.status)

    def parse_detail(self, response):
        if response.status == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            topic_content = soup.find_all(attrs={'class': 'topic-content'})[1]
            if topic_content:
                try:
                    image_array = []
                    result_array = topic_content.find_all(['img'])
                    for item in result_array:
                        if item.name == 'img':
                            img_src = item.get('src')
                            image_array.append(img_src)

                    if len(image_array) != 0:
                        # print '======================================='
                        # print 'URL:' + response.url
                        # print image_array
                        # print '======================================='

                        item = ResScrapySpiderItem()
                        item['image_urls'] = image_array
                        item['topic_id'] = response.url.split('/')[-2]

                        yield item

                except Exception, e:
                    print '[parse_detail] topic content parse error:', e
            else:
                print '[parse_detail] detail page topic content is null'
        else:
            print '[parse_detail] error %s, status code: %s' % (response.url, response.status)
