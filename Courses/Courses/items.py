# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class CoursesItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    className = scrapy.Field()
    CRN = scrapy.Field()
    subject = scrapy.Field()
    classNum = scrapy.Field()
    section = scrapy.Field()

