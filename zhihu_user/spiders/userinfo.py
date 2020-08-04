# -*- coding: utf-8 -*-
import scrapy
import json
from scrapy import Spider,Request
from zhihu_user.items import UserItem
import pymysql
class UserinfoSpider(scrapy.Spider):
    name = 'userinfo'
    allowed_domains = ['www.zhihu.com']
    start_urls = ['http://www.zhihu.com/']
    urls = []

    # 这里把查询的参数单独存储为user_query,user_url存储的为查询用户信息的url地址
    user_url = "https://www.zhihu.com/api/v4/members/{user}?include={include}"
    user_query = "locations,employments,gender,educations,business,voteup_count,thanked_Count,follower_count,following_count,cover_url,following_topic_count,following_question_count,following_favlists_count,following_columns_count,avatar_hue,answer_count,articles_count,pins_count,question_count,columns_count,commercial_question_count,favorite_count,favorited_count,logs_count,marked_answers_count,marked_answers_text,message_thread_token,account_status,is_active,is_bind_phone,is_force_renamed,is_bind_sina,is_privacy_protected,sina_weibo_url,sina_weibo_name,show_sina_weibo,is_blocking,is_blocked,is_following,is_followed,mutual_followees_count,vote_to_count,vote_from_count,thank_to_count,thank_from_count,thanked_count,description,hosted_live_count,participated_live_count,allow_message,industry_category,org_name,org_homepage,badge[?(type=best_answerer)].topics"


    def start_requests(self):
        '''
        这里重写了start_requests方法，分别请求了用户查询的url和关注列表的查询以及粉丝列表信息查询
        :return:
        '''
        db = pymysql.connect(
            host='localhost',
            database='zhihu',
            user='root',
            password='123456',
            port=3306,
            charset='utf8',
            cursorclass=pymysql.cursors.DictCursor,
            use_unicode=True)

        cursor = db.cursor()
        cursor.execute('select url_token from user_info')
        rows = cursor.fetchall()
        for row in rows:
            self.urls.append(row['url_token'])
        db.close()
        for url in self.urls:
            yield Request(self.user_url.format(user=url, include=self.user_query), callback=self.parse_user)

    def parse_user(self, response):
        '''
        因为返回的是json格式的数据，所以这里直接通过json.loads获取结果
        :param response:
        :return:
        '''
        result = json.loads(response.text)
        print(f"result:{result}")
        item = UserItem()
        # 这里循环判断获取的字段是否在自己定义的字段中，然后进行赋值
        for field in item.fields:
            if field in result.keys():
                item[field] = result.get(field)

        # 这里在返回item的同时返回Request请求，继续递归拿关注用户信息的用户获取他们的关注列表
        yield item

    def parse_follows(self, response):
        '''
        用户关注列表的解析，这里返回的也是json数据 这里有两个字段data和page，其中page是分页信息
        :param response:
        :return:
        '''
        results = json.loads(response.text)

        if 'data' in results.keys():
            for result in results.get('data'):
                yield Request(self.user_url.format(user=result.get("url_token"), include=self.user_query),
                              callback=self.parse_user)

        # 这里判断page是否存在并且判断page里的参数is_end判断是否为False，如果为False表示不是最后一页，否则则是最后一页
        if 'page' in results.keys() and results.get('is_end') == False:
            next_page = results.get('paging').get("next")
            # 获取下一页的地址然后通过yield继续返回Request请求，继续请求自己再次获取下页中的信息
            yield Request(next_page, self.parse_follows)

    def parse_followers(self, response):
        '''
        这里其实和关乎列表的处理方法是一样的
        用户粉丝列表的解析，这里返回的也是json数据 这里有两个字段data和page，其中page是分页信息
        :param response:
        :return:
        '''
        results = json.loads(response.text)

        if 'data' in results.keys():
            for result in results.get('data'):
                yield Request(self.user_url.format(user=result.get("url_token"), include=self.user_query),
                              callback=self.parse_user)

        # 这里判断page是否存在并且判断page里的参数is_end判断是否为False，如果为False表示不是最后一页，否则则是最后一页
        if 'page' in results.keys() and results.get('is_end') == False:
            next_page = results.get('paging').get("next")
            # 获取下一页的地址然后通过yield继续返回Request请求，继续请求自己再次获取下页中的信息
            yield Request(next_page, self.parse_followers)
