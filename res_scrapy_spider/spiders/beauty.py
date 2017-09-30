# -*- coding: utf-8 -*-
import scrapy


class BeautySpider(scrapy.Spider):
    name = 'beauty'
    allowed_domains = ['beauty.com']
    start_urls = ['http://beauty.com/']

    def parse(self, response):
        pass
