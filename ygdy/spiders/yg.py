import scrapy

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
        table_list = res.xpath('//*[@class="co_content8"]/ul//table')
        for item in table_list:
            href = res.urljoin(item.xpath('./tr//a[last()]/@href').extract_first())
            # 对详情页发起请求
            yield scrapy.Request(
                url=href,
                callback=self.parse_detailpage
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
        item = YgdyItem()
        item['name'] = res.xpath('//*[contains(@class,"bd3l") or contains(@class,"bd3r")]/div[2]/div[1]/h1/font/text()').extract_first()
        item['source'] = res.xpath('//*[@id="Zoom"]//a[starts-with(@href,"magnet:?xt=urn:") or starts-with(@href,"ftp://")]/@href').extract_first()

        if not item['source']:
            return
        yield item
