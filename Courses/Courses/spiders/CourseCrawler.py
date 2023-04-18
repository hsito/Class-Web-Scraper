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
    assert(splash:wait(5))

    splash:runjs([[document.querySelector('input[type="submit"]').click();]])
    assert(splash:wait(5))
    
        splash:runjs([[document.querySelector("[id='subj_id']").value = "CSC";]])
    assert(splash:wait(5))
    
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
        tableRows = selector.css('table.datadisplaytable:nth-child(6) > tbody:nth-child(2) > tr')


        print('tr')
        print(tableRows)
        print('length of table rows')
        print(len(tableRows))

        for i in range(0, len(tableRows)-1, 2):

            #first table is the course info, second table is the course description
            course_table = tableRows[i]
            course_description_table = tableRows[i + 1]

            # Get the course name, CRN, subject, and section


            course = course_table.css('th a::text').get()

            if not course:
                continue

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

            print(f"Requesting course description for: {loaded_item}")
            # Get the 'View Catalog Entry' URL and make a request to scrape the course description
            view_catalog_url = 'https://seanet.uncw.edu' + course_description_table.css('td a::attr(href)').get()
            print(f"View Catalog URL: {view_catalog_url}")
            yield SplashRequest(view_catalog_url, self.parse_course_description, endpoint='execute',
                                args={'lua_source': self.lua_script, 'user_agent': 'Mozilla/5.0'},
                                meta={'item': loaded_item})

    def parse_course_description(self, response):
        item = response.meta['item']
        html = response.data['html']
        selector = Selector(text=html)

        course_description_element = selector.css('td.ntdefault')

        if course_description_element:
            description_text = course_description_element[0].xpath('text()').get()

            if description_text:
                print(f"Course description found: {description_text.strip()}")
                item['courseDescription'] = description_text.strip()
            else:
                print("No course description found")
                item['courseDescription'] = ''
        else:
            print("No course description found")
            item['courseDescription'] = ''

        yield item