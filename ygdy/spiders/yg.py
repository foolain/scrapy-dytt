import requests
import scrapy
import re

from ygdy.items import YgdyItem

class YgSpider(scrapy.Spider):
    name = 'yg'
    allowed_domains = ['www.ygdy8.com']
    start_urls = ['https://www.ygdy8.com/html/gndy/dyzz/index.html']

    # 1.解析最新电影页面，提取 相关栏目分类
    def parse(self, res):
        # 解析相关栏目分类
        nodes = res.xpath('//*[@class="bd3l"]/div[1]/div[2]//table')

        for i in nodes:
            name = i.xpath('.//a/text()').extract_first()
            if name:
                link = res.urljoin(i.xpath('.//a/@href').extract_first())
            else:
                continue
            # 对列表页发起请求
            yield scrapy.Request(
                url=link,
                callback=self.parse_listpage
            )

    # 2.解析电影列表页面，提取详情页面链接
    def parse_listpage(self, res):
        cat = res.xpath('//*[@class="bd2"]/div[@class="path"]/ul/a[last()]/text()').extract_first()
        table_list = res.xpath('//*[@class="co_content8"]/ul//table')
        tmp = {}
        tmp['cat']= cat

        for item in table_list:
            href = res.urljoin(item.xpath('./tr//a[last()]/@href').extract_first())
            # 对详情页发起请求
            yield scrapy.Request(
                url=href,
                callback=self.parse_detailpage,
                meta={'tmp': tmp}
            )
        # 获取下一页
        next_link = res.xpath('//*[@class="co_content8"]/div//a[contains(text(),"下一页")]/@href').extract_first()

        if not next_link:
            return None

        next_page = res.urljoin(next_link)

        yield scrapy.Request(
            url=next_page,
            callback=self.parse_listpage
        )

    # 3.解析电影详情页，提取电影下载地址……
    def parse_detailpage(self, res):
        tmp = res.meta['tmp']
        item = YgdyItem()
        item['cat'] = tmp['cat']
        item['url'] = res.url
        item['title'] = res.xpath('//*[contains(@class,"bd3l") or contains(@class,"bd3r")]/div[2]/div[1]/h1/font/text()').extract_first()
        item['cover'] = res.xpath('//*[@id="Zoom"]//img[1]/@src').extract_first()
        item['source'] = res.xpath('//*[@id="Zoom"]//a[starts-with(@href,"magnet:?xt=urn:") or starts-with(@href,"ftp://")]/@href').extract_first()

        # 如果资源地址找不到，直接返回
        if not item['source']:
            return

        # 提取详情页面电影信息
        zoom_el = res.xpath('//*[@id="Zoom"]')[0].extract()
        film_info = {}
        film_info['trans_name'] = re.search(r'◎译　　名(.*?)<br>', zoom_el, re.S)
        if film_info['trans_name'] is None:
            film_info['trans_name'] = re.search(r'◎中文　名(.*?)<br>', zoom_el, re.S)

        film_info['name'] = re.search(r'◎片　　名(.*?)<br>', zoom_el, re.S)
        film_info['year'] = re.search(r'◎年　　代(.*?)<br>', zoom_el, re.S)
        film_info['country'] = re.search(r'◎国　　家(.*?)<br>', zoom_el, re.S)
        if film_info['country'] is None:
            film_info['country'] = re.search(r'◎产　　地(.*?)<br>', zoom_el, re.S)

        film_info['type'] = re.search(r'◎类　　别(.*?)<br>', zoom_el, re.S)
        film_info['language'] = re.search(r'◎语　　言(.*?)<br>', zoom_el, re.S)
        film_info['subtitles'] = re.search(r'◎字　　幕(.*?)<br>', zoom_el, re.S)
        film_info['length'] = re.search(r'◎片　　长(.*?)<br>', zoom_el, re.S)
        film_info['director'] = re.search(r'◎导　　演(.*?)<br>', zoom_el, re.S)
        film_info['actor'] = re.search(r'◎演　　员(.*?)◎', zoom_el, re.S)
        if film_info['actor'] is None:
            film_info['actor'] = re.search(r'◎主　　演(.*?)<br>', zoom_el, re.S)

        film_info['introduce'] = re.search(r'◎简　　介(.*?)<a ', zoom_el, re.S)

        for key, value in film_info.items():
            if value is not None:
                item[key] = value.group(1).strip()
            else:
                item[key] = 'No Value'
        if item['actor'] != 'No Value':
            lists = item['actor'].split('<br>')
            for index, value in enumerate(lists):
                lists[index] = value.strip()
                if index > 9:
                    lists = lists[: 10]
                    break
            item['actor'] = lists

        if len(item['introduce']) > 150:
            item['introduce'] = item['introduce'][:150]

        yield item
