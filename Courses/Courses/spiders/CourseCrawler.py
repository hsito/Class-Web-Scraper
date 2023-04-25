import scrapy
from scrapy_splash import SplashRequest
from scrapy.selector import Selector
import re
from Courses.items import CoursesItem 
from scrapy.loader import ItemLoader
from scrapy.loader.processors import TakeFirst
from datetime import datetime

class CoursecrawlerSpider(scrapy.Spider):
    name = "CourseCrawler"
    start_urls = ['https://seanet.uncw.edu/TEAL/bwckschd.p_disp_dyn_sched']

    # Splash Lua script to interact with the website
    lua_script = '''
function main(splash, args)
    splash:set_user_agent(args.user_agent)
    assert(splash:go(args.url))
    assert(splash:wait(10))

    -- Set the value for the dropdown with the name 'p_term' to '202410' (Fall 2023)
    splash:runjs([[document.querySelector("[name='p_term']").value = "202410";]])
    assert(splash:wait(10))

    splash:runjs([[document.querySelector('input[type="submit"]').click();]])
    assert(splash:wait(10))
    
        splash:runjs([[document.querySelector("[id='subj_id']").value = "CSC";]])
    assert(splash:wait(10))
    
        splash:runjs([[document.querySelector('input[type="submit"]').click();]])
    assert(splash:wait(10))
    
    

    return {
        html = splash:html(),
        url = splash:url(),
    }
end
'''


    def start_requests(self):
        for url in self.start_urls:
            yield SplashRequest(url, self.parse, endpoint='execute',
                                args={'lua_source': self.lua_script, 'user_agent': 'Mozilla/5.0', 'timeout': 90, 'wait': 5})

    def parse(self, response):
        html = response.data['html']
        selector = Selector(text=html)
        tableRows = selector.css('table.datadisplaytable:nth-child(6) > tbody:nth-child(2) > tr')


        # print('tr')
        # print(tableRows)
        # print('length of table rows')
        # print(len(tableRows))
        # table.datadisplaytable: nth - child(6) > tbody:nth - child(2) > tr: nth - child(154) > td:nth - child(
        #     1) > table: nth - child(20) > tbody:nth - child(2) > tr: nth - child(2) > td:nth - child(
        #     2) > abbr: nth - child(1)


        for i in range(0, len(tableRows)-1, 2):
            loader = ItemLoader(item=CoursesItem())
            #first table is the course info, second table is the course description
            course_table = tableRows[i]
            course_description_table = tableRows[i + 1]
            time = course_description_table.css("td > table > tbody > tr:nth-child(2) > td:nth-child(2)::text").get()
            days = course_description_table.css("td > table > tbody > tr:nth-child(2) > td:nth-child(3)::text").get()
            professor = course_description_table.css("td > table > tbody > tr:nth-child(2) > td:nth-child(7)::text").get()



            if professor is None:
                continue


            professor = professor.strip()
            professor = professor.split()
            print('Professor List of Names ')
            print(professor)


            if len(professor) == 3:
                loader.add_value('professorFirstName', professor[0])
                loader.add_value('professorLastName', professor[1])
            elif len(professor) == 4:
                loader.add_value('professorFirstName', professor[0])
                loader.add_value('professorLastName', professor[2])






            # if there are no days then we will not count this course
            if days is None or days == "" or days == " ":
                continue

            if time is None:
                continue
            start_time_str, end_time_str = time.split(" - ")

            start_time = datetime.strptime(start_time_str.strip(), "%I:%M %p")
            end_time = datetime.strptime(end_time_str.strip(), "%I:%M %p")

            # Convert to military (24-hour) format
            start_time_military = start_time.strftime("%H%M")
            end_time_military = end_time.strftime("%H%M")

     

            # #convert to string
            # start_time_military = str(start_time_military)
            # end_time_military = str(end_time_military)
            
            course = course_table.css('th a::text').get()

            if not course:
                continue

            course = course.strip()
            course_tokens = re.split(r'\s+-\s+', course)
            if len(course_tokens) == 4:
                subject = course_tokens[2]
                subject, classNum = subject.split(" ")

                loader.default_output_processor = TakeFirst()
                loader.add_value('className', course_tokens[0])
                loader.add_value('CRN', course_tokens[1])
                loader.add_value('subject', subject)
                loader.add_value('classNum', classNum)
                loader.add_value('section', course_tokens[3])
                loader.add_value("startTime", start_time_military)
                loader.add_value('endTime', end_time_military)
                loader.add_value('days', days)



            elif len(course_tokens) == 5:
                subject = course_tokens[3]
                subject, classNum = subject.split(" ")
                loader.default_output_processor = TakeFirst()
                loader.add_value('className', course_tokens[1])
                loader.add_value('CRN', course_tokens[2])
                loader.add_value('subject', subject)
                loader.add_value('classNum', classNum)
                loader.add_value('section', course_tokens[4])
                loader.add_value("startTime", start_time_military)
                loader.add_value('endTime', end_time_military)
                loader.add_value('days', days)


            yield loader.load_item()
    #         print(f"Requesting course description for: {loaded_item}")
    #         # Get the 'View Catalog Entry' URL and make a request to scrape the course description
    #         view_catalog_url = 'https://seanet.uncw.edu' + course_description_table.css('td a::attr(href)').get()
    #         print(f"View Catalog URL: {view_catalog_url}")
    #         yield SplashRequest(view_catalog_url, self.parse_course_description, endpoint='execute',
    #                             args={'lua_source': self.lua_script, 'user_agent': 'Mozilla/5.0', 'wait' : 10, 'timeout': 90'},
    #                             meta={'item': loaded_item})


    # def parse_course_description(self, response):
    #     item = response.meta['item']
    #     html = response.data['html']
    #     selector = Selector(text=html)
    
    #     course_description_element = selector.css('td.ntdefault')
    
    #     if course_description_element:
    #         description_text = course_description_element[0].xpath('text()').get()
    
    #         if description_text:
    #             print(f"Course description found: {description_text.strip()}")
    #             item['courseDescription'] = description_text.strip()
    #         else:
    #             print("No course description found")
    #             item['courseDescription'] = ''
    #     else:
    #         print("No course description found")
    #         item['courseDescription'] = ''
    
        # yield item