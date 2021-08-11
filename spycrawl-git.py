# -*- coding: utf-8 -*-
"""
Created on Mon Aug  9 16:39:24 2021

@author: sabya
"""
import requests
import scrapy
from crochet import setup, wait_for
from scrapy.crawler import CrawlerRunner
from bs4 import BeautifulSoup
import os
from urllib.request import urlopen
from urllib.parse import urljoin, urlparse
from urllib.error import URLError, HTTPError
from bs4 import BeautifulSoup, SoupStrainer
import advertools as adv
import random
import json
from flask import Flask, jsonify, redirect, url_for
from flask_restful import Api, Resource, reqparse
from flask import Flask, jsonify, request

app = Flask(__name__)

app.config['JSON_SORT_KEYS'] = False
bw_api = Api(app)

# ============================== Parameter Start ==================================
crawl_get_args = reqparse.RequestParser()
crawl_get_args.add_argument("url", type=str, help="Enter target page url:",required=True)

crawl_get_args.add_argument("Limit", type=int, help="Enter the number of page you want to crawl",required=True)

# ============================== Parameter End ==================================

class scrapy_crawler(Resource):
    def post(self):
        try:
            args = crawl_get_args.parse_args()
            url = args.url
            limit = args.Limit
            my_string = url.rstrip('/')
            #creating robots.txt link to grab website sitemap url
            r_url=my_string+'/robots.txt'
            try:
                robot = adv.robotstxt_to_df(r_url)
                #logger.info(robot)
                rt_sitemap = (robot
                                    [robot['directive'] == 'Sitemap']
                                    ['content'].tolist() or robot
                                    [robot['directive'] == 'sitemap']
                                    ['content'].tolist())
                s_url=rt_sitemap[0]
    
            except:
                s_url=my_string+'/sitemap.xml'
            
            #after getting the website sitemap url we using advertools to get all sitemap pages as a list
            sitemap = adv.sitemap_to_df(s_url)
            sm=sitemap['loc'].values.tolist()
            ul=sm[:limit]  #here the ul is slicing the all page to limited list as per user input
            
            #scrapy spuder starts here..in order to run it in falsk we need crochet setup
            setup()
            class stormbreaker(scrapy.Spider):
                name = 'Thor'
            
                def parse(self, response):
                    res_code = response.status
                    title = response.css('title::text').getall()
                    h1_tag = response.css('h1::text').getall()
                    h1_List = [x for x in h1_tag if str(x) != '\n']
            
                    img_urls = response.xpath('//img/@src').extract()
                    img_List = [x for x in img_urls if str(x) != '']
            
                    ssl_check = response.certificate != None
            
                    yield {'url': response.request.url, 'status_code': res_code, 'title': title, 'h1_text': h1_List,
                           'img_src': img_List, 'ssl': ssl_check}
            
            #temp file name for the save the scrapy result
            digt=random.randint(10000, 100000)
            file='crawl'+str(digt)+'.json'
            
            @wait_for(1000)
            def run_spider():
                SETTINGS = {
                    'USER_AGENT': 'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1)',
                    'FEED_FORMAT': 'json',
                    'FEED_URI': file,
                    'CONCURRENT_ITEMS': 1
                }
                crawler = CrawlerRunner(settings=SETTINGS)
                d = crawler.crawl(stormbreaker,start_urls=ul)
                #print(d)
                return d
            
            
            runn=run_spider()
            
            with open(file) as f:
                data = json.loads(f.read())
                
            if os.path.exists(file):
                os.remove(file)
            else:
                print("The file does not exist") 
                
            return jsonify({"status": "SUCCESS","code":200,"Result":data})
        except:
            return jsonify({"status": "Failed","code":404,"Result":[]})
        
        
bw_api.add_resource(scrapy_crawler, "/scrapy_crawler")

# ========================== App Runing Mode ================================
if __name__ == "__main__":
    app.run(port=5000)
