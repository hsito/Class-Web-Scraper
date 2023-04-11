import scrapy
from scrapy_splash import SplashRequest
from scrapy import FormRequest
from scrapy.selector import Selector
import re
from Courses.items import CoursesItem
from scrapy.loader import ItemLoader
from scrapy.loader.processors import TakeFirst

class CoursecrawlerSpider(scrapy.Spider):
    name = "CourseCrawler"
    start_urls = ['https://seanet.uncw.edu/TEAL/bwckschd.p_disp_dyn_sched']

    # Splash Lua script to interact with the website
    lua_script = '''
function main(splash, args)
    splash:set_user_agent(args.user_agent)
    assert(splash:go(args.url))
    assert(splash:wait(5))

    -- Set the value for the dropdown with the name 'p_term' to '202410' (Fall 2023)
    splash:runjs([[document.querySelector("[name='p_term']").value = "202410";]])
    assert(splash:wait(1))

    splash:runjs([[document.querySelector('input[type="submit"]').click();]])
    assert(splash:wait(1))
    
        splash:runjs([[document.querySelector("[id='subj_id']").value = "CSC";]])
    assert(splash:wait(1))
    
        splash:runjs([[document.querySelector('input[type="submit"]').click();]])
    assert(splash:wait(3))
    
    

    return {
        html = splash:html(),
        url = splash:url(),
    }
end
'''


    def start_requests(self):
        for url in self.start_urls:
            yield SplashRequest(url, self.parse, endpoint='execute',
                                args={'lua_source': self.lua_script, 'user_agent': 'Mozilla/5.0'})

    def parse(self, response):

        html = response.data['html']
        selector = Selector(text=html)
        courses = selector.css('th a::text').getall()

        for course in courses:
            course = course.strip()
            course_tokens = re.split(r'\s+-\s+', course)

            loader = ItemLoader(item=CoursesItem())
            loader.default_output_processor = TakeFirst()

            loader.add_value('className', course_tokens[0])
            loader.add_value('CRN', course_tokens[1])
            loader.add_value('subject', course_tokens[2])
            loader.add_value('section', course_tokens[3])

            loaded_item = loader.load_item()

            yield loaded_item

