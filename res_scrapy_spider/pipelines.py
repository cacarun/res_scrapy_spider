# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html


# class ResScrapySpiderPipeline(object):
#
#     def process_item(self, item, spider):
#         # if item:
#         #     image_urls = item['image_urls']
#         #     if len(image_urls) > 0:
#         #         print 'pipe image_urls...'
#         return item

import scrapy
from scrapy.pipelines.images import ImagesPipeline
from scrapy.exceptions import DropItem

import re


class MyImagesPipeline(ImagesPipeline):

    CONVERTED_ORIGINAL = re.compile('^full/[0-9,a-f]+.jpg$')

    def get_media_requests(self, item, info):
        for image_url in item['image_urls']:
            image_url_suffix = image_url.split('/')[-1]
            yield scrapy.Request(image_url, meta={'topic_id': item['topic_id'], 'image_url_suffix': image_url_suffix})

    def item_completed(self, results, item, info):
        image_paths = [x['path'] for ok, x in results if ok]
        if not image_paths:
            raise DropItem("Item contains no images")
        item['image_paths'] = image_paths
        return item

    # this is where the image is extracted from the HTTP response
    def get_images(self, response, request, info):
        for key, image, buf, in super(MyImagesPipeline, self).get_images(response, request, info):
            if self.CONVERTED_ORIGINAL.match(key):
                key = self.change_name(key, response)
            yield key, image, buf

    def change_name(self, key, response):
        topic_id = response.meta['topic_id']
        image_url_suffix = response.meta['image_url_suffix']
        return "%s_%s" % (topic_id, image_url_suffix)
